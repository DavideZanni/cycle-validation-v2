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
    assert feedback_text(RESULTS[1]) == "Warning: [non controllabile] T2 assente"
    # campo assente: `N/A` esatto (grigio nel frontend, come nella v1)
    assert feedback_text(RESULTS[3]) == "N/A"
    excluded = res(CheckName.PROCESS_SHEET, op(0), Reason.NON_VERIFICATO_PER_PROFILO, "EJ200")
    assert feedback_text(excluded) == "N/A - EJ200"
    blocked = res(CheckName.TASK_CODE, op(0), Reason.BLOCCATO_A_MONTE, "DR")
    assert feedback_text(blocked) == "N/A"
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


def _dr_payload(reason: Reason, key: str, serial: str | None = "SN-1") -> dict[str, object]:
    dr = make_result(
        CheckName.DR_RECOMMENDATION,
        Target.cycle(),
        reason,
        "motivo DR",
        evidence=[Evidence(document_key=key, quote="Repair")],
    )
    meta = META.model_copy(update={"selectors": {"serial_number": serial, "conditions": []}})
    built = build_report(
        meta, CYCLE, [*RESULTS, dr], timings_ms={}, pipeline_errors=[], blocked=False
    )
    return build_legacy_payload(built)


def test_dr_outcome_goes_in_the_source_that_cites_the_dr() -> None:
    """Il frontend non legge `drRecommendationFeedback`: l'esito DR va nella riga della fonte
    (colonna Type «DR Case» quando c'è `DRCase`)."""
    payload = _dr_payload(Reason.DR_NON_VERIFICATA, "m1")
    (source,) = payload["sources"]  # type: ignore[misc]
    assert source["DRCase"] == "M1" and source["serialNumber"] == "SN-1"
    assert source["sourceFeedback"] == "Warning: [non controllabile] motivo DR"


def test_dr_error_comes_first_and_keeps_the_source_warning() -> None:
    cycle_results = [
        res(CheckName.SOURCE, Target.source(0, CYCLE.sources[0]), Reason.FONTE_ASSENTE, "manca")
    ]
    dr = make_result(
        CheckName.DR_RECOMMENDATION,
        Target.cycle(),
        Reason.DR_NON_APPLICABILE,
        "Reject",
        evidence=[Evidence(document_key="M1")],
    )
    built = build_report(
        META, CYCLE, [*cycle_results, dr], timings_ms={}, pipeline_errors=[], blocked=True
    )
    (source,) = build_legacy_payload(built)["sources"]
    assert source["sourceFeedback"] == "Error found: Reject | Warning: [non controllabile] manca"


def test_dr_outcome_gets_its_own_row_when_no_source_cites_the_dr() -> None:
    payload = _dr_payload(Reason.DR_NESSUNA_CORRISPONDENZA, "DR-999")
    first, second = payload["sources"]  # type: ignore[misc]
    assert first["DRCase"] == "DR-999" and first["serialNumber"] == "SN-1"
    assert first["sourceFeedback"] == "Error found: motivo DR"
    assert "DRCase" not in second and second["sourceFeedback"] == "No errors found."


def test_payload_sheet_has_the_tab_number_the_frontend_shows() -> None:
    first = build_legacy_payload(report())["operations"][0]
    assert first["scheda"]["tabNumber"] == "SP-1" and first["scheda"]["code"] == "SP-1"


def test_civil_sheet_task_is_the_code_after_sp_orig() -> None:
    """Come la v1 (C13): nei cicli civili `scheda.task` è il codice dopo «SP.ORIG.»."""
    cycle = CYCLE.model_copy(
        update={
            "operations": [
                Operation(
                    operation_number="0010",
                    process_sheet=ProcessSheet(code="16", sp_orig="70-11-22-333-444"),
                )
            ]
        }
    )
    built = report().model_copy(update={"cycle": cycle, "results": []})
    (operation,) = build_legacy_payload(built)["operations"]
    assert operation["scheda"]["task"] == "70-11-22-333-444"
    assert operation["scheda"]["class"] is None


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


def test_ej200_payload_has_the_columns_of_the_results_table() -> None:
    """Op #, Description + RC, Targa C.Resp, Task Code, Scheda (codice + SP.ORIG.), 4 feedback."""
    from cycle_validation.domain.check import TargetKind, Verdict

    cycle = Cycle(
        engine_model="EJ200",
        repair_code="A3",
        operations=[
            Operation(
                operation_number="030",
                operation_description="LAVAGGIO DEL COMPONENTE SECONDO SCHEDA PROCESSO.",
                repair_code="A3",
                machine_tag="IM0294",
                process_sheet=ProcessSheet(code="PG 300", sp_orig="X1Y22300001Z999ZZ"),
            )
        ],
    )
    sheet = CheckResult(
        check=CheckName.PROCESS_SHEET,
        target=Target(kind=TargetKind.OPERATION, index=0, label="030"),
        verdict=Verdict.NON_APPLICABILE,
        reason=Reason.NON_VERIFICATO_PER_PROFILO,
        rationale="Schede EJ200 non verificate.",
    )
    built = report().model_copy(update={"cycle": cycle, "results": [sheet]})
    (operation,) = build_legacy_payload(built)["operations"]
    assert operation == {
        "operationNumber": "030",
        "repairCode": "A3",
        "operationDescription": "LAVAGGIO DEL COMPONENTE SECONDO SCHEDA PROCESSO.",
        "targaCResp": "IM0294",
        "taskCodeCited": None,
        "scheda": {
            "code": "PG 300",
            "sp_orig": "X1Y22300001Z999ZZ",
            "tabNumber": "PG 300",
            "task": None,
            "class": None,
        },
        "operationFeedback": "N/A",
        "targaCRespFeedback": "N/A",
        "taskCodeFeedback": "N/A",
        "schedaFeedback": "N/A - Schede EJ200 non verificate.",
    }


def test_warnings_are_split_in_two_kinds() -> None:
    """H15: «da guardare» (un dubbio vero) e «non controllabile» (il programma non ha potuto
    controllare). L'esito resta WARNING."""
    from cycle_validation.domain.check import WarningKind, warning_kind

    assert warning_kind(Reason.FONTE_ASSENTE) is WarningKind.NON_CONTROLLABILE
    assert warning_kind(Reason.EVIDENZA_NON_TROVATA) is WarningKind.NON_CONTROLLABILE
    assert warning_kind(Reason.GIUDIZIO_INSTABILE) is WarningKind.DA_GUARDARE
    assert warning_kind(Reason.SCHEDA_FORSE_MANCANTE) is WarningKind.DA_GUARDARE
    assert warning_kind(Reason.CONTRADDIZIONE) is None
    assert warning_kind(Reason.VERIFICATO) is None
    doubt = res(CheckName.TASK_CODE, op(0), Reason.GIUDIZIO_INSTABILE, "una volta sì")
    assert feedback_text(doubt) == "Warning: [da guardare] una volta sì"
    built = build_report(
        META, CYCLE, [*RESULTS, doubt], timings_ms={}, pipeline_errors=[], blocked=False
    )
    counts = built.counts
    assert (counts.warning, counts.warning_da_guardare, counts.warning_non_controllabili) == (
        2,
        1,
        1,
    )
