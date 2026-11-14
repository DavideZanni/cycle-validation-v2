"""Esecuzione di una variante sui casi: un file di risultati grezzi per prova."""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from ej200_fixtures import judge as ej200_judge
from fakes import ScriptedSession
from support import scripted_judge

from cycle_validation.agent.session import AgentSession, SessionRequest
from cycle_validation.config import AgentSettings
from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.run import load_suites, run_variant
from cycle_validation.evaluation.variant import Variant, load_variant

ROOT = Path(__file__).parents[1]
SINTETICI = ROOT / "eval" / "casi" / "sintetici"


def judge(request: SessionRequest, attempt: int) -> dict[str, Any]:
    if "EJ200" in request.prompt:
        return ej200_judge(request, attempt)
    return scripted_judge(request, attempt)


def factory(script: Any = judge) -> Any:
    def make(settings: AgentSettings, transcripts: Path | None) -> AgentSession:
        return ScriptedSession(script)

    return make


def baseline(tmp_path: Path, **agent: Any) -> Variant:
    config = tmp_path / "settings.yaml"
    lines = ["agent:", "  retry_backoff_s: 0"] + [f"  {k}: {v}" for k, v in agent.items()]
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return load_variant(ROOT / "eval" / "varianti" / "baseline.yaml", config_override=config)


def run(tmp_path: Path, variant: Variant, cases: Path = SINTETICI, **kwargs: Any) -> Path:
    return asyncio.run(
        run_variant(
            variant,
            load_suites(cases),
            repetitions=kwargs.pop("repetitions", 1),
            results_dir=tmp_path / "risultati",
            session_factory=kwargs.pop("session_factory", factory()),
            project_root=ROOT,
            runs_dir=tmp_path / "runs",
            **kwargs,
        )
    )


def test_suites_are_loaded_with_their_cases() -> None:
    suites = load_suites(SINTETICI)
    assert [(s.name, len(s.cases)) for s in suites] == [("dr", 5), ("ej200", 7), ("mos", 5)]
    assert [s.name for s in load_suites(SINTETICI / "mos")] == ["mos"]
    with pytest.raises(ConfigError):
        load_suites(ROOT / "tests")


def test_a_run_writes_one_raw_record_per_case_and_repetition(tmp_path: Path) -> None:
    lines: list[str] = []
    path = run(
        tmp_path, baseline(tmp_path), repetitions=2, environment="prova", progress=lines.append
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == tmp_path / "risultati"
    assert path.name.endswith("_baseline.json")
    assert (data["variante"], data["ambiente"], data["ripetizioni"]) == ("baseline", "prova", 2)
    assert data["impostazioni"]["agent"]["retry_backoff_s"] == 0
    assert data["commit"]
    runs = data["esecuzioni"]
    assert len(runs) == 2 * 17
    assert len(lines) == 2 * 17
    first = runs[0]
    assert (first["suite"], first["caso"], first["ripetizione"]) == (
        "dr",
        "accept_as_is_per_intersezione",
        1,
    )
    assert first["guasto"] is None
    assert {"check", "kind", "index", "verdict", "reason"} <= set(first["attesi"][0])
    assert {"check", "kind", "index", "verdict", "reason", "decided_by", "prova"} <= set(
        first["ottenuti"][0]
    )
    assert "total" in first["tempi_ms"]
    assert "cost_usd" in first["consumi"]


def test_the_environment_is_deduced_from_the_settings(tmp_path: Path) -> None:
    local = run(tmp_path, baseline(tmp_path, use_bedrock="false"), cases=SINTETICI / "dr")
    assert json.loads(local.read_text(encoding="utf-8"))["ambiente"] == "login-locale"
    bedrock = run(tmp_path, baseline(tmp_path, aws_region="eu-west-1"), cases=SINTETICI / "dr")
    assert json.loads(bedrock.read_text(encoding="utf-8"))["ambiente"] == "bedrock-eu-west-1"
    assert local != bedrock


def test_a_case_that_raises_is_recorded_and_does_not_stop_the_run(tmp_path: Path) -> None:
    suite = tmp_path / "casi" / "rotta"
    (suite / "uno").mkdir(parents=True)
    (suite / "suite.yaml").write_text(
        f"conoscenza: {(ROOT / 'examples' / 'sintetico' / 'knowledge').as_posix()}\n",
        encoding="utf-8",
    )
    (suite / "uno" / "ciclo.json").write_text("{non è json", encoding="utf-8")
    (suite / "uno" / "expected.json").write_text('{"profile": "mos", "rows": []}', encoding="utf-8")
    path = run(tmp_path, baseline(tmp_path), cases=suite)
    record = json.loads(path.read_text(encoding="utf-8"))["esecuzioni"][0]
    assert record["guasto"]
    assert record["ottenuti"] == []


def test_a_failing_model_gives_technical_outcomes_not_a_crash(tmp_path: Path) -> None:
    def broken(request: SessionRequest, attempt: int) -> Exception:
        return RuntimeError("Bedrock non risponde")

    variant = baseline(tmp_path, retries=0)
    path = run(tmp_path, variant, cases=SINTETICI / "mos", session_factory=factory(broken))
    runs = json.loads(path.read_text(encoding="utf-8"))["esecuzioni"]
    reasons = {row["reason"] for record in runs for row in record["ottenuti"]}
    assert "ERRORE_TECNICO" in reasons
    assert all(record["guasto"] is None for record in runs)
