"""Payload nel formato che il frontend riceve oggi: feedback a prefisso, stessi nomi di campo.

Come il frontend legge i testi (risposta di Copilot sul codice del frontend, 22-11-2026):

- bollino: `N/A` grigio se il testo è vuoto o è esattamente `N/A`; `Error`, `Warning`, `OK` se
  comincia con `error`, `warning`, `no error`; `Info` azzurro per ogni altro testo;
- «Completed with Errors» se `cycle_errors_count > 0` o `_pipeline_errors` non è vuoto;
- non legge `drRecommendationFeedback` né `cycle_status`: l'esito DR va in una riga di
  `sources` (colonna *Type* «DR Case» quando la riga ha `DRCase`);
- della scheda mostra `tabNumber`, `task`, `class` (come li riempie la v1: `_scheda`).
"""

from typing import Any

from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Reason,
    TargetKind,
    Verdict,
    WarningKind,
    warning_kind,
)
from cycle_validation.domain.cycle import Source
from cycle_validation.domain.report import Report
from cycle_validation.text import normalize_code

# Esiti che la v1 mostra come `N/A` grigio senza testo: il campo non c'è, oppure il controllo
# non è partito perché il DR ha fermato il ciclo (il motivo sta nella riga DR delle fonti).
# Gli altri N/A tengono il motivo e il frontend li mostra come `Info`, come fa la v1 con
# «N/A, non verificato per EJ200».
_PLAIN_NA = (Reason.CAMPO_ASSENTE, Reason.BLOCCATO_A_MONTE)

# Dal più grave al meno grave, per scegliere quale testo mostrare per primo in una cella.
_SEVERITY = {Verdict.ERRATO: 0, Verdict.WARNING: 1, Verdict.CORRETTO: 2, Verdict.NON_APPLICABILE: 3}


def feedback_text(result: CheckResult | None) -> str:
    """Traduce un esito tipizzato nelle stringhe a prefisso del sistema attuale."""
    if result is None or result.reason in _PLAIN_NA:
        return "N/A"
    match result.verdict:
        case Verdict.CORRETTO:
            return "No errors found."
        case Verdict.ERRATO:
            return f"Error found: {result.rationale}"
        case Verdict.WARNING:
            # H15: «Warning:» resta all'inizio, come lo legge il frontend; il tipo subito dopo
            if warning_kind(result.reason) is WarningKind.NON_CONTROLLABILE:
                return f"Warning: [non controllabile] {result.rationale}"
            return f"Warning: [da guardare] {result.rationale}"
        case Verdict.NON_APPLICABILE:
            return f"N/A - {result.rationale}"


def _merged(first: CheckResult, second: CheckResult | None) -> str:
    """Testo del più grave dei due; l'altro si aggiunge se dice qualcosa da guardare."""
    if second is not None and _SEVERITY[second.verdict] < _SEVERITY[first.verdict]:
        first, second = second, first
    text = feedback_text(first)
    if (
        second is not None
        and second.verdict in (Verdict.ERRATO, Verdict.WARNING)
        and second.reason not in _PLAIN_NA
    ):
        text += f" | {feedback_text(second)}"
    return text


def _index(report: Report) -> dict[tuple[CheckName, TargetKind, int | None], CheckResult]:
    return {(item.check, item.target.kind, item.target.index): item for item in report.results}


def _dr_source_index(sources: list[Source], dr: CheckResult) -> int | None:
    """La fonte del ciclo che cita il DR della recommendation, se c'è."""
    keys = {normalize_code(item.document_key) for item in dr.evidence if item.document_key}
    for index, source in enumerate(sources):
        manual = normalize_code(source.manual)
        if any(key and (key == manual or key in manual) for key in keys):
            return index
    return None


def _scheda(operation_sheet: Any, ej200: bool) -> dict[str, Any] | None:
    """La scheda con i campi che il frontend mostra, riempiti come nella v1 (risposta di
    Copilot C13): `tabNumber` è il codice; `task` è il codice dopo «SP.ORIG.» della riga
    SCHEDA nei cicli civili, vuoto negli EJ200 (lì è un task code dell'operazione); `class`
    la v2 non la legge."""
    if operation_sheet is None:
        return None
    sheet: dict[str, Any] = operation_sheet.model_dump(exclude_none=True)
    sheet.setdefault("tabNumber", sheet.get("code"))
    sheet.setdefault("task", None if ej200 else sheet.get("sp_orig"))
    sheet.setdefault("class", None)
    return sheet


def build_legacy_payload(report: Report) -> dict[str, Any]:
    found = _index(report)
    cycle = report.cycle

    def result(check: CheckName, kind: TargetKind, index: int | None) -> CheckResult | None:
        return found.get((check, kind, index))

    def feedback(check: CheckName, kind: TargetKind, index: int | None) -> str:
        return feedback_text(result(check, kind, index))

    sources: list[dict[str, Any]] = [
        {
            "repairCode": source.repair_code,
            "manual": source.manual,
            "task": source.task,
            "section": source.section,
            "sourceFeedback": feedback(CheckName.SOURCE, TargetKind.SOURCE, index),
        }
        for index, source in enumerate(cycle.sources)
    ]
    dr = result(CheckName.DR_RECOMMENDATION, TargetKind.CYCLE, None)
    if dr is not None:
        serial = report.meta.selectors.get("serial_number")
        at = _dr_source_index(cycle.sources, dr)
        if at is None:
            reference = next((item.document_key for item in dr.evidence), None) or "DR"
            sources.insert(
                0,
                {
                    "repairCode": cycle.repair_code,
                    "DRCase": reference,
                    "manual": reference,
                    "serialNumber": serial,
                    "task": None,
                    "section": None,
                    "sourceFeedback": feedback_text(dr),
                },
            )
        else:
            row = sources[at]
            row["DRCase"] = row["manual"]
            row["serialNumber"] = serial
            row["sourceFeedback"] = _merged(dr, result(CheckName.SOURCE, TargetKind.SOURCE, at))

    ej200 = "EJ200" in normalize_code(cycle.engine_model or "")
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
                "scheda": _scheda(operation.process_sheet, ej200),
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
    if dr is not None:
        payload["drRecommendationFeedback"] = feedback_text(dr)
    return payload
