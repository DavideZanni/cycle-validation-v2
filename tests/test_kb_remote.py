import json
from pathlib import Path
from typing import Any

import pytest
from kb_fixtures import EXAMPLE_KB, example_store, snapshot_store

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.remote import RemoteKnowledgeBase
from cycle_validation.kb.snapshot import SnapshotManualSource
from cycle_validation.kb.stores import (
    InMemoryObjectStore,
    LocalDirObjectStore,
    ObjectNotFoundError,
    S3ObjectStore,
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
    manuals = SnapshotManualSource(InMemoryObjectStore(), "kb/vuoto", tmp_path)
    kb = RemoteKnowledgeBase("v", InMemoryObjectStore(), manuals)
    with pytest.raises(KnowledgeError):
        kb.preload()
    with pytest.raises(SourceUnavailableError):
        kb.find_machine_tag("TM-1001")


def test_documents_of_kind_come_from_the_manual_snapshot(tmp_path: Path) -> None:
    # I documenti SPM servono al report dei manuali e ai codici sbagliati: la conoscenza
    # remota li prende dallo snapshot dei manuali, come quella locale.
    store = snapshot_store()
    manifest = json.loads(store.get_bytes("kb/sintetico/manifest.json"))
    manifest["documents"][1]["kind"] = "SPM"
    store.put("kb/sintetico/manifest.json", manifest)
    kb = RemoteKnowledgeBase(
        "v", example_store(), SnapshotManualSource(store, "kb/sintetico", tmp_path)
    )
    assert [document.key for document in kb.documents_of_kind("spm")] == ["MAN-DEMO-75"]
    assert kb.documents_of_kind("RN") == []


def test_example_store_fixture_is_loadable() -> None:
    assert example_store().list_keys("structured/") and EXAMPLE_KB.is_dir()


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
