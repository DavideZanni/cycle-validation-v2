"""Suite di contratto della porta KnowledgeBase.

Ogni implementazione, alimentata con il contenuto di examples/sintetico/knowledge,
deve superare questi test. Per un adattatore nuovo: aggiungere un caso a `KNOWLEDGE`.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from kb_fixtures import EXAMPLE_KB, memory_knowledge, remote_knowledge

from cycle_validation.kb.documents import page_at, read_lines
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.port import KnowledgeBase

KNOWLEDGE: dict[str, Callable[[Path], KnowledgeBase]] = {
    "cartella_locale": lambda workdir: load_local_knowledge(EXAMPLE_KB),
    "in_memoria": lambda workdir: memory_knowledge(),
    "remota_snapshot_s3": remote_knowledge,
}


@pytest.fixture(params=sorted(KNOWLEDGE))
def kb(request: pytest.FixtureRequest, tmp_path: Path) -> KnowledgeBase:
    return KNOWLEDGE[request.param](tmp_path)


def test_version(kb: KnowledgeBase) -> None:
    assert kb.version == "sintetico-2026-11"


@pytest.mark.parametrize("name", ["MAN-DEMO-72", "man-demo-72", "Manuale Demo 72", " md72 "])
def test_manual_by_key_or_alias(kb: KnowledgeBase, name: str) -> None:
    documents = kb.find_manuals(name)
    assert [document.key for document in documents] == ["MAN-DEMO-72"]
    assert documents[0].version == "Rev. 12"
    assert documents[0].path.is_file()


def test_unknown_manual(kb: KnowledgeBase) -> None:
    assert kb.find_manuals("MAN-DEMO-99") == []


def test_task_location(kb: KnowledgeBase) -> None:
    location = kb.find_task("md72", "72-00-01-350-003")
    assert location is not None
    assert location.manual_key == "MAN-DEMO-72"
    assert location.n_lines == 4
    first = read_lines(location.document.path)[location.line_start - 1]
    assert "TASK 72-00-01-350-003" in first or "Rettificare la sede" in first
    assert page_at(location.document.path, location.line_start) == 2


def test_task_is_searched_only_in_its_manual(kb: KnowledgeBase) -> None:
    assert kb.find_task("MAN-DEMO-75", "72-00-01-350-003") is None
    assert kb.find_task("MAN-DEMO-72", "72-00-01-999-009") is None
    assert kb.find_task("MAN-DEMO-99", "72-00-01-350-003") is None


def test_machine_tag(kb: KnowledgeBase) -> None:
    entry = kb.find_machine_tag("tm-2002")
    assert entry is not None and entry.function == "Rettificatrice per interni"
    assert kb.find_machine_tag("TM-9999") is None


def test_process_sheet(kb: KnowledgeBase) -> None:
    entry = kb.find_process_sheet("sp-0101")
    assert entry is not None
    assert (entry.edition, entry.engine_families) == ("B", ("GENX",))
    assert kb.find_process_sheet("SP-9999") is None


def test_dr_recommendations(kb: KnowledgeBase) -> None:
    found = kb.find_dr_recommendations("sn-demo-001")
    assert [item.reference for item in found] == ["DR-DEMO-01", "DR-DEMO-02"]
    assert found[0].tasks == ("72-00-01-350-003",)
    assert kb.find_dr_recommendations("SN-ASSENTE") == []


def test_stats(kb: KnowledgeBase) -> None:
    stats = kb.stats()
    assert {key: stats[key] for key in ("targhe", "schede", "recommendation_dr")} == {
        "targhe": 3,
        "schede": 2,
        "recommendation_dr": 3,
    }


def test_task_by_document_kind_needs_a_document_of_that_kind(kb: KnowledgeBase) -> None:
    # la conoscenza sintetica non ha documenti con `kind`: nessun task per tipo
    assert kb.find_task_in_kind("SPM", "72-00-01-350-003") is None
