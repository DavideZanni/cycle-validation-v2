"""Stadio 1 esteso: PDF con testo → PDFium; immagini e PDF scansionati → trascrittore (modello).

Regola: PDFium se c'è un livello di testo, altrimenti si renderizzano le pagine in PNG e le si
trascrive con il modello. Le immagini (JPEG, PNG) sono una pagina sola.
"""

import io
from collections import deque
from collections.abc import Generator, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import Any

from PIL import Image

from cycle_validation.config import FileLimits
from cycle_validation.domain.check import Usage
from cycle_validation.errors import IngestError
from cycle_validation.ingest.pdf import (
    PDFIUM_LOCK,
    NoTextLayerError,
    PdfDocument,
    PdfPage,
    check_required_text,
    check_size,
    is_pdf,
    open_pdf,
    read_pdf_bytes,
)
from cycle_validation.ingest.transcribe import PageTranscriber

_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"
_RENDER_SCALE = 2.5  # ~180 dpi: abbastanza per testo da 8 pt senza pagine enormi
_MAX_RENDER_SIDE_PX = 3000  # un A3 a 180 dpi; oltre, la scala si riduce
# Limiti per immagine dell'API Converse di Bedrock (3,75 MB, 8000 px per lato): valori noti
# dalla documentazione pubblica, da riconfermare nell'account aziendale.
_MODEL_IMAGE_BYTES = 3_750_000
_MODEL_IMAGE_SIDE_PX = 8000
_MAX_IMAGE_PIXELS = 50_000_000  # oltre non si decodifica: sarebbe più di 150 MB in memoria
_JPEG_QUALITIES = (85, 70)


def _media_type(data: bytes) -> str | None:
    if data.startswith(_PNG):
        return "image/png"
    if data.startswith(_JPEG):
        return "image/jpeg"
    return None


def _image_size(data: bytes, name: str) -> tuple[int, int]:
    """Dimensioni lette dall'intestazione, senza decodificare i pixel. Rifiuta ciò che ha solo
    la firma di un'immagine e ciò che è troppo grande per essere aperto senza rischi."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            too_many = width * height > _MAX_IMAGE_PIXELS
            if not too_many:
                image.verify()
    except Image.DecompressionBombError:
        too_many = True
    except Exception as exc:
        raise IngestError(f"L'immagine {name} non è leggibile ({type(exc).__name__}).") from exc
    if too_many:
        megapixels = _MAX_IMAGE_PIXELS // 1_000_000
        raise IngestError(f"L'immagine {name} supera {megapixels} milioni di pixel.", 413)
    return width, height


def _encode_under_limit(image: Image.Image) -> bytes:
    """JPEG sotto il limite di peso del modello: prima si abbassa la qualità, poi la misura."""
    image = image.convert("RGB")
    while True:
        for quality in _JPEG_QUALITIES:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            if buffer.tell() <= _MODEL_IMAGE_BYTES:
                return buffer.getvalue()
        image = image.resize((max(image.width * 3 // 4, 1), max(image.height * 3 // 4, 1)))


def _fit_for_model(data: bytes, media_type: str, size: tuple[int, int]) -> tuple[bytes, str]:
    """L'immagine così com'è se il modello la accetta, altrimenti ridotta e ricodificata."""
    if len(data) <= _MODEL_IMAGE_BYTES and max(size) <= _MODEL_IMAGE_SIDE_PX:
        return data, media_type
    with Image.open(io.BytesIO(data)) as image:
        image.thumbnail((_MAX_RENDER_SIDE_PX, _MAX_RENDER_SIDE_PX))
        return _encode_under_limit(image), "image/jpeg"


def _render_page(document: Any, index: int) -> tuple[bytes, str]:
    page = document[index]
    try:
        # una pagina enorme (formato dichiarato dal file) non deve diventare una bitmap enorme
        scale = min(_RENDER_SCALE, _MAX_RENDER_SIDE_PX / max(*page.get_size(), 1.0))
        image = page.render(scale=scale).to_pil().convert("RGB")
    finally:
        page.close()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    if buffer.tell() <= _MODEL_IMAGE_BYTES:
        return buffer.getvalue(), "image/png"
    # una scansione rumorosa in PNG può superare il limite: in JPEG pesa molto meno
    return _encode_under_limit(image), "image/jpeg"


def _rendered_pages(
    data: bytes, name: str, limits: FileLimits
) -> Generator[tuple[bytes, str], None, None]:
    """Le pagine come immagini, una alla volta: in memoria ce n'è una sola, e se la trascrizione di
    una pagina fallisce le successive non vengono nemmeno renderizzate."""
    with PDFIUM_LOCK:
        document = open_pdf(data, name)
        n_pages = len(document)
    try:
        if n_pages > limits.max_transcribed_pages:
            raise IngestError(
                f"Il PDF {name} è una scansione di {n_pages} pagine: se ne trascrivono al "
                f"massimo {limits.max_transcribed_pages}.",
                http_status=413,
            )
        for index in range(n_pages):
            # il lock copre il solo rendering: durante la chiamata al modello resta libero
            with PDFIUM_LOCK:
                image = _render_page(document, index)
            yield image
    finally:
        with PDFIUM_LOCK:
            document.close()


def _transcribe_pages(
    images: Iterable[tuple[bytes, str]], tr: PageTranscriber, concurrency: int
) -> list[tuple[str, Usage]]:
    """Le trascrizioni in ordine di pagina. Con `concurrency` > 1 le pagine vanno al modello
    insieme, al massimo `concurrency` alla volta: la pagina successiva si renderizza solo quando
    un posto si libera, così in memoria restano poche immagini e, se una pagina fallisce, le
    successive non partono."""
    if concurrency <= 1:
        return [tr.transcribe(image, media_type) for image, media_type in images]
    results: list[tuple[str, Usage]] = []
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="trascrizione") as pool:
        pending: deque[Future[tuple[str, Usage]]] = deque()
        try:
            for image, media_type in images:
                pending.append(pool.submit(tr.transcribe, image, media_type))
                if len(pending) >= concurrency:
                    results.append(pending.popleft().result())
            while pending:
                results.append(pending.popleft().result())
        finally:
            for future in pending:
                future.cancel()
    return results


def _transcribe(
    images: Iterable[tuple[bytes, str]],
    data: bytes,
    name: str,
    limits: FileLimits,
    tr: PageTranscriber,
    concurrency: int = 1,
) -> tuple[PdfDocument, Usage]:
    usage = Usage()
    pages: list[PdfPage] = []
    for number, (text, used) in enumerate(_transcribe_pages(images, tr, concurrency), 1):
        usage = usage + used
        pages.append(PdfPage(number=number, text=text.strip()))
    document = PdfDocument.of(data, name, tuple(pages))
    if document.n_chars < limits.min_chars:
        raise IngestError(
            f"La trascrizione di {name} contiene meno di {limits.min_chars} caratteri: "
            "immagine illeggibile o non è un ciclo."
        )
    check_required_text(document, limits)
    return document, usage


def read_document_bytes(
    data: bytes,
    name: str,
    limits: FileLimits,
    transcriber: PageTranscriber | None,
    *,
    concurrency: int = 1,
) -> tuple[PdfDocument, Usage]:
    """Legge PDF o immagine. Restituisce il documento e i consumi del modello (zero se PDFium).
    `concurrency`: pagine scansionate trascritte insieme (`agent.transcribe_concurrency`)."""
    if not data:
        raise IngestError(f"Il file {name} è vuoto.", http_status=400)
    pdf = is_pdf(data)
    media_type = None if pdf else _media_type(data)
    if not pdf and media_type is None:
        raise IngestError(f"Il file {name} non è un PDF né un'immagine JPEG o PNG.", 415)
    check_size(data, name, limits)
    if media_type is not None:
        if transcriber is None:
            raise IngestError(
                f"Il file {name} è un'immagine e nessun trascrittore è configurato.", 415
            )
        image = _fit_for_model(data, media_type, _image_size(data, name))
        return _transcribe([image], data, name, limits, transcriber)
    try:
        return read_pdf_bytes(data, name, limits), Usage()
    except NoTextLayerError:
        if transcriber is None:
            raise
    with closing(_rendered_pages(data, name, limits)) as pages:
        return _transcribe(pages, data, name, limits, transcriber, concurrency)


def read_document(
    path: Path,
    limits: FileLimits,
    transcriber: PageTranscriber | None,
    *,
    concurrency: int = 1,
) -> tuple[PdfDocument, Usage]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise IngestError(f"Impossibile leggere {path}: {exc}", http_status=400) from exc
    return read_document_bytes(data, path.name, limits, transcriber, concurrency=concurrency)
