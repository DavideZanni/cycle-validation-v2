"""Payload nel formato che il frontend riceve oggi: feedback a prefisso, stessi nomi di campo."""

from typing import Any

from cycle_validation.domain.check import CheckName, CheckResult, TargetKind, Verdict
from cycle_validation.domain.report import Report


def feedback_text(result: CheckResult | None) -> str:
    """Traduce un esito tipizzato nelle stringhe a prefisso del sistema attuale."""
    if result is None:
        return "N/A"
    match result.verdict:
        case Verdict.CORRETTO:
            return "No errors found."
        case Verdict.ERRATO:
            return f"Error found: {result.rationale}"
        case Verdict.WARNING:
            return f"Warning: {result.rationale}"
        case Verdict.NON_APPLICABILE:
            return f"N/A - {result.rationale}"


def _index(report: Report) -> dict[tuple[CheckName, TargetKind, int | None], CheckResult]:
    return {(item.check, item.target.kind, item.target.index): item for item in report.results}


def build_legacy_payload(report: Report) -> dict[str, Any]:
    found = _index(report)
    cycle = report.cycle

    def feedback(check: CheckName, kind: TargetKind, index: int | None) -> str:
        return feedback_text(found.get((check, kind, index)))

    sources = [
        {
            "repairCode": source.repair_code,
            "manual": source.manual,
            "task": source.task,
            "sourceFeedback": feedback(CheckName.SOURCE, TargetKind.SOURCE, index),
        }
        for index, source in enumerate(cycle.sources)
    ]
    operations: list[dict[str, Any]] = []
    for index, operation in enumerate(cycle.operations):
        kind = TargetKind.OPERATION
        operations.append(
            {
                "operationNumber": operation.operation_number,
                "repairCode": operation.repair_code,
                "operationDescription": operation.operation_description,
                "targaCResp": operation.machine_tag,
                "taskCodeCited": ", ".join(operation.task_codes) or None,
                "scheda": (
                    operation.process_sheet.model_dump(exclude_none=True)
                    if operation.process_sheet is not None
                    else None
                ),
                "operationFeedback": feedback(CheckName.OPERATION_DESCRIPTION, kind, index),
                "targaCRespFeedback": feedback(CheckName.MACHINE_TAG, kind, index),
                "taskCodeFeedback": feedback(CheckName.TASK_CODE, kind, index),
                "schedaFeedback": feedback(CheckName.PROCESS_SHEET, kind, index),
            }
        )
    payload: dict[str, Any] = {
        "cycleCode": cycle.cycle_code,
        "cycleDescription": cycle.cycle_description,
        "engineModel": cycle.engine_model,
        "operationType": cycle.operation_type,
        "repairCode": cycle.repair_code,
        "sources": sources,
        "operations": operations,
        "cycle_errors_count": report.counts.errato,
        "cycle_errors_count_perc": report.counts.errors_ratio,
        "profile": dict(report.timings_ms),
        "cycle_status": report.status.value,
        "_pipeline_errors": [item.model_dump() for item in report.pipeline_errors],
    }
    dr = found.get((CheckName.DR_RECOMMENDATION, TargetKind.CYCLE, None))
    if dr is not None:
        payload["drRecommendationFeedback"] = feedback_text(dr)
    return payload
