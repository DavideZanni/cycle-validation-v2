import json
from typing import Any

import pytest

from cycle_validation.api.storage import CIVIL, EJ200, FeedbackStore, SessionStore
from cycle_validation.errors import SourceUnavailableError
from cycle_validation.kb.stores import InMemoryObjectStore, S3ObjectStore


def session(identifier: str, updated: str) -> dict[str, Any]:
    return {"id": identifier, "name": identifier, "updatedAt": updated, "messages": []}


def test_save_writes_active_and_complete_copy_at_the_documented_keys() -> None:
    store = InMemoryObjectStore()
    SessionStore(store, CIVIL).save("sso1", "s1", session("s1", "2026-01-01"))
    assert store.list_keys("") == [
        "Manufacturing AI/CycleValidationMemory/ChatSessions/sso1/s1.json",
        "Manufacturing AI/CycleValidationMemory/ChatSessionsComplete/sso1/s1.json",
    ]


def test_ej200_keys_live_under_their_own_prefix() -> None:
    store = InMemoryObjectStore()
    SessionStore(store, EJ200).save("sso1", "s1", session("s1", "x"))
    assert all("/EJ200/" in key for key in store.list_keys(""))


def test_delete_keeps_the_complete_copy() -> None:
    store = InMemoryObjectStore()
    sessions = SessionStore(store, CIVIL)
    sessions.save("sso1", "s1", session("s1", "x"))
    sessions.delete("sso1", "s1")
    assert sessions.get("sso1", "s1") is None
    assert len(store.list_keys("Manufacturing AI/CycleValidationMemory/ChatSessionsComplete/")) == 1


def test_list_is_per_owner_and_sorted_by_update() -> None:
    sessions = SessionStore(InMemoryObjectStore(), CIVIL)
    sessions.save("a", "old", session("old", "2026-01-01"))
    sessions.save("a", "new", session("new", "2026-02-01"))
    sessions.save("b", "other", session("other", "2026-03-01"))
    assert [s["id"] for s in sessions.list("a")] == ["new", "old"]
    assert sessions.get("a", "missing") is None


def test_one_object_per_feedback() -> None:
    store = InMemoryObjectStore()
    feedback = FeedbackStore(store, CIVIL)
    one = feedback.save("sso", "2026-11-13T10:00:00Z", "m1", {"vote": "up"})
    two = feedback.save("sso", "2026-11-13T10:00:01Z", "m2", {"vote": "down"})
    assert (
        one != two
        and len(store.list_keys("Manufacturing AI/CycleValidationMemory/Feedback/sso/")) == 2
    )
    assert json.loads(store.get_bytes(one)) == {"vote": "up"}


def test_write_failure_is_raised_not_swallowed() -> None:
    class Down:
        def put_object(self, **_: Any) -> None:
            raise TimeoutError

    with pytest.raises(SourceUnavailableError):
        FeedbackStore(S3ObjectStore(Down(), "b"), CIVIL).save("sso", "t", "i", {})
