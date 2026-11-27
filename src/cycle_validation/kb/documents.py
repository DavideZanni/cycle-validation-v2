"""Documenti di riferimento come file di testo a righe.

Una riga di file per riga di testo; `<!-- page N -->` segna l'inizio della pagina N.
Le righe si contano da 1, come fanno Read e Grep.
"""

import hashlib
import re
from functools import lru_cache
from pathlib import Path

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


# Un codice di task completo nel testo, con gli stessi confini della ricerca dei fratelli.
_FULL_TASK_CODE = re.compile(r"(?<![\dA-Za-z-])(\d{2}-\d{2}-\d{2}-\d{3}-\d{3})(?![\dA-Za-z]|-\d)")


@lru_cache(maxsize=512)
def _cached_codes(path: str, mtime_ns: int) -> frozenset[str]:
    return frozenset(_FULL_TASK_CODE.findall("\n".join(_cached_lines(path, mtime_ns))))


def full_task_codes(path: Path) -> frozenset[str]:
    """I codici di task completi scritti nel documento, in cache finché il file non cambia:
    con 2900 documenti la ricerca dei codici sbagliati non rilegge gli SPM a ogni codice."""
    try:
        return _cached_codes(str(path), path.stat().st_mtime_ns)
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceUnavailableError(f"Documento non leggibile: {path.name} ({exc})") from exc


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
