"""`manuali`: quali manuali servono, letti dai report delle prove già fatte (codici inventati)."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.errors import CycleValidationError
from cycle_validation.report.manuals import needed_manuals, parse_errors


def _report(sources: list[tuple[str, str, str]], operations: list[tuple[str, list[str]]]) -> dict:
    """sources: (manuale, task, esito del controllo della fonte); operations: (numero, task)."""
    return {
        "cycle": {
            "sources": [{"manual": m, "task": t, "issue": "Rev. 3"} for m, t, _ in sources],
            "operations": [
                {"operation_number": number, "task_codes": tasks} for number, tasks in operations
            ],
        },
        "results": [
            {"check": "source", "target": {"kind": "source", "index": i}, "reason": reason}
            for i, (_, _, reason) in enumerate(sources)
        ]
        + [{"check": "task_code", "target": {"kind": "operation", "index": 0}, "reason": "X"}],
    }


REPORTS = {
    "errori-aaaa1111": _report(
        [
            ("MAN-FINTO-72", "72-10-01-110-001", "FONTE_ASSENTE"),
            ("MAN-FINTO-72", "72-20-02-300-004", "FONTE_ASSENTE"),
            ("MAN-SPM", "70-00-00-000-001", "VERIFICATO"),
        ],
        [("0005", ["72-10-01-110-001"]), ("0010", ["70-00-00-000-001"]), ("0035", [])],
    ),
    "errori-bbbb2222": _report(
        [("man-finto-72", "72-10-01-110-001", "FONTE_ASSENTE")],
        [("030", ["72-10-01-110-001"])],
    ),
}


def test_errors_are_hash_and_operations() -> None:
    assert parse_errors(["AAAA1111=005,035", "aaaa1111=40"]) == {"aaaa1111": {"5", "35", "40"}}
    with pytest.raises(CycleValidationError, match="impronta=op"):
        parse_errors(["aaaa1111"])


def test_manuals_needed_for_the_errors_come_first() -> None:
    errors = parse_errors(["aaaa1111=005,035", "bbbb2222=030"])
    result = needed_manuals(REPORTS, errors)
    first, second = result.manuals
    assert first.code == "MAN-FINTO-72" and first.state == "manca"
    assert first.cycles == {"errori-aaaa1111", "errori-bbbb2222"}  # maiuscole e minuscole
    assert first.chapters == ["72-10", "72-20"] and first.error_count == 2
    assert first.error_ops == {"errori-aaaa1111": {"5"}, "errori-bbbb2222": {"30"}}
    assert second.code == "MAN-SPM" and second.state == "c'è" and not second.error_ops
    assert result.unmatched == ["errori-aaaa1111 op 35: 0 task, nessuno nelle fonti del ciclo"]


def test_the_command_hides_the_codes_on_screen(tmp_path: Path) -> None:
    folders = []
    for name, report in REPORTS.items():
        folder = tmp_path / name
        folder.mkdir()
        (folder / "report.json").write_text(json.dumps(report), encoding="utf-8")
        folders.append(str(folder))
    (tmp_path / "errori-rotto").mkdir()
    out = tmp_path / "manuali.txt"
    result = CliRunner().invoke(
        cli.app,
        [
            "manuali",
            *folders,
            str(tmp_path / "errori-rotto"),
            "--errori",
            "aaaa1111=005",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "MAN-FINTO" not in result.output and "72-10" not in result.output
    assert "M1: manca · 2 cicli · 2 task in 2 capitoli" in result.output
    assert "serve per 1 errori (errori-aaaa1111 op 5)" in result.output
    assert "errori-rotto: report.json non letto" in result.output
    text = out.read_text(encoding="utf-8")
    assert "M1  MAN-FINTO-72  (manca)" in text and "capitoli: 72-10, 72-20" in text


def test_the_command_stops_without_reports(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli.app, ["manuali", str(tmp_path / "niente")])
    assert result.exit_code == 1 and "Nessun report.json" in result.output
