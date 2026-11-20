"""Knowledge base da cartella locale. Il formato è definito da questo progetto:

    knowledge/
    ├── manifest.json            versione ed elenco dei documenti
    ├── documents/<chiave>.md    testo a righe, con marcatori di pagina
    ├── tasks.json               manuale, task → righe          (facoltativo)
    ├── machine_tags.json        targhe e funzione              (facoltativo)
    ├── process_sheets.json      schede di processo             (facoltativo)
    ├── dr_recommendations.json  recommendation per S/N         (facoltativo)
    └── uncertainty.json         voci incerte e perché          (facoltativo)

`uncertainty.json` lo scrive knowledge-index: per targhe e schede i motivi per codice, per
le recommendation DR per serial number, condition e procedura. I motivi finiscono nel campo
`uncertain` della voce.

Ogni difetto dei file letti per validare produce un KnowledgeError che dice in quale file e in
quale voce. `uncertainty.json` è un'aggiunta: se non si legge, o cita voci che non ci sono, la
parte che non torna si ignora con un avviso (il servizio parte lo stesso, con le voci come se
fossero certe) e il problema va in `problems`; `kb-check` lo usa per fallire.
"""

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from cycle_validation.errors import KnowledgeError
from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.text import normalize_code

log = logging.getLogger(__name__)


class _Row(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _ManifestDocument(_Row):
    key: str = Field(min_length=1)
    file: str = Field(min_length=1)
    version: str | None = None
    title: str = ""
    aliases: list[str] = Field(default_factory=list)
    code: str | None = None
    kind: str | None = None
    published: bool = True
    partial: bool = False
    # Numero di righe del file, scritto da knowledge-index: con 2000 documenti evita di
    # aprirli tutti all'avvio solo per controllare gli intervalli dei task.
    lines: int | None = Field(default=None, ge=0)


class _Manifest(_Row):
    format: Literal[1] = 1
    version: str = Field(min_length=1)
    documents: list[_ManifestDocument]


class _TaskRow(_Row):
    manual: str
    task: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)


class _TagRow(_Row):
    tag: str
    function: str | None = None
    # Promemoria di chi cura l'indice ("da ricontrollare a mano"): si accetta e si ignora,
    # non cambia nessun esito. Vale anche per schede e recommendation DR.
    needs_review: bool = False


class _SheetRow(_Row):
    code: str
    edition: str | None = None
    treatment: str | None = None
    engine_families: list[str] = Field(default_factory=list)
    needs_review: bool = False


class _DrRow(_Row):
    serial_number: str
    conditions: list[int]
    procedure: str
    reference: str | None = None
    manual: str | None = None
    tasks: list[str] = Field(default_factory=list)
    needs_review: bool = False


class _UncertainDr(_Row):
    serial_number: str
    conditions: list[int]
    procedure: str
    reasons: list[str] = Field(min_length=1)


class _Uncertainty(_Row):
    format: Literal[1]
    machine_tags: dict[str, list[str]] = Field(default_factory=dict)
    process_sheets: dict[str, list[str]] = Field(default_factory=dict)
    dr_recommendations: list[_UncertainDr] = Field(default_factory=list)


_UNCERTAINTY = "uncertainty.json"


def _by_code(
    items: dict[str, list[str]], known: set[str], label: str, problems: list[str]
) -> dict[str, tuple[str, ...]]:
    """Motivi per codice normalizzato. Un codice che l'indice non contiene si salta."""
    out: dict[str, tuple[str, ...]] = {}
    for code, reasons in items.items():
        name = normalize_code(code)
        if name not in known:
            problems.append(f"{_UNCERTAINTY}: {label} '{code}' non è nell'indice, ignorata.")
            continue
        out[name] = tuple(sorted({*out.get(name, ()), *reasons}))
    return out


def _dr_key(serial: str, conditions: list[int], procedure: str) -> tuple[str, tuple[int, ...], str]:
    return normalize_code(serial), tuple(sorted(conditions)), procedure.strip().casefold()


def _uncertain_dr(
    items: list[_UncertainDr], rows: list[_DrRow], problems: list[str]
) -> dict[tuple[str, tuple[int, ...], str], tuple[str, ...]]:
    known = {_dr_key(row.serial_number, row.conditions, row.procedure) for row in rows}
    out: dict[tuple[str, tuple[int, ...], str], tuple[str, ...]] = {}
    for item in items:
        key = _dr_key(item.serial_number, item.conditions, item.procedure)
        if key not in known:
            problems.append(
                f"{_UNCERTAINTY}: recommendation DR '{item.serial_number}' {item.conditions} "
                f"'{item.procedure}' non è nell'indice, ignorata."
            )
            continue
        out[key] = tuple(sorted({*out.get(key, ()), *item.reasons}))
    return out


def _read_uncertainty(path: Path, problems: list[str]) -> _Uncertainty:
    """Il file, oppure nessuna incertezza se manca o non si legge."""
    if not path.is_file():
        return _Uncertainty(format=1)
    try:
        return _parse(TypeAdapter(_Uncertainty), path)
    except KnowledgeError as exc:
        problems.append(f"{_UNCERTAINTY} ignorato: {exc}")
        return _Uncertainty(format=1)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise KnowledgeError(f"Impossibile leggere {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise KnowledgeError(f"JSON non valido in {path}: {exc}") from exc


def _parse[T](adapter: TypeAdapter[T], path: Path) -> T:
    try:
        return adapter.validate_python(_load_json(path))
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in exc.errors()[:5]
        )
        raise KnowledgeError(f"Contenuto non valido in {path}: {details}") from exc


def _optional[T](adapter: TypeAdapter[list[T]], path: Path) -> list[T]:
    return _parse(adapter, path) if path.is_file() else []


def _documents(
    directory: Path, manifest: _Manifest
) -> tuple[dict[str, DocumentInfo], dict[str, int]]:
    """Documenti per chiave e, per quelli che lo dichiarano, il numero di righe."""
    root = directory.resolve()
    documents: dict[str, DocumentInfo] = {}
    line_counts: dict[str, int] = {}
    for row in manifest.documents:
        if row.key in documents:
            raise KnowledgeError(f"manifest.json: chiave di documento duplicata '{row.key}'.")
        path = (root / row.file).resolve()
        if not path.is_relative_to(root):
            raise KnowledgeError(f"manifest.json: il file di '{row.key}' esce dalla cartella.")
        if not path.is_file():
            raise KnowledgeError(f"manifest.json: file di '{row.key}' non trovato: {row.file}")
        documents[row.key] = DocumentInfo(
            key=row.key,
            path=path,
            version=row.version,
            title=row.title,
            code=row.code,
            kind=row.kind,
            published=row.published,
            partial=row.partial,
        )
        if row.lines is not None:
            line_counts[row.key] = row.lines
    return documents, line_counts


def _tasks(
    rows: list[_TaskRow], documents: dict[str, DocumentInfo], line_counts: dict[str, int]
) -> list[TaskLocation]:
    by_name = {normalize_code(key): document for key, document in documents.items()}
    locations: list[TaskLocation] = []
    for row in rows:
        document = by_name.get(normalize_code(row.manual))
        where = f"tasks.json: task '{row.task}' di '{row.manual}'"
        if document is None:
            raise KnowledgeError(f"{where}: il manuale non è nel manifest.")
        n_lines = line_counts.get(document.key)
        if n_lines is None:
            n_lines = line_counts[document.key] = len(read_lines(document.path))
        if row.line_end < row.line_start or row.line_end > n_lines:
            raise KnowledgeError(
                f"{where}: righe {row.line_start}-{row.line_end} fuori dal file ({n_lines} righe)."
            )
        locations.append(
            TaskLocation(
                manual_key=document.key,
                task=row.task,
                document=document,
                line_start=row.line_start,
                line_end=row.line_end,
            )
        )
    return locations


def load_local_knowledge(
    directory: Path, *, version: str | None = None, problems: list[str] | None = None
) -> IndexedKnowledgeBase:
    """`version` sostituisce quella del manifest (conoscenza pubblicata: vale il puntatore).
    In `problems`, se data, finiscono i difetti tollerati di `uncertainty.json` (sempre anche
    nel log)."""
    if not directory.is_dir():
        raise KnowledgeError(f"Cartella della knowledge base non trovata: {directory}")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise KnowledgeError(f"manifest.json non trovato in {directory}")
    manifest = _parse(TypeAdapter(_Manifest), manifest_path)
    documents, line_counts = _documents(directory, manifest)
    task_rows = _optional(TypeAdapter(list[_TaskRow]), directory / "tasks.json")
    tag_rows = _optional(TypeAdapter(list[_TagRow]), directory / "machine_tags.json")
    sheet_rows = _optional(TypeAdapter(list[_SheetRow]), directory / "process_sheets.json")
    dr_rows = _optional(TypeAdapter(list[_DrRow]), directory / "dr_recommendations.json")
    found: list[str] = []
    uncertainty = _read_uncertainty(directory / _UNCERTAINTY, found)
    tag_doubts = _by_code(
        uncertainty.machine_tags, {normalize_code(row.tag) for row in tag_rows}, "targa", found
    )
    sheet_doubts = _by_code(
        uncertainty.process_sheets,
        {normalize_code(row.code) for row in sheet_rows},
        "scheda",
        found,
    )
    dr_doubts = _uncertain_dr(uncertainty.dr_recommendations, dr_rows, found)
    for problem in found:
        log.warning("Conoscenza in %s: %s", directory.name, problem)
    if problems is not None:
        problems.extend(found)
    return IndexedKnowledgeBase(
        version or manifest.version,
        documents=documents.values(),
        aliases={row.key: row.aliases for row in manifest.documents},
        tasks=_tasks(task_rows, documents, line_counts),
        machine_tags=[
            MachineTagEntry(
                tag=row.tag,
                function=row.function,
                uncertain=tag_doubts.get(normalize_code(row.tag), ()),
            )
            for row in tag_rows
        ],
        process_sheets=[
            ProcessSheetEntry(
                code=row.code,
                edition=row.edition,
                treatment=row.treatment,
                engine_families=tuple(row.engine_families),
                uncertain=sheet_doubts.get(normalize_code(row.code), ()),
            )
            for row in sheet_rows
        ],
        dr_recommendations=[
            DrRecommendation(
                serial_number=row.serial_number,
                conditions=tuple(row.conditions),
                procedure=row.procedure,
                reference=row.reference,
                manual=row.manual,
                tasks=tuple(row.tasks),
                uncertain=dr_doubts.get(
                    _dr_key(row.serial_number, row.conditions, row.procedure), ()
                ),
            )
            for row in dr_rows
        ],
    )
