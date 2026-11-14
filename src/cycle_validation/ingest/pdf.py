"""Stadio 1: PDF → pagine di testo con PDFium. Deterministico, nessuna chiamata al modello."""

import hashlib
import threading
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
from pydantic import BaseModel, ConfigDict

from cycle_validation.config import FileLimits
from cycle_validation.errors import IngestError
from cycle_validation.text import squash

_HEADER = b"%PDF-"
_HEADER_WINDOW = 1024
# PDFium non è thread-safe, nemmeno su documenti diversi, e l'ingest gira in un thread per
# richiesta: ogni chiamata alla libreria passa da questo lock.
PDFIUM_LOCK = threading.RLock()


class NoTextLayerError(IngestError):
    """Il PDF non ha testo estraibile: è una scansione. Si può trascrivere con un modello."""


class PdfPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    number: int
    text: str


class PdfDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    sha256: str
    size_bytes: int
    pages: tuple[PdfPage, ...]

    @property
    def text(self) -> str:
        return "\n".join(page.text for page in self.pages)

    @property
    def n_chars(self) -> int:
        return sum(len(page.text) for page in self.pages)


def _page_text(document: Any, index: int) -> str:
    page = document[index]
    textpage = page.get_textpage()
    try:
        raw: str = textpage.get_text_bounded()
    finally:
        textpage.close()
        page.close()
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def read_pdf_bytes(data: bytes, name: str, limits: FileLimits) -> PdfDocument:
    """Valida e legge un PDF già in memoria. Solleva IngestError con il codice HTTP adatto."""
    if not data:
        raise IngestError(f"Il file {name} è vuoto.", http_status=400)
    if limits.require_pdf_header and _HEADER not in data[:_HEADER_WINDOW]:
        raise IngestError(f"Il file {name} non è un PDF.", http_status=415)
    if limits.max_bytes is not None and len(data) > limits.max_bytes:
        megabytes = limits.max_bytes / (1024 * 1024)
        raise IngestError(f"Il file {name} supera il limite di {megabytes:.0f} MB.", 413)
    with PDFIUM_LOCK:
        try:
            document = pdfium.PdfDocument(data)
        except pdfium.PdfiumError as exc:
            raise IngestError(f"Il PDF {name} non è leggibile: {exc}") from exc
        try:
            n_pages = len(document)
            if limits.max_pages is not None and n_pages > limits.max_pages:
                raise IngestError(
                    f"Il PDF {name} ha {n_pages} pagine: il limite è {limits.max_pages}."
                )
            texts = [_page_text(document, index) for index in range(n_pages)]
        finally:
            document.close()
    pages = tuple(PdfPage(number=number, text=text) for number, text in enumerate(texts, 1))
    result = PdfDocument(
        name=name, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data), pages=pages
    )
    if result.n_chars < limits.min_chars:
        raise NoTextLayerError(
            f"Il PDF {name} contiene meno di {limits.min_chars} caratteri di testo "
            "(è una scansione?). Senza trascrittore l'OCR non è disponibile."
        )
    check_required_text(result, limits)
    return result


def check_required_text(document: PdfDocument, limits: FileLimits) -> None:
    haystack = squash(document.text)
    missing = [marker for marker in limits.required_text if squash(marker) not in haystack]
    if missing:
        raise IngestError(
            f"Il documento {document.name} non è del tipo atteso: manca il testo "
            f"{', '.join(missing)}."
        )


def read_pdf(path: Path, limits: FileLimits) -> PdfDocument:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise IngestError(f"Impossibile leggere {path}: {exc}", http_status=400) from exc
    return read_pdf_bytes(data, path.name, limits)
