"""Testo dei manuali da una cartella di S3 nel formato locale (manifest, documents, tasks).

Sostituisce l'indice di ricerca: l'ingestion pubblica markdown e JSON, qui si scaricano
in una cartella di lavoro e si leggono con lo stesso lettore della knowledge base locale.
"""

import threading
from pathlib import Path

import pytest
from kb_fixtures import EXAMPLE_KB, snapshot_store

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.snapshot import SnapshotManualSource, sync_snapshot
from cycle_validation.kb.stores import InMemoryObjectStore, ObjectStore

PREFIX = "kb/sintetico"


def test_sync_copies_every_object_under_the_prefix(tmp_path: Path) -> None:
    store = snapshot_store()
    store.put("kb/altro/manifest.json", b"{}")
    count = sync_snapshot(store, PREFIX, tmp_path)
    assert count == len(list(EXAMPLE_KB.rglob("*.*")))
    assert (tmp_path / "manifest.json").is_file()
    assert not (tmp_path / "altro").exists()


def test_sync_without_manifest_is_a_knowledge_error(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeError, match=r"manifest.json"):
        sync_snapshot(InMemoryObjectStore({"kb/sintetico/documents/x.md": b"x"}), PREFIX, tmp_path)


def test_sync_refuses_keys_that_escape_the_folder(tmp_path: Path) -> None:
    store = InMemoryObjectStore({f"{PREFIX}/manifest.json": b"{}", f"{PREFIX}/../fuori.txt": b"x"})
    with pytest.raises(KnowledgeError, match="fuori"):
        sync_snapshot(store, PREFIX, tmp_path / "work")


def test_find_manual_by_key_and_alias(tmp_path: Path) -> None:
    source = SnapshotManualSource(snapshot_store(), PREFIX, tmp_path)
    for name in ("MAN-DEMO-72", "md72", " Manuale Demo 72 "):
        documents = source.find_manuals(name)
        assert [d.key for d in documents] == ["MAN-DEMO-72"]
        assert documents[0].version == "Rev. 12"
        assert documents[0].path.is_file()
    assert source.find_manuals("MAN-DEMO-99") == []


def test_find_task_gives_lines_of_the_downloaded_file(tmp_path: Path) -> None:
    source = SnapshotManualSource(snapshot_store(), PREFIX, tmp_path)
    location = source.find_task("md72", "72-00-01-350-003")
    assert location is not None and location.n_lines == 4
    assert "Rettificare la sede" in " ".join(
        read_lines(location.document.path)[location.line_start - 1 : location.line_end]
    )
    assert source.find_task("MAN-DEMO-75", "72-00-01-350-003") is None


def test_snapshot_is_downloaded_once_even_with_concurrent_calls(tmp_path: Path) -> None:
    inner = snapshot_store()
    reads = 0
    lock = threading.Lock()

    class Counting:
        def get_bytes(self, key: str) -> bytes:
            nonlocal reads
            with lock:
                reads += 1
            return inner.get_bytes(key)

        def list_keys(self, prefix: str) -> list[str]:
            return inner.list_keys(prefix)

    store: ObjectStore = Counting()
    source = SnapshotManualSource(store, PREFIX, tmp_path)
    threads = [
        threading.Thread(target=source.find_task, args=("md72", "72-00-01-350-003"))
        for _ in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert reads == len(list(EXAMPLE_KB.rglob("*.*")))


def test_unreachable_store_is_source_unavailable_during_a_check(tmp_path: Path) -> None:
    class Down:
        def get_bytes(self, key: str) -> bytes:
            raise SourceUnavailableError("S3 non raggiungibile")

        def list_keys(self, prefix: str) -> list[str]:
            raise SourceUnavailableError("S3 non raggiungibile")

    source = SnapshotManualSource(Down(), PREFIX, tmp_path)
    with pytest.raises(SourceUnavailableError):
        source.find_manuals("MAN-DEMO-72")


def test_broken_content_is_source_unavailable_during_a_check(tmp_path: Path) -> None:
    store = InMemoryObjectStore({f"{PREFIX}/manifest.json": b"non json"})
    source = SnapshotManualSource(store, PREFIX, tmp_path)
    with pytest.raises(SourceUnavailableError, match=r"manifest.json"):
        source.find_task("M", "T")


def test_preload_reports_broken_content_as_knowledge_error(tmp_path: Path) -> None:
    store = InMemoryObjectStore({f"{PREFIX}/manifest.json": b"non json"})
    with pytest.raises(KnowledgeError):
        SnapshotManualSource(store, PREFIX, tmp_path).preload()
