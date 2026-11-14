import asyncio
from pathlib import Path

import pytest
from kb_fixtures import BrokenKnowledge
from support import example_cycle, make_deps

from cycle_validation.domain.check import CheckName, Reason, Verdict
from cycle_validation.golden import load_cases, run_golden
from cycle_validation.pipeline import RunRequest, run_validation
from cycle_validation.resolve.dr import DrSelectors, SelectorError
from cycle_validation.testing.pdf import synthetic_cycle_pdf

GOLDEN = Path(__file__).parents[1] / "eval" / "casi" / "sintetici" / "dr"


def dr_cycle():  # type: ignore[no-untyped-def]
    cycle = example_cycle()
    operation = cycle.operations[1].model_copy(update={"task_codes": [], "process_sheet": None})
    return cycle.model_copy(update={"sources": [], "operations": [operation]})


def dr_deps(tmp_path: Path, **overrides):  # type: ignore[no-untyped-def]
    path = tmp_path / "dr.json"
    path.write_text(dr_cycle().model_dump_json(), encoding="utf-8")
    deps, session = make_deps("dr", cycle_path=path)
    return type(deps)(**{**deps.__dict__, **overrides}), session


def run_dr(serial: str, conditions: tuple[int, ...], deps):  # type: ignore[no-untyped-def]
    cycle = dr_cycle()
    request = RunRequest(
        pdf_bytes=synthetic_cycle_pdf(cycle), selectors=DrSelectors(serial, conditions)
    )
    return run_validation(request, deps)


def test_dr_golden_set_covers_every_branch_and_is_concordant() -> None:
    cases = load_cases(GOLDEN)
    assert len(cases) == 5

    def deps_for(case):  # type: ignore[no-untyped-def]
        return make_deps("dr", cycle_path=case.cycle_path)[0]

    summary = asyncio.run(run_golden(cases, deps_for))
    assert summary.concordance == 1.0, summary.render()


def test_dr_selectors_are_attached_to_the_cycle_record(tmp_path: Path) -> None:
    report = run_dr("SN-DEMO-001", (1,), dr_deps(tmp_path)[0])
    assert report.cycle.dr_record == {"serial_number": "SN-DEMO-001", "conditions": [1]}


def test_dr_recommendation_tasks_feed_the_operation_context(tmp_path: Path) -> None:
    deps, session = dr_deps(tmp_path)
    report = run_dr("SN-DEMO-001", (1,), deps)
    (request,) = session.requests
    assert "72-00-01-350-003" in request.prompt  # task della recommendation DR-DEMO-01
    assert report.status.value == "completo"


def test_blocked_dr_runs_no_session(tmp_path: Path) -> None:
    deps, session = dr_deps(tmp_path)
    report = run_dr("SN-DEMO-002", (1, 2), deps)
    assert session.requests == []
    assert report.status.value == "bloccato"
    reasons = {
        r.check: r.reason for r in report.results if r.check is not CheckName.EXTRACTION_INTEGRITY
    }
    assert reasons[CheckName.DR_RECOMMENDATION] is Reason.DR_NON_APPLICABILE
    assert reasons[CheckName.OPERATION_DESCRIPTION] is Reason.BLOCCATO_A_MONTE
    assert report.counts.errato == 1


def test_dr_data_not_loadable_blocks_with_a_warning_not_an_error(tmp_path: Path) -> None:
    deps, session = dr_deps(tmp_path, kb=BrokenKnowledge())
    report = run_dr("SN-DEMO-001", (1,), deps)
    dr = next(r for r in report.results if r.check is CheckName.DR_RECOMMENDATION)
    assert (dr.verdict, dr.reason) == (Verdict.WARNING, Reason.ERRORE_TECNICO)
    assert report.status.value == "bloccato"
    assert session.requests == []
    assert report.counts.errato == 0


def test_dr_profile_requires_selectors() -> None:
    with pytest.raises(SelectorError):
        run_validation(RunRequest(pdf_bytes=synthetic_cycle_pdf(dr_cycle())), make_deps("dr")[0])


def test_payload_exposes_the_dr_feedback(tmp_path: Path) -> None:
    from cycle_validation.report.legacy_payload import build_legacy_payload

    payload = build_legacy_payload(run_dr("SN-DEMO-002", (1, 2), dr_deps(tmp_path)[0]))
    assert payload["drRecommendationFeedback"].startswith("Error found:")
    assert payload["cycle_status"] == "bloccato"
