"""Knowledge base da cartella locale. Il formato è definito da questo progetto:

    knowledge/
    ├── manifest.json            versione ed elenco dei documenti
    ├── documents/<chiave>.md    testo a righe, con marcatori di pagina
    ├── tasks.json               manuale, task → righe          (facoltativo)
    ├── machine_tags.json        targhe e funzione              (facoltativo)
    ├── process_sheets.json      schede di processo             (facoltativo)
    └── dr_recommendations.json  recommendation per S/N         (facoltativo)

Ogni difetto produce un KnowledgeError che dice in quale file e in quale voce.
"""

import json
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


class _SheetRow(_Row):
    code: str
    edition: str | None = None
    treatment: str | None = None
    engine_families: list[str] = Field(default_factory=list)


class _DrRow(_Row):
    serial_number: str
    conditions: list[int]
    procedure: str
    reference: str | None = None
    manual: str | None = None
    tasks: list[str] = Field(default_factory=list)


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


def _documents(directory: Path, manifest: _Manifest) -> dict[str, DocumentInfo]:
    root = directory.resolve()
    documents: dict[str, DocumentInfo] = {}
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
    return documents


def _tasks(rows: list[_TaskRow], documents: dict[str, DocumentInfo]) -> list[TaskLocation]:
    by_name = {normalize_code(key): document for key, document in documents.items()}
    locations: list[TaskLocation] = []
    for row in rows:
        document = by_name.get(normalize_code(row.manual))
        where = f"tasks.json: task '{row.task}' di '{row.manual}'"
        if document is None:
            raise KnowledgeError(f"{where}: il manuale non è nel manifest.")
        n_lines = len(read_lines(document.path))
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


def load_local_knowledge(directory: Path) -> IndexedKnowledgeBase:
    if not directory.is_dir():
        raise KnowledgeError(f"Cartella della knowledge base non trovata: {directory}")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise KnowledgeError(f"manifest.json non trovato in {directory}")
    manifest = _parse(TypeAdapter(_Manifest), manifest_path)
    documents = _documents(directory, manifest)
    task_rows = _optional(TypeAdapter(list[_TaskRow]), directory / "tasks.json")
    tag_rows = _optional(TypeAdapter(list[_TagRow]), directory / "machine_tags.json")
    sheet_rows = _optional(TypeAdapter(list[_SheetRow]), directory / "process_sheets.json")
    dr_rows = _optional(TypeAdapter(list[_DrRow]), directory / "dr_recommendations.json")
    return IndexedKnowledgeBase(
        manifest.version,
        documents=documents.values(),
        aliases={row.key: row.aliases for row in manifest.documents},
        tasks=_tasks(task_rows, documents),
        machine_tags=[MachineTagEntry(tag=row.tag, function=row.function) for row in tag_rows],
        process_sheets=[
            ProcessSheetEntry(
                code=row.code,
                edition=row.edition,
                treatment=row.treatment,
                engine_families=tuple(row.engine_families),
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
            )
            for row in dr_rows
        ],
    )
