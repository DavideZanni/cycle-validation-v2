"""Misure e classifica, calcolate dai file grezzi dei risultati."""

import json
from pathlib import Path
from typing import Any

from test_eval_run import baseline, run

from cycle_validation.evaluation.leaderboard import build_leaderboard, render_leaderboard
from cycle_validation.evaluation.metrics import measure


def row(check: str, index: int, verdict: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "check": check,
        "kind": "operation",
        "index": index,
        "verdict": verdict,
        "reason": reason,
        **extra,
    }


def got(check: str, index: int, verdict: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"decided_by": "code", "prova": False, **row(check, index, verdict, reason), **extra}


def record(
    repetition: int,
    ottenuti: list[dict[str, Any]],
    *,
    caso: str = "c1",
    total: int = 1000,
    attesi: list[dict[str, Any]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    base = {
        "suite": "mos",
        "caso": caso,
        "ripetizione": repetition,
        "profilo": "mos",
        "attesi": attesi
        if attesi is not None
        else [
            row("task_code", 0, "ERRATO", "CONTRADDIZIONE"),
            row("operation_description", 0, "CORRETTO", "VERIFICATO"),
        ],
        "stato_atteso": None,
        "guasto": None,
        "ottenuti": ottenuti,
        "stato": "completo",
        "tempi_ms": {"ingest": 10, "extract": 20, "checks": total - 30, "total": total},
        "consumi": {
            "cost_usd": 0.01,
            "input_tokens": 100,
            "output_tokens": 10,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "sessions": 2,
            "wall_ms": 900,
            "api_duration_ms": 500,
        },
        "sessioni": {"inline": 2},
        "errori_pipeline": 0,
    }
    base.update(extra)
    return base


def results(name: str, records: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    reps = max(r["ripetizione"] for r in records)
    return {
        "formato": 1,
        "variante": name,
        "descrizione": "",
        "ambiente": "prova",
        "commit": "abc",
        "data": "2026-11-14T10:00:00",
        "ripetizioni": reps,
        "esecuzioni": records,
        **extra,
    }


GOOD = [
    got("task_code", 0, "ERRATO", "CONTRADDIZIONE"),
    got("operation_description", 0, "CORRETTO", "VERIFICATO", decided_by="agent", prova=True),
]


def test_perfect_runs_score_full_concordance_and_no_errors() -> None:
    m = measure(results("baseline", [record(1, GOOD), record(2, GOOD)]))
    assert m.concordance == 1.0
    assert (m.false_errato, m.missed_errors, m.technical) == (0, 0, 0)
    assert (m.unstable_rows, m.unstable_cases) == (0, 0)
    assert m.citations_verified == 1.0
    assert m.time_median_ms == 1000
    assert m.cost_per_cycle == 0.01
    assert m.tokens_per_cycle == 110
    assert m.agent_overhead_ms == 200  # (900 - 500) / 2 sessioni
    assert m.phase_median_ms == {"ingest": 10, "extract": 20, "checks": 970}


def test_false_errato_missed_errors_and_instability_are_counted_per_repetition() -> None:
    wrong = [
        got("task_code", 0, "WARNING", "FONTE_ASSENTE"),  # errore mancato
        got("operation_description", 0, "ERRATO", "CONTRADDIZIONE"),  # ERRATO falso
        got("machine_tag", 0, "ERRATO", "MACCHINA_NON_ATTIVA"),  # ERRATO non previsto
    ]
    m = measure(results("x", [record(1, GOOD), record(2, wrong)]))
    assert m.false_errato == 1.0  # 2 nella seconda ripetizione, 0 nella prima: media 1
    assert m.missed_errors == 0.5
    assert m.unstable_rows == 2
    assert m.unstable_cases == 1
    assert m.concordance == 0.5
    assert m.by_check["task_code"] == 0.5


def test_stability_is_not_measured_with_a_single_repetition() -> None:
    m = measure(results("x", [record(1, GOOD)]))
    assert m.unstable_rows is None


def test_technical_outcomes_and_crashes_are_counted() -> None:
    tech = [
        got("task_code", 0, "WARNING", "ERRORE_TECNICO"),
        got("operation_description", 0, "WARNING", "BUDGET_ESAURITO"),
    ]
    crashed = record(1, [], caso="c2", guasto="KnowledgeError: x", errori_pipeline=0)
    m = measure(results("x", [record(1, tech, errori_pipeline=1), crashed]))
    assert m.technical == 4  # 2 esiti + 1 errore di pipeline + 1 guasto
    assert m.failures == 1
    assert m.missed_errors == 2  # il task_code ERRATO non c'è in nessuno dei due casi


def test_worst_case_is_the_slowest_median() -> None:
    m = measure(
        results(
            "x",
            [
                record(1, GOOD, total=1000),
                record(1, GOOD, caso="c2", total=5000),
                record(2, GOOD, total=1200),
                record(2, GOOD, caso="c2", total=7000),
            ],
        )
    )
    assert m.time_max_ms == 7000
    assert m.worst_case == ("mos/c2", 6000)


def write(folder: Path, name: str, data: dict[str, Any]) -> None:
    folder.mkdir(exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def slower(records: list[dict[str, Any]], factor: float) -> list[dict[str, Any]]:
    return [
        {**r, "tempi_ms": {**r["tempi_ms"], "total": int(r["tempi_ms"]["total"] * factor)}}
        for r in records
    ]


def test_leaderboard_rules_out_variants_that_break_a_guardrail(tmp_path: Path) -> None:
    good = [record(1, GOOD), record(2, GOOD)]
    bad = [
        record(1, GOOD),
        record(2, [GOOD[0], got("operation_description", 0, "ERRATO", "CONTRADDIZIONE")]),
    ]
    write(tmp_path, "1_baseline", results("baseline", good))
    write(tmp_path, "2_veloce", results("veloce", slower(good, 0.5)))
    write(tmp_path, "3_lenta", results("lenta", slower(good, 2)))
    write(tmp_path, "4_rotta", results("rotta", slower(bad, 0.1)))
    write(tmp_path, "5_altrove", results("altrove", good, ambiente="bedrock-eu-west-1"))
    boards = build_leaderboard(tmp_path)
    assert [b.environment for b in boards] == ["bedrock-eu-west-1", "prova"]
    board = boards[1]
    assert [e.name for e in board.admitted] == ["veloce", "baseline", "lenta"]
    assert [e.name for e in board.rejected] == ["rotta"]
    assert any("ERRATO falsi" in reason for reason in board.rejected[0].reasons)
    assert any("concordanza" in reason for reason in board.rejected[0].reasons)
    text = render_leaderboard(boards)
    assert "## Ambiente: prova" in text
    assert "veloce" in text and "-50%" in text
    assert "nessuna prova della variante baseline" in text  # ambiente bedrock


def test_only_the_latest_run_of_a_variant_counts(tmp_path: Path) -> None:
    good = [record(1, GOOD)]
    write(tmp_path, "1_baseline", results("baseline", good))
    write(tmp_path, "2_veloce", results("veloce", slower(good, 3), data="2026-11-14T10:00:00"))
    write(tmp_path, "3_veloce", results("veloce", slower(good, 0.5), data="2026-11-14T11:00:00"))
    board = build_leaderboard(tmp_path)[0]
    assert [e.name for e in board.admitted] == ["veloce", "baseline"]


def test_runs_on_different_cases_are_not_compared(tmp_path: Path) -> None:
    write(tmp_path, "1_baseline", results("baseline", [record(1, GOOD)]))
    write(tmp_path, "2_altri", results("altri", [record(1, GOOD, caso="zz")]))
    board = build_leaderboard(tmp_path)[0]
    assert [e.name for e in board.rejected] == ["altri"]
    assert "casi diversi" in board.rejected[0].reasons[0]


def test_the_synthetic_cases_are_concordant_with_the_fake_model(tmp_path: Path) -> None:
    path = run(tmp_path, baseline(tmp_path), repetitions=2)
    m = measure(json.loads(path.read_text(encoding="utf-8")))
    assert m.concordance == 1.0, m.mismatches
    assert (m.false_errato, m.missed_errors, m.technical, m.unstable_rows) == (0, 0, 0, 0)
