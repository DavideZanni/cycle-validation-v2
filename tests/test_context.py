"""Testo di contesto per l'agente: task dell'operazione, delle fonti, dei DR e dei LEAP."""

from pathlib import Path

from kb_fixtures import DOC_72, memory_knowledge

from cycle_validation.checks.dr_recommendation import dr_documents, dr_tasks
from cycle_validation.domain.cycle import Cycle
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import DocumentInfo, DrRecommendation, TaskLocation
from cycle_validation.resolve.civil import context_locations
from cycle_validation.resolve.dr import DrSelectors

LEAP = "LEAP-00-99-88-77-01A-123A-D"  # inventato


def _cycle(*sources: dict[str, str]) -> Cycle:
    return Cycle.model_validate(
        {
            "sources": list(sources),
            "operations": [{"operation_number": "0010", "operation_description": "Pulire"}],
        }
    )


def _kb_with_unlinked_dr() -> IndexedKnowledgeBase:
    """La DR dell'esempio senza manuale: l'indice lo toglie quando è contraddetto."""
    base = memory_knowledge()
    task = base.find_task("MAN-DEMO-72", "72-00-01-350-003")
    assert task is not None
    return IndexedKnowledgeBase(
        base.version,
        documents=[DOC_72],
        tasks=[task],
        dr_recommendations=[
            DrRecommendation(
                serial_number="SN-1", conditions=(1,), procedure="Repair", tasks=(task.task,)
            )
        ],
    )


def test_dr_tasks_without_a_manual_are_kept() -> None:
    kb = _kb_with_unlinked_dr()
    assert dr_tasks(kb, DrSelectors("SN-1", (1,))) == [(None, "72-00-01-350-003")]


def test_dr_tasks_without_a_manual_are_searched_in_the_cycle_manuals() -> None:
    kb = _kb_with_unlinked_dr()
    cycle = _cycle({"manual": "MAN-DEMO-72"})
    locations = context_locations(
        cycle, cycle.operations[0], kb, extra_tasks=dr_tasks(kb, DrSelectors("SN-1", (1,)))
    )
    assert [(item.manual_key, item.task) for item in locations] == [
        ("MAN-DEMO-72", "72-00-01-350-003")
    ]


def test_dr_tasks_without_a_manual_are_not_searched_outside_the_cycle_manuals() -> None:
    kb = _kb_with_unlinked_dr()
    cycle = _cycle({"manual": "MAN-DEMO-75"})
    locations = context_locations(
        cycle, cycle.operations[0], kb, extra_tasks=dr_tasks(kb, DrSelectors("SN-1", (1,)))
    )
    assert locations == ()


def _leap_kb(tmp_path: Path, key: str = LEAP) -> IndexedKnowledgeBase:
    path = tmp_path / "leap.md"
    path.write_text(f"<!-- page 1 -->\n{LEAP}\nPulire il disco.\nControllare.\n", "utf-8")
    document = DocumentInfo(key=key, path=path, code=LEAP, kind="SPM")
    whole = TaskLocation(manual_key=key, task=LEAP, document=document, line_start=1, line_end=4)
    return IndexedKnowledgeBase("leap", documents=[document], tasks=[whole])


def test_a_leap_document_cited_without_task_is_its_own_context(tmp_path: Path) -> None:
    kb = _leap_kb(tmp_path)
    cycle = _cycle({"manual": LEAP})
    locations = context_locations(cycle, cycle.operations[0], kb)
    assert [(item.task, item.line_start, item.line_end) for item in locations] == [(LEAP, 1, 4)]


def test_a_leap_document_cited_by_its_key_finds_the_task_by_code(tmp_path: Path) -> None:
    kb = _leap_kb(tmp_path, key="DM motore 01A")
    cycle = _cycle({"manual": "DM motore 01A"})
    assert [item.task for item in context_locations(cycle, cycle.operations[0], kb)] == [LEAP]


def test_an_ordinary_manual_cited_without_task_adds_nothing() -> None:
    cycle = _cycle({"manual": "MAN-DEMO-72"})
    assert context_locations(cycle, cycle.operations[0], memory_knowledge()) == ()


def _kb_with_dr_procedure(tmp_path: Path, kind: str = "DR_PROC") -> IndexedKnowledgeBase:
    """DR collegata alla sua procedura, che non ha task con codice (come accade di solito)."""
    path = tmp_path / "proc.md"
    path.write_text(
        "<!-- page 1 -->\nPROCEDURA DI PROVA\n1. Raccordare.\n2. Ispezionare.\n", "utf-8"
    )
    document = DocumentInfo(key="DR_PROC_77", path=path, code="DR-77", kind=kind)
    return IndexedKnowledgeBase(
        "v",
        documents=[document, DOC_72],
        tasks=[],
        dr_recommendations=[
            DrRecommendation(
                serial_number="SN-1",
                conditions=(1,),
                procedure="Repair",
                reference="DR-77",
                manual="DR_PROC_77",
                tasks=("PASSO 001",),
            )
        ],
    )


def test_a_dr_procedure_without_the_cited_task_is_the_whole_context(tmp_path: Path) -> None:
    kb = _kb_with_dr_procedure(tmp_path)
    selectors = DrSelectors("SN-1", (1,))
    cycle = _cycle({"manual": "MAN-DEMO-72"})
    locations = context_locations(
        cycle,
        cycle.operations[0],
        kb,
        extra_tasks=dr_tasks(kb, selectors),
        extra_documents=dr_documents(kb, selectors),
    )
    assert [(item.manual_key, item.task, item.line_start, item.line_end) for item in locations] == [
        ("DR_PROC_77", "", 1, 4)
    ]


def test_only_dr_procedures_become_whole_context(tmp_path: Path) -> None:
    kb = _kb_with_dr_procedure(tmp_path, kind="RM")
    assert dr_documents(kb, DrSelectors("SN-1", (1,))) == []
    assert dr_documents(kb, DrSelectors("SN-2", (1,))) == []
    assert dr_documents(kb, None) == []


def test_found_tasks_win_over_the_whole_dr_procedure(tmp_path: Path) -> None:
    procedure = _kb_with_dr_procedure(tmp_path)
    task = memory_knowledge().find_task("MAN-DEMO-72", "72-00-01-350-003")
    assert task is not None
    kb = IndexedKnowledgeBase(
        "v",
        documents=[*procedure.find_manuals("DR_PROC_77"), DOC_72],
        tasks=[task],
        dr_recommendations=procedure.find_dr_recommendations("SN-1"),
    )
    cycle = Cycle.model_validate(
        {
            "sources": [{"manual": "MAN-DEMO-72", "task": "72-00-01-350-003"}],
            "operations": [{"operation_number": "0010", "operation_description": "Pulire"}],
        }
    )
    selectors = DrSelectors("SN-1", (1,))
    locations = context_locations(
        cycle, cycle.operations[0], kb, extra_documents=dr_documents(kb, selectors)
    )
    assert [item.task for item in locations] == ["72-00-01-350-003"]


def test_a_dr_without_manual_finds_its_procedure_by_the_dr_code(tmp_path: Path) -> None:
    # Come lo scrive l'indice quando i task non indicano un manuale: `manual` vuoto,
    # il codice del DR in `reference`, uguale al codice della procedura.
    linked = _kb_with_dr_procedure(tmp_path)
    kb = IndexedKnowledgeBase(
        "v",
        documents=[*linked.find_manuals("DR_PROC_77"), DOC_72],
        tasks=[],
        dr_recommendations=[
            DrRecommendation(
                serial_number="SN-1",
                conditions=(1,),
                procedure="Repair",
                reference="DR-77",
                tasks=("PASSO 001",),
            ),
            DrRecommendation(
                serial_number="SN-2", conditions=(1,), procedure="Repair", reference="DR-99"
            ),
        ],
    )
    found = dr_documents(kb, DrSelectors("SN-1", (1,)))
    assert [document.key for document in found] == ["DR_PROC_77"]
    assert dr_documents(kb, DrSelectors("SN-2", (1,))) == []
