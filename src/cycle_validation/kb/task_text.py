"""Ricerca di un task nel testo del manuale, quando l'indice non lo ha.

L'indice riconosce come titolo di un task solo la forma del suo `regole.json` (oggi il codice
completo, 72-00-01-110-001). Un ciclo può citare un task in un'altra forma (con sezione ATA,
tipo e numero: 72-00-01 REPAIR 002) che nel manuale c'è ma che l'indice non ha registrato.

Qui si applica la stessa regola dell'indice al codice citato: una riga apre il task se, tolti
spazi, `#` del markdown, grassetto e un eventuale `TASK`, **comincia** con quel codice (un
codice dentro una frase non apre nulla; le righe di sommario nemmeno). Il task finisce alla
riga prima del titolo di un altro task, in una delle due forme, oppure a fine documento. Se il
codice si apre in più punti si tiene il blocco più lungo, come fa l'indice.
"""

import re
from collections.abc import Sequence

from cycle_validation.text import normalize_code, normalize_quote

_PREFIX = re.compile(r"^\s*(?:#{1,6}\s*)?[*_]*\s*(?:TASK\b[\s:.\-]*)?[*_]*\s*", re.IGNORECASE)
_TOC = re.compile(r"(?:\.\s*){4,}\d+\s*$")
_PAGE_MARKER = re.compile(r"^<!--\s*page\s+\d+\s*-->\s*$")
# Titolo di un task qualsiasi, per capire dove finisce quello cercato.
_ANY_TASK = re.compile(
    _PREFIX.pattern
    + r"(?:\d{2}-\d{2}-\d{2}-\d{3}-\d{3}|\d{2}-\d{2}-\d{2}\s+[A-Z]+\s+\d{3})(?![\dA-Za-z])",
    re.IGNORECASE,
)
# Si cercano nel testo solo codici con la forma di un task, nelle due forme sopra: un codice
# di documento (o una parola) non deve diventare un task di una riga.
_TASK_SHAPE = re.compile(r"\d{2}-\d{2}-\d{2}(?:-\d{3}-\d{3}|[A-Z]+\d{3})")


def _code_pattern(wanted: str) -> re.Pattern[str]:
    """Il codice (già normalizzato, senza spazi) con spazi ammessi tra un carattere e l'altro,
    seguito da qualcosa che non continua il codice."""
    body = r"\s*".join(re.escape(char) for char in wanted.casefold())
    return re.compile(rf"{body}(?![0-9a-z])")


def _opens(line: str, pattern: re.Pattern[str]) -> bool:
    """La riga apre il task del `pattern`."""
    if _TOC.search(line):
        return False
    prefix = _PREFIX.match(line)
    rest = normalize_quote(line[prefix.end() if prefix else 0 :])
    return pattern.match(rest) is not None


def _opens_other(line: str, pattern: re.Pattern[str]) -> bool:
    return _ANY_TASK.match(line) is not None and not _TOC.search(line) and not _opens(line, pattern)


def find_task_in_text(lines: Sequence[str], task: str) -> tuple[int, int] | None:
    """Righe (iniziale, finale), da 1 e incluse, del task citato; None se non c'è un titolo."""
    wanted = normalize_code(task)
    if _TASK_SHAPE.fullmatch(wanted) is None:
        return None
    pattern = _code_pattern(wanted)
    best: tuple[int, int] | None = None
    index = 0
    while index < len(lines):
        if not _opens(lines[index], pattern):
            index += 1
            continue
        start = index
        end = index + 1
        while end < len(lines) and not _opens_other(lines[end], pattern):
            end += 1
        last = end
        while last > start + 1 and (
            not lines[last - 1].strip() or _PAGE_MARKER.match(lines[last - 1])
        ):
            last -= 1
        if best is None or last - start > best[1] - best[0] + 1:
            best = (start + 1, last)
        index = end
    return best
