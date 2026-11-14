# Cycle Validation v2 — Fase 1 (Fondamenta) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** una pipeline di validazione che gira dall'inizio alla fine su dati sintetici (profilo MOS), con knowledge base locale, controlli a codice, giudizio per operazione tramite agente, report e payload compatibile.

**Architecture:** libreria Python con CLI. Stadi `ingest → extract → integrity → check → consolidate → report`. La conoscenza sta dietro la porta `KnowledgeBase`; l'agente sta dietro la porta `AgentSession`. Il codice trova documento e righe, l'agente confronta, il codice verifica la citazione e assegna l'esito.

**Tech Stack:** Python 3.12, uv, pydantic 2, PyYAML, typer, pypdfium2, claude-agent-sdk, pytest, ruff, mypy.

**Design di riferimento:** `docs/superpowers/specs/2026-11-13-cycle-validation-v2-design.md`.

**Nota sul formato:** il piano elenca file, interfacce esatte, casi di test e criteri. Il codice non è duplicato qui: sta nel repo, un commit per task.

## Global Constraints

- Solo validazione dei cicli. Niente che riguardi `ingestion_v2`.
- Python `>=3.12`; sviluppo su 3.12.
- Nessun materiale aziendale in git: `docs/doc_lavoro/`, `data/`, `runs/`, `.env` restano ignorati. Esempi e test usano solo dati inventati.
- Nessuna credenziale o valore di secret nel codice, nella configurazione o nei documenti.
- I test girano offline: nessuna chiamata a Bedrock, S3, OpenSearch, Redshift.
- Esiti: `CORRETTO`, `WARNING`, `ERRATO`, `NON_APPLICABILE`. `ERRATO` solo con prova; guasto tecnico o riferimento assente danno `WARNING`.
- `CORRETTO` ed `ERRATO` decisi dall'agente richiedono almeno una citazione verificata dal codice.
- Tool dell'agente: solo `Read` e `Grep`, solo sui file ammessi per la sessione, `Read` sempre con `limit` entro soglia (GRASP).
- Messaggi all'utente e motivazioni in italiano. Identificatori in inglese.
- `ruff check`, `ruff format --check`, `mypy --strict` e `pytest` puliti a ogni commit.

## Mappa dei file

```
pyproject.toml  .python-version  README.md
config/settings.yaml
config/profiles/{mos,dr,ej200}.yaml
prompts/operation_check.md
examples/sintetico/{ciclo.pdf, ciclo.json, macchine_attive.json, knowledge/...}
src/cycle_validation/
  errors.py            gerarchia degli errori
  text.py              normalizzazione di codici e citazioni
  config.py            Settings, ProfileConfig, caricamento con errori leggibili
  domain/cycle.py      Cycle, Source, Operation, ProcessSheet
  domain/check.py      Verdict, Reason, CheckName, Target, Evidence, Usage, CheckResult
  domain/report.py     Report, RunMeta, Counts, CycleStatus, PipelineError
  ingest/pdf.py        PDF → PdfDocument, limiti per profilo
  extract/base.py      porta CycleExtractor
  extract/from_file.py ciclo già estratto letto da JSON
  extract/integrity.py valori estratti presenti nel testo del PDF
  kb/port.py           porta KnowledgeBase e voci
  kb/documents.py      file a righe: lettura, marcatori di pagina
  kb/memory.py         IndexedKnowledgeBase (indici in memoria)
  kb/local.py          caricamento della cartella locale
  services/machines.py porta MachineRegistry, implementazione da file
  resolve/civil.py     riferimenti del ciclo → voci della conoscenza
  checks/base.py       CheckContext, costruzione dei CheckResult
  checks/source.py  task_code.py  machine_tag.py  process_sheet.py
  checks/operation.py  giudizio per operazione (pianifica, decide)
  agent/session.py     porta AgentSession, SessionRequest, SessionOutcome
  agent/hooks.py       politica dei tool e hook PreToolUse
  agent/runner.py      parallelismo, retry, consumi
  agent/prompt.py      schema dell'output, messaggi, versione dei prompt
  agent/sdk_session.py unico modulo che importa claude-agent-sdk
  verdict/citations.py verifica delle citazioni
  verdict/consolidate.py integrità, blocchi, conteggi, stato del ciclo
  report/builder.py  markdown_writer.py  legacy_payload.py
  pipeline.py          orchestrazione
  cli.py               run, kb-check
tests/                 un file di test per modulo, più test_e2e_mos.py
```

---

### Task 1: Scheletro, errori, testo

**Files:** `pyproject.toml`, `.python-version`, `src/cycle_validation/{__init__,errors,text}.py`, `tests/test_text.py`

**Produces:**
- `errors.py`: `CycleValidationError` (base); `ConfigError`; `IngestError(message, http_status=422)`; `ExtractionError`; `KnowledgeError` (knowledge base non caricabile: run fallito); `SourceUnavailableError` (sorgente non raggiungibile durante un controllo: warning); `ProfileUnavailableError`.
- `text.py`: `normalize_code(value: str) -> str` (maiuscole, senza spazi); `squash(value: str) -> str` (senza spazi, casefold, NFKC); `normalize_quote(value: str) -> str` (spazi compressi, casefold, NFKC, trattini e apici unificati).

- [ ] Test: codici con spazi e minuscole coincidono; citazioni con a capo e doppi spazi coincidono; trattini tipografici equivalgono a `-`.
- [ ] Implementazione, `uv sync`, `uv run pytest`, commit.

### Task 2: Modello di dominio

**Files:** `domain/{__init__,cycle,check,report}.py`, `tests/test_domain.py`

**Produces:**
- `Source(manual, task?, repair_code?, page?)`; `ProcessSheet(code, …campi extra ammessi)`; `Operation(operation_number, operation_description, repair_code?, machine_tag?, task_codes: list[str], process_sheet?, page?)`; `Cycle(cycle_code?, cycle_description?, engine_model?, operation_type?, repair_code?, sources, operations)`. Stringhe ripulite; stringa vuota → `None` nei campi opzionali.
- `Verdict`, `Reason`, `REASON_VERDICT: dict[Reason, Verdict]`, `CheckName`, `TargetKind`, `Target(kind, index?, label)` con `Target.cycle()`, `Target.source(i, source)`, `Target.operation(i, operation)`.
- `Evidence(document_key, version?, page?, line?, quote)`; `Usage(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd, duration_ms, turns, sessions)` con somma.
- `CheckResult(check, target, verdict, reason, rationale, evidence, decided_by: "code"|"agent", usage)`. Validazione: `reason` coerente con `verdict`; se `decided_by="agent"` e l'esito è `CORRETTO` o `ERRATO`, `evidence` non vuota.
- `CycleStatus(COMPLETO, BLOCCATO, PARZIALE)`, `PipelineError(stage, target, message)`, `RunMeta`, `Counts(total, corretto, warning, errato, non_applicabile, errors_ratio)`, `Report`.

- [ ] Test: ogni `Reason` ha un `Verdict`; `CheckResult` incoerente rifiutato; `CORRETTO` dell'agente senza evidenza rifiutato; somma di `Usage`; ciclo con campi vuoti normalizzato.
- [ ] Implementazione, test, commit.

### Task 3: Configurazione

**Files:** `config.py`, `config/settings.yaml`, `config/profiles/{mos,dr,ej200}.yaml`, `tests/test_config.py`

**Produces:**
- `AgentSettings(model="haiku", effort=None, use_bedrock=True, aws_region=None, max_turns=10, inline_max_turns=3, concurrency=6, retries=2, retry_backoff_s=2.0, invalid_output_retries=1, read_limit=40, read_window=30, read_before=15, grep_max_context=10, inline_max_lines=150, citation_window=3, save_transcripts=True)`.
- `PathSettings(profiles_dir, prompts_dir, knowledge_dir, runs_dir, machines_file?)`, relativi alla cartella di lavoro.
- `Settings(agent, paths)`; `load_settings(path: Path | None) -> Settings`.
- `FileLimits(require_pdf_header, max_bytes?, max_pages?, min_chars=100)`; `ProfileConfig(name, enabled, disabled_reason, file_limits, checks, blocking_checks, excluded_sheet_prefixes, engine_families, verify_process_sheet)`; `load_profile(name, profiles_dir) -> ProfileConfig`.
- Errori di validazione tradotti in `ConfigError` con file, campo e problema.

Profili: `mos` attivo; `dr` ed `ej200` dichiarati con `enabled: false` e motivo (arrivano nelle fasi 4 e 5). EJ200: `max_bytes` 20 MB, `max_pages` 60.

- [ ] Test: valori predefiniti; file con campo sconosciuto o valore fuori intervallo → `ConfigError` che nomina il campo; profilo inesistente → `ConfigError`; i tre profili del repo si caricano.
- [ ] Implementazione, test, commit.

### Task 4: Ingest del PDF

**Files:** `ingest/{__init__,pdf}.py`, `tests/conftest.py` (fabbrica `build_pdf`, fixture `make_pdf`), `tests/test_ingest.py`

**Produces:** `PdfPage(number, text)`; `PdfDocument(name, sha256, size_bytes, pages)` con `text` e `n_chars`; `read_pdf(path: Path, limits: FileLimits) -> PdfDocument`.

Rifiuti (`IngestError`): file assente (400); intestazione `%PDF-` assente nei primi 1024 byte (415); oltre `max_bytes` o `max_pages` (413); non apribile (422); meno di `min_chars` caratteri (422, con nota che l'OCR non è supportato). La corrispondenza esatta con i codici HTTP attuali è da verificare.

- [ ] Test: testo per pagina senza `\r`; hash stabile; ciascun rifiuto con il suo codice.
- [ ] Implementazione, test, commit.

### Task 5: Knowledge base e registro macchine

**Files:** `kb/{__init__,port,documents,memory,local}.py`, `services/{__init__,machines}.py`, `tests/kb_fixtures.py`, `tests/test_kb_contract.py`, `tests/test_kb_local.py`, `tests/test_machines.py`

**Produces:**
- `DocumentInfo(key, version?, title, path)`; `TaskLocation(manual_key, task, document, line_start, line_end)` con `n_lines`; `MachineTagEntry(tag, function?)`; `ProcessSheetEntry(code, edition?, treatment?, engine_families)`.
- Porta `KnowledgeBase`: `version: str`; `find_manual(manual) -> DocumentInfo | None`; `find_task(manual, task) -> TaskLocation | None`; `find_machine_tag(tag) -> MachineTagEntry | None`; `find_process_sheet(code) -> ProcessSheetEntry | None`; `stats() -> dict[str, int]`.
- `kb/documents.py`: `read_lines(path) -> tuple[str, ...]` (in cache); `page_at(path, line) -> int | None`; marcatore `<!-- page N -->`.
- `IndexedKnowledgeBase(version, documents, aliases, tasks, machine_tags, process_sheets)`.
- `load_local_knowledge(directory: Path) -> IndexedKnowledgeBase`; formato della cartella nel design §6.2. Ogni difetto (cartella o manifest assente, JSON non valido, file di documento mancante, intervallo di righe fuori dal file, chiavi duplicate) → `KnowledgeError` che dice dove.
- Porta `MachineRegistry`: `is_active(tag) -> bool`. `StaticMachineRegistry(active)`; `UnavailableMachineRegistry(reason)` solleva `SourceUnavailableError`; `load_machine_registry(path | None)`.

- [ ] Test di contratto, parametrizzati su knowledge base costruita in memoria e caricata da cartella: manuale per chiave e per alias, senza distinzione di maiuscole e spazi; task trovato e non trovato; targa; scheda; `stats`.
- [ ] Test del caricamento: ogni difetto dà il suo messaggio. Test di `page_at`. Test del registro macchine.
- [ ] Implementazione, test, commit.

### Task 6: Controlli a codice

**Files:** `resolve/{__init__,civil}.py`, `checks/{__init__,base,source,task_code,machine_tag,process_sheet}.py`, `extract/{__init__,base,from_file,integrity}.py`, `tests/test_checks_code.py`, `tests/test_integrity.py`

**Produces:**
- `CheckContext(cycle, kb, machines, profile)`; `make_result(check, target, reason, rationale, *, evidence=(), decided_by="code", usage=None) -> CheckResult`; `evidence_at(document, line) -> Evidence`.
- `resolve/civil.py`: `manuals_for_operation(cycle, operation) -> list[str]` (fonti con lo stesso `repair_code`, altrimenti tutte); `OperationRefs(found, missing)`; `resolve_operation(cycle, operation, kb) -> OperationRefs`; `context_locations(cycle, operation, kb) -> tuple[TaskLocation, ...]` (task dell'operazione, altrimenti task delle fonti collegate).
- `check_sources(ctx)`, `check_task_codes(ctx)`, `check_machine_tags(ctx)`, `check_process_sheets(ctx)`: ciascuno `-> list[CheckResult]`, una riga per fonte o per operazione.
- `CycleExtractor` (porta, `extract(pdf) -> Cycle`); `FileCycleExtractor(path)`.
- `IntegrityOutcome(results, unconfirmed: frozenset[tuple[CheckName, TargetKind, int]])`; `check_extraction_integrity(cycle, pdf) -> IntegrityOutcome`.

Regole:

| Controllo | Situazione | Esito |
|---|---|---|
| `source` | manuale non trovato; task non trovato nel manuale | `WARNING` / `FONTE_ASSENTE` |
| | trovato | `CORRETTO`, evidenza: prima riga del task |
| `task_code` | nessun task code | `NON_APPLICABILE` / `CAMPO_ASSENTE` |
| | almeno un codice non trovato nei manuali collegati | `WARNING` / `FONTE_ASSENTE` |
| | tutti trovati | `CORRETTO` |
| `machine_tag` | targa assente | `NON_APPLICABILE` / `CAMPO_ASSENTE` |
| | macchina non attiva nel registro | `ERRATO` / `MACCHINA_NON_ATTIVA` |
| | registro non raggiungibile | `WARNING` / `ERRORE_TECNICO` |
| | attiva ma assente dai dati TM | `WARNING` / `FONTE_ASSENTE` |
| | attiva e presente | `CORRETTO` |
| `process_sheet` | scheda assente | `NON_APPLICABILE` / `CAMPO_ASSENTE` |
| | profilo che non verifica le schede | `NON_APPLICABILE` / `NON_VERIFICATO_PER_PROFILO` |
| | prefisso escluso | `NON_APPLICABILE` / `ESCLUSO_DA_REGOLA` |
| | non trovata | `WARNING` / `FONTE_ASSENTE` |
| | trovata ma non per la famiglia del motore | `WARNING` / `EVIDENZA_NON_TROVATA` |
| | trovata e applicabile | `CORRETTO` |
| tutti | sorgente non raggiungibile | `WARNING` / `ERRORE_TECNICO` |
| `extraction_integrity` | numero operazione, targa, task code, scheda o task della fonte assenti dal testo del PDF | `WARNING` / `ESTRAZIONE_NON_CONFERMATA` sull'elemento |

- [ ] Test: una prova per riga della tabella.
- [ ] Implementazione, test, commit.

### Task 7: Citazioni

**Files:** `verdict/{__init__,citations}.py`, `tests/test_citations.py`

**Produces:** `Citation(file, line, quote)`; `verify_citation(citation, allowed: Sequence[DocumentInfo], window: int) -> Evidence | None`.

Regole: il file deve essere uno dei documenti ammessi (percorso, nome del file o chiave); la citazione normalizzata, di almeno 8 caratteri, deve comparire nelle righe `line ± window`; l'evidenza riporta documento, versione, pagina e la riga in cui la citazione inizia.

- [ ] Test: citazione esatta; con spazi e maiuscole diversi; su due righe; riga spostata entro la finestra; riga fuori finestra; file non ammesso; testo inventato; citazione troppo corta; riga oltre la fine del file.
- [ ] Implementazione, test, commit.

### Task 8: Hook GRASP

**Files:** `agent/{__init__,hooks}.py`, `tests/test_hooks.py`

**Produces:** `ALLOWED_TOOLS = ("Read", "Grep")`; `ToolPolicy(allowed_files: frozenset[Path], base_dir: Path, read_limit, read_window, read_before, grep_max_context)`; `Decision(allowed, reason)`; `check_tool_call(tool_name, tool_input, policy) -> Decision`; `make_pre_tool_use_hook(policy)`.

Regole: `Read` solo su file ammessi e solo con `limit` intero tra 1 e `read_limit`; `Grep` solo con `path` uguale a un file ammesso e contesto entro `grep_max_context`; ogni altro tool rifiutato. Il rifiuto spiega come richiamare il tool correttamente. Formato del rifiuto verso l'SDK: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": …}}`; nessuna obiezione → `{}`.

- [ ] Test: lettura a finestra ammessa; senza `limit`, con `limit` oltre soglia, zero, negativo, booleano o stringa → rifiuto; file non ammesso, anche nella stessa cartella → rifiuto; `Grep` senza `path` o su cartella → rifiuto; altri tool → rifiuto; formato dell'hook.
- [ ] Implementazione, test, commit.

### Task 9: Sessione e runner

**Files:** `agent/{session,runner}.py`, `tests/fakes.py` (`ScriptedSession`), `tests/test_runner.py`

**Produces:**
- `SessionStatus(OK, MAX_TURNS, ERROR, INVALID_OUTPUT)`; `SessionRequest(session_id, prompt, allowed_files, use_tools, max_turns, output_schema)`; `SessionOutcome(status, output?, error, usage, attempts)`; porta `AgentSession.run(request) -> SessionOutcome`.
- `run_sessions(session, requests, *, concurrency, retries, backoff_s, invalid_output_retries, validate=None, sleep=asyncio.sleep) -> list[SessionOutcome]`.

Regole: ordine dei risultati uguale a quello delle richieste; al più `concurrency` sessioni insieme; `ERROR` o eccezione → fino a `retries` nuovi tentativi con attesa crescente; output che non passa `validate` → `INVALID_OUTPUT`, fino a `invalid_output_retries` nuovi tentativi; `MAX_TURNS` non si ritenta; i consumi di tutti i tentativi si sommano; un guasto non tocca le altre sessioni.

- [ ] Test: uno per regola.
- [ ] Implementazione, test, commit.

### Task 10: Giudizio per operazione e adattatore SDK

**Files:** `agent/{prompt,sdk_session}.py`, `checks/operation.py`, `prompts/operation_check.md`, `tests/test_operation_check.py`, `tests/test_sdk_session.py`

**Produces:**
- `Judgement(COERENTE, CONTRADDETTO, NON_VERIFICABILE)`; `OperationJudgement(judgement, rationale, citations)`; `judgement_schema() -> dict`; `load_system_prompt(prompts_dir) -> str`; `prompt_version(text) -> str`; `build_operation_prompt(cycle, operation, facts, locations, *, inline, settings) -> str`.
- `OperationJob(index, operation, locations, request)`; `plan_operation_checks(ctx, settings) -> tuple[list[OperationJob], list[CheckResult]]`; `decide_operation(job, outcome, settings) -> tuple[CheckResult, PipelineError | None]`; `check_operations(ctx, session, settings) -> tuple[list[CheckResult], list[PipelineError]]`.
- `SdkAgentSession(settings, system_prompt, transcripts_dir?)`; `outcome_from_result(result) -> SessionOutcome`; `build_options(request)`.

Regole:

| Situazione | Esito |
|---|---|
| descrizione vuota | `NON_APPLICABILE` / `CAMPO_ASSENTE` |
| nessun riferimento risolto | `WARNING` / `FONTE_ASSENTE`, nessuna sessione |
| testo ≤ `inline_max_lines` righe | sessione senza tool, testo nel messaggio con numeri di riga |
| testo più lungo | sessione con `Read` e `Grep` sui soli documenti dell'operazione |
| `contraddetto` con citazione verificata | `ERRATO` / `CONTRADDIZIONE` |
| `coerente` con citazione verificata | `CORRETTO` / `VERIFICATO` |
| `non_verificabile` | `WARNING` / `EVIDENZA_NON_TROVATA` |
| `coerente` o `contraddetto` senza citazione verificata | `WARNING` / `CITAZIONE_NON_VERIFICATA` |
| limite di turni | `WARNING` / `BUDGET_ESAURITO` |
| errore tecnico o output non conforme dopo i tentativi | `WARNING` / `ERRORE_TECNICO` più `PipelineError` |

Opzioni SDK: `tools` e `allowed_tools` uguali a `Read`, `Grep` oppure vuoti; `permission_mode="dontAsk"`; `setting_sources=[]`; `strict_mcp_config=True`; `output_format` con lo schema; hook `PreToolUse` solo con i tool; variabili d'ambiente Bedrock da configurazione, senza credenziali.

- [ ] Test: una prova per riga della tabella, con `ScriptedSession`; scelta in linea / in ricerca; contenuto del messaggio; opzioni dell'SDK costruite senza avviare processi; traduzione del messaggio finale dell'SDK.
- [ ] Implementazione, test, commit.

### Task 11: Consolidamento

**Files:** `verdict/consolidate.py`, `tests/test_consolidate.py`

**Produces:** `expected_rows(cycle, checks) -> list[tuple[CheckName, Target]]`; `apply_integrity(results, unconfirmed) -> list[CheckResult]`; `blocked_results(cycle, checks, blocked_by: CheckResult) -> list[CheckResult]`; `is_blocking_failure(result) -> bool`; `compute_counts(results) -> Counts`; `cycle_status(results, *, blocked, pipeline_errors) -> CycleStatus`.

Regole: un esito `CORRETTO` o `ERRATO` su un valore non confermato dall'integrità diventa `WARNING` / `ESTRAZIONE_NON_CONFERMATA`; un controllo bloccante fallisce se un suo esito non è `CORRETTO` né `NON_APPLICABILE`, e i controlli a valle escono `WARNING` / `BLOCCATO_A_MONTE`; i conteggi escludono `extraction_integrity`; `errors_ratio = errati / (totale − non applicabili)`, tra 0 e 1; stato `BLOCCATO` se bloccato, `PARZIALE` se ci sono errori di pipeline, `ERRORE_TECNICO` o `BUDGET_ESAURITO`, altrimenti `COMPLETO`.

- [ ] Test: uno per regola.
- [ ] Implementazione, test, commit.

### Task 12: Report

**Files:** `report/{__init__,builder,markdown_writer,legacy_payload}.py`, `tests/test_report.py`

**Produces:** `build_report(meta, cycle, results, *, timings_ms, pipeline_errors, blocked) -> Report`; `render_markdown(report) -> str`; `build_legacy_payload(report) -> dict[str, Any]`; `feedback_text(result | None) -> str`; `write_outputs(report, run_dir) -> None` (`cycle.json`, `report.json`, `report.md`, `payload.json`).

Payload: `sources[]` con `repairCode`, `manual`, `task`, `sourceFeedback`; `operations[]` con `operationNumber`, `repairCode`, `operationDescription`, `targaCResp`, `taskCodeCited`, `scheda`, `operationFeedback`, `targaCRespFeedback`, `taskCodeFeedback`, `schedaFeedback`; `cycle_errors_count`; `cycle_errors_count_perc`; `profile` (tempi per stadio); `_pipeline_errors`.

Feedback: `No errors found.`; `Error found: <motivazione>`; `Warning: <motivazione>`; `N/A - <motivazione>`; controllo non eseguito → `N/A`.

Da verificare sul codice attuale: forma di `taskCodeCited` (qui stringa con i codici separati da virgola), di `scheda`, di `profile` e di `_pipeline_errors`.

- [ ] Test: i quattro prefissi; payload con tutte le chiavi; Markdown con una riga per operazione e una colonna per controllo; `report.json` rileggibile come `Report`.
- [ ] Implementazione, test, commit.

### Task 13: Pipeline, CLI, esempio, README

**Files:** `pipeline.py`, `cli.py`, `examples/sintetico/…`, `README.md`, `tests/test_e2e_mos.py`, `tests/test_cli.py`

**Produces:**
- `RunRequest(pdf_path, profile, selectors, skip_checks)`; `Dependencies(settings, profile, kb, machines, extractor, session, prompt_version)`; `run_validation(request, deps, run_dir: Path | None) -> Report`.
- `cycle-validation run PDF --profile mos --cycle-json FILE [--knowledge DIR] [--machines FILE] [--config FILE] [--out DIR] [--skip-check NOME]`; `cycle-validation kb-check DIR`.

Regole: profilo non attivo → errore chiaro, nessun run; ciclo senza operazioni → run fallito; knowledge base non caricabile → run fallito; `--skip-check` toglie un controllo (nel payload esce `N/A`); senza `--cycle-json` errore che spiega che l'estrattore arriva in Fase 3.

- [ ] Test end-to-end MOS sull'esempio sintetico con `ScriptedSession`: un'operazione corretta, una contraddetta, una con macchina non attiva, una con scheda esclusa, una con riferimento assente; payload e report scritti; conteggi attesi.
- [ ] Test CLI: `kb-check` sull'esempio; `run` con `--skip-check operation_description`; profilo `dr` rifiutato.
- [ ] Implementazione, suite completa, `ruff`, `mypy`, commit.

---

## Fuori da questa fase

- Estrattore LLM e parser di layout (Fase 3), logica DR (Fase 4), EJ200 (Fase 5), API (Fase 6).
- Adattatori su S3, OpenSearch, Redshift (Fase 2 e 6).
- Smoke test reale su Bedrock: è `cycle-validation run` sull'esempio sintetico senza `--skip-check`, da eseguire dove ci sono le credenziali.
