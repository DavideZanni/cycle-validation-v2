import json
from pathlib import Path

import pytest
from fakes import ScriptedSession
from kb_fixtures import EXAMPLE_DIR, EXAMPLE_KB
from support import example_cycle, scripted_judge, write_cycle_pdf
from typer.testing import CliRunner

from cycle_validation import cli

runner = CliRunner()


@pytest.fixture(autouse=True)
def fake_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli, "make_session", lambda settings, transcripts: ScriptedSession(scripted_judge)
    )


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    return write_cycle_pdf(tmp_path / "ciclo.pdf", example_cycle())


def base_args(pdf: Path, out: Path) -> list[str]:
    return [
        "run",
        str(pdf),
        "--cycle-json",
        str(EXAMPLE_DIR / "ciclo.json"),
        "--knowledge",
        str(EXAMPLE_KB),
        "--machines",
        str(EXAMPLE_DIR / "macchine_attive.json"),
        "--out",
        str(out),
    ]


def test_kb_check_prints_counts() -> None:
    result = runner.invoke(cli.app, ["kb-check", str(EXAMPLE_KB)])
    assert result.exit_code == 0, result.output
    assert "documenti" in result.output
    assert "sintetico-2026-11" in result.output


def test_kb_check_reports_a_broken_knowledge_base(tmp_path: Path) -> None:
    result = runner.invoke(cli.app, ["kb-check", str(tmp_path)])
    assert result.exit_code == 1
    assert "manifest" in result.output.lower()


def test_run_writes_the_outputs(pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = runner.invoke(cli.app, base_args(pdf, out))
    assert result.exit_code == 0, result.output
    assert "completo" in result.output
    payload = json.loads((out / "payload.json").read_text(encoding="utf-8"))
    assert payload["cycle_errors_count"] == 2


def test_run_with_skip_check(pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    args = [*base_args(pdf, out), "--skip-check", "operation_description"]
    assert runner.invoke(cli.app, args).exit_code == 0
    payload = json.loads((out / "payload.json").read_text(encoding="utf-8"))
    assert payload["operations"][0]["operationFeedback"] == "N/A"


def test_unknown_skip_check_is_refused(pdf: Path, tmp_path: Path) -> None:
    args = [*base_args(pdf, tmp_path / "o"), "--skip-check", "boh"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 2


def test_unknown_profile_is_refused(pdf: Path, tmp_path: Path) -> None:
    args = [*base_args(pdf, tmp_path / "o"), "--profile", "nope"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 1
    assert "nope" in result.output


def test_run_without_cycle_json_extracts_with_the_model(
    pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cycle = example_cycle().model_dump(mode="json")
    for operation in cycle["operations"]:
        operation["process_sheet"] = (
            {"code": operation["process_sheet"]["code"]} if operation["process_sheet"] else None
        )
    for source in cycle["sources"]:
        source.setdefault("issue", None)

    def script(request: object, attempt: int) -> dict[str, object]:
        if getattr(request, "session_id", "") == "extract":
            return cycle
        return scripted_judge(request, attempt)  # type: ignore[arg-type]

    monkeypatch.setattr(cli, "make_session", lambda settings, transcripts: ScriptedSession(script))
    out = tmp_path / "o"
    args = [
        "run",
        str(pdf),
        "--knowledge",
        str(EXAMPLE_KB),
        "--machines",
        str(EXAMPLE_DIR / "macchine_attive.json"),
        "--out",
        str(out),
    ]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    payload = json.loads((out / "payload.json").read_text(encoding="utf-8"))
    assert payload["cycleCode"] == "CICLO-DEMO-001"
    assert payload["cycle_errors_count"] == 2


def test_golden_command(tmp_path: Path) -> None:
    from pathlib import Path as P

    golden = P(__file__).parent / "golden" / "mos"
    result = runner.invoke(
        cli.app,
        [
            "golden",
            str(golden),
            "--knowledge",
            str(EXAMPLE_KB),
            "--machines",
            str(EXAMPLE_DIR / "macchine_attive.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "concordanza 100.0%" in result.output


def test_dr_profile_requires_selectors(pdf: Path, tmp_path: Path) -> None:
    args = [*base_args(pdf, tmp_path / "o"), "--profile", "dr"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 1
    assert "serial" in result.output.lower()


def test_dr_profile_blocks_on_not_applicable_recommendation(pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "o"
    args = [
        *base_args(pdf, out),
        "--profile",
        "dr",
        "--serial-number",
        "SN-DEMO-002",
        "--condition",
        "1,2",
    ]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    assert "bloccato" in result.output


def test_kb_export_from_snapshot_then_kb_check(tmp_path: Path) -> None:
    import json as _json

    from kb_fixtures import example_chunks, example_store

    snapshot = tmp_path / "snapshot"
    for key in example_store().list_keys(""):
        target = snapshot / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(example_store().get_bytes(key))
    chunks = tmp_path / "chunks.jsonl"
    chunks.write_text("\n".join(_json.dumps(c) for c in example_chunks()), encoding="utf-8")
    out = tmp_path / "kb"
    result = runner.invoke(
        cli.app,
        [
            "kb-export",
            "--structured-dir",
            str(snapshot),
            "--chunks",
            str(chunks),
            "--cycle-json",
            str(EXAMPLE_DIR / "ciclo.json"),
            "--out",
            str(out),
            "--version",
            "export-test",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "task esportati" in result.output
    check = runner.invoke(cli.app, ["kb-check", str(out)])
    assert check.exit_code == 0 and "export-test" in check.output
