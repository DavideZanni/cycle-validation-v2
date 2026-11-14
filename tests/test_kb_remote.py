import json
from pathlib import Path
from typing import Any

import pytest
from kb_fixtures import EXAMPLE_KB, example_chunks, example_store, remote_knowledge

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.export import export_local_knowledge
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.manuals import ChunkSchema, IndexedManualSource
from cycle_validation.kb.remote import RemoteKnowledgeBase
from cycle_validation.kb.stores import (
    InMemoryObjectStore,
    InMemorySearchIndex,
    LocalDirObjectStore,
    ObjectNotFoundError,
    OpenSearchIndex,
    S3ObjectStore,
    load_jsonl_index,
)
from cycle_validation.kb.structured import FieldMap, StructuredLayout, load_structured


class FakeS3Client:
    def __init__(self, objects: dict[str, bytes], page_size: int = 2) -> None:
        self.objects = objects
        self.page_size = page_size

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self.objects:
            error = Exception("NoSuchKey")
            error.response = {"Error": {"Code": "NoSuchKey"}}  # type: ignore[attr-defined]
            raise error
        data = self.objects[Key]
        return {"Body": type("B", (), {"read": lambda self: data})()}

    def list_objects_v2(self, **args: Any) -> dict[str, Any]:
        keys = sorted(k for k in self.objects if k.startswith(args["Prefix"]))
        start = int(args.get("ContinuationToken", 0))
        page = keys[start : start + self.page_size]
        more = start + self.page_size < len(keys)
        out: dict[str, Any] = {"Contents": [{"Key": k} for k in page], "IsTruncated": more}
        if more:
            out["NextContinuationToken"] = str(start + self.page_size)
        return out


def test_s3_store_reads_lists_with_pagination_and_maps_missing() -> None:
    client = FakeS3Client({f"p/{i}.json": b"[]" for i in range(5)} | {"other": b"x"})
    store = S3ObjectStore(client, "bucket")
    assert store.list_keys("p/") == [f"p/{i}.json" for i in range(5)]
    assert store.get_bytes("p/1.json") == b"[]"
    with pytest.raises(ObjectNotFoundError):
        store.get_bytes("p/9.json")


def test_s3_store_failure_is_source_unavailable() -> None:
    class Down:
        def get_object(self, **_: Any) -> Any:
            raise TimeoutError

        def list_objects_v2(self, **_: Any) -> Any:
            raise TimeoutError

    store = S3ObjectStore(Down(), "b")
    with pytest.raises(SourceUnavailableError):
        store.get_bytes("k")
    with pytest.raises(SourceUnavailableError):
        store.list_keys("k")


def test_opensearch_index_builds_exact_term_filters() -> None:
    sent: dict[str, Any] = {}

    class Client:
        def search(self, *, index: str, body: dict[str, Any]) -> dict[str, Any]:
            sent.update(index=index, body=body)
            return {"hits": {"hits": [{"_source": {"manual": "M"}}]}}

    index = OpenSearchIndex(Client(), "manuali", sort_field="chunk_index")
    assert index.search({"manual": "M", "task": "T"}, size=5) == [{"manual": "M"}]
    assert sent["index"] == "manuali"
    assert sent["body"]["query"]["bool"]["filter"] == [
        {"term": {"manual": "M"}},
        {"term": {"task": "T"}},
    ]
    assert sent["body"]["size"] == 5 and sent["body"]["sort"] == [{"chunk_index": "asc"}]


def test_opensearch_failure_is_source_unavailable() -> None:
    class Client:
        def search(self, **_: Any) -> Any:
            raise ConnectionError

    with pytest.raises(SourceUnavailableError):
        OpenSearchIndex(Client(), "i").search({"a": "b"})


def test_local_dir_store_mirrors_keys_and_blocks_escape(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.json").write_text("[]", encoding="utf-8")
    store = LocalDirObjectStore(tmp_path)
    assert store.list_keys("a/") == ["a/x.json"]
    assert store.get_bytes("a/x.json") == b"[]"
    with pytest.raises(ObjectNotFoundError):
        store.get_bytes("../x")
    with pytest.raises(ObjectNotFoundError):
        store.get_bytes("a/nope.json")


def test_structured_loading_accepts_prefixes_wrappers_and_aliases() -> None:
    store = InMemoryObjectStore(
        {
            "TM/1.json": {"items": [{"targa": "T-1", "funzione": "Forno"}]},
            "TM/2.json": [{"machine_tag": "T-2"}],
            "SP/a.json": [{"scheda": "S-1", "engines": "GENX, LEAP"}],
            "DR/a.json": [
                {
                    "sn": "SN1",
                    "repair_conditions": "1,2",
                    "disposition": "Repair",
                    "task_codes": "T1",
                }
            ],
        }
    )
    data = load_structured(store, StructuredLayout(tm="TM/", sp="SP/", dr="DR/"))
    assert [t.tag for t in data.machine_tags] == ["T-1", "T-2"]
    assert data.machine_tags[0].function == "Forno"
    assert data.process_sheets[0].engine_families == ("GENX", "LEAP")
    assert data.dr_recommendations[0].conditions == (1, 2)
    assert data.dr_recommendations[0].tasks == ("T1",)


def test_custom_field_map() -> None:
    store = InMemoryObjectStore({"tm.json": [{"mch": "Z"}], "sp.json": [{"c": "S"}], "dr.json": []})
    layout = StructuredLayout(tm="tm.json", sp="sp.json", dr="dr.json")
    layout = StructuredLayout(
        tm="tm.json",
        sp="sp.json",
        dr="dr.json",
        fields=FieldMap(tag=("mch",), sheet_code=("c",)),
    )
    assert load_structured(store, layout).machine_tags[0].tag == "Z"


@pytest.mark.parametrize(
    ("objects", "message"),
    [
        ({}, "TM"),
        ({"structured/TM/a.json": "{non json"}, "JSON non valido"),
        ({"structured/TM/a.json": [{"x": 1}]}, "senza targa"),
        ({"structured/TM/a.json": "42"}, "lista di oggetti"),
    ],
)
def test_structured_defects_are_explicit(objects: dict[str, Any], message: str) -> None:
    with pytest.raises(KnowledgeError, match=message):
        load_structured(InMemoryObjectStore(objects), StructuredLayout())


def test_preload_fails_but_lookups_during_checks_are_warnings(tmp_path: Path) -> None:
    manuals = IndexedManualSource(InMemorySearchIndex([]), tmp_path)
    kb = RemoteKnowledgeBase("v", InMemoryObjectStore(), manuals)
    with pytest.raises(KnowledgeError):
        kb.preload()
    with pytest.raises(SourceUnavailableError):
        kb.find_machine_tag("TM-1001")


def test_search_is_exact_and_cached(tmp_path: Path) -> None:
    index = InMemorySearchIndex(example_chunks())
    source = IndexedManualSource(index, tmp_path)
    assert source.find_task("MAN-DEMO-72", "72-00-01-350-003") is not None
    assert source.find_task("man-demo-72", "72-00-01-350-003") is not None
    assert index.queries == [{"manual": "MAN-DEMO-72", "task": "72-00-01-350-003"}]


def test_task_document_has_unique_key_and_page_markers(tmp_path: Path) -> None:
    source = IndexedManualSource(InMemorySearchIndex(example_chunks()), tmp_path)
    one = source.find_task("MAN-DEMO-72", "72-00-01-110-001")
    two = source.find_task("MAN-DEMO-72", "72-00-01-350-003")
    assert one and two and one.document.key != two.document.key
    assert one.document.code == "MAN-DEMO-72"
    assert one.document.path.read_text(encoding="utf-8").startswith("<!-- page 1 -->")


def test_custom_schema_and_multiple_chunks_in_order(tmp_path: Path) -> None:
    schema = ChunkSchema(manual="doc", task="tc", version="rev", page="pg", order="n", text="body")
    chunks = [
        {"doc": "M", "tc": "T", "rev": "A", "pg": 2, "n": 2, "body": "seconda\nriga"},
        {"doc": "M", "tc": "T", "rev": "A", "pg": 1, "n": 1, "body": "prima"},
    ]
    source = IndexedManualSource(InMemorySearchIndex(chunks), tmp_path, schema)
    location = source.find_task("M", "T")
    assert location is not None
    text = location.document.path.read_text(encoding="utf-8").splitlines()
    assert text == ["<!-- page 1 -->", "prima", "<!-- page 2 -->", "seconda", "riga"]
    assert (location.line_start, location.line_end) == (2, 5)


def test_fallback_answers_when_exact_search_finds_nothing(tmp_path: Path) -> None:
    class Fallback:
        calls = 0

        def find_chunks(self, manual: str, task: str) -> list[dict[str, Any]]:
            self.calls += 1
            return [{"manual": manual, "task": task, "page": 1, "text": "dal ripiego"}]

    fallback = Fallback()
    source = IndexedManualSource(InMemorySearchIndex([]), tmp_path, fallback=fallback)
    location = source.find_task("M", "T")
    assert location is not None and fallback.calls == 1
    assert "dal ripiego" in location.document.path.read_text(encoding="utf-8")


def test_unreachable_index_is_source_unavailable(tmp_path: Path) -> None:
    class Down:
        def search(self, filters: Any, *, size: int = 1) -> Any:
            raise SourceUnavailableError("giù")

    source = IndexedManualSource(Down(), tmp_path)
    with pytest.raises(SourceUnavailableError):
        source.find_manuals("M")


def test_export_roundtrip_gives_the_same_answers(tmp_path: Path) -> None:
    remote = remote_knowledge(tmp_path / "work")
    out = tmp_path / "export"
    report = export_local_knowledge(
        remote,
        out,
        [
            ("MAN-DEMO-72", ["72-00-01-110-001", "72-00-01-220-002", "72-00-01-350-003", "x"]),
            ("MAN-DEMO-75", ["75-10-02-400-001"]),
        ],
    )
    assert (report.manuals, report.tasks, report.missing) == (2, 4, ["MAN-DEMO-72 / x"])
    local = load_local_knowledge(out)
    assert local.version == "sintetico-2026-11"
    assert local.stats() == {
        "documenti": 2,
        "task": 4,
        "targhe": 3,
        "schede": 2,
        "recommendation_dr": 3,
    }
    for manual, task in [("MAN-DEMO-72", "72-00-01-350-003"), ("MAN-DEMO-75", "75-10-02-400-001")]:
        a, b = remote.find_task(manual, task), local.find_task(manual, task)
        assert a is not None and b is not None
        assert a.n_lines == b.n_lines
    assert local.find_dr_recommendations("SN-DEMO-001")[0].tasks == ("72-00-01-350-003",)


def test_jsonl_index(tmp_path: Path) -> None:
    path = tmp_path / "chunks.jsonl"
    path.write_text("\n".join(json.dumps(c) for c in example_chunks()), encoding="utf-8")
    assert load_jsonl_index(path).search({"manual": "MAN-DEMO-75"})
    with pytest.raises(SourceUnavailableError):
        load_jsonl_index(tmp_path / "manca.jsonl")


def test_example_store_fixture_is_loadable() -> None:
    assert example_store().list_keys("structured/") and EXAMPLE_KB.is_dir()


# --- metadati dell'indice di forma non garantita --------------------------------------------


def _task_lines(tmp_path: Path, chunks: list[dict[str, Any]]) -> list[str]:
    location = IndexedManualSource(InMemorySearchIndex(chunks), tmp_path).find_task("M", "T")
    assert location is not None
    return location.document.path.read_text(encoding="utf-8").splitlines()


def test_pages_stored_as_text_give_one_marker_per_page(tmp_path: Path) -> None:
    chunks = [
        {"manual": "M", "task": "T", "page": "1", "chunk_index": 0, "text": "uno"},
        {"manual": "M", "task": "T", "page": "1", "chunk_index": 1, "text": "due"},
        {"manual": "M", "task": "T", "page": "2", "chunk_index": 2, "text": "tre"},
    ]
    assert _task_lines(tmp_path, chunks) == [
        "<!-- page 1 -->",
        "uno",
        "due",
        "<!-- page 2 -->",
        "tre",
    ]


def test_a_page_that_is_not_a_number_does_not_stop_the_lookup(tmp_path: Path) -> None:
    chunks = [
        {"manual": "M", "task": "T", "page": 4, "chunk_index": 0, "text": "uno"},
        {"manual": "M", "task": "T", "page": "A-3", "chunk_index": 1, "text": "due"},
    ]
    assert _task_lines(tmp_path, chunks) == ["<!-- page 4 -->", "uno", "due"]


def test_chunk_order_stored_as_text_is_still_numeric(tmp_path: Path) -> None:
    chunks = [
        {"manual": "M", "task": "T", "page": 1, "chunk_index": "10", "text": "dopo"},
        {"manual": "M", "task": "T", "page": 1, "chunk_index": "9", "text": "prima"},
    ]
    assert _task_lines(tmp_path, chunks) == ["<!-- page 1 -->", "prima", "dopo"]


def test_a_chunk_without_text_adds_no_line_and_the_task_starts_at_its_first_text(
    tmp_path: Path,
) -> None:
    chunks = [
        {"manual": "M", "task": "T", "page": 1, "chunk_index": 0, "text": None},
        {"manual": "M", "task": "T", "page": 2, "chunk_index": 1, "text": "testo"},
    ]
    source = IndexedManualSource(InMemorySearchIndex(chunks), tmp_path)
    location = source.find_task("M", "T")
    assert location is not None
    lines = location.document.path.read_text(encoding="utf-8").splitlines()
    assert "None" not in lines
    assert lines[location.line_start - 1] == "testo"


def test_tasks_whose_names_differ_only_by_punctuation_keep_separate_files(tmp_path: Path) -> None:
    # i due nomi diventavano lo stesso file: il secondo riscriveva il testo del primo
    chunks = [
        {"manual": "M", "task": "T/1", "page": 1, "chunk_index": 0, "text": "testo del primo"},
        {"manual": "M", "task": "T 1", "page": 1, "chunk_index": 0, "text": "testo del secondo"},
    ]
    source = IndexedManualSource(InMemorySearchIndex(chunks), tmp_path)
    first = source.find_task("M", "T/1")
    second = source.find_task("M", "T 1")
    assert first is not None and second is not None
    assert "testo del primo" in first.document.path.read_text(encoding="utf-8")
    assert "testo del secondo" in second.document.path.read_text(encoding="utf-8")


def test_export_keeps_manuals_whose_names_differ_only_by_punctuation_apart(tmp_path: Path) -> None:
    chunks = [
        {"manual": "M/1", "task": "T", "page": 1, "chunk_index": 0, "text": "testo del primo"},
        {"manual": "M 1", "task": "T", "page": 1, "chunk_index": 0, "text": "testo del secondo"},
    ]
    manuals = IndexedManualSource(InMemorySearchIndex(chunks), tmp_path / "work")
    remote = RemoteKnowledgeBase("v", example_store(), manuals)
    out = tmp_path / "export"
    export_local_knowledge(remote, out, [("M/1", ["T"]), ("M 1", ["T"])])
    local = load_local_knowledge(out)
    first, second = local.find_task("M/1", "T"), local.find_task("M 1", "T")
    assert first is not None and second is not None
    assert "testo del primo" in first.document.path.read_text(encoding="utf-8")
    assert "testo del secondo" in second.document.path.read_text(encoding="utf-8")


def test_lookups_of_different_tasks_do_not_wait_for_each_other(tmp_path: Path) -> None:
    import threading

    inside = threading.Barrier(2)
    met: list[bool] = []

    class SlowIndex(InMemorySearchIndex):
        def search(self, filters: Any, *, size: int = 1000) -> list[dict[str, Any]]:
            try:
                inside.wait(2)  # si esce solo se anche l'altra ricerca è arrivata fin qui
                met.append(True)
            except threading.BrokenBarrierError:
                met.append(False)
            return super().search(filters, size=size)

    source = IndexedManualSource(SlowIndex(example_chunks()), tmp_path)
    tasks = ["72-00-01-110-001", "72-00-01-350-003"]
    workers = [
        threading.Thread(target=source.find_task, args=("MAN-DEMO-72", task)) for task in tasks
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(10)
    assert met == [True, True]


def test_concurrent_lookups_of_the_same_task_query_the_index_once(tmp_path: Path) -> None:
    import threading

    started, release = threading.Event(), threading.Event()

    class SlowIndex(InMemorySearchIndex):
        def search(self, filters: Any, *, size: int = 1000) -> list[dict[str, Any]]:
            hits = super().search(filters, size=size)
            started.set()
            release.wait(5)
            return hits

    index = SlowIndex(example_chunks())
    source = IndexedManualSource(index, tmp_path)
    workers = [
        threading.Thread(target=source.find_task, args=("MAN-DEMO-72", "72-00-01-110-001"))
        for _ in range(2)
    ]
    workers[0].start()
    assert started.wait(5)
    workers[1].start()
    workers[1].join(0.3)
    release.set()
    for worker in workers:
        worker.join(5)
    assert len(index.queries) == 1


def test_store_write_failures_are_source_unavailable_without_the_cause_text(
    tmp_path: Path,
) -> None:
    class Down:
        def put_object(self, **_: Any) -> Any:
            raise RuntimeError("contenuto riservato")

        def delete_object(self, **_: Any) -> Any:
            raise RuntimeError("contenuto riservato")

    store = S3ObjectStore(Down(), "b")
    for action in (lambda: store.put_bytes("k", b"x"), lambda: store.delete("k")):
        with pytest.raises(SourceUnavailableError) as caught:
            action()
        assert "riservato" not in str(caught.value) and "RuntimeError" in str(caught.value)

    (tmp_path / "occupato").write_text("un file dove servirebbe una cartella", encoding="utf-8")
    local = LocalDirObjectStore(tmp_path)
    with pytest.raises(SourceUnavailableError):
        local.put_bytes("occupato/oggetto.json", b"{}")
