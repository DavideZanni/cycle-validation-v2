"""Testo di contesto per l'agente: task dell'operazione, delle fonti, dei DR e dei LEAP."""

from pathlib import Path

from kb_fixtures import DOC_72, memory_knowledge

from cycle_validation.checks.dr_recommendation import dr_tasks
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
