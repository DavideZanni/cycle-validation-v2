"""Verifica delle citazioni: una citazione vale solo se il codice la ritrova nel file.

L'agente indica file, riga e testo letterale. Il codice riapre il file e cerca il testo
attorno a quella riga. Senza riscontro la citazione non conta e l'esito resta un warning.
"""

from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from cycle_validation.domain.check import Evidence
from cycle_validation.kb.documents import PAGE_MARKER, page_at, read_lines
from cycle_validation.kb.port import DocumentInfo
from cycle_validation.text import normalize_code, normalize_quote

MIN_QUOTE_CHARS = 8


class Citation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    file: str
    line: int
    quote: str


def _match_document(file: str, allowed: Sequence[DocumentInfo]) -> DocumentInfo | None:
    cited = Path(file.strip())
    for document in allowed:
        same_path = cited.is_absolute() and cited.resolve() == document.path.resolve()
        same_name = cited.name.casefold() == document.path.name.casefold()
        same_key = normalize_code(file) == normalize_code(document.key)
        if same_path or same_key or (not cited.is_absolute() and same_name):
            return document
    return None


def verify_citation(
    citation: Citation, allowed: Sequence[DocumentInfo], window: int
) -> Evidence | None:
    """Restituisce l'evidenza se la citazione compare nel documento, altrimenti None."""
    document = _match_document(citation.file, allowed)
    wanted = normalize_quote(citation.quote)
    if document is None or len(wanted) < MIN_QUOTE_CHARS:
        return None
    lines = read_lines(document.path)
    if not 1 <= citation.line <= len(lines):
        return None
    first = max(citation.line - window, 1)
    last = min(citation.line + window, len(lines))
    numbers = [
        number for number in range(first, last + 1) if not PAGE_MARKER.match(lines[number - 1])
    ]
    # Si cerca la citazione a partire da ogni riga della finestra, unendo le righe successive:
    # così una citazione su più righe viene ritrovata e si conosce la riga in cui inizia.
    for position, start in enumerate(numbers):
        joined = ""
        first_len = len(normalize_quote(lines[start - 1]))
        if not first_len:
            # una riga vuota non può essere l'inizio della citazione: riga e pagina riportate
            # sarebbero quelle prima del testo citato
            continue
        for number in numbers[position:]:
            joined = normalize_quote(f"{joined} {lines[number - 1]}")
            # La citazione deve cominciare nella prima riga: così la riga riportata è quella giusta.
            if 0 <= joined.find(wanted) < first_len:
                return Evidence(
                    document_key=document.key,
                    version=document.version,
                    page=page_at(document.path, start),
                    line=start,
                    quote=" ".join(citation.quote.split()),
                )
            if len(joined) > len(wanted) + 400:
                break
    return None
