"""`manuali`: quali manuali servono per i cicli di prova (codici inventati)."""

import json
from pathlib import Path

import pytest
from pvrm320_report_fixtures import civil_pages, ej200_pages
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.errors import CycleValidationError
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.report.manuals import (
    from_report,
    match_files,
    needed_manuals,
    parse_errors,
)
from cycle_validation.testing.pdf import build_pdf

KNOWLEDGE = Path("examples/sintetico/knowledge")


def _report(
    sources: list[tuple[str, str, str, str | None]],
    operations: list[tuple[str, str | None, list[str]]],
) -> dict:
    """sources: (manuale, task, esito del controllo della fonte, repair code);
    operations: (numero, repair code, task)."""
    return {
        "cycle": {
            "sources": [
                {"manual": m, "task": t, "issue": "Rev. 3", "repair_code": rc}
                for m, t, _, rc in sources
            ],
            "operations": [
                {"operation_number": number, "repair_code": rc, "task_codes": tasks}
                for number, rc, tasks in operations
            ],
        },
        "results": [
            {"check": "source", "target": {"kind": "source", "index": i}, "reason": reason}
            for i, (_, _, reason, _) in enumerate(sources)
        ]
        + [{"check": "task_code", "target": {"kind": "operation", "index": 0}, "reason": "X"}],
    }


REPORTS = {
    "errori-aaaa1111": _report(
        [
            ("MAN-DEMO-99", "99-20-02-300-004", "FONTE_ASSENTE", "R1"),
            ("MAN-DEMO-72", "72-00-01-110-001", "VERIFICATO", "R2"),
        ],
        [
            ("0005", "R1", ["99-10-01-110-001"]),  # task nella descrizione, non tra le fonti
            ("0010", "R2", ["72-00-01-110-001", "70-00-00-000-001"]),
            ("0035", "R1", []),  # senza task: si confronta con le fonti del suo repair code
        ],
    ),
    "errori-bbbb2222": _report(
        [("man-demo-99", "", "FONTE_ASSENTE", None)],
        [("030", None, ["99-10-01-110-001"])],
    ),
}


def _cycles() -> list:
    return [from_report(name, report) for name, report in REPORTS.items()]


def test_errors_are_hash_and_operations() -> None:
    assert parse_errors(["AAAA1111=005,035", "aaaa1111=40"]) == {"aaaa1111": {"5", "35", "40"}}
    with pytest.raises(CycleValidationError, match="impronta=op"):
        parse_errors(["aaaa1111"])


def test_operation_tasks_go_to_the_manual_of_their_repair_code() -> None:
    errors = parse_errors(["aaaa1111=005,035", "bbbb2222=030"])
    result = needed_manuals(_cycles(), errors)
    first, spm, last = result.manuals
    assert first.code == "MAN-DEMO-99" and first.state == "manca"
    assert first.cycles == {"errori-aaaa1111", "errori-bbbb2222"}  # maiuscole e minuscole
    assert first.tasks == {"99-10-01-110-001", "99-20-02-300-004"}
    assert first.chapters == ["99-10", "99-20"] and first.error_count == 3
    assert first.error_ops == {"errori-aaaa1111": {"5", "35"}, "errori-bbbb2222": {"30"}}
    assert spm.standard_practices and spm.tasks == {"70-00-00-000-001"}
    assert last.code == "MAN-DEMO-72" and last.state == "c'è" and not last.error_ops
    assert last.tasks == {"72-00-01-110-001"}  # il task 70- non è suo
    assert not result.loose_tasks and not result.unmatched


def test_with_the_knowledge_the_state_comes_from_it() -> None:
    cycles = _cycles()
    cycles[0].sources.append({"manual": "MAN-DEMO-72", "task": "72-99-99-999-999"})
    result = needed_manuals(cycles, {}, load_local_knowledge(KNOWLEDGE))
    states = {need.code: need.state for need in result.manuals}
    assert states["MAN-DEMO-99"] == "manca"
    assert states["MAN-DEMO-72"] == "c'è, ma mancano 1 task"


def test_manual_files_on_the_pc_are_matched_by_code_and_chapter() -> None:
    result = needed_manuals(_cycles(), {})
    match_files(
        result,
        [
            "C:/manuali/MAN DEMO 99/cap_99-10 riparazioni.pdf",
            "C:/manuali/MAN-DEMO-99/indice.pdf",
            "C:/manuali/MAN-DEMO-99/cap 99-100.pdf",  # 99-100 non è il capitolo 99-10
            "C:/manuali/SPM/70-00 pratiche.pdf",
            "C:/altro/documento.pdf",
        ],
    )
    first, spm, _ = result.manuals
    assert first.chapter_files == ["C:/manuali/MAN DEMO 99/cap_99-10 riparazioni.pdf"]
    assert len(first.files) == 3
    assert spm.chapter_files == ["C:/manuali/SPM/70-00 pratiche.pdf"]


def test_the_command_reads_the_prints_and_hides_the_codes(tmp_path: Path) -> None:
    prints = tmp_path / "stampe"
    prints.mkdir()
    pdf = build_pdf(civil_pages())
    (prints / "ciclo.pdf").write_bytes(pdf)
    (prints / "copia dello stesso ciclo.pdf").write_bytes(pdf)
    (prints / "non un ciclo.pdf").write_bytes(build_pdf(["testo qualunque " * 20]))
    military = [page.replace("MOTORE-1/MOTORE-2", "EJ200") for page in ej200_pages()]
    (prints / "militare.pdf").write_bytes(build_pdf(military))
    manual = build_pdf(["pagina di manuale " * 20])
    (prints / "ABC123456 capitolo 72-00.pdf").write_bytes(manual)
    (prints / "ABC123456 indice.pdf").write_bytes(manual + b" ")
    run = tmp_path / "errori-aaaa1111"
    run.mkdir()
    (run / "report.json").write_text(json.dumps(REPORTS["errori-aaaa1111"]), encoding="utf-8")
    out = tmp_path / "manuali.txt"
    result = CliRunner().invoke(
        cli.app,
        [
            "manuali",
            str(prints),
            str(run),
            "--errori",
            "aaaa1111=005",
            "--conoscenza",
            str(KNOWLEDGE),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Stampe: 6 file, 5 diverse; cicli letti: 3; non lette" in result.output
    for code in ("ABC123456", "MAN-DEMO", "72-00", "ciclo.pdf"):
        assert code not in result.output
    assert "M1: manca · 1 cicli · 2 task in 2 capitoli · serve per 1 errori" in result.output
    assert "PDF sul PC: 2, dei capitoli citati: 1" in result.output  # i file del manuale
    assert "cicli EJ200 lasciati fuori (conoscenza solo su AWS): 1" in result.output
    assert "da ingestionare: 3" in result.output
    text = out.read_text(encoding="utf-8")
    assert "M1  MAN-DEMO-99  (manca)" in text and "capitoli: 99-10, 99-20" in text
    assert "task: 72-00-00 REPAIR 001" in text  # il task della stampa, con gli spazi
    assert "ciclo.pdf | copia dello stesso ciclo.pdf" in text
    assert "non un ciclo.pdf" not in text
    assert "ABC123456 capitolo 72-00.pdf" in text


def test_the_command_stops_without_cycles(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli.app, ["manuali", str(tmp_path)])
    assert result.exit_code == 1 and "Nessun ciclo letto" in result.output
