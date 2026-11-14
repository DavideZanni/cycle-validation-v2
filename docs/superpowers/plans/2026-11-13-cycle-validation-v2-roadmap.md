# Cycle Validation v2 — Piano di refactoring

**Data:** 2026-11-13
**Design:** `docs/superpowers/specs/2026-11-13-cycle-validation-v2-design.md`
**Sostituisce:** `archivio/2026-11-13-cycle-validation-foundation-SUPERATO.md`

Questo documento è il piano per fasi. Ogni fase, quando i suoi input sono disponibili, riceve un piano di dettaglio da eseguire task per task, con i test prima del codice. Il piano di dettaglio della Fase 1 è in `2026-11-13-cycle-validation-v2-fase1.md`.

**Perimetro:** solo la validazione dei cicli. `ingestion_v2` è sviluppato al lavoro, separatamente, e non entra in questo piano.

---

## 1. In sintesi

Oggi: due pipeline separate (civile ed EJ200), conoscenza su OpenSearch con embedding, quattro chiamate LLM per operazione più estrazione e consolidamento, test solo su EJ200.

Dopo: una pipeline con tre profili (MOS, DR, EJ200), conoscenza dietro un'unica interfaccia (cartella locale di file, poi adattatori sulle sorgenti attuali), controlli di esistenza decisi dal codice, una sola sessione Haiku per operazione con lettura a paragrafo, esiti con citazione verificata, payload identico per il frontend.

Il passaggio avviene per profilo, dopo un confronto in ombra con il sistema attuale sugli stessi cicli.

## 2. Fasi e dipendenze

```
Fase 1  Fondamenta ───────────────┬──► Fase 3  MOS ──► Fase 4  DR ──┐
        (parte subito)            │                                 ├──► Fase 7  Confronto in ombra
Fase 2  Knowledge base ───────────┤                                 │            e passaggio
        (servono dati S3, indici) ├──► Fase 5  EJ200 ───────────────┤
                                  └──► Fase 6  API compatibile ─────┘
Fase 0  Raccolta input: in parallelo a tutto
```

| Fase | Contenuto | Dimensione | Dipende da |
|---|---|---|---|
| 0 | Raccolta degli input e della baseline | piccola | te |
| 1 | Fondamenta: dominio, pipeline, agente, report | grande | niente |
| 2 | Knowledge base: adattatori sulle sorgenti attuali | media | forma dei JSON su S3, mappatura degli indici |
| 3 | Profilo MOS su dati reali | grande | 1, 2, PDF e prompt MOS |
| 4 | Profilo DR | media | 3, PDF DR |
| 5 | Profilo EJ200 | grande | 1, PDF e codice EJ200 |
| 6 | API compatibile | media | 3 |
| 7 | Confronto in ombra e passaggio | media | 3-6 |

## 3. Cosa resta del lavoro già fatto

Il piano precedente era costruito su un modello generico (campi scalari con tolleranze). Con la documentazione reale quel modello non regge, ma metà dei componenti resta valida perché non dipende dal dominio. Il codice è già scritto e verificato nel piano archiviato.

| Componente del piano archiviato | Sorte |
|---|---|
| Scheletro del progetto, strumenti (Task 1) | Resta, su Python 3.12 |
| Confinamento dei path, verifica delle citazioni (Task 5) | Resta. L'evidenza guadagna documento, versione e pagina |
| Hook GRASP (Task 8) | Resta. Si aggiunge l'elenco dei file ammessi per sessione |
| Runner parallelo con retry (Task 9) | Resta invariato |
| Adattatore Claude Agent SDK (Task 10) | Resta. Cambiano prompt e schema dell'output |
| Ingest PDF con PDFium (Task 11) | Resta. Si aggiungono i limiti per profilo |
| Modelli, configurazione (Task 1-2) | Riscritti sul dominio reale: ciclo, fonti, operazioni |
| Precheck, regole di tolleranza, `decide` (Task 3, 4, 6) | Sostituiti dai controlli del design v2. Le tolleranze numeriche escono: il dominio non le usa |
| Report, pipeline, CLI (Task 7, 12) | Riscritti: tabella per operazione, payload compatibile, profili |

---

## Fase 0 — Input e baseline

**Obiettivo:** avere ciò che serve alle fasi 2-7 senza fermare la Fase 1.

| Input | Per la fase |
|---|---|
| Forma dei JSON strutturati su S3 (TM, SP, DR) e mappatura degli indici OpenSearch civile ed EJ200 (campi dei metadati), con esempi sintetici | 2 |
| Sistema attuale: `src/prompts/use_cases/*.yaml`, `src/template/cycle_template.py`, `src/main_validation.py`, `src/ej200/`, `tests/` | 3, 4, 5 |
| PDF di esempio: almeno 5 MOS, 5 DR (con serial number e condition), 5 EJ200. Per ciascuno il payload che il sistema attuale restituisce, con i tempi in `profile` | 3, 4, 5, 7 |
| Id del modello Haiku abilitato su Bedrock in `eu-south-1` | prima esecuzione reale |
| Query Redshift delle macchine attive; costo LLM medio per ciclo dalla metrica CloudWatch | 6, 7 |

Materiale aziendale: va in `data/` e `docs/doc_lavoro/`, entrambi esclusi da git.

---

## Fase 1 — Fondamenta

**Obiettivo:** la pipeline completa funziona dall'inizio alla fine su dati sintetici, con una knowledge base locale. Tutto ciò che non dipende dal formato reale dei PDF e dalle sorgenti aziendali è finito e testato.

**Lavori:**

1. **Scheletro del progetto.** `pyproject.toml`, Python 3.12, uv, ruff, mypy, pytest, `.gitignore`.
2. **Modello di dominio.** `Cycle`, `Source`, `Operation`; `CheckResult`, `Verdict`, `Reason`; `Report`.
3. **Configurazione.** `settings.yaml` e un file per profilo, validati all'avvio con messaggi chiari.
4. **Ingest.** PDF → pagine con testo (PDFium); limiti per profilo (intestazione PDF, dimensione, pagine, caratteri minimi).
5. **Interfacce e prime implementazioni.** `KnowledgeBase` (cartella locale e in memoria), `MachineRegistry` (file), `CycleExtractor` (ciclo da file), controlli a codice `source`, `task_code`, `machine_tag`, `process_sheet`, `extraction_integrity`.
6. **Citazioni.** Verifica che la citazione compaia nel file alla riga indicata; riconduzione a documento, versione, pagina.
7. **Hook GRASP.** `Read` solo con `limit` entro soglia; `Read` e `Grep` solo sui file ammessi per la sessione.
8. **Runner.** Una sessione per operazione, concorrenza limitata, retry sugli errori tecnici, consumi sommati.
9. **Adattatore Claude Agent SDK.** Opzioni restrittive, output strutturato, trascrizione su file.
10. **Giudizio per operazione.** Scelta "in linea" o "in ricerca" in base alla dimensione del testo; prompt; passaggio dal giudizio dell'agente al `CheckResult` secondo le regole del design §8.3.
11. **Consolidamento.** Stato del ciclo (completo, bloccato, parziale), propagazione dei blocchi, conteggi.
12. **Report.** `report.json`, `report.md` con tabella per operazione, `payload.json` nel formato attuale con i feedback a prefisso.
13. **Pipeline e CLI.** `cycle-validation run PDF --profile mos|dr|ej200`, con ciclo già estratto passato da file finché mancano gli estrattori.

**Consegna:** `cycle-validation run` produce report e payload compatibile su un ciclo sintetico. Suite offline verde, mypy e ruff puliti. Uno smoke test reale su Bedrock per una sessione, da eseguire dove ci sono le credenziali.

**Accettazione:**
- un test end-to-end offline sul profilo MOS, con knowledge base locale sintetica e sessione finta; DR ed EJ200 sono dichiarati ma rifiutati con un messaggio chiaro fino alle loro fasi;
- il payload generato rispetta la forma descritta nella guida del sistema attuale;
- nello smoke test reale ogni `Read` ha `limit` entro soglia e la citazione restituita supera la verifica.

---

## Fase 2 — Knowledge base sulle sorgenti attuali

**Obiettivo:** la stessa interfaccia `KnowledgeBase` usata in locale, alimentata dalle sorgenti che il sistema usa oggi. Da fare dove ci sono accesso e credenziali.

**Lavori:**

1. **Lettura della forma reale** dei JSON strutturati su S3 (TM, SP, DR) e della mappatura degli indici OpenSearch. Nota scritta dei campi utili.
2. **Adattatore S3** per targhe, schede e recommendation: caricamento, indici per codice, errori espliciti se un oggetto manca o non è valido.
3. **Adattatore dei manuali civili:** ricerca esatta per manuale e task sui metadati dell'indice; il testo trovato viene riscritto a righe in una cartella di lavoro, con mappa riga → pagina. Se i metadati non bastano, ripiego sulla ricerca attuale dietro la stessa interfaccia.
4. **Esportazione verso la cartella locale:** un comando che scrive una knowledge base nel formato locale a partire dalle sorgenti reali, per golden set e sviluppo senza rete.
5. **Suite di contratto** eseguita anche sui nuovi adattatori, con risposte registrate.

**Consegna:** `cycle-validation kb-check` stampa i conteggi (documenti, task, targhe, schede) su una knowledge base reale.

**Accettazione:**
- la suite di contratto passa su ogni adattatore;
- un ciclo sintetico dà gli stessi esiti con la cartella locale e con le sorgenti reali, a parità di contenuto.

**Punto aperto da chiudere all'inizio della fase:** se i metadati dell'indice civile consentono la ricerca esatta per manuale e task.

---

## Fase 3 — Profilo MOS

**Obiettivo:** un ciclo MOS reale validato dall'inizio alla fine, con esiti uguali o migliori di quelli attuali.

**Lavori:**

1. **Lettura dei prompt attuali** (`cycle_extraction`, `source_validation`, `operations_validation`, `task_codes_validation`, `TM_validation`, `SP_validation`, `cycle_validation`) e nota scritta di cosa giudica ciascuno. Decide se la sessione per operazione valuta solo la descrizione o anche la pertinenza di task, targa e scheda.
2. **Estrattore MOS** con output strutturato, più verifica di integrità.
3. **Prova del parser di layout** sui PDF di esempio. Se regge su tutti, diventa l'estrattore principale e l'LLM resta come riserva. Decisione annotata.
4. **Risoluzione delle fonti** (manuale + task) sugli indici.
5. **Controlli a codice:** `source`, `task_code`, `machine_tag` (registro macchine da file), `process_sheet` con i prefissi esclusi.
6. **Giudizio per operazione** sulla conoscenza reale; taratura del prompt.
7. **Golden set MOS** e misura: concordanza con gli esiti attesi, tempo, costo, quota di operazioni risolte "in linea".

**Consegna:** `cycle-validation run ciclo.pdf --profile mos` su PDF reali.

**Accettazione:** sul golden set MOS nessun esito peggiore di quello atteso; ogni `CORRETTO` ed `ERRATO` deciso dall'agente ha una citazione verificata.

---

## Fase 4 — Profilo DR

**Obiettivo:** aggiungere a MOS la logica DR.

**Lavori:**

1. **Selettori.** `dr_serial_number` e `dr_condition` normalizzati a `list[int]` da intero, lista, `"1,2"`, `"[1,2]"`. `is_dr=false` vieta i selettori; `is_dr=true` li richiede.
2. **Record DR dal ciclo.**
3. **Controllo `dr_recommendation`.** Ricerca per serial number; più corrispondenze → intersezione delle condition; nessuna corrispondenza, selettori mancanti o dati DR non caricabili → blocco; `Accept as is` o `Reject` → errore e blocco.
4. **Contesto dai riferimenti e dai task della recommendation**, poi gli stessi controlli di MOS.
5. **Golden set DR**, con almeno un caso per ogni ramo di blocco.

**Accettazione:** ogni ramo descritto nella guida ("Flusso civile DR") ha un test; golden set DR senza esiti peggiori.

---

## Fase 5 — Profilo EJ200

**Obiettivo:** portare EJ200 sulla stessa pipeline.

**Lavori:**

1. **Controlli sul file:** intestazione `%PDF-` nei primi 1024 byte, ≤ 20 MB, ≤ 60 pagine, ≥ 100 caratteri, testo che identifica EJ200.
2. **Estrattore PVRM320:** unione delle operazioni ripetute tra pagine, righe "note" escluse, verifica di integrità su numeri operazione, targhe e codici data-module.
3. **Conoscenza EJ200:** adattatore sul catalogo attuale e sui documenti dell'indice EJ200, dietro la stessa interfaccia `KnowledgeBase`.
4. **Risoluzione di RN, EF, RDR:** pubblicazione più recente; issue diversa o ignota, pubblicazione parziale, documento non pubblicato, RDR ambiguo → warning.
5. **Controlli:** codici data-module nel testo dei documenti citati (a codice), `machine_tag` (condiviso), `process_sheet` → non applicabile, giudizio per operazione sui soli documenti citati, con preferenza RDR, EF, RN.
6. **Test attuali come specifica.** La suite esistente copre proprio EJ200: i suoi casi diventano test di caratterizzazione di v2.
7. **Golden set EJ200.**

**Accettazione:** i casi della suite attuale riprodotti in v2; golden set EJ200 senza esiti peggiori; nessun troncamento del contesto.

---

## Fase 6 — API compatibile

**Obiettivo:** il frontend parla con v2 senza accorgersene.

**Lavori:**

1. **Rotte civili ed EJ200** identiche: `health`, `flow/start`, `conversation`, `upload`, `sessions`, `feedback`. Stessi modelli, stessi codici HTTP, stessa forma degli errori.
2. **Middleware** di autenticazione e autorizzazione dell'SDK condiviso, chiavi `cv` e `cv_ej200`.
3. **Sessioni e feedback** sulle stesse chiavi S3. Feedback civile: un oggetto per feedback e risposta d'errore se la scrittura fallisce.
4. **Adattatori reali:** Redshift per le macchine attive, metrica di costo su CloudWatch, bootstrap da Secrets Manager.
5. **Avvio:** validazione della configurazione con messaggi chiari, kill switch EJ200, Dockerfile e Gunicorn.
6. **Test di contratto:** le risposte di v2 confrontate con risposte registrate dal sistema attuale.

**Accettazione:** i test di contratto passano; il frontend di collaudo funziona puntando a v2 senza modifiche.

---

## Fase 7 — Confronto in ombra e passaggio

**Obiettivo:** decidere il passaggio su numeri, non su impressioni.

**Lavori:**

1. **Raccolta** dei payload del sistema attuale sugli stessi cicli.
2. **Strumento di confronto:** per ogni campo, uguale / migliorato / peggiorato; per ogni ciclo, tempo e costo dei due sistemi.
3. **Revisione delle differenze** con chi conosce il dominio; taratura di prompt e politiche.
4. **Passaggio per profilo**, dietro un interruttore. Il ritorno indietro è riattivare il servizio attuale.

**Criteri di passaggio, per profilo:**

| Misura | Soglia |
|---|---|
| Campi classificati "peggiorato" | zero |
| Tempo mediano per ciclo | non superiore all'attuale |
| Costo LLM medio per ciclo | non superiore all'attuale |
| Payload | accettato dal frontend senza modifiche |

---

## 4. Decisioni da confermare prima di partire

Sono nel design, §16. Le tre che cambiano di più il lavoro:

1. **Il frontend non cambia** (stesse rotte, stesso payload). Se invece si può cambiare, la Fase 6 si semplifica.
2. **La conoscenza sta dietro un'interfaccia della validazione.** In locale una cartella di file; in azienda adattatori sulle sorgenti attuali, da scrivere dove c'è accesso (Fase 2).
3. **Una sessione per operazione**, non per singolo campo.

## 5. Prossimo passo

Esecuzione della Fase 1 secondo `2026-11-13-cycle-validation-v2-fase1.md`. In parallelo, la Fase 0. Le fasi 2-7 richiedono accesso a codice, dati e credenziali aziendali.
