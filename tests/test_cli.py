import json
import shutil
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


def _knowledge_with_doubts(tmp_path: Path, doubts: object) -> Path:
    target = tmp_path / "knowledge"
    shutil.copytree(EXAMPLE_KB, target)
    (target / "uncertainty.json").write_text(json.dumps(doubts), encoding="utf-8")
    return target


def test_kb_check_counts_the_doubtful_entries(tmp_path: Path) -> None:
    knowledge = _knowledge_with_doubts(
        tmp_path,
        {
            "format": 1,
            "machine_tags": {"TM-1001": ["valori_alternativi"]},
            "process_sheets": {"SP-0101": ["da_record_parziale"], "SP-0202": ["x"]},
        },
    )
    result = runner.invoke(cli.app, ["kb-check", str(knowledge)])
    assert result.exit_code == 0, result.output
    assert "targhe_incerte: 1" in result.output
    assert "schede_incerte: 2" in result.output
    assert "recommendation_dr_incerte: 0" in result.output


def test_kb_check_fails_on_an_inconsistent_uncertainty_file(tmp_path: Path) -> None:
    knowledge = _knowledge_with_doubts(
        tmp_path, {"format": 1, "process_sheets": {"SP-9999": ["valori_alternativi"]}}
    )
    result = runner.invoke(cli.app, ["kb-check", str(knowledge)])
    assert result.exit_code == 1
    assert "SP-9999" in result.output


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

    golden = P(__file__).parents[1] / "eval" / "casi" / "sintetici" / "mos"
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


def test_eval_runs_a_variant_and_writes_the_leaderboard(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    results = tmp_path / "risultati"
    common = ["--risultati", str(results)]
    for variant in ("baseline", "effort_low"):
        result = runner.invoke(
            cli.app,
            [
                "eval",
                "esegui",
                "--variante",
                str(root / "eval" / "varianti" / f"{variant}.yaml"),
                "--casi",
                str(root / "eval" / "casi" / "sintetici" / "dr"),
                "--ripetizioni",
                "2",
                "--ambiente",
                "prova",
                "--runs",
                str(tmp_path / "runs"),
                *common,
            ],
        )
        assert result.exit_code == 0, result.output
        assert "[10/10]" in result.output
        assert "concordanza 100,0%" in result.output
    out = tmp_path / "classifica.md"
    result = runner.invoke(cli.app, ["eval", "classifica", *common, "--out", str(out)])
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "## Ambiente: prova" in text
    assert "`effort_low`" in text and "`baseline`" in text
    assert "Ambiente: prova" in result.output
    # Senza --out la classifica va accanto ai risultati che legge, non in eval/risultati.
    result = runner.invoke(cli.app, ["eval", "classifica", *common])
    assert result.exit_code == 0, result.output
    results = Path(common[common.index("--risultati") + 1])
    assert "## Ambiente: prova" in (results / "classifica.md").read_text(encoding="utf-8")


def test_eval_reports_a_bad_variant_clearly(tmp_path: Path) -> None:
    result = runner.invoke(cli.app, ["eval", "esegui", "--variante", str(tmp_path / "x.yaml")])
    assert result.exit_code == 1
    assert "Variante non trovata" in result.output


def test_eval_pipeline_runs_every_variant_and_writes_the_leaderboard(tmp_path: Path) -> None:
    import shutil

    root = Path(__file__).parents[1]
    variants = tmp_path / "varianti"
    variants.mkdir()
    for name in ("baseline", "effort_low"):
        shutil.copy(root / "eval" / "varianti" / f"{name}.yaml", variants)
    results = tmp_path / "risultati"
    result = runner.invoke(
        cli.app,
        [
            "eval",
            "pipeline",
            "--salta-verifiche",
            "--casi",
            str(root / "eval" / "casi" / "sintetici" / "dr"),
            "--varianti",
            str(variants),
            "--ripetizioni",
            "1",
            "--ambiente",
            "prova",
            "--risultati",
            str(results),
            "--runs",
            str(tmp_path / "runs"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "2 varianti x 5 casi x 1 ripetizioni (baseline, effort_low)" in result.output
    assert "variante 1/2: baseline" in result.output
    assert "`effort_low`" in (results / "classifica.md").read_text(encoding="utf-8")


def test_eval_pipeline_stops_when_no_case_has_been_reviewed(tmp_path: Path) -> None:
    suite = tmp_path / "s"
    (suite / "c").mkdir(parents=True)
    (suite / "suite.yaml").write_text(f"conoscenza: {EXAMPLE_KB.as_posix()}\n", encoding="utf-8")
    (suite / "c" / "ciclo.json").write_text("{}", encoding="utf-8")
    (suite / "c" / "expected.json").write_text(
        '{"profile": "mos", "rivisto": false, "rows": []}', encoding="utf-8"
    )
    result = runner.invoke(cli.app, ["eval", "pipeline", "--salta-verifiche", "--casi", str(suite)])
    assert result.exit_code == 1
    assert "Nessun caso rivisto" in result.output


def test_eval_prepare_writes_a_draft_to_review(tmp_path: Path) -> None:
    suite = tmp_path / "aziendali"
    case = suite / "caso"
    case.mkdir(parents=True)
    (suite / "suite.yaml").write_text(
        f"conoscenza: {EXAMPLE_KB.as_posix()}\n"
        f"macchine: {(EXAMPLE_DIR / 'macchine_attive.json').as_posix()}\n",
        encoding="utf-8",
    )
    write_cycle_pdf(case / "ciclo.pdf", example_cycle())
    (case / "ciclo.json").write_text(example_cycle().model_dump_json(), encoding="utf-8")
    result = runner.invoke(cli.app, ["eval", "prepara", str(case), "--profilo", "mos"])
    assert result.exit_code == 0, result.output
    assert "Bozza scritta" in result.output
    expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
    assert expected["rivisto"] is False and expected["rows"]
    again = runner.invoke(cli.app, ["eval", "prepara", str(case)])
    assert again.exit_code == 0  # una bozza non rivista si può rifare
    reviewed = {**expected, "rivisto": True}
    (case / "expected.json").write_text(json.dumps(reviewed), encoding="utf-8")
    refused = runner.invoke(cli.app, ["eval", "prepara", str(case)])
    assert refused.exit_code == 1
    assert "già stato rivisto" in refused.output


def test_eval_mutazioni_writes_the_mutated_suites(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    out = tmp_path / "mutazioni"
    result = runner.invoke(
        cli.app,
        ["eval", "mutazioni", "--casi", str(root / "eval/casi/sintetici/mos"), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert "targa_non_attiva" in result.output
    assert (out / "mos" / "suite.yaml").is_file()
    assert f"eval pipeline --casi {out}" in result.output
