"""Documenti di riferimento come file di testo a righe.

Una riga di file per riga di testo; `<!-- page N -->` segna l'inizio della pagina N.
Le righe si contano da 1, come fanno Read e Grep.
"""

import hashlib
import re
from collections.abc import Iterable, Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from cycle_validation.errors import SourceUnavailableError
from cycle_validation.text import normalize_quote

PAGE_MARKER = re.compile(r"^<!--\s*page\s+(\d+)\s*-->\s*$")
_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def digest(*identity: str) -> str:
    """Impronta breve di un'identità, per nomi di file e cartelle."""
    return hashlib.sha256(repr(identity).encode("utf-8")).hexdigest()[:10]


def file_name(label: str) -> str:
    """Nome di file per `label`. Se ripulirlo dai caratteri non ammessi lo cambia, il nome
    porta anche l'impronta dell'originale: due nomi che si ripuliscono allo stesso modo non
    finiscono nello stesso file, uno sopra l'altro. L'agente cita i documenti per nome di
    file, quindi i nomi già puliti restano quelli che sono."""
    readable = _UNSAFE.sub("_", label).strip("_")[:80]
    if readable == label:
        return f"{label}.md"
    return f"{readable or 'x'}-{digest(label)}.md"


@lru_cache(maxsize=256)
def _cached_lines(path: str, mtime_ns: int) -> tuple[str, ...]:
    return tuple(Path(path).read_text(encoding="utf-8").splitlines())


def read_lines(path: Path) -> tuple[str, ...]:
    """Righe del documento, in cache finché il file non cambia."""
    try:
        mtime_ns = path.stat().st_mtime_ns
        return _cached_lines(str(path), mtime_ns)
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceUnavailableError(f"Documento non leggibile: {path.name} ({exc})") from exc


@lru_cache(maxsize=64)
def _cached_folded(path: str, mtime_ns: int) -> str:
    lines = _cached_lines(path, mtime_ns)
    return "\n".join("" if PAGE_MARKER.match(line) else normalize_quote(line) for line in lines)


def folded_text(path: Path) -> str:
    """Testo normalizzato per le ricerche esatte (minuscole, trattini e spazi unificati), con
    le stesse righe del file e i marcatori di pagina svuotati. In cache finché il file non cambia."""
    try:
        return _cached_folded(str(path), path.stat().st_mtime_ns)
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceUnavailableError(f"Documento non leggibile: {path.name} ({exc})") from exc


def _whole(value: object) -> int | None:
    """Intero da un metadato dell'indice, comunque sia stato salvato (12, "12", 12.0)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str) and value.strip().isdecimal():
        return int(value.strip())
    return None


def chunk_lines(
    hits: Iterable[Mapping[str, Any]], *, order: str, page: str, text: str
) -> tuple[list[str], int]:
    """Righe di un documento dai chunk dell'indice, nell'ordine del campo `order`, con un
    marcatore a ogni cambio di pagina. Restituisce anche la riga del primo testo (0 se manca).

    Un numero di pagina non leggibile non ferma la lettura: il chunk resta sotto l'ultima
    pagina nota."""

    def position(hit: Mapping[str, Any]) -> tuple[bool, int]:
        number = _whole(hit.get(order))
        return number is None, number or 0

    lines: list[str] = []
    current: int | None = None
    first_text = 0
    for hit in sorted(hits, key=position):
        number = _whole(hit.get(page))
        if number is not None and number != current:
            lines.append(f"<!-- page {number} -->")
            current = number
        body = str(hit.get(text) or "").splitlines()
        if body and not first_text:
            first_text = len(lines) + 1
        lines.extend(body)
    return lines, first_text


def page_at(path: Path, line: int) -> int | None:
    """Pagina a cui appartiene la riga, secondo l'ultimo marcatore che la precede."""
    lines = read_lines(path)
    for index in range(min(line, len(lines)) - 1, -1, -1):
        match = PAGE_MARKER.match(lines[index])
        if match:
            return int(match.group(1))
    return None


def numbered_lines(path: Path, start: int, end: int) -> list[str]:
    """Righe da `start` a `end` incluse, ciascuna preceduta dal proprio numero."""
    lines = read_lines(path)
    first = max(start, 1)
    last = min(end, len(lines))
    return [f"{number}: {lines[number - 1]}" for number in range(first, last + 1)]
