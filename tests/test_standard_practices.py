"""Task del capitolo 70 (pratiche standard): stanno nel manuale SPM anche quando il ciclo
cita solo il manuale del motore. Tutti i dati sono inventati."""

from pathlib import Path

from kb_fixtures import DOC_72, _task

from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import DocumentInfo
from cycle_validation.resolve.civil import context_locations, resolve_operation

SPM_LINES = [
    "# Pratiche standard di prova",
    "",
    "TASK 70-11-00-350-002 PULIZIA DI PROVA",
    "Pulire il pezzo con il solvente di prova.",
    "",
    "TASK 70-11-00-350-003 ASCIUGATURA DI PROVA",
    "Asciugare il pezzo.",
]


def _knowledge(tmp_path: Path, *, kind: str | None = "SPM") -> IndexedKnowledgeBase:
    path = tmp_path / "spm.md"
    path.write_text("\n".join(SPM_LINES) + "\n", "utf-8")
    spm = DocumentInfo(key="SPM_DEMO_pb70-11-00_ch1", path=path, code="SPM-DEMO", kind=kind)
    return IndexedKnowledgeBase(
        "v",
        documents=[DOC_72, spm],
        tasks=[_task(DOC_72, "72-00-01-350-003", 17, 20), _task(spm, "70-11-00-350-002", 3, 4)],
    )


def _cycle(*codes: str) -> tuple[Cycle, Operation]:
    operation = Operation(operation_number="005", task_codes=list(codes))
    return Cycle(sources=[Source(manual="MAN-DEMO-72")], operations=[operation]), operation


def test_a_chapter_70_task_is_found_in_the_spm_when_the_cycle_cites_the_engine_manual(
    tmp_path: Path,
) -> None:
    cycle, operation = _cycle("70-11-00-350-002", "72-00-01-350-003")
    refs = resolve_operation(cycle, operation, _knowledge(tmp_path))
    assert refs.missing == ()
    assert [(hit.manual_key, hit.line_start) for hit in refs.found] == [
        ("SPM_DEMO_pb70-11-00_ch1", 3),
        ("MAN-DEMO-72", 17),
    ]


def test_the_spm_text_is_searched_when_the_index_lacks_the_task(tmp_path: Path) -> None:
    cycle, operation = _cycle("70-11-00-350-003")
    refs = resolve_operation(cycle, operation, _knowledge(tmp_path))
    assert [(hit.manual_key, hit.line_start, hit.line_end) for hit in refs.found] == [
        ("SPM_DEMO_pb70-11-00_ch1", 6, 7)
    ]


def test_only_chapter_70_goes_to_the_spm(tmp_path: Path) -> None:
    # un task di un altro capitolo che non è nel manuale citato resta mancante
    cycle, operation = _cycle("72-00-01-999-009", "70-11-00-999-009")
    refs = resolve_operation(cycle, operation, _knowledge(tmp_path))
    assert refs.found == ()
    assert refs.missing == ("72-00-01-999-009", "70-11-00-999-009")


def test_without_an_spm_document_the_chapter_70_task_is_missing(tmp_path: Path) -> None:
    cycle, operation = _cycle("70-11-00-350-002")
    refs = resolve_operation(cycle, operation, _knowledge(tmp_path, kind="MANUAL"))
    assert refs.missing == ("70-11-00-350-002",)


def test_a_dr_task_without_manual_is_found_in_the_spm(tmp_path: Path) -> None:
    cycle, operation = _cycle()
    locations = context_locations(
        cycle, operation, _knowledge(tmp_path), extra_tasks=[(None, "70-11-00-350-002")]
    )
    assert [(hit.manual_key, hit.line_start) for hit in locations] == [
        ("SPM_DEMO_pb70-11-00_ch1", 3)
    ]


def test_a_dr_procedure_cited_as_in_the_print_is_found_by_its_number(tmp_path: Path) -> None:
    from cycle_validation.resolve.civil import resolve_document

    path = tmp_path / "dr.md"
    path.write_text("# Procedura DR di prova\n", "utf-8")
    procedure = DocumentInfo(
        key="DR_01000002_Repair_Procedure", path=path, code="01000002", kind="DR_PROC"
    )
    kb = IndexedKnowledgeBase("v", documents=[procedure])
    for name in ("D.R. CASE #01000002", "D.R. CASE / #01000002", "DR CASE 01000002"):
        resolution = resolve_document(name, kb)
        assert resolution.document is procedure, name
    assert resolve_document("D.R. CASE #09999999", kb).document is None
