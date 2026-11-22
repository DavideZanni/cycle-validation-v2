"""Stampa modificata a mano: le righe toccate finiscono in fondo al PDF, ma sulla pagina stanno
al loro posto. La lettura le rimette nell'ordine in cui si vedono."""

from pathlib import Path

from pvrm320_report_fixtures import civil_pages

from cycle_validation.config import FileLimits
from cycle_validation.extract.pvrm320 import parse_pvrm320
from cycle_validation.ingest.pdf import read_pdf_bytes
from cycle_validation.testing.pdf import build_positioned_pdf

LIMITS = FileLimits(require_pdf_header=True, min_chars=10)


def _pieces(text: str) -> list[tuple[int, int, str]]:
    return [(row, 0, line) for row, line in enumerate(text.split("\n"))]


def _edited(text: str, word: str) -> list[tuple[int, int, str]]:
    """Come una modifica a mano: la riga con `word` e le tre dopo vanno in fondo al PDF, e la
    riga con `word` è spezzata in due (colonne a sinistra al loro posto, testo in fondo)."""
    lines = text.split("\n")
    at = next(index for index, line in enumerate(lines) if word in line)
    row = lines[at]
    cut = row.index("*", row.index("*") + 1) + 1
    moved = [(index, 0, lines[index]) for index in range(at + 1, at + 4)]
    kept = [piece for piece in _pieces(text) if not at <= piece[0] < at + 4]
    return [*kept, (at, 0, row[:cut]), *moved, (at, cut, row[cut:])]


def test_a_print_in_order_is_left_as_it_is() -> None:
    pages = civil_pages()
    pdf = read_pdf_bytes(build_positioned_pdf([_pieces(p) for p in pages]), "c.pdf", LIMITS)
    assert not any(page.reordered for page in pdf.pages)


def test_an_edited_print_is_read_in_the_order_of_the_page() -> None:
    pages = civil_pages()
    clean = read_pdf_bytes(build_positioned_pdf([_pieces(p) for p in pages]), "c.pdf", LIMITS)
    edited_pages = [_edited(pages[1], "RITIRO"), *(_pieces(p) for p in pages[2:])]
    edited = read_pdf_bytes(
        build_positioned_pdf([_pieces(pages[0]), *edited_pages]), "e.pdf", LIMITS
    )
    assert [page.reordered for page in edited.pages] == [False, True] + [False] * (len(pages) - 2)
    assert parse_pvrm320(edited) == parse_pvrm320(clean)


def test_leggi_says_which_pages_were_put_back_in_order(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from cycle_validation import cli

    pages = civil_pages()
    printed = tmp_path / "e.pdf"
    printed.write_bytes(build_positioned_pdf([_pieces(pages[0]), _edited(pages[1], "RITIRO")]))
    result = CliRunner().invoke(cli.app, ["leggi", str(printed)])
    assert result.exit_code == 0, result.output
    assert "  pagine rimesse nell'ordine della pagina: 2" in result.output.splitlines()
