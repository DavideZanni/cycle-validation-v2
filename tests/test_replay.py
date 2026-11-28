"""Regole finali e prove rigiocate (`eval rigioca`, 28-11): dati inventati, niente modello."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_trials import KNOWN, _report

from cycle_validation.checks.base import make_result
from cycle_validation.config import AgentSettings, Settings
from cycle_validation.domain.check import CheckName, CheckResult, Reason, Target, Verdict
from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import ConfigError
from cycle_validation.evaluation import replay
from cycle_validation.evaluation.trials import (
    build_trial,
    build_variants,
    load_known_errors,
    load_trials,
    score_cycle,
    write_trial,
)
from cycle_validation.report.builder import write_outputs
from cycle_validation.verdict import final_rules


def _ok_on(op: str):  # type: ignore[no-untyped-def]
    """Regola finta: il WARNING della descrizione su `op` diventa CORRETTO."""

    def rule(cycle: Cycle, results: list[CheckResult]) -> list[CheckResult]:
        return [
            make_result(r.check, r.target, Reason.VERIFICATO, "regola finta")
            if r.verdict is Verdict.WARNING and r.target.label.startswith(op)
            else r
            for r in results
        ]

    return rule


@pytest.fixture
def rules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(final_rules.RULES, "ok_010", _ok_on("010"))
    monkeypatch.setitem(final_rules.RULES, "ok_tutto", _ok_on(""))


def test_a_final_rule_changes_the_results_but_not_the_integrity_rows(rules: None) -> None:
    report = _report("bbbb2222", [])
    integrity = make_result(
        CheckName.EXTRACTION_INTEGRITY, Target.cycle(), Reason.EVIDENZA_NON_TROVATA, "x"
    )
    results = [integrity, *report.results]
    out = final_rules.apply_final_rules(report.cycle, results, ["ok_tutto"])
    assert out[0] == integrity
    assert [r.verdict for r in out[1:]] == [Verdict.CORRETTO] * 3
    assert final_rules.apply_final_rules(report.cycle, results, []) == results
    replayed = final_rules.replay_report(report, ["ok_010"])
    assert (replayed.counts.corretto, replayed.counts.warning) == (1, 2)
    with pytest.raises(ConfigError):
        final_rules.apply_final_rules(report.cycle, results, ["nessuna"])
    with pytest.raises(ValidationError):
        AgentSettings(final_rules=["nessuna"])


def test_only_a_variant_of_final_rules_can_be_replayed(rules: None) -> None:
    base = Settings()
    rule = Settings(agent=AgentSettings(final_rules=["ok_010"]))
    code = Settings(agent=AgentSettings(final_rules=["ok_010"], task_stage_check=True))
    assert replay.other_changes(base, rule) == []
    assert replay.other_changes(base, code) == ["agent.task_stage_check"]
    assert replay.extra_rules(base, rule) == ["ok_010"]
    both = Settings(agent=AgentSettings(final_rules=["ok_010", "ok_tutto"]))
    assert replay.extra_rules(rule, both) == ["ok_tutto"]
    with pytest.raises(ValueError):
        replay.extra_rules(both, rule)


def _reference_trials(tmp_path: Path) -> Path:
    """Due prove di `quasi_finale`: la 005 trovata, la 030 (errore noto) e tutto il ciclo
    giusto con WARNING. Più una prova di un'altra variante, che non si rigioca."""
    known = load_known_errors(_known_file(tmp_path))
    root = tmp_path / "prove-piccolo"
    for hour, name in ((9, "quasi_finale"), (10, "quasi_finale"), (11, "altra")):
        folder = root / f"2030-{hour}-{name}"
        reports = [_report("aaaa1111", ["005"]), _report("bbbb2222", [])]
        for report in reports:
            write_outputs(report, folder / report.meta.pdf_sha256[:8])
        scores = [score_cycle(r, known) for r in reports]
        write_trial(
            build_trial(name, datetime(2030, 1, 1, hour, tzinfo=UTC), reports, scores), folder
        )
    return root


def _known_file(tmp_path: Path) -> Path:
    path = tmp_path / "errori.yaml"
    path.write_text(KNOWN, "utf-8")
    return path


def test_a_safe_rule_is_kept_and_a_rule_that_hides_an_error_is_not(
    tmp_path: Path, rules: None
) -> None:
    root = _reference_trials(tmp_path)
    known = load_known_errors(_known_file(tmp_path))
    pairs = replay.replay_trials(root, "quasi_finale", "meno_avvisi", ["ok_010"], known)
    assert len(pairs) == 2
    before, after = pairs[0]
    assert before.name == "quasi_finale" and after.name == "meno_avvisi"
    assert (before.clean_warnings, after.clean_warnings) == (3.0, 2.0)
    variants = {v.name: v for v in build_variants([t for p in pairs for t in p], "quasi_finale")}
    assert variants["meno_avvisi"].decision == "si tiene: stessi errori, WARNING per ciclo -1.0"
    # la regola che dice OK anche sulla 030 (errore noto mancato) dà un falso OK
    pairs = replay.replay_trials(root, "quasi_finale", "troppo", ["ok_tutto"], known)
    variants = {v.name: v for v in build_variants([t for p in pairs for t in p], "quasi_finale")}
    assert variants["troppo"].false_ok == 1.0
    assert variants["troppo"].decision.startswith("non si tiene: falsi OK 1.0")
    # le prove rigiocate in una cartella loro, con il riepilogo contro il riferimento
    summary = replay.write_replay(tmp_path / "rigioca-piccolo", "quasi_finale", pairs)
    assert "troppo" in summary.read_text("utf-8")
    assert len(load_trials(tmp_path / "rigioca-piccolo")) == 4
    assert len(load_trials(root)) == 3  # le prove della campagna non si toccano
