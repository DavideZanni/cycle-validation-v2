"""Task cercato nel testo del manuale quando l'indice non lo ha (codici inventati)."""

from pathlib import Path

from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import DocumentInfo, TaskLocation
from cycle_validation.kb.task_text import find_task_in_text

LINES = [
    "<!-- page 1 -->",
    "11-22-33 REPAIR 002 ........ 4",  # sommario: non apre
    "Refer to 11-22-33 REPAIR 002",  # citazione in una frase: non apre
    "## TASK 11-22-33 Repair 002 - RIPARAZIONE",
    "1. a",
    "",
    "<!-- page 2 -->",
    "**11-22-33 REPAIR 002**",  # stesso titolo in cima alla pagina: il task continua
    "2. b",
    "",
    "11-22-33 INSPECTION 001",
    "1. c",
    "11-22-33-100-001 PULIZIA",
    "1. d",
]


def test_a_ge_task_is_found_from_its_heading_to_the_next_task() -> None:
    assert find_task_in_text(LINES, "11-22-33 REPAIR 002") == (4, 9)
    assert find_task_in_text(LINES, "11-22-33  repair 002") == (4, 9)
    assert find_task_in_text(LINES, "11-22-33 INSPECTION 001") == (11, 12)
    assert find_task_in_text(LINES, "11-22-33-100-001") == (13, 14)


def test_missing_or_partial_codes_are_not_found() -> None:
    assert find_task_in_text(LINES, "11-22-33 REPAIR 003") is None
    assert find_task_in_text(LINES, "11-22-33 REPAIR 00") is None  # codice più corto
    assert find_task_in_text(LINES, "REPAIR") is None  # nessuna cifra
    assert find_task_in_text(LINES, "") is None
    # un codice di documento non è un task: non diventa un task di una riga
    assert find_task_in_text(["ABC12345 MANUALE", "testo"], "ABC12345") is None
    assert find_task_in_text(["BLEND 001", "testo"], "BLEND 001") is None


def test_the_longest_block_wins_when_the_code_opens_twice() -> None:
    lines = ["11-22-33 REPAIR 002", "a", "11-22-33 TESTING 001", "x", "11-22-33 REPAIR 002"]
    assert find_task_in_text(lines, "11-22-33 REPAIR 002") == (1, 2)


def _kb(tmp_path: Path, tasks: list[TaskLocation] | None = None) -> IndexedKnowledgeBase:
    path = tmp_path / "man.md"
    path.write_text("\n".join(LINES) + "\n", "utf-8")
    document = DocumentInfo(key="MAN_X_ch10", path=path, code="MAN-X", version="ch10")
    return IndexedKnowledgeBase("v", documents=[document], tasks=tasks or [])


def test_the_knowledge_base_falls_back_to_the_text(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    location = kb.find_task("MAN-X", "11-22-33 REPAIR 002")
    assert location is not None
    assert (location.manual_key, location.task, location.line_start, location.line_end) == (
        "MAN_X_ch10",
        "11-22-33 REPAIR 002",
        4,
        9,
    )
    assert kb.find_task("MAN-X", "11-22-33 REPAIR 003") is None
    assert kb.find_task("ALTRO", "11-22-33 REPAIR 002") is None


def test_the_index_wins_over_the_text(tmp_path: Path) -> None:
    document = _kb(tmp_path).find_manuals("MAN-X")[0]
    indexed = TaskLocation(
        manual_key=document.key,
        task="11-22-33 REPAIR 002",
        document=document,
        line_start=4,
        line_end=5,
    )
    kb = IndexedKnowledgeBase("v", documents=[document], tasks=[indexed])
    location = kb.find_task("MAN-X", "11-22-33 REPAIR 002")
    assert location is not None and location.line_end == 5
