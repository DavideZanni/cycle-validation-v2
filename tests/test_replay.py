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
    base = Settings(agent=AgentSettings(final_rules=[]))
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


def _ops(*descriptions: str) -> Cycle:
    from cycle_validation.domain.cycle import Operation

    return Cycle(
        operations=[
            Operation(operation_number=f"{(n + 1) * 10:03d}", operation_description=text)
            for n, text in enumerate(descriptions)
        ]
    )


def test_a_missing_source_is_said_once_per_cycle() -> None:
    """MG83: il manuale fuori dalla conoscenza dava un WARNING per operazione, più quelli dei
    task code sulle stesse operazioni. Ne resta uno, con l'elenco delle operazioni."""
    cycle = _ops("A", "B", "C", "D")
    target = [Target.operation(n, op) for n, op in enumerate(cycle.operations)]
    absent = "Nessun riferimento dell'operazione è disponibile nella knowledge base."
    description = CheckName.OPERATION_DESCRIPTION
    results = [
        make_result(CheckName.TASK_CODE, target[0], Reason.FONTE_ASSENTE, "Task X non trovato."),
        make_result(description, target[0], Reason.FONTE_ASSENTE, absent),
        make_result(description, target[1], Reason.FONTE_ASSENTE, absent),
        make_result(description, target[2], Reason.FONTE_ASSENTE, absent),
        make_result(description, target[3], Reason.EVIDENZA_NON_TROVATA, "non trovato"),
        make_result(CheckName.PROCESS_SHEET, target[3], Reason.FONTE_ASSENTE, "Scheda Y."),
    ]
    out = final_rules.once_missing_source(cycle, results)
    assert [r.reason for r in out] == [
        Reason.FONTE_ASSENTE,
        Reason.GIA_SEGNALATO,
        Reason.GIA_SEGNALATO,
        Reason.GIA_SEGNALATO,
        Reason.EVIDENZA_NON_TROVATA,
        Reason.FONTE_ASSENTE,  # un'altra fonte, su un'operazione senza altri avvisi
    ]
    assert out[0].rationale == (
        f"Task X non trovato. Stesso avviso anche per le operazioni 020, 030. "
        f"Sulle stesse operazioni: {absent}"
    )
    assert "dell'operazione 010 (task_code)" in out[2].rationale
    assert out[1].verdict is Verdict.NON_APPLICABILE
    assert final_rules.once_missing_source(cycle, results[4:]) == results[4:]


def test_a_correct_against_its_own_quote_on_a_limit_becomes_wrong() -> None:
    """MG87: il modello dice CORRETTO, ma la riga che cita dà lo stesso valore con il limite al
    contrario (copia cieca «limite invertito» in tutte e due le lingue)."""
    from cycle_validation.domain.check import Evidence

    cycle = _ops(
        "PROFONDITA' ALMENO 0,5 MM / DEPTH AT LEAST 0.5 MM",
        "PROFONDITA' AL MASSIMO 0,5 MM / DEPTH NOT TO EXCEED 0.5 MM",
        "PULIRE / CLEAN",
    )
    target = [Target.operation(n, op) for n, op in enumerate(cycle.operations)]
    quote = Evidence(document_key="m1", quote="Blend to a depth of 0.5 mm maximum.")
    description = CheckName.OPERATION_DESCRIPTION

    def ok(n: int) -> CheckResult:
        return make_result(
            description,
            target[n],
            Reason.VERIFICATO,
            "uguale",
            evidence=[quote],
            decided_by="agent",
        )

    out = final_rules.limit_against_quote(cycle, [ok(0), ok(1), ok(2)])
    assert [r.reason for r in out] == [
        Reason.LIMITE_CONTRO_CITAZIONE,
        Reason.VERIFICATO,
        Reason.VERIFICATO,
    ]
    assert out[0].verdict is Verdict.ERRATO and out[0].evidence == (quote,)
    assert "almeno 0.5" in out[0].rationale and "al massimo 0.5" in out[0].rationale


def test_limits_written_after_the_number() -> None:
    from decimal import Decimal

    from cycle_validation.checks.languages import limit_ways

    quote = "Blend 0.010 in. (0.25 mm) max. Hold for 5 min. Depth 2 MM MINIMUM."
    assert limit_ways(quote, "en", after=True) == {
        Decimal("0.25"): {"giù"},
        Decimal("2"): {"su"},
    }
    assert limit_ways(quote, "en") == {}  # senza `after` come prima (MG75)


def test_the_quote_diagnosis_says_only_yes_and_no() -> None:
    """MG87: perché la regola non scatta, senza mostrare il testo della riga citata."""
    from cycle_validation.domain.check import Evidence

    cycle = _ops("PROFONDITA' ALMENO 0,5 MM / DEPTH AT LEAST 0.5 MM", "PULIRE / CLEAN")
    target = [Target.operation(n, op) for n, op in enumerate(cycle.operations)]

    def ok(n: int, quote: str) -> CheckResult:
        evidence = [Evidence(document_key="m1", quote=quote)]
        return make_result(
            CheckName.OPERATION_DESCRIPTION,
            target[n],
            Reason.VERIFICATO,
            "uguale",
            evidence=evidence,
            decided_by="agent",
        )

    seen = final_rules.quote_diagnosis(cycle, [ok(0, "Depth 0.5 mm maximum.")], "010")
    assert seen == (
        "citazioni 1 · limite letto nella descrizione sì · stesso numero nella riga citata sì "
        "· parole di limite nella riga sì · verso letto vicino al numero giù"
    )
    other = final_rules.quote_diagnosis(cycle, [ok(0, "Blend the damage.")], "010")
    assert "stesso numero nella riga citata no" in other and "Blend" not in other
    assert final_rules.quote_diagnosis(cycle, [ok(1, "x")], "010") == (
        "nessun CORRETTO della descrizione"
    )
