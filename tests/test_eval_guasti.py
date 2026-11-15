"""Guasti simulati: il modello che non risponde, risponde storto o finisce i passi, la conoscenza
che non si legge. La regola da verificare: un guasto dà WARNING, mai ERRATO."""

import asyncio
import json
from pathlib import Path

import pytest
from fakes import ScriptedSession
from test_eval_metrics import got, record, results, row, write
from test_eval_run import ROOT, SINTETICI, baseline, judge, run

from cycle_validation.agent.session import SessionRequest, SessionStatus
from cycle_validation.errors import ConfigError, SourceUnavailableError
from cycle_validation.evaluation.faults import Faults, FaultyKnowledge, FaultySession
from cycle_validation.evaluation.leaderboard import build_leaderboard, render_leaderboard
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.variant import load_variant
from cycle_validation.kb.local import load_local_knowledge


def request(session_id: str = "op-000-0010") -> SessionRequest:
    return SessionRequest(
        session_id=session_id, system_prompt="s", prompt="p", output_schema={"type": "object"}
    )


def test_a_failed_session_does_not_reach_the_model() -> None:
    inner = ScriptedSession(judge)
    session = FaultySession(inner, Faults(errore=1.0))
    outcome = asyncio.run(session.run(request()))
    assert outcome.status is SessionStatus.ERROR
    assert "simulato" in outcome.error
    assert inner.requests == []


@pytest.mark.parametrize(
    ("faults", "status"),
    [
        (Faults(risposta_storta=1.0), SessionStatus.OK),
        (Faults(budget=1.0), SessionStatus.MAX_TURNS),
    ],
)
def test_bent_answers_and_exhausted_budgets(faults: Faults, status: SessionStatus) -> None:
    outcome = asyncio.run(FaultySession(ScriptedSession(judge), faults).run(request()))
    assert outcome.status is status
    if status is SessionStatus.OK:
        assert outcome.output is not None and "judgement" not in outcome.output


def test_faults_are_the_same_at_every_run_with_the_same_seed() -> None:
    def statuses(seed: int) -> list[SessionStatus]:
        session = FaultySession(ScriptedSession(judge), Faults(errore=0.5, seme=seed))
        ids = [f"op-{n:03d}" for n in range(30)]
        return [asyncio.run(session.run(request(i))).status for i in ids]

    assert statuses(1) == statuses(1)
    assert statuses(1) != statuses(2)
    assert SessionStatus.ERROR in statuses(1) and SessionStatus.OK in statuses(1)


def test_the_cycle_extraction_is_never_broken() -> None:
    # Se l'estrazione fallisce il caso si ferma senza esito: i guasti servono a provare i controlli.
    inner = ScriptedSession(lambda _request, _attempt: {"operations": []})
    session = FaultySession(inner, Faults(errore=1.0))
    outcome = asyncio.run(session.run(request("extract")))
    assert outcome.status is SessionStatus.OK
    assert len(inner.requests) == 1


def test_each_repetition_rolls_its_own_dice() -> None:
    def statuses(repetition: int) -> list[SessionStatus]:
        session = FaultySession(
            ScriptedSession(judge), Faults(errore=0.5, seme=1), repetition=repetition
        )
        return [asyncio.run(session.run(request(f"op-{n:03d}"))).status for n in range(30)]

    assert statuses(1) == statuses(1)
    assert statuses(1) != statuses(2)


def test_unreachable_knowledge_raises_the_error_the_checks_expect() -> None:
    kb = load_local_knowledge(ROOT / "examples" / "sintetico" / "knowledge")
    faulty = FaultyKnowledge(kb, Faults(conoscenza=1.0))
    assert faulty.version == kb.version
    with pytest.raises(SourceUnavailableError, match="simulato"):
        faulty.find_manuals("MAN-DEMO-72")
    assert FaultyKnowledge(kb, Faults()).find_manuals("MAN-DEMO-72")


def test_a_variant_declares_its_faults(tmp_path: Path) -> None:
    (tmp_path / "baseline.yaml").write_text("nome: baseline\n", encoding="utf-8")
    (tmp_path / "guasti.yaml").write_text(
        "nome: guasti\nbase: baseline\nguasti:\n  errore: 0.3\n  seme: 7\n", encoding="utf-8"
    )
    variant = load_variant(tmp_path / "guasti.yaml", config_override=ROOT / "config/settings.yaml")
    assert variant.faults == Faults(errore=0.3, seme=7)
    (tmp_path / "sbagliata.yaml").write_text(
        "nome: sbagliata\nbase: baseline\nguasti:\n  errore: 2\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="guasti"):
        load_variant(tmp_path / "sbagliata.yaml", config_override=ROOT / "config/settings.yaml")


def test_under_faults_the_synthetic_cases_never_give_a_false_errato(tmp_path: Path) -> None:
    variant = baseline(tmp_path)
    faulty = Faults(errore=0.3, risposta_storta=0.2, budget=0.1, conoscenza=0.1, seme=3)
    variant = type(variant)(**{**variant.__dict__, "name": "guasti", "faults": faulty})
    path = run(tmp_path, variant, cases=SINTETICI, repetitions=2)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["guasti_simulati"]["errore"] == 0.3
    m = measure(data)
    assert m.technical > 0, "i guasti non sono arrivati ai controlli"
    assert m.false_errato == 0, m.mismatches


def test_robustness_runs_are_judged_apart_from_the_ranking(tmp_path: Path) -> None:
    expected_ok = [row("task_code", 0, "CORRETTO", "VERIFICATO")]
    warning = [got("task_code", 0, "WARNING", "ERRORE_TECNICO")]
    errato = [got("task_code", 0, "ERRATO", "CONTRADDIZIONE")]
    write(
        tmp_path,
        "1_baseline",
        results(
            "baseline",
            [record(1, [got("task_code", 0, "CORRETTO", "VERIFICATO")], attesi=expected_ok)],
        ),
    )
    faults = {"errore": 0.5}
    write(
        tmp_path,
        "2_regge",
        results("regge", [record(1, warning, attesi=expected_ok)], guasti_simulati=faults),
    )
    write(
        tmp_path,
        "3_cede",
        results("cede", [record(1, errato, attesi=expected_ok)], guasti_simulati=faults),
    )
    board = build_leaderboard(tmp_path)[0]
    assert [e.name for e in board.admitted] == ["baseline"]
    assert board.rejected == []
    assert [(e.name, bool(e.reasons)) for e in board.robustness] == [
        ("cede", True),
        ("regge", False),
    ]
    text = render_leaderboard([board])
    assert "Prove con guasti simulati" in text
    assert "`regge`: regge" in text
    assert "`cede`: NON regge" in text
