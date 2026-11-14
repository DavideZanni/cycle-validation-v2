# Cycle Validation v2 — Avanzamento esecuzione completa (Fasi 1-6)

Stato finale: TUTTE LE FASI 1-6 COMPLETATE. Fase 7 (confronto in ombra) fuori da questo ciclo: richiede il sistema attuale e dati reali.

Regole: TDD, tutto offline (nessuna rete, nessun AWS), ogni servizio esterno dietro Protocol con fake.
Verifica: `uv run pytest` verde, `uv run ruff check .` pulito. (`mypy` è bloccato da una policy di
questa macchina: DLL non caricabile; non fa parte dei criteri di fine lavoro.)

## Fase 1 — Fondamenta  [COMPLETATA]
- [x] 1.1 Scheletro, errori, testo
- [x] 1.2 Dominio (ciclo, esiti, report)
- [x] 1.3 Configurazione e profili
- [x] 1.4 Ingest PDF
- [x] 1.5 Knowledge base (porta, memoria, cartella locale), registro macchine
- [x] 1.6 Controlli a codice, integrità, risolutori civili, DR (selettori e controllo)
- [x] 1.7 Test: citazioni
- [x] 1.8 Test: hook GRASP
- [x] 1.9 Test: runner
- [x] 1.10 Test: prompt, giudizio per operazione, adattatore SDK
- [x] 1.11 Consolidamento
- [x] 1.12 Report (json, md, payload compatibile)
- [x] 1.13 Pipeline, CLI, e2e MOS

## Fase 2 — Knowledge base su sorgenti attuali  [COMPLETATA]
- [x] 2.1 Porte ObjectStore / SearchIndex; implementazioni in memoria, cartella, S3 (client iniettato), OpenSearch (client iniettato), JSONL
- [x] 2.2 Dati strutturati TM/SP/DR con mappa dei campi configurabile (forma reale non nota: alias estendibili)
- [x] 2.3 Manuali: ricerca esatta per manuale+task, riscrittura a righe con pagine, ripiego e alias
- [x] 2.4 RemoteKnowledgeBase (porta KnowledgeBase), preload vs. lookup (KnowledgeError / SourceUnavailable)
- [x] 2.5 Esportazione verso cartella locale + `kb-export`
- [x] 2.6 Suite di contratto estesa all'adattatore remoto
## Fase 3 — Profilo MOS  [COMPLETATA]
- [x] 3.1 Loader dei prompt YAML legacy + nota (docs/superpowers/notes/fase3-mos-note.md)
- [x] 3.2 Estrattore LLM a output strutturato (schema chiuso) + prompt di estrazione
- [x] 3.3 Estrazione a cascata (parser di layout → LLM); decisione sul parser annotata
- [x] 3.4 Risoluzione fonti e controlli a codice (già in Fase 1) + registro macchine Redshift (DB-API)
- [x] 3.5 Giudizio per operazione, statistiche sessioni in linea/ricerca
- [x] 3.6 Golden set MOS e comando `golden`
- [x] 3.7 CLI `run` senza `--cycle-json` estrae con il modello
## Fase 4 — Profilo DR  [COMPLETATA]
- [x] 4.1 Selettori (normalizzazione, regole is_dr) — già coperti da test
- [x] 4.2 Record DR attaccato al ciclo (`dr_record`)
- [x] 4.3 Controllo `dr_recommendation` bloccante con tutti i rami
- [x] 4.4 Contesto dai task della recommendation
- [x] 4.5 Golden set DR (5 casi, uno per ramo di blocco) + e2e DR
## Fase 5 — Profilo EJ200  [COMPLETATA]
- [x] 5.1 Controlli sul file (header, 20 MB, 60 pagine, 100 caratteri, testo EJ200) con test
- [x] 5.2 Parser di layout PVRM320 (unione operazioni tra pagine, note escluse), layout configurabile
- [x] 5.3 Catalogo pubblicazioni con TTL (errore non memorizzato) + Ej200KnowledgeBase (lookup esatto document_id+content_hash)
- [x] 5.4 Risoluzione RN/EF/RDR (issue diversa, ignota, parziale, non pubblicato, ambiguo → warning)
- [x] 5.5 Controlli EJ200: data-module nel testo, targa condivisa, scheda N/A, giudizio con preferenza RDR>EF>RN, nessun troncamento
- [x] 5.6 Test di caratterizzazione dal comportamento documentato in DOCUMENTAZIONE_TECNICA (suite originale non disponibile)
- [x] 5.7 Golden set EJ200 (4 casi)
## Fase 6 — API FastAPI  [COMPLETATA]
- [x] 6.1 Scrittura sugli store (WritableObjectStore) + sessioni e feedback con le chiavi S3 attuali (feedback: un oggetto per invio, errore di scrittura propagato)
- [x] 6.2 Modelli, autenticazione/autorizzazione per servizio (cv, cv_ej200, all) dietro AuthBackend
- [x] 6.3 Rotte civili ed EJ200 (health, flow/start, conversation, upload, sessions, feedback), codici HTTP e forma errori
- [x] 6.4 Adattatori: CloudWatch (costo LLM), bootstrap Secrets Manager, validazione impostazioni all'avvio, kill switch EJ200 (501)
- [x] 6.5 Entrypoint, Dockerfile, Gunicorn
- [x] 6.6 Test di contratto contro risposte registrate (tests/contract)
