# Indice della conoscenza per cycle-validation-v2 · piano di implementazione

> **Per gli agenti:** SUB-SKILL RICHIESTA: `superpowers:executing-plans` (in linea, regola di `AGENTS.md`) oppure `superpowers:subagent-driven-development`. I passi usano le caselle (`- [ ]`).

**Obiettivo:** alla fine di ogni giro `run`, costruire dai JSON già salvati un indice per codice nel formato letto da `cycle-validation-v2` e pubblicarlo su S3 come fotografia completa con puntatore.

**Architettura:** nuovo pacchetto `src/ingestion/knowledge/` con quattro moduli indipendenti dal trasporto: testo a righe e intervalli dei task (`text.py`), voci per tipo di documento (`entries.py`), costruzione e validazione dell'indice (`build.py`), pubblicazione con puntatore (`publish.py`). `batch.run` lo chiama dopo l'elaborazione dei documenti; un comando locale lo costruisce da un archivio su disco. Nessuna chiamata al modello: l'indice si ricava solo dai record.

**Tecnologie:** Python 3.12, Pydantic, pytest, Ruff. Nessuna nuova dipendenza.

**Specifica:** la conversazione del 16/11/2026 (decisioni sotto) e il formato letto da cycle-validation-v2: `kb/local.py`, `kb/documents.py`, `kb/structured.py`, `kb/ej200.py`, `resolve/dr.py`.

---

## Decisioni di partenza (persona, 16/11/2026)

- **Indice per codice, non indice semantico:** v2 trova file e righe dal codice citato.
- **Posizione:** `Manufacturing AI/cv3/knowledge/<programma>/` (nello store: `knowledge/<programma>/`).
- **Documenti `needs_review`:** inclusi con `partial: true`. Documenti `blocked`: inclusi con `published: false` (v2 li segnala come «fonte non pubblicata», non come assenti).
- **Alias:** automatici (chiave, codice) più un file `aliases.json` mantenuto da una persona. Quali nomi usano davvero i cicli resta da ricavare dai cicli reali (punto aperto, non bloccante).

---

## Vincoli globali

- Nessuna chiamata a Bedrock o AWS nei test; nessuna nuova dipendenza; nessuna modifica a `indexing/`, a `docs/` o alle repo del collega.
- Nessun commit, ramo o push senza autorizzazione registrata in `metodo/stato.yaml` (D-121); i passi «Checkpoint» si fermano alla verifica.
- Nei log e nel report solo chiavi, codici e conteggi, mai testo dei documenti (D-10).
- Il formato scritto deve passare i lettori di v2 senza modifiche, tranne il puntatore (sezione «Fuori da questo piano»).
- Righe contate da 1; marcatore di pagina esattamente `<!-- page N -->` su una riga a sé.
- Procedure DR per v2: `repair` -> `"Repair"`, `accept_as_is` -> `"Accept as is"`, `reject` -> `"Reject"` (v2 confronta `"accept as is"` e `"reject"` dopo la normalizzazione).
- Tipo RI nel catalogo EJ200: `kind: "EF"` (convenzione di v2 e nome della cartella su S3).
- Comandi: `uv run pytest -q <percorsi>` e `uv run ruff check src tests`.

---

## Formato pubblicato

```text
knowledge/<programma>/
├── current.json                 {"format": 1, "version": "<run_id>", "prefix": "knowledge/<programma>/v/<run_id>/"}
├── aliases.json                 facoltativo, scritto da una persona: {"<chiave o codice>": ["alias", ...]}
└── v/<run_id>/
    ├── manifest.json            civil: documenti RM, SPM, DR_PROC
    ├── documents/<chiave>.md
    ├── tasks.json
    ├── structured/TM/tm.json    civil
    ├── structured/SP/sp.json    civil
    ├── structured/DR/dr.json    civil
    ├── catalog.json             ej200: RDR, RN, RI
    └── text/<document_id>/<content_hash>.md  ej200
```

---

## Punti da verificare in revisione

- **Intestazione ripetuta (`TASK 72-00-01-110-001` in cima a ogni pagina):** un solo intervallo, che arriva fino al task successivo diverso. Test in Task 1.
- **Codice citato dentro un altro task (`Refer to TASK 72-00-01-220-002`):** non apre un nuovo intervallo. Test in Task 1.
- **Riga DR senza serial o senza decisione:** esclusa e contata. Una sola riga non valida fa rifiutare a v2 tutta la conoscenza. Test in Task 2.
- **Giro con molti documenti mancanti o elenco della sorgente incompleto:** il puntatore non si sposta. Test in Task 4 e Task 5.
- **Due edizioni della stessa tabella SP o due file RDR con lo stesso `rdr_no` e la stessa issue:** una sola voce, scelta deterministica, conflitto nel riepilogo. Test in Task 2 e Task 3.

---

## Task 1: Testo a righe e intervalli dei task

### File:
- **Crea:** `src/ingestion/knowledge/__init__.py` (vuoto), `src/ingestion/knowledge/text.py`
- **Test:** `tests/knowledge/test_knowledge_text.py`

### Interfacce:
- **Usa:** `PageResult` (`ingestion.models`), `TASK_CODE_RE` (`ingestion.extractors.manual`).
- **Produce:**
  - `pages_text(pages: Sequence[PageResult]) -> list[str]`: per ogni pagina, prima il marcatore e poi le righe di `page.text.lines`. Una pagina senza testo diventa `[pagina N non letta]`.
  - `markdown_pages_text(page_markdown: Mapping[int, str]) -> list[str]`: stessa forma per RN/RI.
  - `task_ranges(lines: Sequence[str]) -> dict[str, tuple[int, int]]`: codice -> (riga iniziale, riga finale), da 1 e incluse.

### Regola di `task_ranges`:
- una riga apre un task solo se, togliendo gli spazi iniziali, comincia con il codice o con `TASK` seguito dal codice (maiuscole e minuscole indifferenti);
- un'altra riga che apre lo stesso codice non chiude né riapre l'intervallo;
- il task finisce alla riga prima dell'apertura di un codice diverso oppure all'ultima riga;
- un codice senza riga di apertura non ha intervallo.

### Passi:
- [ ] **Passo 1:** scrivere i test che falliscono
```python
def test_pages_text_marks_each_page_and_unread_pages():
    lines = pages_text([page(1, ["A", "B"]), page(2, None)])
    assert lines == ["<!-- page 1 -->", "A", "B", "<!-- page 2 -->", "[pagina 2 non letta]"]


def test_task_range_runs_to_next_task():
    lines = [
        "<!-- page 1 -->",
        "TASK 72-00-01-110-001 - PULIZIA",
        "1. a",
        "2. b",
        "TASK 72-00-01-220-002 - ISPEZIONE",
        "1. c",
    ]
    assert task_ranges(lines) == {"72-00-01-110-001": (2, 4), "72-00-01-220-002": (5, 6)}


def test_repeated_heading_on_next_page_extends_the_same_task():
    lines = [
        "<!-- page 1 -->",
        "TASK 72-00-01-110-001",
        "x",
        "<!-- page 2 -->",
        "TASK 72-00-01-110-001",
        "y",
        "TASK 72-00-01-220-002",
        "z",
    ]
    assert task_ranges(lines)["72-00-01-110-001"] == (2, 6)


def test_cross_reference_does_not_open_a_task():
    lines = ["TASK 72-00-01-110-001", "Refer to TASK 72-00-01-220-002", "end"]
    assert task_ranges(lines) == {"72-00-01-110-001": (1, 3)}
```
*`page(n, lines)` è un helper del test che costruisce un `PageResult` con `PageText` nativo, oppure `text=None`.*

- [ ] **Passo 2:** `uv run pytest -q tests/knowledge/test_knowledge_text.py`. Risultato atteso: `FAIL (ModuleNotFoundError)`.
- [ ] **Passo 3:** implementare le tre funzioni in `text.py`.
- [ ] **Passo 4:** rieseguire lo stesso comando. Risultato atteso: tutti passati.
- [ ] **Passo 5:** checkpoint. `uv run ruff check src/ingestion/knowledge tests/knowledge` pulito; commit solo se autorizzato.

---

## Task 2: Voci dell'indice per tipo di documento

### File:
- **Crea:** `src/ingestion/knowledge/entries.py`
- **Test:** `tests/knowledge/test_knowledge_entries.py`

### Interfacce:
- **Usa:** `load_record(kind, data)` (`ingestion.documents`), i modelli di `ingestion.models` ed `ingestion.extractors.repair.RepairExtraction`, e da Task 1 `pages_text`, `markdown_pages_text` e `task_ranges`.
- **Produce, con classi Contract congelate:**
  - `Bundle(key: str, doc_type: DocType, status: str, record_json: bytes)`: `key` è il nome della cartella del documento;
  - `ManualDoc(key, code, version, title, kind, published, partial, lines: list[str], tasks: dict[str, tuple[int, int]])`;
  - `TagRow(tag, function)`;
  - `SheetRow(code, edition, treatment, engine_families: list[str], table_id: str, edition_rank: tuple[int, str])` (numero dell'edizione e data AAAAMMGG da `document.version.label`, es. `ed42_20260504` -> `(42, "20260504")`);
  - `DrRow(serial_number, conditions: list[int], procedure, reference, tasks: list[str])`;
  - `CatalogDoc(code, kind, issue, document_id, content_hash, title, published, partial, references: list[str], lines: list[str])`;
  - `entries_for(bundle: Bundle) -> Entries`, dove `Entries` contiene le liste `manuals`, `tags`, `sheets`, `dr`, `catalog` e `dropped: list[str]` (codici dei motivi, mai testo).

### Corrispondenze:

| Tipo | Voce | Campi |
| :--- | :--- | :--- |
| **RM, SPM** | `ManualDoc` | `code=document.doc_code`, `version=document.version.label`, `lines=pages_text`, `tasks=task_ranges(lines)` |
| **DR_PROC** | `ManualDoc` | `code = numero DR dal nome`; `lines = titoli e paragrafi delle sezioni, un marcatore di pagina per sezione` |
| **TM** | `TagRow` | una riga per targa; `function = "; ".join(functions)`; righe annullata o senza targa scartate |
| **SP** | `SheetRow` | `code=scheda`, `treatment=trattamento`, `edition=extraction.edition`; `engine_families` contiene `"GENX"` se genx è valorizzato e `"LEAP"` se leap è valorizzato; righe annullata scartate |
| **DR** | `DrRow` | `procedure` secondo la mappa dei vincoli; `reference=document.doc_code`; scartate con motivo `dr_row_no_serial` o `dr_row_no_decision` |
| **RDR** | `CatalogDoc` | `code=rdr_no`, `issue=issue_no`, `kind="RDR"`, `references=[rdr_base]` se diverso; senza `rdr_no`: scartato (`rdr_no_code`) |
| **RN, RI** | `CatalogDoc` | `code=document_code`, `issue=issue`, `kind "RN"` o `"EF"`, `lines=markdown_pages_text(page_markdown)` |

*Per ogni voce documento: `published = status != "blocked"`, `partial = status == "needs_review"`. Nel catalogo, `content_hash` sono i primi 16 caratteri del sha256 di `"\n".join(lines)` e `document_id = bundle.key`.*

### Passi:
- [ ] **Passo 1:** scrivere i test che falliscono, uno per riga della tabella, con record sintetici costruiti con i modelli. Asserzioni chiave:
```python
assert dr.procedure == "Accept as is" and dr.conditions == [2]
assert entries_for(dr_bundle_with_none_serial).dr == [] and "dr_row_no_serial" in ...dropped
assert sheet.engine_families == ["GENX"]
assert rdr.code == "RDR-9A" and rdr.references == ["RDR-9"]
assert ri.kind == "EF"
assert manual.partial is True    # stato needs_review
assert blocked.published is False
```
- [ ] **Passo 2:** `uv run pytest -q tests/knowledge/test_knowledge_entries.py`. Risultato atteso: `FAIL`.
- [ ] **Passo 3:** implementare `entries_for` e le classi in `entries.py`.
- [ ] **Passo 4:** rieseguire. Risultato atteso: tutti passati.
- [ ] **Passo 5:** checkpoint (Ruff; commit solo se autorizzato).

---

## Task 3: Costruzione e validazione dell'indice

### File:
- **Crea:** `src/ingestion/knowledge/build.py`
- **Test:** `tests/knowledge/test_knowledge_build.py`

### Interfacce:
- **Usa da Task 2:** `Bundle`, `entries_for` e le voci.
- **Produce:**
  - `KnowledgeIndex(version: str, files: dict[str, bytes], counts: dict[str, int], conflicts: list[str], dropped: dict[str, int])`, con percorsi relativi alla cartella della versione;
  - `build_index(program: Program, bundles: Iterable[Bundle], *, version: str, aliases: Mapping[str, list[str]]) -> KnowledgeIndex`;
  - `parse_aliases(data: bytes | None) -> dict[str, list[str]]`: `None` diventa un dizionario vuoto; un JSON non valido produce `ValueError("aliases.json")`.

### Regole:
- `civil` scrive `manifest.json` (`format: 1`, `version`; documenti ordinati per chiave, con `file: "documents/<chiave>.md"` e `alias = aliases[chiave] U aliases[codice]`), `documents/<chiave>.md`, `tasks.json` e i tre file `structured/*/*.json`, anche se vuoti come lista `[]`;
- `ej200` scrive `catalog.json`, ordinato per `(codice, issue)`, e i file `text/<document_id>/<content_hash>.md`;
- **SP:** per ogni `table_id` resta solo l'edizione con il `edition_rank` più alto; le altre vanno in `conflicts` come `sp_older_edition:<table_id>`;
- **catalogo:** per due voci con lo stesso `(codice, issue)` resta quella con `document_id` minore; l'altra va in `conflicts` come `catalog_duplicate:<codice>`;
- **riga DR con manual:** se tutti i suoi tasks stanno in un solo `ManualDoc`, `manual` è la chiave di quel documento; altrimenti `null`;
- **controlli prima di restituire l'indice, con gli stessi criteri dei lettori di v2:** chiavi uniche, ogni intervallo dentro il proprio file, ogni riga DR con serial e procedura. Una violazione produce `ValueError` con il solo codice del controllo.

### Passi:
- [ ] **Passo 1:** scrivere i test che falliscono
```python
def test_civil_index_files_and_manifest():
    index = build_index(
        Program.civil, [spm, tm, sp, dr], version="v1", aliases={"GEK9250": ["GEK 9250"]}
    )
    assert set(index.files) == {
        "manifest.json",
        "documents/SPM_X.md",
        "tasks.json",
        "structured/TM/tm.json",
        "structured/SP/sp.json",
        "structured/DR/dr.json",
    }
    manifest = json.loads(index.files["manifest.json"])
    assert manifest["documents"][0]["aliases"] == ["GEK 9250"]


def test_task_lines_point_inside_the_written_file(): ...  # rilegge il .md e confronta le righe


def test_older_sp_edition_is_dropped_and_reported(): ...  # conflicts == ["sp_older_edition:fpi"]


def test_duplicate_catalog_code_and_issue_keeps_one(): ...


def test_dr_manual_resolved_only_when_unique(): ...


def test_bad_aliases_json_is_an_error():
    with pytest.raises(ValueError, match="aliases.json"):
        parse_aliases(b"{")
```
- [ ] **Passo 2:** `uv run pytest -q tests/knowledge/test_knowledge_build.py`. Risultato atteso: `FAIL`.
- [ ] **Passo 3:** implementare `build.py`. Il JSON va scritto con `ensure_ascii=False`, `indent=2` e una riga finale vuota, così lo stesso input produce sempre gli stessi byte.
- [ ] **Passo 4:** rieseguire. Risultato atteso: tutti passati.
- [ ] **Passo 5:** checkpoint.

---

## Task 4: Pubblicazione con puntatore

### File:
- **Crea:** `src/ingestion/knowledge/publish.py`
- **Modifica:** `src/ingestion/batch.py`, aggiungendo `def list(self, prefix: str) -> Listing: ...` al protocollo `OutputStore` (`S3ObjectStore` lo ha già)
- **Modifica:** `tests/platform/test_run_batch.py`, aggiungendo a `FakeStore` il metodo `list(prefix) -> Listing(keys=self.keys(prefix), complete=True)`
- **Test:** `tests/knowledge/test_knowledge_publish.py`

### Interfacce:
- **Usa:** `KnowledgeIndex` (Task 3), `OutputStore` e `Listing` (`ingestion.publish.snapshot`).
- **Produce:**
  - `PublishResult(status: Literal["published", "unchanged", "drop_blocked", "pointer_conflict"], version: str | None, previous: str | None, documents: int)`;
  - `publish_index(store: OutputStore, program: Program, index: KnowledgeIndex, *, max_drop_percent: int = 10, keep: int = 3) -> PublishResult`;
  - la costante `DOCUMENT_FILES = ("manifest.json", "catalog.json")`, che indica dove contare i documenti.

### Ordine delle operazioni:
1. leggere `knowledge/<p>/current.json`;
2. se la fotografia corrente ha esattamente gli stessi byte, restituire `unchanged` senza scrivere nulla;
3. se i documenti scendono di più del `max_drop_percent` rispetto alla fotografia corrente, restituire `drop_blocked` senza scrivere nulla;
4. scrivere tutti i file sotto `v/<version>/`, con `manifest.json` o `catalog.json` per ultimo;
5. spostare il puntatore con `put_if_match` sull'Etag letto, oppure `put_if_absent` se non esiste. Se la scrittura fallisce, restituire `pointer_conflict`;
6. cancellare le versioni sotto `v/` oltre le ultime `keep`, mai quella corrente.

### Passi:
- [ ] **Passo 1:** scrivere i test che falliscono: `test_first_publish_writes_version_then_pointer` (l'ordine delle scritture registrato da un fake), `test_same_index_is_unchanged`, `test_drop_over_ten_percent_keeps_old_pointer` (10 -> 8 documenti: `drop_blocked`, puntatore invariato), `test_pointer_moved_meanwhile_is_a_conflict` e `test_old_versions_pruned_keep_three`.
- [ ] **Passo 2:** `uv run pytest -q tests/knowledge/test_knowledge_publish.py`. Risultato atteso: `FAIL`.
- [ ] **Passo 3:** implementare `publish.py` e aggiungere `list` al protocollo e al fake.
- [ ] **Passo 4:** `uv run pytest -q tests/knowledge tests/platform/test_run_batch.py`. Risultato atteso: tutti passati.
- [ ] **Passo 5:** checkpoint.

---

## Task 5: Indice alla fine del giro `run`

### File:
- **Modifica:** `src/ingestion/batch.py`: funzione `run`, classi `RunReport`, `render_report` e `run_notification`
- **Test:** `tests/platform/test_run_batch.py`

### Interfacce:
- **Usa:** Task 3 (`build_index`, `parse_aliases`), Task 4 (`publish_index`) e `Bundle`.
- **Produce:** `RunReport.knowledge: dict[str, Any] | None`, con `status`, `version`, `documents`, `conflicts` e `dropped`; `RunReport.complete` è vero solo se, oltre alle condizioni attuali, `knowledge["status"]` vale `published` o `unchanged`.

### Comportamento in `run`, dopo `job.execute`:
1. se l'elenco della sorgente è incompleto, `knowledge = {"status": "skipped_listing_incomplete"}`;
2. altrimenti raccogliere le cartelle distinte dagli esiti con `bundle`, senza `duplicate_of` e con `skipped != "older_revision"`. Per ognuna leggere `<cartella>/<nome>.json` e `<nome>.source.json` (`doc_type`, `status`); se il JSON manca, saltare la cartella;
3. leggere `knowledge/<p>/aliases.json` e chiamare `build_index(..., version=run_id)`, quindi `publish_index`;
4. un'eccezione produce `knowledge = {"status": "failed", "error_type": <tipo>}` e non interrompe il report;
5. aggiungere una sezione «Indice della conoscenza» a `report.md` e una riga alla notifica.

### Passi:
- [ ] **Passo 1:** scrivere i test che falliscono: `test_run_publishes_knowledge_index` (due SPM sintetici -> `knowledge/civil/current.json` punta a `v/r1/` e `manifest.json` ha due documenti), `test_second_run_leaves_index_unchanged`, `test_incomplete_listing_does_not_publish` e `test_index_failure_is_reported_not_raised` (un `aliases.json` non valido -> `status == "failed"` e `report.complete is False`).
- [ ] **Passo 2:** `uv run pytest -q tests/platform/test_run_batch.py`. Risultato atteso: i nuovi test falliscono.
- [ ] **Passo 3:** implementare in `batch.py`.
- [ ] **Passo 4:** `uv run pytest -q`. Risultato atteso: suite completa verde, salvo il test preesistente `test_no_document_text_in_repo` già segnalato in `docs/DaFare.txt`.
- [ ] **Passo 5:** checkpoint.

---

## Task 6: Comando locale `knowledge-build`

### File:
- **Modifica:** `src/ingestion/cli.py`: un nuovo sottocomando in `_parser` e nel blocco di comandi di `main` che non richiedono configurazione AWS
- **Test:** `tests/knowledge/test_knowledge_cli.py`

### Interfacce:
- **Uso:** `python -m ingestion.cli knowledge-build --program {civil,ej200} --from <cartella archivio> --out <cartella nuova> [--aliases <file>] [--version <testo>]`.
- `--from` ha la forma `<tipo>/<documento>/<documento>.json` più `.source.json` (come `eval/prove_ingestion/file_ingestion_final_02`). Il comando considera solo i tipi del programma richiesto.
- Il comando scrive `index.files` sotto `--out`, nella forma di `v/<versione>/`. Si rifiuta di scrivere se `--out` esiste già o si trova dentro `--from`. Stampa `counts`, `conflicts` e `dropped` in JSON. Termina con codice 0 se tutto va bene, 2 se gli argomenti non sono validi.

### Passi:
- [ ] **Passo 1:** scrivere i test che falliscono: `test_builds_from_archive_folder` (archivio sintetico in `tmp_path`), `test_refuses_existing_or_nested_out` e `test_ignores_types_of_other_program`.
- [ ] **Passo 2:** `uv run pytest -q tests/knowledge/test_knowledge_cli.py`. Risultato atteso: `FAIL`.
- [ ] **Passo 3:** implementare il comando.
- [ ] **Passo 4:** rieseguire. Risultato atteso: tutti passati.
- [ ] **Passo 5:** prova sul campione reale, solo in locale: `uv run python -m ingestion.cli knowledge-build --program civil --from eval/prove_ingestion/file_ingestion_final_02 --out eval/prove_ingestion/risultati/<esecuzione>/knowledge_civil`, poi la stessa cosa per `ej200`. Annotare conteggi e conflitti nella scheda dell'esecuzione.
- [ ] **Passo 6:** verifica con v2. Serve l'autorizzazione della persona, perché bisogna clonare v2 e installarne le dipendenze. Eseguire `uv run cycle-validation kb-check <out>/knowledge_civil`. Risultato atteso: nessun errore e conteggi uguali a quelli del passo 5.
- [ ] **Passo 7:** checkpoint.

---

## Task 7: Permessi e documentazione

### File:
- **Modifica:** `infra/cloudformation/program.yaml`. Aggiungere `"${StorePrefix}knowledge/${Program}/*"` sia alla condizione `s3:prefix` del secondo `ListBucket` sia alla risorsa con `GetObject`, `PutObject` e `DeleteObject`.
- **Modifica:** `tests/infra/checks.py`: `STORE_AREAS` e `DELETE_AREAS` includono `"knowledge"`. Aggiornare le asserzioni corrispondenti in `tests/infra/test_c3_c4_ruoli.py`.
- **Modifica:** `infra/DEPLOY_QA.md`, passo 5, aggiungendo il controllo «Indice: .../cv3/knowledge/$PROG/current.json», e `docs/DaFare.txt`, aggiungendo questo lavoro al punto 2 come condizione per il deploy QA.

### Passi:
- [ ] **Passo 1:** aggiornare prima i test infra. `uv run pytest -q tests/infra`. Risultato atteso: `FAIL` sulle aree di scrittura.
- [ ] **Passo 2:** aggiornare il template.
- [ ] **Passo 3:** `uv run pytest -q tests/infra`. Risultato atteso: tutti passati.
- [ ] **Passo 4:** aggiornare i due documenti; `uv run pytest -q tests/infra/test_docs_infra.py`. Risultato atteso: tutti passati.
- [ ] **Passo 5:** checkpoint finale. `uv run pytest -q` e `uv run ruff check src tests` verdi; poi revisione indipendente (chi implementa non certifica).

---

## Fuori da questo piano (repo cycle-validation-v2)

v2 oggi legge un prefisso fisso. Serve una piccola modifica, da pianificare a parte nella repo di v2: leggere `knowledge/<programma>/current.json` e usare `prefix` come prefisso dello snapshot civile, e `prefix + "catalog.json"` e `prefix + "text/"` per EJ200. Il puntatore va riletto a ogni ricarica del catalogo, cioè alla scadenza del TTL. Il TM per EJ200 si legge da `knowledge/civil/<versione>/structured/TM/`.

---

## Punti aperti (non bloccano l'implementazione)

- **Contenuto di `aliases.json`:** i nomi con cui i cicli reali citano manuali e documenti.
- Gli intervalli dei task vanno misurati sui manuali veri (Task 6, passo 5). Se la regola di apertura sbaglia, si corregge solo `task_ranges`.
- Le 4 voci RDR che non sono RDR (`detected OTHER`, vedi `docs/DaFare.txt`) oggi entrano nel catalogo se hanno `rdr_no`: da decidere se escluderle.

