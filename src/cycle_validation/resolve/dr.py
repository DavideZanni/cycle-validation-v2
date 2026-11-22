"""Selettori DR (serial number e repair condition) e scelta delle recommendation."""

import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from cycle_validation.errors import CycleValidationError
from cycle_validation.kb.port import DrRecommendation
from cycle_validation.text import normalize_quote

# Disposizioni del DR diverse da una riparazione. `Reject`: il pezzo si scarta. `Accept as is`:
# il pezzo si accetta così com'è. In tutti e due i casi un ciclo di riparazione non dovrebbe
# esistere (come nella v1, confermato dall'utente il 22-11-2026).
REJECT_PROCEDURES = ("reject",)
ACCEPT_AS_IS_PROCEDURES = ("accept as is", "use as is")
_INTEGER = re.compile(r"-?[0-9]+")
# Serial number scritto nella stampa: "APPLY ON S/N XXXX0000", anche "S/N:XXXX0000",
# "S / N. XXXX-0000". Almeno 6 caratteri, con almeno una cifra: "S/N DEL PARTICOLARE",
# "S/N ......" e "S/N:" vuoto non contano.
SERIAL_IN_TEXT = re.compile(
    r"\bS\s*/\s*N\b\.?\s*[:#]?\s*(?=[A-Z0-9-]*\d)([A-Z0-9][A-Z0-9-]{4,}[A-Z0-9])\b"
)


class SelectorError(CycleValidationError):
    """Selettori DR mancanti, non validi o inviati per un ciclo non DR."""


@dataclass(frozen=True)
class DrSelectors:
    """Serial number e repair condition di un ciclo DR. Tutti e due facoltativi: il serial
    number, se manca, si cerca nella stampa; la condition serve solo quando il serial number
    ha più recommendation."""

    serial_number: str | None = None
    conditions: tuple[int, ...] = ()


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
    """Senza DR i selettori sono vietati. Con DR sono facoltativi (22-11-2026): quelli dati
    si controllano, quelli che mancano restano vuoti."""
    has_serial = isinstance(serial_number, str) and bool(serial_number.strip())
    has_conditions = conditions is not None and conditions != "" and conditions != []
    if not is_dr:
        if has_serial or has_conditions:
            raise SelectorError("Serial number e repair condition valgono solo per i cicli DR.")
        return None
    serial = serial_number.strip() if isinstance(serial_number, str) and has_serial else None
    parsed = tuple(normalize_conditions(conditions)) if has_conditions else ()
    return DrSelectors(serial, parsed)


def serials_in_text(text: str) -> list[str]:
    """I serial number scritti nella stampa, senza ripetizioni, nell'ordine in cui compaiono."""
    return list(dict.fromkeys(SERIAL_IN_TEXT.findall(text)))


def serial_in_text(text: str, known: Callable[[str], bool] | None = None) -> str | None:
    """Il serial number scritto nella stampa ("APPLY ON S/N ..."), se ce n'è uno solo. Se ce
    ne sono più d'uno (per esempio un altro numero dopo la scritta S/N della testata), vale
    quello che ha recommendation nei dati DR (`known`), se è uno solo."""
    found = serials_in_text(text)
    if len(found) > 1 and known is not None:
        found = [serial for serial in found if known(serial)]
    return found[0] if len(found) == 1 else None


def with_serial_from_text(
    selectors: DrSelectors, text: str, known: Callable[[str], bool] | None = None
) -> DrSelectors:
    """Se il serial number non è stato indicato, lo prende dalla stampa."""
    if selectors.serial_number:
        return selectors
    found = serial_in_text(text, known)
    return DrSelectors(found, selectors.conditions) if found else selectors


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
