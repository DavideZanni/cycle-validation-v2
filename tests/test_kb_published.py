"""Conoscenza pubblicata con puntatore (`current.json`) dal repo knowledge-index.

    knowledge/<programma>/current.json   {"format": 1, "version": "r1", "path": "v/r1/"}
    knowledge/<programma>/v/r1/...       la fotografia completa

Il servizio rilegge il puntatore a intervalli e passa alla nuova versione senza riavvio; una
validazione già partita resta sulla versione con cui è partita.
"""

import dataclasses
import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from ej200_fixtures import catalog_entries, text_objects
from kb_fixtures import EXAMPLE_KB, memory_knowledge
from support import example_cycle, make_deps, write_cycle_pdf

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.ej200 import DEFAULT_TEXT_PREFIX, Ej200Catalog, Ej200KnowledgeBase
from cycle_validation.kb.pointer import read_pointer
from cycle_validation.kb.port import MachineTagEntry
from cycle_validation.kb.published import PublishedKnowledgeBase
from cycle_validation.kb.snapshot import sync_snapshot
from cycle_validation.kb.stores import InMemoryObjectStore
from cycle_validation.pipeline import RunRequest, run_validation

CIVIL = "knowledge/civil/"
POINTER = CIVIL + "current.json"


def _pointer(version: str) -> dict[str, Any]:
    return {"format": 1, "version": version, "path": f"v/{version}/"}


def publish_example(
    store: InMemoryObjectStore, version: str, *, extra_tag: str | None = None
) -> None:
    """La knowledge base dell'esempio pubblicata come versione `version`."""
    for path in EXAMPLE_KB.rglob("*"):
        if path.is_file():
            data: Any = path.read_bytes()
            if path.name == "machine_tags.json" and extra_tag:
                data = [*json.loads(data), {"tag": extra_tag, "function": "Nuova"}]
            store.put(f"{CIVIL}v/{version}/{path.relative_to(EXAMPLE_KB).as_posix()}", data)
    store.put(POINTER, _pointer(version))


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class CountingStore(InMemoryObjectStore):
    def __init__(self) -> None:
        super().__init__()
        self.gets = 0

    def get_bytes(self, key: str) -> bytes:
        self.gets += 1
        return super().get_bytes(key)


# ---------------------------------------------------------------- puntatore


def test_read_pointer_gives_the_prefix_next_to_the_pointer() -> None:
    store = InMemoryObjectStore({POINTER: _pointer("r1")})
    pointer = read_pointer(store, POINTER)
    assert pointer.version == "r1"
    assert pointer.prefix == "knowledge/civil/v/r1/"


def test_missing_pointer_is_an_unavailable_source() -> None:
    with pytest.raises(SourceUnavailableError, match=r"current.json"):
        read_pointer(InMemoryObjectStore(), POINTER)


@pytest.mark.parametrize(
    "content",
    [
        b"{non json",
        {"format": 2, "version": "r1", "path": "v/r1/"},
        {"format": 1, "version": "", "path": "v/r1/"},
        {"format": 1, "version": "r1", "path": "../altro/"},
        {"format": 1, "version": "r1", "path": "/assoluto/"},
        {"format": 1, "version": "r1"},
    ],
)
def test_invalid_pointer_is_a_knowledge_error(content: Any) -> None:
    with pytest.raises(KnowledgeError, match="Puntatore"):
        read_pointer(InMemoryObjectStore({POINTER: content}), POINTER)


# ---------------------------------------------------------------- civile


def test_published_knowledge_answers_from_the_pointed_version(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path)
    kb.preload()

    assert kb.version == "r1"
    assert [d.key for d in kb.find_manuals("md72")] == ["MAN-DEMO-72"]
    location = kb.find_task("MAN-DEMO-72", "72-00-01-220-002")
    assert location is not None and (location.line_start, location.line_end) == (12, 15)
    assert kb.find_machine_tag("TM-1001") is not None
    assert kb.find_dr_recommendations("SN-DEMO-001")
    assert kb.stats()["task"] == 4


def test_a_new_version_is_picked_up_after_the_check_interval(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    clock = Clock()
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path, check_every_s=300, clock=clock)
    kb.preload()

    publish_example(store, "r2", extra_tag="TM-9999")
    clock.now = 299
    assert kb.version == "r1"
    assert kb.find_machine_tag("TM-9999") is None

    clock.now = 301
    assert kb.find_machine_tag("TM-9999") is not None
    assert kb.version == "r2"


def test_a_pinned_version_stays_readable_after_the_switch(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    clock = Clock()
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path, check_every_s=1, clock=clock)
    pinned = kb.current()
    location = pinned.find_task("MAN-DEMO-72", "72-00-01-110-001")
    assert location is not None

    publish_example(store, "r2", extra_tag="TM-9999")
    clock.now = 10
    assert kb.current().version == "r2"

    assert pinned.version == "r1"
    assert location.document.path.is_file()
    assert pinned.find_machine_tag("TM-9999") is None


def test_old_downloads_are_removed_but_the_last_three_kept(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    clock = Clock()
    publish_example(store, "r1")
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path, check_every_s=1, clock=clock)
    for number in range(2, 6):
        publish_example(store, f"r{number}")
        clock.now += 10
        assert kb.current().version == f"r{number}"

    assert len([path for path in tmp_path.iterdir() if path.is_dir()]) == 3


def test_a_failing_refresh_keeps_the_current_version(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    clock = Clock()
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path, check_every_s=1, clock=clock)
    kb.preload()

    store.put(POINTER, b"{rotto")
    clock.now = 10
    assert kb.version == "r1"

    # Nuova versione con un manifest non valido: si resta sulla precedente.
    store.put(f"{CIVIL}v/r2/manifest.json", b"{rotto")
    store.put(POINTER, _pointer("r2"))
    clock.now = 20
    assert kb.version == "r1"
    assert kb.find_manuals("MAN-DEMO-72")


def test_without_any_version_lookups_are_unavailable_and_preload_fails(tmp_path: Path) -> None:
    kb = PublishedKnowledgeBase(InMemoryObjectStore(), POINTER, tmp_path)
    with pytest.raises(SourceUnavailableError):
        kb.find_manuals("MAN-DEMO-72")
    with pytest.raises(KnowledgeError):
        kb.preload()


def test_a_restart_reuses_a_complete_download(tmp_path: Path) -> None:
    store = CountingStore()
    publish_example(store, "r1")
    PublishedKnowledgeBase(store, POINTER, tmp_path).preload()
    first = store.gets

    PublishedKnowledgeBase(store, POINTER, tmp_path).preload()

    assert store.gets - first == 1  # solo il puntatore


def test_an_interrupted_download_is_not_reused(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path)
    kb.preload()
    folder = next(path for path in tmp_path.iterdir() if path.is_dir())
    (folder / ".completo").unlink()
    (folder / "tasks.json").write_text("[]", encoding="utf-8")

    fresh = PublishedKnowledgeBase(store, POINTER, tmp_path)
    assert fresh.find_task("MAN-DEMO-72", "72-00-01-110-001") is not None


def test_readers_do_not_wait_for_a_slow_download(tmp_path: Path) -> None:
    started, release = threading.Event(), threading.Event()

    class SlowStore(InMemoryObjectStore):
        def get_bytes(self, key: str) -> bytes:
            if "/v/r2/" in key:
                started.set()
                release.wait(5)
            return super().get_bytes(key)

    store = SlowStore()
    publish_example(store, "r1")
    clock = Clock()
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path, check_every_s=1, clock=clock)
    kb.preload()
    publish_example(store, "r2")
    clock.now = 10

    refresher = threading.Thread(target=kb.current)
    refresher.start()
    assert started.wait(5)
    began = time.monotonic()
    assert kb.version == "r1"  # chi arriva durante il download usa la versione corrente
    assert time.monotonic() - began < 1
    release.set()
    refresher.join(5)
    assert kb.version == "r2"


def test_a_validation_uses_a_single_version(tmp_path: Path) -> None:
    pinned = memory_knowledge()

    class Switching:
        """Ogni accesso diretto risponde con una versione diversa: la validazione non deve
        passare di qui, ma dalla versione fissata con `current()` all'inizio."""

        calls = 0

        def current(self) -> Any:
            Switching.calls += 1
            return pinned

        def __getattr__(self, name: str) -> Any:
            raise AssertionError(f"accesso diretto a {name}")

    deps, _ = make_deps()
    deps = dataclasses.replace(deps, kb=Switching())  # type: ignore[arg-type]
    pdf = write_cycle_pdf(tmp_path / "ciclo.pdf", example_cycle())

    report = run_validation(RunRequest(pdf_path=pdf), deps, tmp_path / "run")

    assert Switching.calls == 1
    assert report.meta.knowledge_version == pinned.version


def test_a_validation_on_published_knowledge_reports_its_version(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    kb = PublishedKnowledgeBase(store, POINTER, tmp_path / "kb")
    deps, _ = make_deps()
    deps = dataclasses.replace(deps, kb=kb)
    pdf = write_cycle_pdf(tmp_path / "ciclo.pdf", example_cycle())

    report = run_validation(RunRequest(pdf_path=pdf), deps, tmp_path / "run")

    assert report.meta.knowledge_version == "r1"


# ---------------------------------------------------------------- download


def test_sync_downloads_in_parallel(tmp_path: Path) -> None:
    lock = threading.Lock()
    state = {"now": 0, "max": 0}

    class Tracking(InMemoryObjectStore):
        def get_bytes(self, key: str) -> bytes:
            with lock:
                state["now"] += 1
                state["max"] = max(state["max"], state["now"])
            time.sleep(0.02)
            with lock:
                state["now"] -= 1
            return super().get_bytes(key)

    store = Tracking({"p/manifest.json": b"{}", **{f"p/documents/{n}.md": b"x" for n in range(20)}})

    assert sync_snapshot(store, "p", tmp_path, workers=8) == 21
    assert state["max"] > 1
    assert len(list((tmp_path / "documents").iterdir())) == 20


# ---------------------------------------------------------------- EJ200

EJ200 = "knowledge/ej200/"


def publish_ej200(store: InMemoryObjectStore, version: str, entries: list[dict[str, Any]]) -> None:
    store.put(f"{EJ200}v/{version}/catalog.json", entries)
    for key, text in text_objects().items():
        relative = key.removeprefix(DEFAULT_TEXT_PREFIX)
        store.put(f"{EJ200}v/{version}/text/{relative}", text)
    store.put(EJ200 + "current.json", _pointer(version))


def test_ej200_catalog_and_texts_come_from_the_pointed_version(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_ej200(store, "r1", catalog_entries())
    clock = Clock()
    catalog = Ej200Catalog(store, pointer_key=EJ200 + "current.json", ttl_s=300, clock=clock)
    kb = Ej200KnowledgeBase(
        "fisso",
        catalog,
        tmp_path,
        store,
        tags=lambda: [MachineTagEntry(tag="TM-1001", function="Banco")],
    )
    kb.preload()

    assert kb.version == "r1"
    latest = next(d for d in kb.find_manuals("RN-100") if d.version == "2")
    assert "Pulire la pala con solvente tipo A." in latest.path.read_text(encoding="utf-8")
    assert kb.find_machine_tag("tm-1001") is not None
    assert kb.stats()["targhe"] == 1

    changed = [dict(entry, title="nuovo") for entry in catalog_entries()]
    publish_ej200(store, "r2", changed)
    store.delete(f"{EJ200}v/r1/catalog.json")
    clock.now = 301
    assert kb.version == "r2"
    assert {entry.title for entry in catalog.entries()} == {"nuovo"}


def test_ej200_text_of_an_entry_comes_from_the_version_of_its_catalog(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_ej200(store, "r1", catalog_entries())
    catalog = Ej200Catalog(store, pointer_key=EJ200 + "current.json")
    (entry,) = [e for e in catalog.find("RN-100") if e.issue == "2"]
    assert entry.text_prefix == f"{EJ200}v/r1/text/"


def test_ej200_without_pointer_keeps_the_fixed_keys(tmp_path: Path) -> None:
    store = InMemoryObjectStore({"cat.json": catalog_entries()})
    catalog = Ej200Catalog(store, key="cat.json")
    assert catalog.version is None
    assert all(entry.text_prefix is None for entry in catalog.entries())


def test_ej200_machine_tags_follow_the_published_civil_knowledge(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    publish_ej200(store, "e1", catalog_entries())
    clock = Clock()
    civil = PublishedKnowledgeBase(store, POINTER, tmp_path / "c", check_every_s=1, clock=clock)
    ej = Ej200KnowledgeBase(
        "x",
        Ej200Catalog(store, pointer_key=EJ200 + "current.json"),
        tmp_path / "e",
        store,
        tags=civil.machine_tags,
    )
    ej.preload()
    assert ej.find_machine_tag("TM-1001") is not None
    assert ej.find_machine_tag("TM-9999") is None

    publish_example(store, "r2", extra_tag="TM-9999")
    clock.now = 10
    assert ej.find_machine_tag("TM-9999") is not None
