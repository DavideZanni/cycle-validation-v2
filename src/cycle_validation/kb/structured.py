"""Dati strutturati su S3: targhe (TM), schede di processo (SP), recommendation DR.

La forma esatta dei JSON aziendali non è nota a questa macchina: `FieldMap` dice quali
nomi di campo cercare per ciascun dato (il primo presente vince). Per adattare un file
reale basta estendere gli alias, senza toccare il resto.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from cycle_validation.errors import KnowledgeError
from cycle_validation.kb.port import DrRecommendation, MachineTagEntry, ProcessSheetEntry
from cycle_validation.kb.stores import ObjectNotFoundError, ObjectStore


@dataclass(frozen=True)
class FieldMap:
    tag: Sequence[str] = ("tag", "machine_tag", "targa", "code")
    tag_function: Sequence[str] = ("function", "funzione", "description")
    sheet_code: Sequence[str] = ("code", "sheet", "scheda", "process_sheet")
    sheet_edition: Sequence[str] = ("edition", "edizione", "revision")
    sheet_treatment: Sequence[str] = ("treatment", "trattamento", "description")
    sheet_families: Sequence[str] = ("engine_families", "engines", "famiglie_motore")
    dr_serial: Sequence[str] = ("serial_number", "serial", "sn")
    dr_conditions: Sequence[str] = ("conditions", "repair_conditions", "condition")
    dr_procedure: Sequence[str] = ("procedure", "disposition")
    dr_reference: Sequence[str] = ("reference", "dr_number", "dr")
    dr_manual: Sequence[str] = ("manual",)
    dr_tasks: Sequence[str] = ("tasks", "task_codes")


@dataclass(frozen=True)
class StructuredLayout:
    """Prefissi o chiavi S3 dei tre insiemi di dati."""

    tm: str | None = "structured/TM/"
    sp: str | None = "structured/SP/"
    dr: str | None = "structured/DR/"
    fields: FieldMap = field(default_factory=FieldMap)


@dataclass(frozen=True)
class StructuredData:
    machine_tags: tuple[MachineTagEntry, ...] = ()
    process_sheets: tuple[ProcessSheetEntry, ...] = ()
    dr_recommendations: tuple[DrRecommendation, ...] = ()


def _pick(row: Mapping[str, Any], names: Sequence[str]) -> Any:
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    return None


def _text(value: Any) -> str | None:
    return None if value is None else str(value).strip() or None


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _rows(store: ObjectStore, location: str, label: str) -> list[Mapping[str, Any]]:
    """Righe di un insieme di dati: una chiave `.json`, oppure tutte le `.json` sotto un prefisso."""
    keys = (
        [location]
        if location.endswith(".json")
        else [key for key in store.list_keys(location) if key.endswith(".json")]
    )
    if not keys:
        raise KnowledgeError(f"Dati {label} non trovati su S3 in '{location}'.")
    rows: list[Mapping[str, Any]] = []
    for key in keys:
        try:
            loaded = json.loads(store.get_bytes(key))
        except ObjectNotFoundError as exc:
            raise KnowledgeError(f"Oggetto {label} mancante: {key}") from exc
        except json.JSONDecodeError as exc:
            raise KnowledgeError(f"JSON non valido in {key}: {exc}") from exc
        if isinstance(loaded, dict):
            loaded = next((v for v in loaded.values() if isinstance(v, list)), None)
        if not isinstance(loaded, list) or not all(isinstance(item, dict) for item in loaded):
            raise KnowledgeError(f"{key}: attesa una lista di oggetti ({label}).")
        rows.extend(loaded)
    return rows


def load_structured(store: ObjectStore, layout: StructuredLayout) -> StructuredData:
    """Carica e valida gli insiemi indicati nel layout (`None` = non usato da questo profilo).
    Ogni oggetto assente o non valido è un KnowledgeError."""
    f = layout.fields
    tags: list[MachineTagEntry] = []
    for row in _rows(store, layout.tm, "TM") if layout.tm else []:
        tag = _text(_pick(row, f.tag))
        if tag is None:
            raise KnowledgeError(f"TM: riga senza targa (campi cercati: {', '.join(f.tag)}).")
        tags.append(MachineTagEntry(tag=tag, function=_text(_pick(row, f.tag_function))))
    sheets: list[ProcessSheetEntry] = []
    for row in _rows(store, layout.sp, "SP") if layout.sp else []:
        code = _text(_pick(row, f.sheet_code))
        if code is None:
            raise KnowledgeError(f"SP: riga senza codice (campi: {', '.join(f.sheet_code)}).")
        sheets.append(
            ProcessSheetEntry(
                code=code,
                edition=_text(_pick(row, f.sheet_edition)),
                treatment=_text(_pick(row, f.sheet_treatment)),
                engine_families=tuple(str(x) for x in _list(_pick(row, f.sheet_families))),
            )
        )
    recommendations: list[DrRecommendation] = []
    for row in _rows(store, layout.dr, "DR") if layout.dr else []:
        serial = _text(_pick(row, f.dr_serial))
        procedure = _text(_pick(row, f.dr_procedure))
        if serial is None or procedure is None:
            raise KnowledgeError("DR: riga senza serial number o senza procedura.")
        try:
            conditions = tuple(int(x) for x in _list(_pick(row, f.dr_conditions)))
        except (TypeError, ValueError) as exc:
            raise KnowledgeError(f"DR {serial}: repair condition non numeriche.") from exc
        recommendations.append(
            DrRecommendation(
                serial_number=serial,
                conditions=conditions,
                procedure=procedure,
                reference=_text(_pick(row, f.dr_reference)),
                manual=_text(_pick(row, f.dr_manual)),
                tasks=tuple(str(x) for x in _list(_pick(row, f.dr_tasks))),
            )
        )
    return StructuredData(tuple(tags), tuple(sheets), tuple(recommendations))
