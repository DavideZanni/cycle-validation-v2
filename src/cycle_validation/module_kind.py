"""Il file caricato è del tipo scelto? MOS, DR oppure militare (EJ200).

Il tipo si legge dalla testata della stampa del ciclo, senza modello:

- il campo `PROGETTO` dice se il ciclo è militare (EJ200) o civile (GENX, LEAP);
- per un ciclo civile, un riferimento DR in testata lo distingue da un MOS.

Se il tipo letto è diverso da quello scelto si solleva `WrongModuleError`: il run si ferma
prima dell'estrazione. Se la testata non si riconosce non si blocca nulla (assente non
significa sbagliato): restano i limiti del profilo.

Da confermare sulle stampe reali: come una stampa DR si distingue da una MOS. I marcatori
sono in `config/settings.yaml` (`module_check.dr_markers`); vuoti = MOS e DR non distinti.
"""

import re
from collections.abc import Iterator

from cycle_validation.config import ModuleCheckSettings
from cycle_validation.errors import WrongModuleError
from cycle_validation.text import squash

MOS = "mos"
DR = "dr"
EJ200 = "ej200"
CIVIL = "civil"  # civile, senza poter dire se MOS o DR

_LABELS = {
    MOS: "un ciclo civile MOS",
    DR: "un ciclo civile DR",
    EJ200: "un ciclo militare (EJ200)",
    CIVIL: "un ciclo civile",
}
_HEADER_START = re.compile(r"^\s*CICLO\s*:")
_HEADER_END = re.compile(r"^\s*(?:={10,}|TARGA\b)")
_HEADER_MAX_LINES = 10
_PROJECT = re.compile(r"PROGETTO[\s.:]*(.*)$")


def _header_lines(text: str) -> Iterator[str]:
    """Righe delle testate (una per pagina): da `CICLO :` alla riga di separazione o
    all'intestazione della tabella. Il testo delle operazioni resta fuori."""
    remaining = 0
    for line in text.splitlines():
        if _HEADER_START.match(line):
            remaining = _HEADER_MAX_LINES
        elif remaining and _HEADER_END.match(line):
            remaining = 0
        if remaining:
            remaining -= 1
            yield line


def _contains_any(value: str, markers: list[str]) -> bool:
    folded = squash(value)
    return any(squash(marker) in folded for marker in markers if marker.strip())


def detect_module_kind(text: str, rules: ModuleCheckSettings) -> str | None:
    """`mos`, `dr`, `ej200`, `civil` (civile ma MOS/DR non distinguibili) oppure None."""
    header = list(_header_lines(text))
    projects = [match.group(1) for line in header if (match := _PROJECT.search(line))]
    military = any(_contains_any(value, rules.military_projects) for value in projects)
    civil = any(_contains_any(value, rules.civil_projects) for value in projects)
    if military == civil:  # nessun progetto riconosciuto, oppure testate in conflitto
        return None
    if military:
        return EJ200
    if not rules.dr_markers:
        return CIVIL
    patterns = [re.compile(marker, re.IGNORECASE) for marker in rules.dr_markers]
    is_dr = any(pattern.search(line) for line in header for pattern in patterns)
    return DR if is_dr else MOS


def _same(detected: str, chosen: str) -> bool:
    if detected == CIVIL:
        return chosen in (MOS, DR)
    return detected == chosen


def check_module_kind(text: str, chosen: str, rules: ModuleCheckSettings) -> None:
    """Solleva WrongModuleError se il modulo riconosciuto non è quello scelto."""
    if not rules.enabled or chosen not in (MOS, DR, EJ200):
        return
    detected = detect_module_kind(text, rules)
    if detected is None or _same(detected, chosen):
        return
    raise WrongModuleError(
        f"Modulo sbagliato: hai scelto {_LABELS[chosen]}, ma il file caricato è "
        f"{_LABELS[detected]}."
    )
