"""Selettori DR (serial number e repair condition) e scelta delle recommendation."""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass

from cycle_validation.errors import CycleValidationError
from cycle_validation.kb.port import DrRecommendation
from cycle_validation.text import normalize_quote

# Disposizioni del DR diverse da una riparazione. `Reject`: il pezzo si scarta, un ciclo di
# riparazione è sbagliato. `Accept as is`: il pezzo si accetta senza riparazione, ma il ciclo
# può avere comunque ispezioni e registrazioni, quindi non è un errore di per sé (domanda 17).
REJECT_PROCEDURES = ("reject",)
ACCEPT_AS_IS_PROCEDURES = ("accept as is", "use as is")
_INTEGER = re.compile(r"-?[0-9]+")


class SelectorError(CycleValidationError):
    """Selettori DR mancanti, non validi o inviati per un ciclo non DR."""


@dataclass(frozen=True)
class DrSelectors:
    serial_number: str
    conditions: tuple[int, ...]


def normalize_conditions(value: object) -> list[int]:
    """Accetta un intero, una lista, `"1"`, `"1,2"` o `"[1,2]"`; restituisce `list[int]`."""
    if value is None or isinstance(value, bool):
        raise SelectorError("Repair condition mancante o non valida.")
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                return normalize_conditions(json.loads(text))
            except json.JSONDecodeError as exc:
                raise SelectorError(f"Repair condition non valida: {value!r}") from exc
        parts: Sequence[object] = [part for part in text.split(",") if part.strip()]
    elif isinstance(value, (list, tuple)):
        parts = value
    else:
        raise SelectorError(f"Repair condition non valida: {value!r}")
    conditions: list[int] = []
    for part in parts:
        if isinstance(part, int) and not isinstance(part, bool):
            number = part
        elif isinstance(part, str) and _INTEGER.fullmatch(part.strip()):
            number = int(part.strip())
        else:
            raise SelectorError(f"Repair condition non valida: {part!r}")
        if number not in conditions:
            conditions.append(number)
    if not conditions:
        raise SelectorError("Serve almeno una repair condition.")
    return conditions


def parse_selectors(
    *, is_dr: bool, serial_number: object = None, conditions: object = None
) -> DrSelectors | None:
    """Applica la regola: senza DR i selettori sono vietati, con DR sono obbligatori."""
    has_serial = isinstance(serial_number, str) and bool(serial_number.strip())
    has_conditions = conditions is not None and conditions != "" and conditions != []
    if not is_dr:
        if has_serial or has_conditions:
            raise SelectorError("Serial number e repair condition valgono solo per i cicli DR.")
        return None
    if not has_serial:
        raise SelectorError("Per un ciclo DR serve il serial number.")
    if not has_conditions:
        raise SelectorError("Per un ciclo DR serve almeno una repair condition.")
    assert isinstance(serial_number, str)
    return DrSelectors(serial_number.strip(), tuple(normalize_conditions(conditions)))


def match_recommendations(
    recommendations: Sequence[DrRecommendation], conditions: Sequence[int]
) -> list[DrRecommendation]:
    """Una sola recommendation per il serial number vale così com'è; se sono più di una
    restano quelle le cui condition si intersecano con quelle richieste."""
    if len(recommendations) <= 1:
        return list(recommendations)
    wanted = set(conditions)
    return [item for item in recommendations if wanted & set(item.conditions)]


def without_conditions(recommendations: Sequence[DrRecommendation]) -> list[DrRecommendation]:
    """Le recommendation senza condition quando il serial number ne ha più di una: il caso è
    ambiguo (la lista vuota non dice né "tutte" né "nessuna") e va controllato a mano."""
    if len(recommendations) <= 1:
        return []
    return [item for item in recommendations if not item.conditions]


def _procedure(recommendation: DrRecommendation) -> str:
    # "Accept-as-is", "ACCEPT AS IS" e "accept as is." sono la stessa disposizione
    return normalize_quote(recommendation.procedure.replace("-", " ")).rstrip(".")


def is_reject(recommendation: DrRecommendation) -> bool:
    return _procedure(recommendation) in REJECT_PROCEDURES


def is_accept_as_is(recommendation: DrRecommendation) -> bool:
    return _procedure(recommendation) in ACCEPT_AS_IS_PROCEDURES
