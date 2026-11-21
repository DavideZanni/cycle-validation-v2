import json
from pathlib import Path

import pytest
from support import example_cycle, make_deps, write_cycle_pdf

from cycle_validation.domain.check import CheckName, Reason, Verdict
from cycle_validation.errors import ExtractionError, IngestError, ProfileUnavailableError
from cycle_validation.pipeline import RunRequest, run_validation
from cycle_validation.resolve.dr import SelectorError


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    return write_cycle_pdf(tmp_path / "ciclo.pdf", example_cycle())


def by(report, check: CheckName):  # type: ignore[no-untyped-def]
    return [r for r in report.results if r.check is check]


def test_mos_end_to_end(pdf: Path, tmp_path: Path) -> None:
    deps, session = make_deps()
    run_dir = tmp_path / "run"
    report = run_validation(RunRequest(pdf_path=pdf), deps, run_dir)

    ops = by(report, CheckName.OPERATION_DESCRIPTION)
    assert [r.reason for r in ops] == [
        Reason.VERIFICATO,  # 0010 coerente
        Reason.CONTRADDIZIONE,  # 0020 46,00 mm contro 45,00 mm
        Reason.VERIFICATO,  # 0030
        Reason.FONTE_ASSENTE,  # 0040 il task citato non è nel manuale: WARNING, niente modello
    ]
    assert all(r.evidence for r in ops[:3])

    machines = by(report, CheckName.MACHINE_TAG)
    assert [r.reason for r in machines] == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.MACCHINA_NON_ATTIVA,
        Reason.CAMPO_ASSENTE,
    ]
    sheets = by(report, CheckName.PROCESS_SHEET)
    assert [r.reason for r in sheets] == [
        Reason.VERIFICATO,
        Reason.ESCLUSO_DA_REGOLA,
        Reason.CAMPO_ASSENTE,
        Reason.EVIDENZA_NON_TROVATA,  # SP-0202 è LEAP, il motore è GENX
    ]
    sources = by(report, CheckName.SOURCE)
    assert [r.reason for r in sources] == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.FONTE_ASSENTE,
    ]
    codes = by(report, CheckName.TASK_CODE)
    assert codes[3].reason is Reason.FONTE_ASSENTE

    assert report.counts.errato == 2
    assert report.status.value == "completo"
    assert report.meta.knowledge_version == "sintetico-2026-11"
    assert report.meta.profile == "mos"
    assert len(session.planned) == 3  # la 0040 non chiama il modello
    # una delle due contraddizioni è della descrizione: si conferma con due sessioni in più
    assert report.session_modes == {"inline": 3, "search": 0, "conferma": 2}
    assert report.usage.sessions == 5
    assert set(report.timings_ms) >= {"ingest", "extract", "checks", "total"}

    payload = json.loads((run_dir / "payload.json").read_text(encoding="utf-8"))
    assert payload["operations"][2]["targaCRespFeedback"].startswith("Error found:")
    assert payload["operations"][0]["operationFeedback"] == "No errors found."
    assert payload["sources"][2]["sourceFeedback"].startswith("Warning:")
    assert payload["cycle_errors_count"] == 2
    assert (run_dir / "report.md").read_text(encoding="utf-8").startswith("# Validazione")


def test_skip_check_removes_the_check_and_the_sessions(pdf: Path) -> None:
    deps, session = make_deps()
    request = RunRequest(pdf_path=pdf, skip_checks=frozenset({CheckName.OPERATION_DESCRIPTION}))
    report = run_validation(request, deps)
    assert by(report, CheckName.OPERATION_DESCRIPTION) == []
    assert session.requests == []


def test_unconfirmed_value_downgrades_the_verdict(tmp_path: Path) -> None:
    cycle = example_cycle()
    path = tmp_path / "x.pdf"
    write_cycle_pdf(
        path,
        cycle.model_copy(
            update={
                "operations": [
                    o.model_copy(update={"machine_tag": "XX"})
                    if o.operation_number == "0030"
                    else o
                    for o in cycle.operations
                ]
            }
        ),
    )
    report = run_validation(RunRequest(pdf_path=path), make_deps()[0])
    wrong_tag = by(report, CheckName.MACHINE_TAG)[2]
    assert wrong_tag.reason is Reason.ESTRAZIONE_NON_CONFERMATA
    assert wrong_tag.verdict is Verdict.WARNING


def test_technical_failure_does_not_become_a_content_error(pdf: Path) -> None:
    deps, _ = make_deps(script=lambda r, a: RuntimeError("boom"))
    report = run_validation(RunRequest(pdf_path=pdf), deps)
    ops = by(report, CheckName.OPERATION_DESCRIPTION)
    # la 0040 cita un task che non c'è: WARNING senza modello, quindi niente errore tecnico
    assert [r.reason for r in ops] == [Reason.ERRORE_TECNICO] * 3 + [Reason.FONTE_ASSENTE]
    assert len(report.pipeline_errors) == 3
    assert report.status.value == "parziale"
    assert report.counts.errato == 1  # solo la macchina non attiva


def test_inactive_profile_is_refused(pdf: Path) -> None:
    deps, _ = make_deps()
    off = deps.profile.model_copy(update={"enabled": False, "disabled_reason": "non pronto"})
    deps2, _ = make_deps(profile_config=off)
    with pytest.raises(ProfileUnavailableError, match="non pronto"):
        run_validation(RunRequest(pdf_path=pdf), deps2)


def test_mos_rejects_dr_selectors(pdf: Path) -> None:
    from cycle_validation.resolve.dr import DrSelectors

    with pytest.raises(SelectorError):
        run_validation(
            RunRequest(pdf_path=pdf, selectors=DrSelectors("SN-DEMO-001", (1,))), make_deps()[0]
        )


def test_cycle_without_operations_fails(pdf: Path, tmp_path: Path) -> None:
    empty = tmp_path / "vuoto.json"
    empty.write_text('{"sources": [], "operations": []}', encoding="utf-8")
    with pytest.raises(ExtractionError):
        run_validation(RunRequest(pdf_path=pdf), make_deps(cycle_path=empty)[0])


def test_bad_pdf_is_refused(tmp_path: Path) -> None:
    junk = tmp_path / "x.pdf"
    junk.write_bytes(b"non e un pdf")
    with pytest.raises(IngestError) as info:
        run_validation(RunRequest(pdf_path=junk), make_deps()[0])
    assert info.value.http_status == 415


def test_pdf_from_memory(pdf: Path) -> None:
    request = RunRequest(pdf_bytes=pdf.read_bytes(), pdf_name="mem.pdf")
    report = run_validation(request, make_deps()[0])
    assert report.meta.pdf_name == "mem.pdf"


def test_a_description_the_pdf_does_not_confirm_is_not_sent_to_the_model(tmp_path: Path) -> None:
    # il PDF dice 45,00 mm; l'estrazione ha letto 46,00 mm: nessun giudizio su un testo non provato
    cycle = example_cycle()
    printed = cycle.model_copy(
        update={
            "operations": [
                o.model_copy(
                    update={
                        "operation_description": "Rettificare la sede fino al diametro 45,00 mm."
                    }
                )
                if o.operation_number == "0020"
                else o
                for o in cycle.operations
            ]
        }
    )
    deps, session = make_deps()
    report = run_validation(RunRequest(pdf_path=write_cycle_pdf(tmp_path / "x.pdf", printed)), deps)
    described = by(report, CheckName.OPERATION_DESCRIPTION)[1]
    assert described.reason is Reason.ESTRAZIONE_NON_CONFERMATA
    assert described.verdict is Verdict.WARNING
    assert "op-001-0020" not in [r.session_id for r in session.requests]
    assert report.usage.sessions == len(session.requests)
