import asyncio
from pathlib import Path
from typing import Any

import pytest
from ej200_fixtures import (
    DM_A,
    DM_C,
    RecordingStore,
    catalog_entries,
    judge,
    make_kb,
    make_store,
    pvrm320_pages,
    text_key,
    text_objects,
)
from fakes import ScriptedSession
from kb_fixtures import PROFILES_DIR
from support import make_deps

from cycle_validation.config import load_profile
from cycle_validation.domain.check import CheckName, Reason, Verdict
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.errors import (
    ExtractionError,
    IngestError,
    KnowledgeError,
    SourceUnavailableError,
)
from cycle_validation.extract.pvrm320 import Pvrm320LayoutExtractor, parse_pvrm320
from cycle_validation.ingest.pdf import read_pdf_bytes
from cycle_validation.kb.ej200 import (
    DEFAULT_CATALOG_KEY,
    DEFAULT_TEXT_PREFIX,
    Ej200Catalog,
    Ej200KnowledgeBase,
    parse_catalog,
)
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.services.machines import StaticMachineRegistry
from cycle_validation.testing.pdf import build_pdf

EJ = load_profile("ej200", PROFILES_DIR)


def pdf_of(pages: list[str]) -> Any:
    return read_pdf_bytes(build_pdf(pages), "ej.pdf", EJ.file_limits)


# --- controlli sul file -------------------------------------------------------------------


def test_ej200_file_limits() -> None:
    assert pdf_of(pvrm320_pages()).pages
    with pytest.raises(IngestError, match="EJ200") as wrong_type:
        read_pdf_bytes(build_pdf(["Documento qualsiasi " * 10]), "x.pdf", EJ.file_limits)
    assert wrong_type.value.http_status == 422
    with pytest.raises(IngestError) as many:
        read_pdf_bytes(build_pdf(["EJ200 " * 30] * 61), "x.pdf", EJ.file_limits)
    assert many.value.http_status == 422 and "60" in str(many.value)
    with pytest.raises(IngestError) as no_header:
        read_pdf_bytes(b"x" * 200, "x.pdf", EJ.file_limits)
    assert no_header.value.http_status == 415
    small = EJ.file_limits.model_copy(update={"max_bytes": 100})
    with pytest.raises(IngestError) as big:
        read_pdf_bytes(build_pdf(pvrm320_pages()), "x.pdf", small)
    assert big.value.http_status == 413
    assert EJ.file_limits.max_bytes == 20 * 1024 * 1024


# --- estrattore PVRM320 -------------------------------------------------------------------


def test_repeated_operations_are_merged_and_notes_excluded() -> None:
    cycle = parse_pvrm320(pdf_of(pvrm320_pages()))
    assert [o.operation_number for o in cycle.operations] == ["0010", "0020"]
    second = cycle.operations[1]
    assert second.operation_description == "Rettificare la sede fino al diametro 46,00 mm."
    assert second.task_codes == [DM_C] and second.machine_tag == "TM-2002"
    first = cycle.operations[0]
    assert (
        "nota" not in first.operation_description
        and "attenzione" not in first.operation_description
    )
    assert first.task_codes == [DM_A]
    assert cycle.cycle_code == "EJ-C-001" and cycle.engine_model == "EJ200"


def test_references_become_sources_with_issue() -> None:
    cycle = parse_pvrm320(pdf_of(pvrm320_pages()))
    assert [(s.manual, s.issue) for s in cycle.sources] == [
        ("RN-100", "2"),
        ("EF-200", None),
        ("RDR-300", None),
    ]


def test_layout_errors_are_extraction_errors() -> None:
    with pytest.raises(ExtractionError, match="PVRM320"):
        parse_pvrm320(pdf_of(["EJ200 " * 30]))
    with pytest.raises(ExtractionError, match="operazione"):
        parse_pvrm320(pdf_of(["PVRM320 EJ200\nCYCLE: X\n" + "EJ200 " * 20]))
    cycle, usage = asyncio.run(Pvrm320LayoutExtractor().extract(pdf_of(pvrm320_pages())))
    assert len(cycle.operations) == 2 and usage.sessions == 0


# --- catalogo e conoscenza ----------------------------------------------------------------


def test_catalog_is_cached_for_the_ttl_and_failures_are_not_cached() -> None:
    now = {"t": 0.0}
    store = make_store()
    reads = {"n": 0}
    original = store.get_bytes

    def counting(key: str) -> bytes:
        reads["n"] += 1
        return original(key)

    store.get_bytes = counting  # type: ignore[method-assign]
    catalog = Ej200Catalog(store, ttl_s=300, clock=lambda: now["t"])
    catalog.entries()
    catalog.entries()
    assert reads["n"] == 1
    now["t"] = 301
    catalog.entries()
    assert reads["n"] == 2

    broken = Ej200Catalog(make_store([]), key="manca", clock=lambda: now["t"])
    with pytest.raises(SourceUnavailableError):
        broken.entries()
    broken._store.put("manca", catalog_entries())  # type: ignore[attr-defined]
    assert broken.entries()  # l'errore precedente non è stato memorizzato


def test_invalid_catalog_is_explicit() -> None:
    with pytest.raises(KnowledgeError, match="Catalogo"):
        parse_catalog(b"{non json")
    with pytest.raises(KnowledgeError):
        parse_catalog(b'[{"code": "X"}]')


def test_text_is_read_by_exact_document_id_and_hash(tmp_path: Path) -> None:
    kb, store = make_kb(tmp_path)
    documents = kb.find_manuals("rn-100")
    assert {d.key for d in documents} == {"RN-100-1", "RN-100-2"}
    assert store.text_reads() == [text_key("rn100-2")]
    latest = next(d for d in documents if d.version == "2")
    assert "Pulire la pala con solvente tipo A." in latest.path.read_text(encoding="utf-8")
    kb.find_manuals("RN-100")
    assert len(store.text_reads()) == 1  # materializzato una sola volta
    assert kb.find_task("RN-100", "x") is None
    assert kb.find_process_sheet("SP-1") is None
    assert kb.find_machine_tag("tm-1001") is not None
    assert kb.stats()["pubblicazioni"] == 7


def test_preload_failure_is_a_knowledge_error(tmp_path: Path) -> None:
    kb, _ = make_kb(tmp_path, store=make_store([]))
    kb._catalog._store.put("Manufacturing AI/exports/ej200_publication/catalog.json", b"[")  # type: ignore[attr-defined]
    with pytest.raises(KnowledgeError):
        kb.preload()


# --- pipeline EJ200 -----------------------------------------------------------------------


def ej_deps(
    tmp_path: Path, script: Any, cycle: Cycle, **kb_args: Any
) -> tuple[Dependencies, ScriptedSession]:
    path = tmp_path / "ciclo.json"
    path.write_text(cycle.model_dump_json(), encoding="utf-8")
    deps, session = make_deps("ej200", script=script, cycle_path=path)
    kb, _ = make_kb(tmp_path / "work", **kb_args)
    return Dependencies(
        **{**deps.__dict__, "kb": kb, "machines": StaticMachineRegistry(["TM-1001", "TM-2002"])}
    ), session


def ej_cycle(**changes: Any) -> Cycle:
    base = Cycle(
        cycle_code="EJ-C-001",
        engine_model="EJ200",
        sources=[
            Source(manual="RN-100", issue="2"),
            Source(manual="EF-200"),
            Source(manual="RDR-300"),
        ],
        operations=[
            Operation(
                operation_number="0010",
                operation_description="Pulire la pala con solvente tipo A.",
                machine_tag="TM-1001",
                task_codes=[DM_A],
            ),
            Operation(
                operation_number="0020",
                operation_description="Rettificare la sede fino al diametro 46,00 mm.",
                machine_tag="TM-2002",
                task_codes=[DM_C, "DMC-INESISTENTE"],
            ),
        ],
    )
    return base.model_copy(update=changes)


def rows(report: Any, check: CheckName) -> list[Any]:
    return [r for r in report.results if r.check is check]


def run_ej(tmp_path: Path, deps: Dependencies, cycle: Cycle) -> Any:
    from support import write_cycle_pdf

    pdf = write_cycle_pdf(tmp_path / "ej.pdf", cycle)
    return run_validation(RunRequest(pdf_path=pdf), deps)


def test_ej200_end_to_end(tmp_path: Path) -> None:
    cycle = ej_cycle()
    deps, session = ej_deps(tmp_path, judge, cycle)
    report = run_ej(tmp_path, deps, cycle)
    assert [r.reason for r in rows(report, CheckName.SOURCE)] == [Reason.VERIFICATO] * 3
    assert [r.reason for r in rows(report, CheckName.TASK_CODE)] == [
        Reason.VERIFICATO,
        Reason.EVIDENZA_NON_TROVATA,
    ]
    assert [r.reason for r in rows(report, CheckName.MACHINE_TAG)] == [Reason.VERIFICATO] * 2
    assert {r.reason for r in rows(report, CheckName.PROCESS_SHEET)} == {Reason.CAMPO_ASSENTE}
    assert [r.reason for r in rows(report, CheckName.OPERATION_DESCRIPTION)] == [
        Reason.VERIFICATO,
        Reason.CONTRADDIZIONE,
    ]
    assert report.counts.errato == 1
    assert len(session.requests) == 2


def test_process_sheets_are_not_verified_for_ej200(tmp_path: Path) -> None:
    from cycle_validation.domain.cycle import ProcessSheet

    cycle = ej_cycle()
    cycle = cycle.model_copy(
        update={
            "operations": [
                cycle.operations[0].model_copy(update={"process_sheet": ProcessSheet(code="SP-1")})
            ]
        }
    )
    deps, _ = ej_deps(tmp_path, judge, cycle)
    report = run_ej(tmp_path, deps, cycle)
    (sheet,) = rows(report, CheckName.PROCESS_SHEET)
    assert (sheet.verdict, sheet.reason) == (
        Verdict.NON_APPLICABILE,
        Reason.NON_VERIFICATO_PER_PROFILO,
    )


def test_context_prefers_rdr_then_ef_then_rn(tmp_path: Path) -> None:
    cycle = ej_cycle()
    deps, session = ej_deps(tmp_path, judge, cycle, long_document="rn100-2")
    run_ej(tmp_path, deps, cycle)
    prompt = session.requests[0].prompt
    assert prompt.index("RDR-300-1.md") < prompt.index("EF-200-1.md") < prompt.index("RN-100-2.md")


def test_long_documents_are_searched_not_truncated(tmp_path: Path) -> None:
    cycle = ej_cycle()
    deps, session = ej_deps(tmp_path, judge, cycle, long_document="rn100-2")
    run_ej(tmp_path, deps, cycle)
    request = session.requests[0]
    assert request.use_tools
    names = {p.name for p in request.allowed_files}
    assert {"RN-100-2.md", "EF-200-1.md", "RDR-300-1.md"} <= names
    text = next(p for p in request.allowed_files if p.name == "RN-100-2.md").read_text(
        encoding="utf-8"
    )
    assert text.count("\n") >= 400  # nessun troncamento a 150.000 caratteri o simili


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        (Source(manual="RN-100", issue="1"), Reason.VERSIONE_DIVERSA),
        (Source(manual="RN-999"), Reason.FONTE_ASSENTE),
        (Source(manual="RN-400"), Reason.FONTE_ASSENTE),
        (Source(manual="EF-500"), Reason.PUBBLICAZIONE_PARZIALE),
        (Source(manual="RDR-9"), Reason.RIFERIMENTO_AMBIGUO),
    ],
)
def test_publication_states_are_warnings(tmp_path: Path, source: Source, reason: Reason) -> None:
    cycle = ej_cycle(sources=[source, Source(manual="RN-100", issue="2")])
    deps, _ = ej_deps(tmp_path, judge, cycle)
    report = run_ej(tmp_path, deps, cycle)
    first = rows(report, CheckName.SOURCE)[0]
    assert (first.verdict, first.reason) == (Verdict.WARNING, reason)


def test_without_any_available_source_operations_are_not_validated(tmp_path: Path) -> None:
    cycle = ej_cycle(sources=[Source(manual="RN-999")])
    deps, session = ej_deps(tmp_path, judge, cycle)
    report = run_ej(tmp_path, deps, cycle)
    assert {r.reason for r in rows(report, CheckName.OPERATION_DESCRIPTION)} == {
        Reason.FONTE_ASSENTE
    }
    assert {r.reason for r in rows(report, CheckName.TASK_CODE)} == {Reason.FONTE_ASSENTE}
    assert session.requests == []
    assert report.counts.errato == 0  # esito non superato ma senza errori di contenuto


def test_a_failed_check_is_a_warning_with_a_pipeline_error(tmp_path: Path) -> None:
    cycle = ej_cycle()
    deps, _ = ej_deps(tmp_path, lambda r, a: RuntimeError("boom"), cycle)
    report = run_ej(tmp_path, deps, cycle)
    assert {r.reason for r in rows(report, CheckName.OPERATION_DESCRIPTION)} == {
        Reason.ERRORE_TECNICO
    }
    assert len(report.pipeline_errors) == 2 and report.status.value == "parziale"


def test_extraction_discrepancies_are_reported(tmp_path: Path) -> None:
    cycle = ej_cycle()
    pdf_cycle = cycle.model_copy(
        update={"operations": [cycle.operations[0].model_copy(update={"machine_tag": "TM-OTHER"})]}
    )
    from support import write_cycle_pdf

    pdf = write_cycle_pdf(tmp_path / "ej.pdf", pdf_cycle)
    deps, _ = ej_deps(tmp_path, judge, cycle)
    report = run_validation(RunRequest(pdf_path=pdf), deps)
    integrity = rows(report, CheckName.EXTRACTION_INTEGRITY)
    assert any(r.reason is Reason.ESTRAZIONE_NON_CONFERMATA for r in integrity)
    # la targa che il PDF non riporta non può dare un esito pieno, nemmeno se è in anagrafica
    machine = rows(report, CheckName.MACHINE_TAG)[0]
    assert (machine.verdict, machine.reason) == (
        Verdict.WARNING,
        Reason.ESTRAZIONE_NON_CONFERMATA,
    )


def test_ej200_golden_set_is_concordant(tmp_path: Path) -> None:
    from cycle_validation.golden import load_cases, run_golden

    golden = Path(__file__).parent / "golden" / "ej200"
    cases = load_cases(golden)
    assert [c.name for c in cases] == [
        "codice_non_trovato",
        "contraddetto",
        "fonte_non_pubblicata",
        "issue_diversa",
        "pubblicazione_parziale",
        "pulito",
        "riferimento_ambiguo",
    ]

    def deps_for(case: Any) -> Dependencies:
        cycle = Cycle.model_validate_json(case.cycle_path.read_text(encoding="utf-8"))
        return ej_deps(tmp_path / case.name, judge, cycle)[0]

    for case in cases:
        (tmp_path / case.name).mkdir()
    summary = asyncio.run(run_golden(cases, deps_for))
    assert summary.concordance == 1.0, summary.render()


# --- materializzazione dei documenti --------------------------------------------------------


def test_a_new_issue_does_not_replace_the_text_another_validation_is_reading(
    tmp_path: Path,
) -> None:
    # alla scadenza del catalogo la issue 2 non è più l'ultima: il suo segnaposto non deve
    # finire nel file che una validazione in corso sta leggendo come testo completo
    now = {"t": 0.0}
    store = make_store()
    kb = Ej200KnowledgeBase("v", Ej200Catalog(store, clock=lambda: now["t"]), tmp_path, store)
    in_use = next(d for d in kb.find_manuals("RN-100") if d.version == "2")
    assert "Pulire la pala con solvente tipo A." in in_use.path.read_text(encoding="utf-8")

    newer = {
        "code": "RN-100",
        "kind": "RN",
        "issue": "3",
        "document_id": "rn100-3",
        "content_hash": "h-rn100-3",
        "title": "RN-100",
    }
    store.put(DEFAULT_CATALOG_KEY, [*catalog_entries(), newer])
    now["t"] = 10_000.0
    kb.find_manuals("RN-100")
    assert "Pulire la pala con solvente tipo A." in in_use.path.read_text(encoding="utf-8")


def test_concurrent_lookups_read_a_publication_text_once(tmp_path: Path) -> None:
    import threading

    started, release = threading.Event(), threading.Event()

    class SlowStore(RecordingStore):
        def get_bytes(self, key: str) -> bytes:
            data = super().get_bytes(key)
            if key.startswith(DEFAULT_TEXT_PREFIX):
                started.set()
                release.wait(5)
            return data

    store = SlowStore({DEFAULT_CATALOG_KEY: catalog_entries(), **text_objects()})
    kb = Ej200KnowledgeBase("v", Ej200Catalog(store), tmp_path, store)
    found: list[list[Any]] = []
    workers = [
        threading.Thread(target=lambda: found.append(kb.find_manuals("EF-200"))) for _ in range(2)
    ]
    workers[0].start()
    assert started.wait(5)
    workers[1].start()
    workers[1].join(0.3)  # il secondo o aspetta il primo, o (prima) rileggeva il testo
    release.set()
    for worker in workers:
        worker.join(5)
    assert len(store.text_reads()) == 1
    assert len(found) == 2 and found[0][0].path == found[1][0].path


def test_catalog_lookup_by_code_or_reference_follows_a_reload() -> None:
    now = {"t": 0.0}
    store = make_store()
    catalog = Ej200Catalog(store, ttl_s=300, clock=lambda: now["t"])
    assert [entry.issue for entry in catalog.find(" rn - 100 ")] == [
        "1",
        "2",
    ]  # ordine del catalogo
    assert {entry.code for entry in catalog.find("RDR-9")} == {"RDR-9A", "RDR-9B"}
    assert catalog.find("RN-999") == []

    added = {"code": "RN-999", "kind": "RN", "document_id": "d", "content_hash": "h"}
    store.put(DEFAULT_CATALOG_KEY, [*catalog_entries(), added])
    assert catalog.find("RN-999") == []  # entro il TTL vale il catalogo in memoria
    now["t"] = 301
    assert [entry.code for entry in catalog.find("rn-999")] == ["RN-999"]


def test_unreadable_machine_data_during_a_check_is_a_source_failure(tmp_path: Path) -> None:
    # i dati TM si rompono dopo l'avvio: la targa non è "non trovata", è non verificabile
    store = make_store()
    store.put("structured/TM/tm.json", b"{non json")
    kb, _ = make_kb(tmp_path, store=store)
    with pytest.raises(SourceUnavailableError):
        kb.find_machine_tag("TM-1001")
    assert kb.find_dr_recommendations("SN-1") == []
