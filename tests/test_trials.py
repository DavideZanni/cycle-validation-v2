"""Prove sui cicli veri: punteggio, report della prova, riepilogo (dati inventati)."""

from datetime import UTC, datetime
from pathlib import Path

from cycle_validation.checks.base import make_result
from cycle_validation.domain.check import CheckName, Reason, Target, Usage
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.domain.report import Report, RunMeta
from cycle_validation.evaluation.trials import (
    build_trial,
    failed_cycle,
    load_known_errors,
    load_trials,
    render_summary,
    render_trial,
    score_cycle,
    write_summary,
    write_trial,
)
from cycle_validation.report.builder import build_report

KNOWN = """
cicli:
  aaaa1111:
    errori:
      5: numero cambiato
      "030": frase cambiata
  bbbb2222:
    giusto: true
    di: aaaa1111
"""


def _cycle() -> Cycle:
    return Cycle(
        operations=[
            Operation(operation_number=number, operation_description="TESTO")
            for number in ("005", "010", "030")
        ]
    )


def _report(fingerprint: str, errato: list[str]) -> Report:
    cycle = _cycle()
    results = []
    for index, operation in enumerate(cycle.operations):
        wrong = operation.operation_number in errato
        results.append(
            make_result(
                CheckName.OPERATION_DESCRIPTION,
                Target.operation(index, operation),
                Reason.INCOERENZA_LINGUE if wrong else Reason.EVIDENZA_NON_TROVATA,
                "numeri diversi" if wrong else "non trovato",
                usage=Usage(cost_usd=0.01, input_tokens=100, output_tokens=10),
            )
        )
    meta = RunMeta(
        run_id="r",
        started_at=datetime(2030, 1, 1, tzinfo=UTC),
        pdf_name="x.pdf",
        pdf_sha256=fingerprint + "0" * 56,
        profile="mos",
        knowledge_version="kb",
        model="modello",
        prompt_version="p1",
        tool_version="0.1",
    )
    return build_report(
        meta, cycle, results, timings_ms={"total": 2000}, pipeline_errors=[], blocked=False
    )


def _known(tmp_path: Path):  # type: ignore[no-untyped-def]
    path = tmp_path / "errori.yaml"
    path.write_text(KNOWN, "utf-8")
    return load_known_errors(path)


def test_a_cycle_is_scored_against_the_known_errors(tmp_path: Path) -> None:
    known = _known(tmp_path)
    score = score_cycle(_report("aaaa1111", ["005", "010"]), known)
    assert score.kind == "errori"
    assert [f.op for f in score.found] == ["005"]
    assert score.found[0].known == "numero cambiato"
    assert [m.op for m in score.missed] == ["030"]
    assert "EVIDENZA_NON_TROVATA" in score.missed[0].said
    assert [f.op for f in score.extra] == ["010"]
    clean = score_cycle(_report("bbbb2222", ["030"]), known)
    assert clean.kind == "giusto" and [f.op for f in clean.extra] == ["030"]


def test_trial_report_and_summary(tmp_path: Path) -> None:
    known = _known(tmp_path)
    root = tmp_path / "prove"
    for name, hour, errato in (("base", 9, []), ("lingue", 10, ["005"])):
        reports = [_report("aaaa1111", errato), _report("bbbb2222", [])]
        scores = [score_cycle(r, known) for r in reports]
        scores.append(failed_cycle("cccc3333", known, "PDF illeggibile"))
        trial = build_trial(name, datetime(2030, 1, 1, hour), reports, scores)
        write_trial(trial, root / f"2030-{name}")
    trials = load_trials(root)
    assert [t.name for t in trials] == ["base", "lingue"]
    last = trials[-1]
    assert (last.known_found, last.known_total, last.false_errors, last.failures) == (1, 2, 0, 1)
    text = render_trial(last)
    assert "**1 su 2** (50%)" in text
    assert "`INCOERENZA_LINGUE` 1" in text
    assert "| aaaa1111 | 030 | frase cambiata | no |" in text
    summary = render_summary(trials)
    assert "+1 trovati, +0 falsi" in summary
    assert "| aaaa1111 | 005 | numero cambiato | · | ✓ | 1 su 2 |" in summary
    assert "Nessuno." in summary
    assert write_summary(root).read_text("utf-8") == summary


def _trial(tmp_path: Path, name: str, hour: int, errato: list[str], clean: list[str] | None = None):  # type: ignore[no-untyped-def]
    known = _known(tmp_path)
    reports = [_report("aaaa1111", errato), _report("bbbb2222", clean or [])]
    scores = [score_cycle(r, known) for r in reports]
    return build_trial(name, datetime(2030, 1, 1, hour), reports, scores)


def test_the_rule_picks_the_best_variant(tmp_path: Path) -> None:
    from cycle_validation.evaluation.trials import best_variant, build_variants

    trials = [
        _trial(tmp_path, "base", 1, []),
        _trial(tmp_path, "base", 2, []),
        _trial(tmp_path, "lingue", 3, ["005"]),
        _trial(tmp_path, "lingue", 4, ["005", "030"]),
        _trial(tmp_path, "rumorosa", 5, ["005", "030"], clean=["010"]),
        _trial(tmp_path, "rumorosa", 6, ["005", "030"]),
        _trial(tmp_path, "una-volta", 7, ["005", "030"]),
    ]
    variants = {v.name: v for v in build_variants(trials)}
    assert variants["base"].decision == "riferimento"
    lingue = variants["lingue"]
    # stabile solo lo 005: lo 030 è trovato in una prova su due
    assert (lingue.stable, lingue.found_min, lingue.found_mean) == (1, 1, 1.5)
    assert lingue.decision == "si tiene: meglio della base"
    assert variants["rumorosa"].decision == "scartata: 1 falsi errori nei cicli giusti"
    assert variants["una-volta"].decision.startswith("da ripetere")
    best = best_variant(build_variants(trials))
    assert best is not None and best.name == "lingue"
    summary = render_summary(trials)
    assert "## Scelta migliore" in summary and "**«lingue»**" in summary


def test_a_variant_that_loses_a_stable_error_is_not_kept(tmp_path: Path) -> None:
    from cycle_validation.evaluation.trials import build_variants

    trials = [
        _trial(tmp_path, "base", 1, ["005"]),
        _trial(tmp_path, "base", 2, ["005"]),
        _trial(tmp_path, "altra", 3, ["030"]),
        _trial(tmp_path, "altra", 4, ["030"]),
    ]
    variants = {v.name: v for v in build_variants(trials)}
    # stessi numeri (1 stabile), ma non è meglio: si resta sulla base
    assert variants["altra"].decision == "non si tiene: non è meglio della base"


def test_a_real_cycle_has_no_known_errors_and_counts_apart(tmp_path: Path) -> None:
    known = _known(tmp_path)
    reports = [_report("aaaa1111", ["005"]), _report("dddd4444", ["010"])]
    scores = [score_cycle(r, known) for r in reports]
    assert scores[1].kind == "vero" and [f.op for f in scores[1].extra] == ["010"]
    trial = build_trial("base", datetime(2030, 1, 1, 9), reports, scores)
    assert (trial.false_errors, trial.extra_errors, trial.real_errors) == (0, 1, 1)
    assert trial.real_cycles == 1
    assert "nei 1 cicli veri: 1) | 1 |" in render_trial(trial)


def test_the_summary_warns_when_trials_use_different_cycles(tmp_path: Path) -> None:
    known = _known(tmp_path)
    small = _trial(tmp_path, "base", 9, ["005"])
    reports = [_report("aaaa1111", ["005"]), _report("dddd4444", [])]
    big = build_trial(
        "base", datetime(2030, 1, 1, 10), reports, [score_cycle(r, known) for r in reports]
    )
    assert small.cycle_set != big.cycle_set
    assert "non sono tutte sugli stessi cicli" in render_summary([small, big])
    assert "non sono tutte sugli stessi cicli" not in render_summary([small, small])
