import pytest
from pydantic import ValidationError

from cycle_validation.domain.check import (
    REASON_VERDICT,
    CheckName,
    CheckResult,
    Evidence,
    Reason,
    Target,
    Usage,
    Verdict,
)
from cycle_validation.domain.cycle import Cycle, Operation, Source


def test_every_reason_maps_to_a_verdict() -> None:
    assert set(REASON_VERDICT) == set(Reason)
    assert REASON_VERDICT[Reason.VERIFICATO] is Verdict.CORRETTO
    assert REASON_VERDICT[Reason.MACCHINA_NON_ATTIVA] is Verdict.ERRATO
    assert REASON_VERDICT[Reason.FONTE_ASSENTE] is Verdict.WARNING
    assert REASON_VERDICT[Reason.ESCLUSO_DA_REGOLA] is Verdict.NON_APPLICABILE


def test_reason_must_belong_to_verdict() -> None:
    with pytest.raises(ValidationError, match="non appartiene"):
        CheckResult(
            check=CheckName.SOURCE,
            target=Target.cycle(),
            verdict=Verdict.ERRATO,
            reason=Reason.FONTE_ASSENTE,
            rationale="x",
        )


@pytest.mark.parametrize(
    ("verdict", "reason"),
    [(Verdict.CORRETTO, Reason.VERIFICATO), (Verdict.ERRATO, Reason.CONTRADDIZIONE)],
)
def test_agent_verdict_requires_evidence(verdict: Verdict, reason: Reason) -> None:
    with pytest.raises(ValidationError, match="citazione verificata"):
        CheckResult(
            check=CheckName.OPERATION_DESCRIPTION,
            target=Target.cycle(),
            verdict=verdict,
            reason=reason,
            rationale="x",
            decided_by="agent",
        )


def test_agent_verdict_with_evidence_is_accepted() -> None:
    result = CheckResult(
        check=CheckName.OPERATION_DESCRIPTION,
        target=Target.cycle(),
        verdict=Verdict.CORRETTO,
        reason=Reason.VERIFICATO,
        rationale="x",
        decided_by="agent",
        evidence=(Evidence(document_key="M1", line=3, quote="testo"),),
    )
    assert result.evidence[0].document_key == "M1"


def test_usage_adds_up() -> None:
    total = Usage(input_tokens=10, cost_usd=0.5, sessions=1) + Usage(input_tokens=5, turns=2)
    assert (total.input_tokens, total.cost_usd, total.turns, total.sessions) == (15, 0.5, 2, 1)


def test_cycle_fields_are_cleaned() -> None:
    cycle = Cycle.model_validate(
        {
            "cycle_code": "  C-1 ",
            "engine_model": "   ",
            "sources": [{"manual": " M1 ", "task": ""}],
            "operations": [
                {
                    "operation_number": " 0010 ",
                    "operation_description": " Pulire ",
                    "machine_tag": "",
                    "task_codes": "T-1, T-2;T-3",
                    "process_sheet": "SP-9",
                },
                {"operation_number": "0020", "task_codes": None, "process_sheet": ""},
            ],
        }
    )
    assert cycle.cycle_code == "C-1"
    assert cycle.engine_model is None
    assert cycle.sources[0] == Source(manual="M1")
    first, second = cycle.operations
    assert first.operation_number == "0010"
    assert first.machine_tag is None
    assert first.task_codes == ["T-1", "T-2", "T-3"]
    assert first.process_sheet is not None and first.process_sheet.code == "SP-9"
    assert second.task_codes == [] and second.process_sheet is None


def test_process_sheet_keeps_unknown_fields() -> None:
    operation = Operation.model_validate(
        {"operation_number": "1", "process_sheet": {"code": "SP-1", "edizione": "C"}}
    )
    assert operation.process_sheet is not None
    assert operation.process_sheet.model_dump() == {"code": "SP-1", "edizione": "C"}


def test_target_labels() -> None:
    source = Source(manual="M1", task="T-1")
    assert Target.source(0, source).label == "M1 / T-1"
    assert Target.operation(2, Operation(operation_number="0030")).label == "0030"


def test_usage_adds_up_session_and_model_times() -> None:
    total = Usage(wall_ms=300, api_duration_ms=100) + Usage(wall_ms=200, api_duration_ms=50)
    assert (total.wall_ms, total.api_duration_ms) == (500, 150)
