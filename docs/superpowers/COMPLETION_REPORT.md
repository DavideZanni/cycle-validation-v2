# Cycle Validation v2 — Rapporto di completamento (Fasi 1-6)

Esito finale: **488 test superati**, `pytest` verde e `ruff check .` pulito, tutto offline.
I piani di lavoro per fase sono stati tolti il 15 novembre 2026: restano nella history di git.

Dopo le Fasi 1-6 il lavoro è stato riletto in modo critico e ottimizzato sul ramo
`review/correctness-and-optimization` (da 404 a 488 test): vedi "Revisione critica" più sotto.
Per il passaggio in azienda: `docs/IMPORTAZIONE_AZIENDA.md`.

## Cosa non è verificato (leggere prima di fidarsi)

- **Nessun dato aziendale è stato visto.** Forma dei JSON su S3, campi dell'indice OpenSearch,
  prompt YAML attuali, layout reale del PVRM320, query Redshift e SDK di autenticazione non erano
  disponibili. Il codice li assume dietro configurazione (vedi "Punti di aggancio").
- **Nessuna chiamata reale a Bedrock.** L'adattatore del Claude Agent SDK è testato su opzioni e
  traduzione dei messaggi, non su una sessione vera. Lo smoke test va fatto dove ci sono credenziali.
- **`mypy` non è stato eseguito**: su questa macchina una policy ne blocca il caricamento
  (`DLL load failed`). Non faceva parte dei criteri di fine lavoro.
- **I test EJ200 sono di caratterizzazione sul comportamento descritto in
  `DOCUMENTAZIONE_TECNICA`**, non sulla suite originale (non disponibile).
- Il codice di Fase 1 esisteva già in parte (dominio, controlli, agente) con 136 test; i test di
  citazioni, hook, runner, giudizio per operazione e adattatore SDK sono stati scritti dopo il
  codice. Quello per le citazioni ha trovato un bug reale (riga riportata errata), corretto.
- **Fase 7** (confronto in ombra e passaggio) non rientra in questo lavoro.

## Moduli, cartella per cartella (`src/cycle_validation/`)

| Cartella | Contenuto |
|---|---|
| (radice) | `pipeline.py` (orchestrazione, sync e async), `cli.py` (`run`, `kb-check`, `kb-export`, `golden`), `config.py` (impostazioni e profili), `golden.py` (golden set e misure), `legacy_prompts.py` (lettore dei prompt YAML attuali), `text.py`, `errors.py` |
| `domain/` | `Cycle`/`Source`/`Operation`, `CheckResult`/`Verdict`/`Reason` (esiti coerenti per costruzione), `Report` |
| `ingest/` | PDF → pagine con PDFium; limiti per profilo (intestazione, dimensione, pagine, caratteri, testo atteso); immagini e scansioni → trascrittore su Bedrock (una pagina alla volta, tetto di pagine e di pixel, nuovi tentativi sui guasti transitori) |
| `extract/` | porta `CycleExtractor`; da file, LLM a output strutturato (schema chiuso), parser di layout PVRM320, cascata con riserva, verifica di integrità |
| `kb/` | porta `KnowledgeBase`; cartella locale, in memoria; store (in memoria, cartella, S3, JSONL) e indici (in memoria, OpenSearch); dati strutturati TM/SP/DR; manuali con ricerca esatta; `RemoteKnowledgeBase`; catalogo e `Ej200KnowledgeBase`; esportazione verso la cartella locale |
| `resolve/` | risoluzione dei riferimenti (stati di pubblicazione, issue, ambiguità), selettori DR |
| `checks/` | `source`, `task_code`, `machine_tag`, `process_sheet`, `dr_recommendation` (bloccante), `operation_description` (giudizio dell'agente) |
| `agent/` | porta `AgentSession`, hook GRASP, runner (concorrenza, retry, consumi), prompt e schema, adattatore Claude Agent SDK |
| `verdict/` | verifica delle citazioni, consolidamento (integrità, blocchi, conteggi, stato) |
| `report/` | `report.json`, `report.md`, `payload.json` nel formato del frontend attuale |
| `services/` | registro macchine attive: statico, da file, lazy, non disponibile, DB-API (Redshift) |
| `api/` | FastAPI: modelli, autenticazione per servizio, rotte civili ed EJ200, sessioni e feedback, impostazioni, CloudWatch, bootstrap Secrets Manager, avvio |
| `testing/` | fabbrica di PDF sintetici |

Fuori da `src/`: `config/` (impostazioni e tre profili), `prompts/` (giudizio, estrazione MOS/DR ed EJ200),
`examples/sintetico/`, `tests/` (inclusi `golden/` per MOS, DR, EJ200 e `contract/`), `Dockerfile`.

## Test

488 superati. Per area: dominio, configurazione, ingest, integrità, knowledge base (suite di contratto
su cartella locale, in memoria e adattatore remoto), controlli a codice, citazioni, hook, runner,
giudizio per operazione, adattatore SDK, estrattori (LLM, cascata, PVRM320), consolidamento, report,
end-to-end MOS / DR / EJ200, golden set (MOS 5 casi, DR 5 casi, EJ200 7 casi), concorrenza della pipeline, CLI, API (rotte,
autorizzazioni, contratto con risposte registrate), impostazioni e adattatori AWS.

## Punti di aggancio alle sorgenti di produzione

Ogni punto è una porta (Protocol) con implementazione di prova già pronta. Per agganciare la produzione
si costruisce il client aziendale e lo si passa all'adattatore indicato.

| Cosa | Porta | Adattatore pronto (client iniettato) | Da fare in azienda |
|---|---|---|---|
| Dati TM/SP/DR su S3 | `ObjectStore` | `S3ObjectStore(client_boto3, bucket)`; `StructuredLayout` + `FieldMap` | impostare prefissi e **alias dei campi** secondo la forma reale dei JSON |
| Testo manuali civili | `SearchIndex` | `OpenSearchIndex(client, index)`; `ChunkSchema`; `IndexedManualSource` | indicare i **nomi dei campi dei metadati** (manuale, task, pagina, ordine, testo); se non bastano a una ricerca esatta, passare `fallback` (`ChunkFallback`) con la ricerca ibrida attuale |
| Knowledge base civile | `KnowledgeBase` | `RemoteKnowledgeBase(version, store, manuals, layout)` + `preload()` all'avvio | comporre gli adattatori sopra |
| Catalogo e documenti EJ200 | `KnowledgeBase` | `Ej200Catalog(store, key, ttl)` + `Ej200KnowledgeBase(...)` | verificare i campi del catalogo (`CatalogEntry`) e dell'indice (`document_id`, `content_hash`, ...) |
| Macchine attive | `MachineRegistry` | `redshift_machine_registry(connect, query, ttl_s=900)` (DB-API) | fornire `connect` (credenziali da Secrets Manager) e la **query attuale**; confermare ogni quanto l'elenco va riletto |
| Trascrizione di scansioni e foto | `PageTranscriber` | `BedrockPageTranscriber(client, model_id, prompt)` | `agent.transcribe_model` in `config/settings.yaml`; confermare i limiti per immagine di Bedrock (3,75 MB, 8000 px) |
| Modello (estrazione e giudizio) | `AgentSession` | `SdkAgentSession(settings)` via Claude Agent SDK su Bedrock | id del modello Haiku abilitato in `eu-south-1` in `config/settings.yaml`; smoke test reale |
| Estrazione MOS/DR | `CycleExtractor` | `LlmCycleExtractor`; `FallbackCycleExtractor(layout, llm)` | decidere sui PDF reali se un parser di layout MOS sostituisce l'LLM |
| Estrazione EJ200 | `CycleExtractor` | `Pvrm320LayoutExtractor(Pvrm320Layout)` | adattare etichette e regex al **layout reale** |
| Prompt attuali | — | `legacy_prompts.load_use_cases` / `describe_use_cases` | leggere `src/prompts/use_cases/*.yaml` e decidere se la pertinenza di task/targa/scheda entra nel giudizio |
| Autenticazione e permessi | `AuthBackend` | `StaticAuthBackend` (prova) | adattatore sull'SDK `chatbot_ai_sdk.auth` (introspezione + permessi S3, chiavi `cv`, `cv_ej200`) |
| Sessioni e feedback | `WritableObjectStore` | `S3ObjectStore` (scrive e cancella) | stesso client S3 |
| Metrica di costo | `MetricsSink` | `CloudWatchMetrics(client)` (`Chatbot/CV`, `llmInvokationCost`) | client CloudWatch |
| Variabili da secret | — | `bootstrap_environment(client, secret_name)` | nome del secret (`aa-datalake-chatbot-cv-env`) |
| Cablaggio del servizio | — | `api.main.create_app_from_env(environ, factory)` | scrivere la `factory(config) -> ApiServices` che compone i punti sopra |
| Golden set reale | — | `cycle-validation golden DIR` (cartella: `ciclo.json`, `expected.json`, `ciclo.pdf`) | PDF reali con esiti attesi; `kb-export` per lavorare senza rete |

## Revisione critica (ramo `review/correctness-and-optimization`)

Un commit per modifica logica sopra `master`; ogni correzione di comportamento è partita da
un test visto fallire. In sintesi:

- **Materiale aziendale nelle fixture.** `tests/pvrm320_report_fixtures.py`, il suo test e una
  docstring riportavano identificativi reali copiati dagli esempi ignorati. Sono stati sostituiti
  con valori inventati; i test sugli esempi reali leggono gli attesi da file non tracciati.
  **La history precedente li contiene ancora** (commit `3fdb450`, `f061e51`, `5e95a33`): non è
  stata riscritta, va deciso prima di condividere il repository.
- **Garanzie sugli esiti.** Un elenco vuoto di macchine attive non è più "tutte inattive"
  (ERRATO) ma sorgente non disponibile; l'elenco si rinnova ogni 15 minuti; un codice citato deve
  comparire per intero, non come pezzo di un codice più lungo; la verifica di integrità copre
  anche il manuale citato e la descrizione dell'operazione (una descrizione che il PDF non
  conferma non viene mandata al modello); una riga vuota prima della citazione non sposta più
  riga e pagina dell'evidenza; la scheda è detta "applicabile" solo se la famiglia è stata
  confrontata.
- **Parser PVRM320 (stampa reale).** Targa solo dalla riga numerata, continuazioni tra pagine,
  blocchi orfani che falliscono invece di sparire, puntini di compilazione, asterischi
  alternativi, piè di pagina con spazi, codici RDR con almeno una cifra.
- **Modello e trascrizione.** L'adattatore SDK conserva esito e consumi quando la CLI esce con
  errore; una trascrizione troncata è un errore; i guasti transitori di Bedrock si ritentano; le
  scansioni hanno un tetto di pagine (60) e di lato (3000 px); le immagini si controllano e si
  ridimensionano prima dell'invio; PDFium è serializzato da un lock.
- **Testo fuori dai messaggi.** Esiti delle sessioni, errori imprevisti dell'API (busta `failed`
  e 500) ed errore del ciclo da file riportano tipo e posizione, non il testo dell'eccezione.
- **API.** Tetto del file caricato (`API_MAX_UPLOAD_MB`, 50 MB) con 413 prima di ogni lavoro.
- **Knowledge base.** Metadati dell'indice salvati come testo (pagina, ordine) non rompono più
  il documento; due documenti non finiscono nello stesso file; ricerche concorrenti dello stesso
  documento interrogano l'indice una volta.

Misure (sintetiche, latenze simulate; script fuori dal repository):

| Cosa | Prima | Dopo |
|---|---|---|
| EJ200, catalogo di 5008 voci, 60 operazioni, 3 fonti: controlli a codice e pianificazione | 21,4 s | 30 ms |
| `task_code` in modalità documento, 60 operazioni × 2 codici, documento di 10 000 righe | 3372 ms | 394 ms |
| Scansione di 30 pagine: picco di memoria (oggetti Python) | 159,5 MB | 10,9 MB |
| Pipeline MOS, 18 operazioni (indice 30 ms, registro 400 ms, sessione 250 ms): fase `checks` | 1175 ms | 887 ms |
| Stessa prova: avvio della prima sessione dell'agente | 413 ms | 120 ms |

La scansione di rumore puro impiega più tempo di prima (12,1 s → 17,0 s): ogni pagina supera il
limite in PNG e viene ricodificata in JPEG, mentre prima partiva un PNG oltre il limite del modello.

## Come riprodurre

```bash
uv sync && uv run pytest && uv run ruff check .
```
