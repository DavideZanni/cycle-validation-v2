# Cycle Validation v2 — Design del refactoring

**Data:** 2026-11-13
**Stato:** approvato il 2026-11-13, con una modifica di perimetro: `ingestion_v2` è fuori ambito
**Sostituisce:** il design del 2026-11-12 (tolto, resta nella history di git), scritto prima di avere la documentazione del sistema attuale.

**Fonti usate:** `docs/doc_lavoro/DOCUMENTAZIONE_TECNICA_cycle_validation.md` (sistema attuale). Non ho accesso al codice del sistema attuale: dove il design dipende da dettagli che la guida non riporta, il punto è marcato **da verificare** ed è raccolto nel §17.

**Perimetro:** questo lavoro riguarda solo la validazione dei cicli. `ingestion_v2` viene sviluppato al lavoro, separatamente, e non entra in questo progetto: la validazione non ne legge i file, non ne importa il codice e non ne presuppone il formato.

---

## 1. Obiettivo

Rifare il backend di validazione dei cicli di riparazione mantenendo ciò che fa oggi per i tre percorsi (MOS, DR, EJ200) e migliorando quattro cose, in quest'ordine:

1. **Affidabilità.** Ogni esito è sostenuto da un'evidenza verificabile (documento, pagina, citazione). Ciò che si può decidere con una ricerca esatta lo decide il codice, non un modello.
2. **Velocità.** Meno chiamate al modello, tutte in parallelo.
3. **Costo.** Meno chiamate, modello Haiku, ricerca esatta al posto di quella semantica, lettura a paragrafo (GRASP).
4. **Manutenibilità.** Una sola pipeline con tre profili, al posto di due percorsi di codice separati; test su tutti i profili.

Il risultato per l'utente resta una tabella: per ogni fonte e per ogni campo di ogni operazione, un esito tra corretto, warning, errato o non applicabile, con motivazione e fonte.

## 2. Cosa cambia rispetto a oggi

| Aspetto | Sistema attuale | v2 |
|---|---|---|
| Percorsi | Due pipeline distinte: civile (`main_validation.py`) ed EJ200 (`src/ej200/`) | Una pipeline, tre profili (MOS, DR, EJ200) che compongono gli stessi mattoni |
| Conoscenza | Indice OpenSearch civile, indice OpenSearch EJ200, embedding Bedrock, JSON strutturati su S3, chiamati direttamente dal codice dei controlli | Le stesse sorgenti, dietro un'unica interfaccia (`KnowledgeBase`). I controlli non sanno da dove arriva la conoscenza; in locale e nei test arriva da una cartella di file |
| Recupero del contesto | Civile: ricerca semantica/ibrida/keyword top-k. EJ200: documenti citati interi, troncati a 150.000 caratteri | Il codice individua documento e righe del task con una ricerca esatta; l'agente legge solo i paragrafi che servono |
| Controlli per operazione | Quattro casi d'uso LLM (`operations`, `task_codes`, `TM`, `SP`) più un consolidamento LLM | Esistenza e applicabilità decise dal codice; un solo giudizio del modello per operazione; consolidamento a codice |
| Evidenza | Testo di feedback | Documento, versione, pagina e citazione letterale verificata dal codice |
| Verifica dell'estrazione | Solo EJ200 (confronto con il PDF) | Tutti i profili |
| Esito | Stringhe con prefisso (`No errors found.`, `Error found:`, `Warning:`, `N/A`) | Esito tipizzato; un adattatore produce le stesse stringhe per il frontend |
| Test | Solo EJ200, nessun end-to-end civile | Tutti i profili, golden set, confronto in ombra con il sistema attuale |

**Chiamate al modello per un ciclo con N operazioni** (stima dalla guida): oggi circa `4N + 3` (estrazione, fonti, quattro controlli per operazione, consolidamento), ognuna con il proprio contesto RAG. In v2 al massimo `N + 1`: una per l'estrazione e una per operazione, e solo per le operazioni che hanno qualcosa da confrontare con un manuale.

## 3. Principi

1. **Il codice trova il dove, l'agente verifica il cosa, il codice decide l'esito.** La knowledge base dice in quale manuale e in quali righe sta un task. L'agente confronta la descrizione dell'operazione con quel testo. L'esito finale lo assegna il codice, dopo aver verificato la citazione.
2. **Un controllo fallito non è un errore di contenuto.** Guasto tecnico, budget esaurito o citazione non verificata producono `WARNING` e una voce diagnostica, mai `ERRATO`. È la regola che oggi vale solo per EJ200.
3. **Assente non significa sbagliato.** Un riferimento non trovato nella conoscenza disponibile può mancare solo perché il documento non è stato caricato. Produce `WARNING`, salvo dove esiste un sistema di riferimento autorevole (Redshift per le macchine attive).
4. **`ERRATO` richiede una prova.** Una contraddizione esplicita con citazione verificata, oppure un controllo esatto su un sistema autorevole.
5. **Ogni run è riproducibile.** Il report registra la versione della conoscenza usata, l'hash del PDF, il modello e la versione dei prompt.
6. **Il frontend non cambia.** Stesse rotte, stessa forma del payload, stessi prefissi nei feedback.

## 4. Architettura

```
PDF del ciclo + profilo (mos | dr | ej200) + selettori (DR: serial number, condition)
   │
[1 ingest]      PDF → pagine (testo, celle di tabella)            deterministico
[2 extract]     pagine → Cycle (testata, fonti, operazioni)       1 chiamata LLM, oppure parser di layout
[3 integrity]   ogni valore estratto deve comparire nel PDF       deterministico
[4 resolve]     riferimenti del ciclo → voci della conoscenza     deterministico
[5 check]       controlli del profilo, in parallelo
                  ├─ controlli a codice                           millisecondi, 0 token
                  └─ giudizio per operazione                      1 sessione agente ciascuna
[6 consolidate] esiti, verifica citazioni, conteggi               deterministico
[7 report]      report.json, report.md, payload compatibile
```

Gli stadi comunicano con modelli pydantic. Ogni stadio lascia il proprio output nella cartella del run.

### 4.1 Profili

Un profilo è una composizione dichiarativa: quale estrattore, quale risolutore dei riferimenti, quali controlli, quali limiti sul file.

| | MOS | DR | EJ200 |
|---|---|---|---|
| Selettori | nessuno | serial number, una o più repair condition | nessuno |
| Limiti sul file | PDF non vuoto, ≥ 100 caratteri | come MOS | intestazione `%PDF-`, ≤ 20 MB, ≤ 60 pagine, ≥ 100 caratteri, testo che identifica EJ200 |
| Estrazione | ciclo MOS | ciclo MOS + record DR | layout PVRM320, unione delle operazioni ripetute tra pagine, righe "note" escluse |
| Risoluzione | fonti (manuale + task) sull'indice civile | recommendation per serial number e condition, poi riferimenti e task | codici RN, EF, RDR sul catalogo delle pubblicazioni |
| Controlli | fonti, task code, targa, scheda, operazione | recommendation (bloccante), poi come MOS | fonti/pubblicazioni, codici data-module, targa, operazione; scheda non verificata |

I controlli condivisi sono lo stesso codice: la targa macchina si verifica allo stesso modo nei tre profili, come già oggi EJ200 riusa il controllo civile.

## 5. Modello dati

### 5.1 Ciclo estratto

Ricalca il payload attuale, così l'adattatore verso il frontend è diretto.

- **`Cycle`**: `cycle_code`, `cycle_description`, `engine_model`, `operation_type`, `repair_code`, `sources: list[Source]`, `operations: list[Operation]`, più per DR `dr_record` (i dati DR letti dal ciclo).
- **`Source`**: `repair_code`, `manual` (o riferimento DR), `task`.
- **`Operation`**: `operation_number`, `repair_code`, `operation_description`, `machine_tag` (oggi `targaCResp`), `task_codes: list[str]` (oggi `taskCodeCited`), `process_sheet` (oggi `scheda`, oggetto o assente).
- Ogni valore estratto porta la pagina di provenienza.

La forma esatta di `scheda` e dei campi che variano per tipo di ciclo è **da verificare** su `src/template/cycle_template.py`.

### 5.2 Esito di un controllo

**`CheckResult`**:

| Campo | Contenuto |
|---|---|
| `check` | `source`, `dr_recommendation`, `operation_description`, `task_code`, `machine_tag`, `process_sheet`, `extraction_integrity` |
| `target` | a cosa si riferisce: il ciclo, la fonte n, l'operazione n |
| `verdict` | `CORRETTO`, `WARNING`, `ERRATO`, `NON_APPLICABILE` |
| `reason` | codice chiuso (vedi sotto) |
| `rationale` | una o due frasi in italiano |
| `evidence` | lista di `{document_key, version, page, line, quote}` |
| `decided_by` | `code` oppure `agent` |
| `usage` | token, costo, durata, turni (zero per i controlli a codice) |

Aggiungo `NON_APPLICABILE` ai tre esiti concordati: il sistema attuale lo usa già (`N/A`) per i campi assenti e per le schede EJ200, e lo esclude dai conteggi.

**Codici `reason`:**

| Esito | Codici |
|---|---|
| `CORRETTO` | `VERIFICATO` |
| `ERRATO` | `CONTRADDIZIONE` (agente, con citazione), `MACCHINA_NON_ATTIVA` (Redshift), `DR_NON_APPLICABILE` (`Accept as is` o `Reject`), `DR_NESSUNA_CORRISPONDENZA` |
| `WARNING` | `EVIDENZA_NON_TROVATA`, `FONTE_ASSENTE`, `VERSIONE_DIVERSA`, `PUBBLICAZIONE_PARZIALE`, `RIFERIMENTO_AMBIGUO`, `CITAZIONE_NON_VERIFICATA`, `ESTRAZIONE_NON_CONFERMATA`, `BUDGET_ESAURITO`, `ERRORE_TECNICO`, `BLOCCATO_A_MONTE` |
| `NON_APPLICABILE` | `CAMPO_ASSENTE`, `ESCLUSO_DA_REGOLA` (schede `SWJ`, `SSS`, `SPS`), `NON_VERIFICATO_PER_PROFILO` (schede EJ200) |

### 5.3 Report

- **`report.json`**: metadati del run (PDF e hash, profilo, selettori, versione della conoscenza, modello, versione dei prompt), ciclo estratto, lista di `CheckResult`, conteggi, tempi per stadio, consumi, diagnostica.
- **`report.md`**: riepilogo e due tabelle, fonti e operazioni. Nella tabella delle operazioni una riga per operazione e una colonna per controllo, come nel frontend attuale; sotto, il dettaglio con motivazione e fonte.
- **`payload.json`**: il payload nel formato attuale (`sources[].sourceFeedback`, `operations[].operationFeedback`, `targaCRespFeedback`, `taskCodeFeedback`, `schedaFeedback`, `cycle_errors_count`, `cycle_errors_count_perc`, `profile`, `_pipeline_errors`).

Traduzione verso i feedback attuali: `CORRETTO` → `No errors found.`; `ERRATO` → `Error found: <motivazione>`; `WARNING` → `Warning: <motivazione>`; `NON_APPLICABILE` → `N/A` seguito dal motivo. `cycle_errors_count_perc` resta un rapporto tra 0 e 1. La regola di conteggio civile è **da verificare** su `main_validation.py` (la guida avverte che differisce da quella EJ200).

## 6. Knowledge base

### 6.1 Una porta, più sorgenti

La validazione definisce **la propria** interfaccia verso la conoscenza, `KnowledgeBase`, con le sole domande che i controlli fanno:

| Domanda | Usata da |
|---|---|
| Esiste questo manuale? | `source` |
| Dove sta questo task in questo manuale? (documento, versione, righe, pagine) | `source`, `task_code`, `operation_description` |
| Esiste questa targa nei dati TM? | `machine_tag` |
| Esiste questa scheda nella tabella SP, e per quali famiglie di motore? | `process_sheet` |
| Quali recommendation DR ha questo serial number? | `dr_recommendation` (Fase 4) |
| A quale pubblicazione corrisponde questo codice RN, EF, RDR? | profilo EJ200 (Fase 5) |

Controlli, agente e report dipendono solo da questa porta. Chi la alimenta è un dettaglio di un adattatore: cambiare sorgente non tocca il resto.

### 6.2 Cartella locale

L'implementazione di riferimento legge una cartella di file in un formato definito da questo progetto. Serve alla CLI, ai test e al golden set, e dà all'agente ciò di cui ha bisogno: testo a righe.

```
knowledge/
├── manifest.json          versione, elenco documenti (chiave, alias, versione, file)
├── documents/<chiave>.md  una riga per riga di testo; <!-- page N --> a ogni cambio pagina
├── tasks.json             manuale, task code → riga iniziale e finale
├── machine_tags.json      targhe e funzione
└── process_sheets.json    schede, edizione, trattamento, famiglie di motore
```

La citazione dell'agente (file e riga) viene ricondotta dal codice a documento, versione e pagina. La `version` del manifest entra nel report.

### 6.3 Sorgenti attuali (Fase 2)

In azienda la conoscenza resta dov'è oggi. Gli adattatori implementano la stessa porta:

| Dato | Sorgente attuale | Adattatore |
|---|---|---|
| Targhe (TM), schede (SP), recommendation (DR) | JSON strutturati su S3 | lettura e indicizzazione per codice |
| Testo dei manuali civili | indice OpenSearch civile | ricerca **esatta** per manuale e task sui metadati; il testo trovato viene riscritto a righe in una cartella di lavoro |
| Pubblicazioni EJ200 | catalogo S3 (`EJ200_CATALOG_KEY`) e indice EJ200 | come oggi: risoluzione del codice, recupero esatto del documento |

Se i metadati dell'indice civile consentano la ricerca esatta per manuale e task è **da verificare** sulla mappatura dell'indice. Se non la consentono, l'adattatore ripiega sulla ricerca attuale (ibrida, top-k) restando dietro la porta: il resto del design non cambia, cambia solo il risparmio su quel passo.

Gli adattatori richiedono informazioni che stanno al lavoro: forma dei JSON su S3 e mappatura degli indici (§17).

### 6.4 Riferimento assente o sorgente non raggiungibile

| Situazione | Effetto sull'esito |
|---|---|
| Voce trovata | nessuno |
| Voce non trovata | `WARNING` / `FONTE_ASSENTE` |
| Sorgente non raggiungibile durante un controllo | `WARNING` / `ERRORE_TECNICO` e voce in `_pipeline_errors` |
| Knowledge base non caricabile all'avvio del run | run fallito |

## 7. Controlli

| Controllo | Sostituisce | Profili | Chi decide | Logica |
|---|---|---|---|---|
| `extraction_integrity` | confronto col PDF (oggi solo EJ200) | tutti | codice | Numeri operazione, targhe, task code e schede estratti devono comparire nel testo del PDF. Discrepanza → `WARNING` / `ESTRAZIONE_NON_CONFERMATA` sul campo interessato |
| `source` | `source_validation` | tutti | codice | Manuale e task esistono nella conoscenza. EJ200: codice risolto nel catalogo, pubblicazione più recente; issue diversa o ignota, pubblicazione parziale, documento non pubblicato, RDR ambiguo → `WARNING` |
| `dr_recommendation` | logica DR | DR | codice | Serial number → recommendation; più corrispondenze → intersezione delle condition. Nessuna corrispondenza, selettori mancanti o dati DR non caricabili → blocco. Procedura `Accept as is` o `Reject` → `ERRATO` e blocco |
| `task_code` | `task_codes_validation`, `ej200_task_codes_validation` | tutti | codice | Civile: il task code citato esiste nell'indice del manuale citato. EJ200: il codice data-module compare nel testo dei documenti citati |
| `machine_tag` | `TM_validation` + Redshift | tutti | codice | Targa presente nei dati TM; macchina attiva su Redshift (`work_center_usage_cd = 'TO'`). Non attiva → `ERRATO` / `MACCHINA_NON_ATTIVA` |
| `process_sheet` | `SP_validation` | MOS, DR | codice | Prefissi `SWJ`, `SSS`, `SPS` → `NON_APPLICABILE`. Scheda presente nella tabella SP, applicabile alla famiglia del motore (GENX, LEAP). EJ200 → `NON_APPLICABILE` / `NON_VERIFICATO_PER_PROFILO` |
| `operation_description` | `operations_validation`, `ej200_operations_validation` | tutti | agente + codice | La descrizione dell'operazione è coerente con il testo del task o dei documenti citati. Vedi §8 |

I casi d'uso attuali `task_codes_validation`, `TM_validation` e `SP_validation` sono LLM. Dalla guida non risulta se, oltre a esistenza e applicabilità, giudichino anche la **pertinenza** rispetto all'operazione (per esempio: la funzione della macchina è adatta a questa lavorazione). Se sì, quel giudizio entra nella sessione per operazione del §8 come aspetto aggiuntivo, senza altre chiamate. **Da verificare** sui prompt in `src/prompts/use_cases/`.

**Blocchi.** Quando un controllo bloccante fallisce (DR senza recommendation; EJ200 senza nessuna fonte disponibile), i controlli a valle non si eseguono e le loro righe escono `WARNING` / `BLOCCATO_A_MONTE`. Il conteggio degli errori resta quello reale, e il report espone uno stato del ciclo (`completo`, `bloccato`, `parziale`) che il frontend può usare al posto della deduzione attuale.

## 8. Il giudizio per operazione

### 8.1 Una sessione per operazione

Per ogni operazione che ha un riferimento risolto parte una sessione Haiku isolata. Le sessioni girano in parallelo con concorrenza limitata. Un guasto resta confinato alla sua operazione.

Il messaggio contiene: la descrizione dell'operazione, il task code, e i **fatti già risolti dal codice** (la riga TM della targa, la riga SP della scheda, il modello del motore). L'agente non deve cercarli.

### 8.2 Contesto: in linea oppure in ricerca

Il codice sa già dove guardare: l'indice dà le pagine del task. Due modalità, scelte dal codice in base alla dimensione:

- **In linea**: se il testo individuato è breve (soglia configurabile, proposta 150 righe) lo si inserisce nel messaggio con i numeri di riga. Nessun tool, un solo turno. È il caso più veloce e più economico.
- **In ricerca (GRASP)**: se il testo è lungo, o per EJ200 dove i documenti citati arrivano a 150.000 caratteri, l'agente riceve l'elenco dei file ammessi e usa `Grep` e `Read`. Un hook `PreToolUse` rifiuta ogni `Read` senza `limit` o con `limit` oltre soglia, e ogni accesso fuori dai file ammessi **per quella sessione**. Niente troncamento del contesto: l'agente cerca ciò che gli serve.

### 8.3 Output e regole

L'agente restituisce, per ogni aspetto valutato, un giudizio (`coerente`, `contraddetto`, `non verificabile`), una motivazione breve e le citazioni (`file`, `riga`, testo letterale).

Il codice poi:

1. verifica ogni citazione riaprendo il file alla riga indicata;
2. `contraddetto` con citazione verificata → `ERRATO` / `CONTRADDIZIONE`;
3. `coerente` con citazione verificata → `CORRETTO`;
4. `non verificabile`, oppure nessuna citazione verificata → `WARNING`.

È la semantica che oggi vale per EJ200 (contraddizione esplicita → errore; informazione assente o non verificabile → warning), estesa a tutti i profili.

### 8.4 Harness

Claude Agent SDK su Bedrock, verificato sulla versione 0.2.180: tool limitati a `Read` e `Grep` (`Glob` non serve: i file ammessi sono già nel messaggio); `setting_sources=[]` per isolare la sessione da impostazioni e plugin dell'utente; output strutturato con schema JSON; `max_turns` e `effort` configurabili; prompt di sistema identico per tutte le sessioni, così il prompt caching lo riusa. L'SDK sta dietro un'interfaccia: tutto il resto si testa offline.

Ogni sessione avvia un processo, con qualche secondo di avvio. In parallelo pesa poco. Se le misure sul golden set mostrano che per le sessioni "in linea" (senza tool) quel costo conta, si aggiunge un secondo adattatore che chiama Bedrock direttamente, dietro la stessa interfaccia.

## 9. Estrazione del ciclo

Oggi: `pdfplumber` + caso d'uso LLM `cycle_extraction` (e `ej200_cycle_extraction`).

In v2 l'estrazione sta dietro l'interfaccia `CycleExtractor`, con due implementazioni possibili per profilo:

- **LLM con output strutturato** (punto di partenza, equivalente a oggi): una chiamata senza tool, con lo schema di `Cycle`.
- **Parser di layout**: i cicli sono moduli tabellari (PVRM320 per EJ200). Se il layout è stabile, le celle di tabella lette dal PDF bastano e l'estrazione costa zero token ed è ripetibile. Si decide sui PDF di esempio.

In entrambi i casi segue `extraction_integrity` (§7).

Per la lettura del PDF: PDFium per il testo. `pdfplumber` per celle e geometria entra insieme al primo parser di layout, non prima.

## 10. Servizi esterni

Ogni servizio sta dietro un'interfaccia con un'implementazione reale e una per i test.

| Servizio | Uso | Implementazioni |
|---|---|---|
| Bedrock | estrazione, giudizio per operazione | Claude Agent SDK; finta per i test |
| Macchine attive | controllo `machine_tag` | Redshift (query attuale); file locale; finta |
| Knowledge base | tutti i controlli | cartella locale (§6.2); adattatori sulle sorgenti attuali (§6.3); in memoria per i test |
| Sessioni e feedback | solo livello API | S3 (stesse chiavi di oggi) |

Regione, profilo di inferenza Bedrock e id esatto del modello Haiku sono **da verificare** nell'account aziendale.

## 11. Livello API

Il nucleo è una libreria con una CLI. Il servizio FastAPI è un involucro sottile sopra la libreria e mantiene il contratto attuale:

- stesse rotte civili ed EJ200, stessi modelli di richiesta, stessi codici HTTP;
- stesso involucro di risposta (`state`, `result.payload`, `error`, `error_info`; per EJ200 `job_id` e `finished_at`);
- stessi middleware di autenticazione e autorizzazione dell'SDK condiviso;
- stesse chiavi S3 per sessioni e feedback.

Due correzioni a difetti che la guida segnala: il feedback civile oggi risponde con successo anche se la scrittura su S3 fallisce, e usa un file condiviso in lettura-modifica-scrittura. In v2 un oggetto per feedback (come EJ200) e risposta d'errore se la scrittura fallisce.

Resta sincrono, come oggi. Con le sessioni in parallelo il tempo per ciclo scende; il passaggio a job asincroni non serve in questa fase.

## 12. Gestione degli errori

| Situazione | Comportamento |
|---|---|
| File non PDF, vuoto, oltre i limiti del profilo, senza testo | Run rifiutato, stessi codici HTTP di oggi (400, 413, 415, 422) |
| Estrazione senza operazioni | Run fallito |
| Knowledge base assente o non valida all'avvio | Run fallito (503 a livello API) |
| Selettori DR non validi (`is_dr=false` con selettori, o mancanti con `is_dr=true`) | Richiesta rifiutata |
| Controllo bloccante fallito | Stato del ciclo `bloccato`, righe a valle `BLOCCATO_A_MONTE` |
| Throttling o errore Bedrock su una sessione | 2 nuovi tentativi con attesa crescente, poi `WARNING` / `ERRORE_TECNICO` e voce in `_pipeline_errors` |
| Output dell'agente non conforme | 1 nuovo tentativo, poi `WARNING` / `ERRORE_TECNICO` |
| Limite di turni raggiunto | `WARNING` / `BUDGET_ESAURITO` |
| Redshift non raggiungibile | `WARNING` / `ERRORE_TECNICO` sul controllo targa; il resto prosegue |
| Citazione non riscontrata | `WARNING` / `CITAZIONE_NON_VERIFICATA` |

I log non contengono testo di cicli o documenti, come dichiara oggi il percorso EJ200. Le trascrizioni delle sessioni sì: si scrivono solo nella cartella del run, e nel servizio sono disattivabili.

## 13. Configurazione

- `config/settings.yaml`: modello ed `effort` per uso (estrazione, giudizio), concorrenza, turni massimi, tentativi, finestra GRASP, soglia "in linea", cartella della conoscenza, registro macchine.
- `config/profiles/{mos,dr,ej200}.yaml`: limiti sul file, controlli attivi, prefissi di scheda esclusi.
- `prompts/`: un file per uso (`extract_mos.md`, `extract_ej200.md`, `operation_check.md`). I prompt sono versionati: il loro hash entra nel report.

Le impostazioni si validano all'avvio con messaggi chiari. Oggi un valore numerico mancante impedisce l'avvio senza spiegazione.

## 14. Struttura del progetto

Python ≥ 3.12, `uv`, pydantic, typer, pypdfium2, claude-agent-sdk, pytest, ruff, mypy. `pdfplumber` entra con il primo parser di layout.

```
src/cycle_validation/
├── cli.py                 # run, kb-check
├── pipeline.py            # orchestra gli stadi
├── config.py  errors.py  text.py
├── domain/                # cycle.py, check.py (CheckResult, Verdict, Reason), report.py
├── ingest/                # PDF → pagine
├── extract/               # base.py, from_file.py, llm.py, layout_*.py, integrity.py
├── kb/                    # port.py, local.py (cartella locale), memory.py (test),
│                          # adattatori sulle sorgenti attuali (fase 2)
├── resolve/               # civil.py, dr.py, ej200.py
├── checks/                # base.py, source.py, task_code.py, machine_tag.py,
│                          # process_sheet.py, dr_recommendation.py, operation.py
├── agent/                 # session.py, runner.py, hooks.py, prompt.py, sdk_session.py
├── services/              # machines.py (interfaccia, Redshift, file)
├── profiles/              # mos.py, dr.py, ej200.py
├── verdict/               # citations.py, consolidate.py
├── report/                # builder.py, json_writer.py, markdown_writer.py, legacy_payload.py
└── api/                   # FastAPI: rotte, modelli, sessioni, feedback (fase 6)
config/  prompts/  tests/  docs/
data/    runs/             # fuori da git
```

## 15. Test e criteri di accettazione

- **Unit, offline**: ogni controllo, ogni risolutore, hook, runner, adattatore del payload.
- **Contratto della conoscenza**: una sola suite di test eseguita su ogni implementazione di `KnowledgeBase` (cartella locale, in memoria, poi gli adattatori sulle sorgenti attuali con risposte registrate).
- **End-to-end offline** per profilo, con conoscenza e sessione finte.
- **Golden set** per profilo: PDF di esempio con esiti attesi campo per campo.
- **Confronto in ombra**: gli stessi cicli passano dal sistema attuale e da v2. Ogni differenza si classifica: uguale, migliorata, peggiorata. Il sistema attuale espone già i tempi (`profile`) e il costo LLM (metrica CloudWatch), quindi il confronto ha una base misurata.

Criteri per il passaggio a v2, per ciascun profilo:

1. nessuna differenza classificata "peggiorata" sul golden set;
2. tempo mediano per ciclo non superiore a quello attuale;
3. costo LLM medio per ciclo non superiore a quello attuale;
4. payload accettato dal frontend senza modifiche.

## 16. Decisioni prese, da confermare

| # | Decisione | Alternativa |
|---|---|---|
| 1 | Il frontend non cambia: stesse rotte e stesso payload | Nuovo contratto, con modifiche al frontend |
| 2 | La conoscenza sta dietro una porta definita dalla validazione: in locale una cartella di file, in azienda adattatori sulle sorgenti attuali (S3, OpenSearch, catalogo EJ200) | I controlli chiamano direttamente OpenSearch e S3, come oggi |
| 3 | Quarto esito `NON_APPLICABILE` | Solo tre esiti, con `N/A` reso come riga assente |
| 4 | Una sessione agente per operazione (non per singolo campo) | Una per campo: più isolamento, circa 4 volte le sessioni |
| 5 | Ricerca esatta per manuale e task al posto di quella semantica, dove i metadati lo consentono | Restare sulla ricerca ibrida top-k |
| 6 | Voce assente nella conoscenza → `WARNING`, mai `ERRATO` | `ERRATO` per alcuni tipi, se oggi il sistema si comporta così |
| 7 | `ingestion_v2` fuori ambito: nessuna dipendenza dal suo formato o dal suo codice | Nessuna: deciso il 2026-11-13 |
| 8 | EJ200 per ultimo, con adattatore sul catalogo attuale | Anticiparlo |

## 17. Cosa mi serve per procedere

| Cosa | A cosa serve | Blocca |
|---|---|---|
| Forma dei JSON strutturati su S3 (TM, SP, DR) e mappatura degli indici OpenSearch (campi dei metadati), con esempi sintetici | Adattatori della conoscenza sulle sorgenti attuali | Fase 2 |
| `src/prompts/use_cases/*.yaml` e `src/template/cycle_template.py` del sistema attuale | Capire cosa giudicano oggi i casi d'uso, forma esatta del ciclo | Fasi 3-5 |
| `src/main_validation.py` e `src/ej200/` | Regole di conteggio, logica DR, parser PVRM320 | Fasi 3-5 |
| PDF di esempio per MOS, DR, EJ200, con il payload che il sistema attuale produce | Estrattori, golden set, confronto in ombra | Fasi 3-5, 7 |
| Id del modello Haiku abilitato su Bedrock in `eu-south-1` | Configurazione | Prima esecuzione reale |
| Query Redshift attuale per le macchine attive | Adattatore macchine | Fase 6 |

La Fase 1 (fondamenta) non dipende da nessuno di questi.

## 18. Rischi

| Rischio | Effetto | Contromisura |
|---|---|---|
| I metadati dell'indice civile non consentono la ricerca esatta per manuale e task | Su quel passo resta la ricerca semantica, con il suo costo | L'adattatore ripiega sulla ricerca attuale dietro la stessa porta (§6.3); il confronto in ombra misura l'effetto |
| La cartella locale di prova non rappresenta bene i documenti reali | Sorprese al primo run su dati reali | Formato minimo e versionato; golden set su documenti reali appena disponibili |
| Haiku insufficiente per l'estrazione di cicli lunghi | Operazioni mancanti o errate | Verifica di integrità; modello configurabile per uso; parser di layout |
| I prompt attuali contengono regole di dominio non descritte nella guida | Regressioni | Lettura dei prompt prima delle Fasi 3-5; confronto in ombra |
| Avvio di un processo per sessione | Latenza sulle operazioni "in linea" | Parallelismo; adattatore diretto a Bedrock se le misure lo giustificano |

## 19. Fuori ambito

- Modifiche al frontend, al servizio di login, a nginx/ECS.
- `ingestion_v2`, per intero: è sviluppato al lavoro, separatamente. Nessuna modifica e nessuna dipendenza.
- Modifiche alla pipeline storica `indexing/`.
- OCR di PDF scansionati.
- Job asincroni.
- Escalation automatica a un modello più grande sui `WARNING`.
