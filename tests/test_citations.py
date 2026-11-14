from pathlib import Path

import pytest
from kb_fixtures import DOC_72, DOC_75

from cycle_validation.verdict.citations import Citation, verify_citation

ALLOWED = [DOC_72]


def cite(line: int, quote: str, file: str = "MAN-DEMO-72.md") -> Citation:
    return Citation(file=file, line=line, quote=quote)


def test_exact_quote_gives_document_version_page_and_line() -> None:
    evidence = verify_citation(cite(7, "Pulire il supporto con solvente tipo A."), ALLOWED, 3)
    assert evidence is not None
    assert (evidence.document_key, evidence.version, evidence.page, evidence.line) == (
        "MAN-DEMO-72",
        "Rev. 12",
        1,
        7,
    )


def test_page_follows_the_marker() -> None:
    evidence = verify_citation(cite(14, "Cricche non ammesse."), ALLOWED, 3)
    assert evidence is not None
    assert evidence.page == 2


def test_case_and_spacing_are_ignored() -> None:
    assert verify_citation(cite(7, "pulire  il SUPPORTO   con solvente tipo a."), ALLOWED, 3)


def test_quote_over_two_lines() -> None:
    evidence = verify_citation(
        cite(7, "Pulire il supporto con solvente tipo A. 3. Asciugare con aria"), ALLOWED, 3
    )
    assert evidence is not None
    assert evidence.line == 7


def test_line_shifted_within_window() -> None:
    evidence = verify_citation(cite(9, "Pulire il supporto con solvente tipo A."), ALLOWED, 3)
    assert evidence is not None
    assert evidence.line == 7


def test_line_outside_window_is_rejected() -> None:
    assert verify_citation(cite(18, "Pulire il supporto con solvente tipo A."), ALLOWED, 3) is None


def test_file_not_allowed_is_rejected() -> None:
    assert verify_citation(cite(5, "TASK 75-10-02-400-001", "MAN-DEMO-75.md"), ALLOWED, 3) is None
    assert verify_citation(cite(5, "x" * 20, "altro.md"), [DOC_72, DOC_75], 3) is None


def test_file_by_key_and_absolute_path() -> None:
    assert verify_citation(cite(7, "Pulire il supporto con solvente", "MAN-DEMO-72"), ALLOWED, 3)
    absolute = str(Path(DOC_72.path).resolve())
    assert verify_citation(cite(7, "Pulire il supporto con solvente", absolute), ALLOWED, 3)


def test_invented_text_is_rejected() -> None:
    assert verify_citation(cite(7, "Immergere il supporto in acido"), ALLOWED, 3) is None


def test_too_short_quote_is_rejected() -> None:
    assert verify_citation(cite(7, "tipo A."), ALLOWED, 3) is None


@pytest.mark.parametrize("line", [0, -1, 999])
def test_line_out_of_file_is_rejected(line: int) -> None:
    assert verify_citation(cite(line, "Pulire il supporto con solvente"), ALLOWED, 3) is None


def test_a_blank_line_before_the_quote_does_not_shift_line_and_page(tmp_path: Path) -> None:
    from cycle_validation.kb.port import DocumentInfo

    path = tmp_path / "doc.md"
    path.write_text(
        "<!-- page 1 -->\nTesto della prima pagina.\n\n<!-- page 2 -->\n"
        "La sede va rettificata a 45,00 mm.\n",
        encoding="utf-8",
    )
    document = DocumentInfo(key="DOC", path=path)
    evidence = verify_citation(
        cite(5, "La sede va rettificata a 45,00 mm.", "doc.md"), [document], 3
    )
    assert evidence is not None
    assert (evidence.line, evidence.page) == (5, 2)
