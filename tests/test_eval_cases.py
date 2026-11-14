"""Casi sintetici degli esperimenti: restano allineati alle fixture dei test."""

from pathlib import Path

from ej200_fixtures import make_store

from cycle_validation.kb.stores import LocalDirObjectStore

SINTETICI = Path(__file__).parents[1] / "eval" / "casi" / "sintetici"


def test_exported_ej200_knowledge_matches_the_test_fixtures() -> None:
    expected = make_store()
    exported = LocalDirObjectStore(SINTETICI / "ej200" / "conoscenza")
    assert exported.list_keys("") == expected.list_keys("")
    for key in expected.list_keys(""):
        assert exported.get_bytes(key) == expected.get_bytes(key), key
