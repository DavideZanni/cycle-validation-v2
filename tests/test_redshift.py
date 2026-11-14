import sqlite3
from typing import Any

import pytest

from cycle_validation.errors import SourceUnavailableError
from cycle_validation.services.redshift import fetch_active_machines, redshift_machine_registry

QUERY = "SELECT work_center_cd FROM work_centers WHERE work_center_usage_cd = 'TO'"


def connect_factory(rows: list[tuple[Any, ...]]) -> Any:
    calls = {"n": 0}

    def connect() -> sqlite3.Connection:
        calls["n"] += 1
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE work_centers (work_center_cd TEXT, work_center_usage_cd TEXT)")
        db.executemany("INSERT INTO work_centers VALUES (?, ?)", rows)
        return db

    connect.calls = calls  # type: ignore[attr-defined]
    return connect


ROWS = [("TM-1001", "TO"), ("TM-2002", "TO"), ("TM-3003", "XX"), (None, "TO")]


def test_only_usage_to_machines_are_returned() -> None:
    assert fetch_active_machines(connect_factory(ROWS), QUERY) == ["TM-1001", "TM-2002"]


def test_registry_loads_once_and_answers_exactly() -> None:
    connect = connect_factory(ROWS)
    registry = redshift_machine_registry(connect, QUERY)
    assert registry.is_active(" tm-1001")
    assert not registry.is_active("TM-3003")
    assert connect.calls["n"] == 1


def test_unreachable_database_is_source_unavailable_and_retried() -> None:
    state = {"up": False}

    def connect() -> sqlite3.Connection:
        if not state["up"]:
            raise ConnectionError("giù")
        return connect_factory(ROWS)()

    registry = redshift_machine_registry(connect, QUERY)
    with pytest.raises(SourceUnavailableError):
        registry.is_active("TM-1001")
    state["up"] = True
    assert registry.is_active("TM-1001")


def test_bad_query_is_source_unavailable() -> None:
    with pytest.raises(SourceUnavailableError):
        fetch_active_machines(connect_factory(ROWS), "SELECT * FROM niente")


def test_an_empty_active_list_is_a_technical_failure_not_all_machines_inactive() -> None:
    # una query che non restituisce nessuna macchina (tabella sbagliata, permessi) non prova
    # che tutte le macchine sono inattive: l'esito deve restare un warning tecnico
    registry = redshift_machine_registry(connect_factory([("TM-3003", "XX")]), QUERY)
    with pytest.raises(SourceUnavailableError):
        registry.is_active("TM-1001")


def test_the_active_list_is_refreshed_after_its_time_to_live() -> None:
    rows = [("TM-1001", "TO")]
    now = {"t": 0.0}
    registry = redshift_machine_registry(
        connect_factory(rows), QUERY, ttl_s=60.0, clock=lambda: now["t"]
    )
    assert not registry.is_active("TM-2002")
    rows.append(("TM-2002", "TO"))
    now["t"] = 59.0
    assert not registry.is_active("TM-2002")  # ancora in cache
    now["t"] = 61.0
    assert registry.is_active("TM-2002")
