import json
import shutil
from pathlib import Path

import pytest
from kb_fixtures import DOC_72, EXAMPLE_DIR, EXAMPLE_KB

from cycle_validation.errors import ConfigError, KnowledgeError, SourceUnavailableError
from cycle_validation.kb.documents import numbered_lines, page_at, read_lines
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.services.machines import (
    LazyMachineRegistry,
    StaticMachineRegistry,
    UnavailableMachineRegistry,
    load_machine_registry,
)


@pytest.fixture
def knowledge(tmp_path: Path) -> Path:
    target = tmp_path / "knowledge"
    shutil.copytree(EXAMPLE_KB, target)
    return target


def _rewrite(path: Path, content: object) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


def test_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeError, match="non trovata"):
        load_local_knowledge(tmp_path / "assente")


def test_missing_manifest(knowledge: Path) -> None:
    (knowledge / "manifest.json").unlink()
    with pytest.raises(KnowledgeError, match=r"manifest\.json non trovato"):
        load_local_knowledge(knowledge)


def test_invalid_json(knowledge: Path) -> None:
    (knowledge / "tasks.json").write_text("[{", encoding="utf-8")
    with pytest.raises(KnowledgeError, match=r"JSON non valido.*tasks\.json"):
        load_local_knowledge(knowledge)


def test_invalid_row_names_the_field(knowledge: Path) -> None:
    _rewrite(knowledge / "machine_tags.json", [{"targa": "TM-1"}])
    with pytest.raises(KnowledgeError, match=r"machine_tags\.json.*tag"):
        load_local_knowledge(knowledge)


def test_missing_document_file(knowledge: Path) -> None:
    (knowledge / "documents" / "MAN-DEMO-75.md").unlink()
    with pytest.raises(KnowledgeError, match="MAN-DEMO-75"):
        load_local_knowledge(knowledge)


def test_document_outside_directory(knowledge: Path) -> None:
    manifest = json.loads((knowledge / "manifest.json").read_text(encoding="utf-8"))
    manifest["documents"][0]["file"] = "../fuori.md"
    _rewrite(knowledge / "manifest.json", manifest)
    with pytest.raises(KnowledgeError, match="esce dalla cartella"):
        load_local_knowledge(knowledge)


def test_duplicate_document_key(knowledge: Path) -> None:
    manifest = json.loads((knowledge / "manifest.json").read_text(encoding="utf-8"))
    manifest["documents"].append(manifest["documents"][0])
    _rewrite(knowledge / "manifest.json", manifest)
    with pytest.raises(KnowledgeError, match="duplicata"):
        load_local_knowledge(knowledge)


def test_task_range_outside_file(knowledge: Path) -> None:
    _rewrite(
        knowledge / "tasks.json",
        [{"manual": "MAN-DEMO-75", "task": "T", "line_start": 5, "line_end": 500}],
    )
    with pytest.raises(KnowledgeError, match="fuori dal file"):
        load_local_knowledge(knowledge)


def test_task_of_unknown_manual(knowledge: Path) -> None:
    _rewrite(
        knowledge / "tasks.json",
        [{"manual": "ASSENTE", "task": "T", "line_start": 1, "line_end": 2}],
    )
    with pytest.raises(KnowledgeError, match="non è nel manifest"):
        load_local_knowledge(knowledge)


def test_optional_files_may_be_missing(knowledge: Path) -> None:
    for name in ("tasks.json", "machine_tags.json", "process_sheets.json"):
        (knowledge / name).unlink()
    (knowledge / "dr_recommendations.json").unlink()
    kb = load_local_knowledge(knowledge)
    assert kb.stats()["documenti"] == 2
    assert kb.stats()["task"] == 0


def test_page_at_follows_markers() -> None:
    assert page_at(DOC_72.path, 1) == 1
    assert page_at(DOC_72.path, 7) == 1
    assert page_at(DOC_72.path, 18) == 2


def test_page_is_unknown_without_marker(tmp_path: Path) -> None:
    path = tmp_path / "senza.md"
    path.write_text("riga uno\nriga due\n", encoding="utf-8")
    assert page_at(path, 2) is None


def test_numbered_lines_use_file_numbers() -> None:
    assert numbered_lines(DOC_72.path, 18, 19) == [
        "18: 1. Rettificare la sede fino al diametro 45,00 mm +0,02/-0,00.",
        "19: 2. Rugosità massima Ra 0,8.",
    ]


def test_unreadable_document_is_source_unavailable(tmp_path: Path) -> None:
    with pytest.raises(SourceUnavailableError):
        read_lines(tmp_path / "assente.md")


def test_static_registry_ignores_case_and_spaces() -> None:
    registry = StaticMachineRegistry(["TM-1001"])
    assert registry.is_active(" tm-1001 ")
    assert not registry.is_active("TM-3003")


def test_registry_from_example_file() -> None:
    registry = load_machine_registry(EXAMPLE_DIR / "macchine_attive.json")
    assert registry.is_active("TM-2002") and not registry.is_active("TM-3003")


def test_registry_accepts_object_form(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text('{"active": ["A-1"]}', encoding="utf-8")
    assert load_machine_registry(path).is_active("a-1")


def test_registry_rejects_wrong_shape(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text('{"attive": 3}', encoding="utf-8")
    with pytest.raises(ConfigError, match="lista di targhe"):
        load_machine_registry(path)


def test_registry_not_configured_is_unavailable() -> None:
    with pytest.raises(SourceUnavailableError, match="non configurato"):
        load_machine_registry(None).is_active("TM-1001")
    with pytest.raises(SourceUnavailableError):
        UnavailableMachineRegistry("giù").is_active("x")


def test_lazy_registry_loads_once_and_retries_after_failure() -> None:
    calls: list[int] = []

    def fetch() -> list[str]:
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionError("rete")
        return ["TM-1"]

    registry = LazyMachineRegistry(fetch)
    with pytest.raises(SourceUnavailableError, match="ConnectionError"):
        registry.is_active("TM-1")
    assert registry.is_active("TM-1")
    assert not registry.is_active("TM-2")
    assert len(calls) == 2
