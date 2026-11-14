import json
from datetime import UTC, datetime
from pathlib import Path

from cycle_validation.checks.base import make_result
from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Evidence,
    Reason,
    Target,
    Usage,
)
from cycle_validation.domain.cycle import Cycle, Operation, ProcessSheet, Source
from cycle_validation.domain.report import PipelineError, Report, RunMeta
from cycle_validation.report.builder import build_report, write_outputs
from cycle_validation.report.legacy_payload import build_legacy_payload, feedback_text
from cycle_validation.report.markdown_writer import render_markdown

CYCLE = Cycle(
    cycle_code="C-1",
    engine_model="GENX-1B",
    sources=[Source(manual="M1", task="T1", repair_code="R-01")],
    operations=[
        Operation(
            operation_number="0010",
            operation_description="Pulire",
            repair_code="R-01",
            machine_tag="TM-1",
            task_codes=["T1", "T2"],
            process_sheet=ProcessSheet(code="SP-1", edition="B"),
        ),
        Operation(operation_number="0020", operation_description="Rettificare"),
    ],
)
META = RunMeta(
    run_id="r1",
    started_at=datetime(2026, 11, 13, tzinfo=UTC),
    pdf_name="c.pdf",
    pdf_sha256="ab",
    profile="mos",
    knowledge_version="kb1",
    model="haiku",
    prompt_version="p1",
    tool_version="0.1.0",
)
EVIDENCE = Evidence(document_key="M1", version="Rev. 2", page=3, line=7, quote="testo")


def res(check: CheckName, target: Target, reason: Reason, why: str = "motivo") -> CheckResult:
    evidence = [EVIDENCE] if reason in (Reason.VERIFICATO, Reason.CONTRADDIZIONE) else []
    return make_result(
        check,
        target,
        reason,
        why,
        evidence=evidence,
        decided_by="agent" if evidence else "code",
        usage=Usage(cost_usd=0.5, sessions=1, input_tokens=10),
    )


def op(i: int) -> Target:
    return Target.operation(i, CYCLE.operations[i])


RESULTS = [
    res(CheckName.SOURCE, Target.source(0, CYCLE.sources[0]), Reason.VERIFICATO),
    res(CheckName.TASK_CODE, op(0), Reason.FONTE_ASSENTE, "T2 assente"),
    res(CheckName.MACHINE_TAG, op(0), Reason.MACCHINA_NON_ATTIVA, "TM-1 non attiva"),
    res(CheckName.PROCESS_SHEET, op(0), Reason.CAMPO_ASSENTE, "nessuna scheda"),
    res(CheckName.OPERATION_DESCRIPTION, op(0), Reason.VERIFICATO),
    res(CheckName.OPERATION_DESCRIPTION, op(1), Reason.CONTRADDIZIONE, "valore diverso"),
]


def report(errors: list[PipelineError] | None = None, blocked: bool = False) -> Report:
    return build_report(
        META,
        CYCLE,
        RESULTS,
        timings_ms={"ingest": 5, "total": 50},
        pipeline_errors=errors or [],
        blocked=blocked,
    )


def test_feedback_prefixes() -> None:
    ok = RESULTS[0]
    assert feedback_text(ok) == "No errors found."
    assert feedback_text(RESULTS[2]) == "Error found: TM-1 non attiva"
    assert feedback_text(RESULTS[1]) == "Warning: T2 assente"
    assert feedback_text(RESULTS[3]) == "N/A - nessuna scheda"
    assert feedback_text(None) == "N/A"


def test_report_counts_status_and_usage() -> None:
    built = report()
    assert built.counts.errato == 2
    assert built.status.value == "completo"
    assert built.usage.sessions == len(RESULTS)
    assert round(built.usage.cost_usd, 2) == 3.0
    assert report(blocked=True).status.value == "bloccato"
    assert report(errors=[PipelineError(stage="s", message="m")]).status.value == "parziale"


def test_payload_has_every_key() -> None:
    payload = build_legacy_payload(report())
    assert payload["cycleCode"] == "C-1"
    assert payload["engineModel"] == "GENX-1B"
    source = payload["sources"][0]
    assert set(source) >= {"repairCode", "manual", "task", "sourceFeedback"}
    assert source["sourceFeedback"] == "No errors found."
    first, second = payload["operations"]
    assert set(first) >= {
        "operationNumber",
        "repairCode",
        "operationDescription",
        "targaCResp",
        "taskCodeCited",
        "scheda",
        "operationFeedback",
        "targaCRespFeedback",
        "taskCodeFeedback",
        "schedaFeedback",
    }
    assert first["taskCodeCited"] == "T1, T2"
    assert first["scheda"]["code"] == "SP-1"
    assert first["targaCRespFeedback"].startswith("Error found:")
    assert second["scheda"] is None
    assert second["taskCodeCited"] is None
    assert second["targaCRespFeedback"] == "N/A"
    assert second["operationFeedback"].startswith("Error found:")
    assert payload["cycle_errors_count"] == 2
    assert payload["cycle_errors_count_perc"] == 2 / 5
    assert payload["profile"] == {"ingest": 5, "total": 50}
    assert payload["cycle_status"] == "completo"
    assert payload["_pipeline_errors"] == []


def test_payload_pipeline_errors_have_no_content() -> None:
    errors = [PipelineError(stage="operation_description", target="0010", message="timeout")]
    payload = build_legacy_payload(report(errors))
    assert payload["_pipeline_errors"] == [
        {"stage": "operation_description", "target": "0010", "message": "timeout"}
    ]


def test_payload_adds_cycle_level_check_feedback_when_present() -> None:
    extra = [
        *RESULTS,
        res(CheckName.DR_RECOMMENDATION, Target.cycle(), Reason.DR_NON_APPLICABILE, "Reject"),
    ]
    built = build_report(META, CYCLE, extra, timings_ms={}, pipeline_errors=[], blocked=True)
    payload = build_legacy_payload(built)
    assert payload["drRecommendationFeedback"] == "Error found: Reject"


def test_markdown_has_one_row_per_operation_and_a_column_per_check() -> None:
    text = render_markdown(report())
    assert "Operazione" in text
    header = next(line for line in text.splitlines() if line.startswith("| Operazione"))
    for column in ("Descrizione", "Task code", "Targa", "Scheda"):
        assert column in header
    rows = [
        line for line in text.splitlines() if line.startswith("| 0010") or line.startswith("| 0020")
    ]
    assert len(rows) == 2
    assert "M1" in text and "Rev. 2" in text and "p. 3" in text  # fonte citata nel dettaglio
    assert "kb1" in text


def test_write_outputs_and_report_json_roundtrip(tmp_path: Path) -> None:
    built = report()
    write_outputs(built, tmp_path)
    for name in ("cycle.json", "report.json", "report.md", "payload.json"):
        assert (tmp_path / name).is_file()
    again = Report.model_validate_json((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert again == built
    payload = json.loads((tmp_path / "payload.json").read_text(encoding="utf-8"))
    assert payload["cycle_errors_count"] == 2
