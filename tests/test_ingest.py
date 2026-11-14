from collections.abc import Callable
from pathlib import Path

import pytest
from pdf_factory import build_pdf

from cycle_validation.config import FileLimits
from cycle_validation.errors import IngestError
from cycle_validation.ingest.pdf import read_pdf, read_pdf_bytes

LIMITS = FileLimits(min_chars=10)


def test_reads_text_per_page(make_pdf: Callable[..., Path]) -> None:
    document = read_pdf(make_pdf(["Operazione 0010\nPulire il pezzo", "Seconda pagina"]), LIMITS)
    assert [page.number for page in document.pages] == [1, 2]
    assert document.pages[0].text == "Operazione 0010\nPulire il pezzo"
    assert "\r" not in document.text
    assert document.name == "ciclo.pdf"


def test_hash_is_stable() -> None:
    data = build_pdf(["Testo di prova lungo abbastanza"])
    first = read_pdf_bytes(data, "a.pdf", LIMITS)
    second = read_pdf_bytes(data, "b.pdf", LIMITS)
    assert first.sha256 == second.sha256 and len(first.sha256) == 64


def _status(data: bytes, limits: FileLimits) -> int:
    with pytest.raises(IngestError) as caught:
        read_pdf_bytes(data, "x.pdf", limits)
    return caught.value.http_status


def test_empty_file_is_400() -> None:
    assert _status(b"", LIMITS) == 400


def test_missing_file_is_400(tmp_path: Path) -> None:
    with pytest.raises(IngestError) as caught:
        read_pdf(tmp_path / "assente.pdf", LIMITS)
    assert caught.value.http_status == 400


def test_non_pdf_is_415() -> None:
    assert _status(b"questo non e un pdf", LIMITS) == 415


def test_too_large_is_413() -> None:
    data = build_pdf(["Testo di prova lungo abbastanza"])
    assert _status(data, FileLimits(max_bytes=100)) == 413


def test_too_many_pages_is_422() -> None:
    data = build_pdf(["pagina uno con testo", "pagina due con testo"])
    assert _status(data, FileLimits(max_pages=1, min_chars=1)) == 422


def test_unreadable_pdf_is_422() -> None:
    assert _status(b"%PDF-1.4\nrotto", LIMITS) == 422


def test_pdf_without_text_is_422() -> None:
    with pytest.raises(IngestError, match="OCR"):
        read_pdf_bytes(build_pdf(["", ""]), "x.pdf", LIMITS)


def test_required_text_missing_is_422() -> None:
    data = build_pdf(["Ciclo civile senza marcatore"])
    with pytest.raises(IngestError, match="EJ200"):
        read_pdf_bytes(data, "x.pdf", FileLimits(min_chars=1, required_text=["EJ200"]))


def test_required_text_is_found_ignoring_layout() -> None:
    data = build_pdf(["Progetto EJ 200 - ciclo di prova"])
    limits = FileLimits(min_chars=1, required_text=["EJ200"])
    assert read_pdf_bytes(data, "x.pdf", limits).n_chars > 0
