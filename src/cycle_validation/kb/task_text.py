"""Ricerca di un task nel testo del manuale, quando l'indice non lo ha.

L'indice riconosce come titolo di un task solo la forma del suo `regole.json` (oggi il codice
completo, 72-00-01-110-001). Un ciclo può citare un task in un'altra forma (con sezione ATA,
tipo e numero: 72-00-01 REPAIR 002) che nel manuale c'è ma che l'indice non ha registrato.

Qui si applica la stessa regola dell'indice al codice citato: una riga apre il task se, tolti
spazi, `#` del markdown, grassetto e un eventuale `TASK` o `CIR`, **comincia** con quel codice
(un codice dentro una frase non apre nulla; le righe di sommario nemmeno). Dopo la sezione può
esserci una virgola: nei manuali GE il titolo è spesso `CIR 72-00-01, REPAIR 002`. Nei
documenti SPM (pratiche standard) basta la sezione: `70-00-01 Pulizia` apre il task `70-00-01`. Il task finisce alla
riga prima del titolo di un altro task, in una delle due forme, oppure a fine documento. Se il
codice si apre in più punti si tiene il blocco più lungo, come fa l'indice.

Un SUBTASK (`SUBTASK 70-00-01-350-002`) sta dentro un task e l'indice non lo registra: se il
codice non apre un task, si cerca la riga che comincia con `SUBTASK` e quel codice; il subtask
finisce al prossimo SUBTASK o al titolo di un altro task.
"""

import re
from collections.abc import Sequence

from cycle_validation.kb.documents import PAGE_MARKER
from cycle_validation.text import normalize_code, normalize_quote

_PREFIX = re.compile(
    r"^\s*(?:#{1,6}\s*)?[*_]*\s*(?:(?:TASK|CIR)\b[\s:.\-]*)?[*_]*\s*", re.IGNORECASE
)
# Virgola dopo la sezione (`72-00-01, REPAIR 002`): si toglie prima del confronto.
_SECTION_COMMA = re.compile(r"(\d{2}-\d{2}-\d{2})\s*,")
_TOC = re.compile(r"(?:\.\s*){4,}\d+\s*$")
# Titolo di un task qualsiasi, per capire dove finisce quello cercato.
_ANY_TASK = re.compile(
    _PREFIX.pattern
    + r"(?:\d{2}-\d{2}-\d{2}-\d{3}-\d{3}|\d{2}-\d{2}-\d{2}\s*,?\s*[A-Z]+\s+\d{3})(?![\dA-Za-z])",
    re.IGNORECASE,
)
# Si cercano nel testo solo codici con la forma di un task, nelle due forme sopra: un codice
# di documento (o una parola) non deve diventare un task di una riga.
_TASK_SHAPE = re.compile(r"\d{2}-\d{2}-\d{2}(?:-\d{3}-\d{3}|[A-Z]+\d{3})")
# Sezione ATA (`72-00-01`): da sola, in una riga o all'inizio di un codice di task.
_SECTION_SHAPE = re.compile(r"\d{2}-\d{2}-\d{2}")


def _code_body(wanted: str) -> str:
    """Espressione regolare del codice (già normalizzato, senza spazi) con spazi ammessi tra
    un carattere e l'altro, seguito da qualcosa che non continua il codice."""
    body = r"\s*".join(re.escape(char) for char in wanted.casefold())
    return rf"{body}(?![0-9a-z]|-\d)"


def _clean(line: str) -> str:
    """Spazi compressi, minuscole e niente virgola dopo una sezione."""
    return _SECTION_COMMA.sub(r"\1 ", normalize_quote(line))


def _opens(line: str, pattern: re.Pattern[str]) -> bool:
    """La riga apre il task del `pattern`."""
    if _TOC.search(line):
        return False
    prefix = _PREFIX.match(line)
    rest = _clean(line[prefix.end() if prefix else 0 :])
    return pattern.match(rest) is not None


# Titolo SPM con la sola sezione (`70-00-01 Pulizia`), per capire dove finisce un task SPM.
_ANY_SECTION = re.compile(_PREFIX.pattern + r"\d{2}-\d{2}-\d{2}\s+[A-Za-z]", re.IGNORECASE)


def _opens_other(
    line: str, pattern: re.Pattern[str], sections: bool = False, section: str | None = None
) -> bool:
    """La riga apre un altro task. Cercando una sezione intera (`section`), solo un titolo di
    un'altra sezione la chiude: i task della stessa sezione ne fanno parte."""
    heading = _ANY_TASK.match(line) or (sections and _ANY_SECTION.match(line))
    if not heading or _TOC.search(line) or _opens(line, pattern):
        return False
    if section is not None:
        found = _SECTION_SHAPE.search(line)
        return found is None or found.group(0) != section
    return True


def find_task_in_text(
    lines: Sequence[str], task: str, *, sections: bool = False
) -> tuple[int, int] | None:
    """Righe (iniziale, finale), da 1 e incluse, del task citato; None se non c'è un titolo.
    `sections`: vale anche la sola sezione (documenti SPM)."""
    if not is_task_code(task, sections=sections):
        return None
    wanted = normalize_code(task)
    pattern = re.compile(_code_body(wanted))
    section = wanted if _SECTION_SHAPE.fullmatch(wanted) else None
    best: tuple[int, int] | None = None
    index = 0
    while index < len(lines):
        if not _opens(lines[index], pattern):
            index += 1
            continue
        start = index
        end = index + 1
        while end < len(lines) and not _opens_other(lines[end], pattern, sections, section):
            end += 1
        last = _last_line(lines, start, end)
        if best is None or last - start > best[1] - best[0] + 1:
            best = (start + 1, last)
        index = end
    if best is None and _FULL_SHAPE.fullmatch(wanted):
        best = _find_subtask(lines, pattern)
    return best


_FULL_SHAPE = re.compile(r"\d{2}-\d{2}-\d{2}-\d{3}-\d{3}")
# Riga che apre un subtask: markdown, grassetto, numerazione di elenco («(1)», «A.»), SUBTASK.
_SUBTASK = re.compile(
    r"^\s*(?:#{1,6}\s*)?[*_]*\s*(?:\(?[0-9A-Za-z]{1,3}[.)]\s*)?[*_]*\s*SUB-?TASK\b[\s:.\-]*[*_]*\s*",
    re.IGNORECASE,
)


def _last_line(lines: Sequence[str], start: int, end: int) -> int:
    """L'ultima riga (da 1) del blocco che va dall'indice `start` a `end` escluso, senza le
    righe vuote e i marcatori di pagina in fondo. La prima riga resta sempre."""
    last = end
    while last > start + 1 and (not lines[last - 1].strip() or PAGE_MARKER.match(lines[last - 1])):
        last -= 1
    return last


def _find_subtask(lines: Sequence[str], pattern: re.Pattern[str]) -> tuple[int, int] | None:
    """Righe del subtask del `pattern`: dalla riga `SUBTASK <codice>` al prossimo SUBTASK o
    titolo di task."""
    for index, line in enumerate(lines):
        heading = _SUBTASK.match(line)
        if heading is None or _TOC.search(line):
            continue
        if pattern.match(_clean(line[heading.end() :])) is None:
            continue
        end = index + 1
        while end < len(lines) and not (_SUBTASK.match(lines[end]) or _ANY_TASK.match(lines[end])):
            end += 1
        return (index + 1, _last_line(lines, index, end))
    return None


def is_task_code(task: str, *, sections: bool = False) -> bool:
    """Il codice ha una delle due forme di task che si cercano nel testo (con `sections`,
    anche la sola sezione)."""
    wanted = normalize_code(task)
    if sections and _SECTION_SHAPE.fullmatch(wanted):
        return True
    return _TASK_SHAPE.fullmatch(wanted) is not None


def lines_with(lines: Sequence[str], code: str, limit: int = 3) -> list[int]:
    """Righe (da 1) in cui il codice compare in un punto qualsiasi, con spazi ammessi tra un
    carattere e l'altro e non attaccato ad altre lettere o cifre."""
    wanted = normalize_code(code).casefold()
    if not wanted:
        return []
    pattern = re.compile(rf"(?<![0-9a-z]){_code_body(wanted)}")
    found: list[int] = []
    for number, line in enumerate(lines, start=1):
        if pattern.search(_clean(line)):
            found.append(number)
            if len(found) >= limit:
                break
    return found


def task_section(task: str) -> str | None:
    """La sezione ATA del task (`72-00-01 REPAIR 002` → `72-00-01`), se c'è."""
    match = _SECTION_SHAPE.match(normalize_code(task))
    return match.group(0) if match else None
