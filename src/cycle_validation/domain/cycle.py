"""Ciclo estratto dal PDF. I campi ricalcano il payload che il frontend riceve oggi."""

import re
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

_CODE_SEPARATORS = re.compile(r"[,;\n]+")
# Come una stampa scrive "nessun codice": "Targa -", "Scheda N/A". Non sono codici veri.
_DASHES_ONLY = re.compile(r"[\s\-\u2010-\u2015_./*]*")
_PLACEHOLDER_WORDS = frozenset(
    {"n/a", "n.a.", "na", "n.d.", "nd", "none", "null", "nessuno", "nessuna"}
)


def _placeholder(value: str) -> bool:
    text = value.strip()
    return _DASHES_ONLY.fullmatch(text) is not None or text.casefold() in _PLACEHOLDER_WORDS


def _clean(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _clean_optional(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


def _clean_code(value: object) -> object:
    """Un codice facoltativo: vuoto o segnaposto vuol dire assente."""
    if isinstance(value, str):
        return None if _placeholder(value) else value.strip()
    return value


def _clean_codes(value: object) -> object:
    """Accetta `null`, una stringa con più codici o una lista; restituisce una lista pulita."""
    if value is None:
        return []
    if isinstance(value, str):
        value = _CODE_SEPARATORS.split(value)
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and not _placeholder(item)]
    return value


def _clean_sheet(value: object) -> object:
    """Accetta `null`, il solo codice della scheda oppure l'oggetto completo."""
    if isinstance(value, str):
        return None if _placeholder(value) else {"code": value}
    if (
        isinstance(value, dict)
        and isinstance(value.get("code"), str)
        and _placeholder(value["code"])
    ):
        return None
    return value


Text = Annotated[str, BeforeValidator(_clean)]
OptionalText = Annotated[str | None, BeforeValidator(_clean_optional)]
OptionalCode = Annotated[str | None, BeforeValidator(_clean_code)]
Codes = Annotated[list[str], BeforeValidator(_clean_codes)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(_Strict):
    """Fonte citata dal ciclo: manuale (o riferimento DR, o pubblicazione) e task."""

    manual: Text = Field(min_length=1)
    task: OptionalCode = None
    repair_code: OptionalCode = None
    issue: OptionalText = None
    # punto della fonte citato insieme al codice ("PAR. 1.1"), se il ciclo lo indica
    section: OptionalText = None
    page: int | None = None


class ProcessSheet(BaseModel):
    """Scheda di processo. I campi oltre al codice variano per tipo di ciclo e passano invariati."""

    model_config = ConfigDict(extra="allow")

    code: Text = Field(min_length=1)


class Operation(_Strict):
    operation_number: Text = Field(min_length=1)
    operation_description: Text = ""
    repair_code: OptionalCode = None
    machine_tag: OptionalCode = None
    task_codes: Codes = Field(default_factory=list)
    process_sheet: Annotated[ProcessSheet | None, BeforeValidator(_clean_sheet)] = None
    page: int | None = None


class Cycle(_Strict):
    cycle_code: OptionalText = None
    cycle_description: OptionalText = None
    engine_model: OptionalText = None
    operation_type: OptionalText = None
    repair_code: OptionalText = None
    sources: list[Source] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)
    dr_record: dict[str, Any] | None = None
