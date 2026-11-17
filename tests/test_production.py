"""Montaggio di produzione: dall'ambiente ai servizi, con client AWS finti."""

import io
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from ej200_fixtures import catalog_entries
from fakes import ScriptedSession
from fastapi.testclient import TestClient
from support import scripted_judge
from test_kb_published import EJ200, POINTER, publish_ej200, publish_example

from cycle_validation.api.aws import CloudWatchMetrics
from cycle_validation.api.production import (
    ProductionConfig,
    assemble_services,
    load_production_config,
)
from cycle_validation.api.settings import AppConfig, load_app_config
from cycle_validation.errors import ConfigError, KnowledgeError, SourceUnavailableError
from cycle_validation.kb.stores import InMemoryObjectStore
from cycle_validation.services.redshift import fetch_with_data_api

SETTINGS = Path("config/settings.yaml")
ENV = {"BUCKETNAME": "b", "REGION_NAME": "eu-south-1", "FRONTEND_URL": "https://fe.example"}


def _machines(tmp_path: Path) -> Path:
    path = tmp_path / "macchine.json"
    path.write_text(json.dumps(["TM-1001", "TM-2002"]), encoding="utf-8")
    return path


def _app_config(**changes: Any) -> AppConfig:
    base = load_app_config(
        {
            **ENV,
            "CIVIL_KNOWLEDGE_POINTER": POINTER,
            "EJ200_KNOWLEDGE_POINTER": EJ200 + "current.json",
        }
    )
    return AppConfig(**{**base.__dict__, **changes})


def _published() -> InMemoryObjectStore:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    publish_ej200(store, "e1", catalog_entries())
    return store


def _session(settings: Any, transcripts: Path | None) -> ScriptedSession:
    return ScriptedSession(scripted_judge)


# ------------------------------------------------------------ configurazione


def test_defaults_with_a_machines_file(tmp_path: Path) -> None:
    production = load_production_config({"MACHINES_FILE": str(_machines(tmp_path))})

    assert production.settings_file == Path("config/settings.yaml")
    assert production.machines_file == _machines(tmp_path)
    assert production.redshift is None
    assert production.cloudwatch_metrics is True
    assert production.knowledge_workdir.name == "knowledge"


def test_redshift_serverless_needs_only_database_and_workgroup() -> None:
    production = load_production_config(
        {"REDSHIFT_DATABASE": "dwh", "REDSHIFT_WORKGROUP": "wg", "MACHINES_QUERY": "SELECT 1"}
    )
    assert production.redshift is not None
    assert production.redshift.parameters() == {"Database": "dwh", "WorkgroupName": "wg"}
    assert production.redshift.query == "SELECT 1"


def test_redshift_cluster_needs_a_user_or_a_secret() -> None:
    with pytest.raises(ConfigError, match="REDSHIFT_DB_USER"):
        load_production_config({"REDSHIFT_DATABASE": "dwh", "REDSHIFT_CLUSTER_ID": "c1"})
    production = load_production_config(
        {"REDSHIFT_DATABASE": "dwh", "REDSHIFT_CLUSTER_ID": "c1", "REDSHIFT_SECRET_ARN": "arn:x"}
    )
    assert production.redshift is not None
    assert production.redshift.parameters() == {
        "Database": "dwh",
        "ClusterIdentifier": "c1",
        "SecretArn": "arn:x",
    }


@pytest.mark.parametrize(
    ("environ", "message"),
    [
        ({}, "MACHINES_FILE"),
        ({"MACHINES_FILE": "m.json", "REDSHIFT_DATABASE": "dwh"}, "una sola"),
        ({"REDSHIFT_DATABASE": "dwh"}, "REDSHIFT_WORKGROUP"),
        (
            {"REDSHIFT_DATABASE": "dwh", "REDSHIFT_WORKGROUP": "w", "REDSHIFT_CLUSTER_ID": "c"},
            "REDSHIFT_WORKGROUP",
        ),
        ({"MACHINES_FILE": "m.json", "CLOUDWATCH_METRICS": "forse"}, "CLOUDWATCH_METRICS"),
        (
            {"REDSHIFT_DATABASE": "d", "REDSHIFT_WORKGROUP": "w", "MACHINES_TTL_S": "x"},
            "MACHINES_TTL_S",
        ),
    ],
)
def test_wrong_machine_settings_are_named(environ: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_production_config(environ)


# ------------------------------------------------------------ montaggio


def _assemble(tmp_path: Path, config: AppConfig | None = None, **changes: Any) -> Any:
    production = ProductionConfig(
        settings_file=SETTINGS,
        knowledge_workdir=tmp_path / "knowledge",
        machines_file=_machines(tmp_path),
    )
    return assemble_services(
        config or _app_config(),
        production,
        store=changes.pop("store", None) or _published(),
        session_factory=_session,
        **changes,
    )


def test_services_read_the_published_knowledge(tmp_path: Path) -> None:
    services = _assemble(tmp_path)
    services.warmup()

    deps_for = services.runner._deps_for
    assert deps_for("mos").kb.version == "r1"
    assert deps_for("dr").kb is deps_for("mos").kb
    assert deps_for("ej200").kb.version == "e1"
    assert deps_for("ej200").kb.find_machine_tag("TM-1001") is not None
    assert deps_for("mos").machines.is_active("TM-1001")
    assert deps_for("mos") is deps_for("mos")  # costruite una volta sola
    assert (tmp_path / "knowledge" / "civil" / "r1").is_dir()


def test_military_cycles_off_means_no_ej200_knowledge(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")  # nessun EJ200 pubblicato: il servizio parte lo stesso
    services = _assemble(tmp_path, _app_config(ej200_enabled=False), store=store)
    services.warmup()
    with pytest.raises(ConfigError, match="ej200"):
        services.runner._deps_for("ej200")


def test_a_broken_publication_stops_the_start(tmp_path: Path) -> None:
    store = InMemoryObjectStore()
    publish_example(store, "r1")
    services = _assemble(tmp_path, store=store)  # EJ200 acceso ma non pubblicato
    with pytest.raises(KnowledgeError, match=r"current.json"):
        services.warmup()


def test_published_civil_knowledge_is_required(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="CIVIL_KNOWLEDGE_POINTER"):
        _assemble(tmp_path, _app_config(civil_knowledge_pointer=None))


def test_cost_goes_to_cloudwatch_when_a_client_is_given(tmp_path: Path) -> None:
    class Client:
        def put_metric_data(self, **kwargs: Any) -> None:
            pass

    assert isinstance(_assemble(tmp_path, cloudwatch=Client()).metrics, CloudWatchMetrics)
    assert not isinstance(_assemble(tmp_path).metrics, CloudWatchMetrics)


# ------------------------------------------------------------ Redshift Data API


class DataApi:
    def __init__(self, states: list[str], pages: list[dict[str, Any]]) -> None:
        self.states = states
        self.pages = pages
        self.executed: dict[str, Any] = {}

    def execute_statement(self, **kwargs: Any) -> dict[str, Any]:
        self.executed = kwargs
        return {"Id": "q1"}

    def describe_statement(self, Id: str) -> dict[str, Any]:
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return {"Status": state, "Error": "tabella inesistente"}

    def get_statement_result(self, Id: str, NextToken: str | None = None) -> dict[str, Any]:
        return self.pages[int(NextToken or 0)]


def test_data_api_reads_every_page_of_the_first_column() -> None:
    client = DataApi(
        ["SUBMITTED", "STARTED", "FINISHED"],
        [
            {"Records": [[{"stringValue": "TM-1001 "}], [{"isNull": True}]], "NextToken": "1"},
            {"Records": [[{"stringValue": "TM-2002"}, {"longValue": 3}]]},
        ],
    )
    tags = fetch_with_data_api(
        client, {"Database": "dwh", "WorkgroupName": "wg"}, "SELECT", sleep=lambda s: None
    )
    assert tags == ["TM-1001", "TM-2002"]
    assert client.executed == {"Database": "dwh", "WorkgroupName": "wg", "Sql": "SELECT"}


def test_data_api_failure_is_a_source_problem() -> None:
    client = DataApi(["FAILED"], [])
    with pytest.raises(SourceUnavailableError, match="FAILED"):
        fetch_with_data_api(client, {"Database": "d"}, "SELECT", sleep=lambda s: None)


def test_data_api_gives_up_after_the_timeout() -> None:
    client = DataApi(["STARTED"], [])
    with pytest.raises(SourceUnavailableError, match="tempo"):
        fetch_with_data_api(
            client, {"Database": "d"}, "SELECT", sleep=lambda s: None, timeout_s=1, poll_s=0.5
        )


# ------------------------------------------------------------ dall'ambiente, boto3 finto


class FakeS3:
    def __init__(self, store: InMemoryObjectStore) -> None:
        self.store = store

    def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        try:
            data = self.store.get_bytes(Key)
        except KeyError as exc:
            error = Exception("NoSuchKey")
            error.response = {"Error": {"Code": "NoSuchKey"}}  # type: ignore[attr-defined]
            raise error from exc
        return {"Body": io.BytesIO(data)}

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> None:
        self.store.put_bytes(Key, Body)

    def delete_object(self, Bucket: str, Key: str) -> None:
        self.store.delete(Key)

    def list_objects_v2(self, Bucket: str, Prefix: str) -> dict[str, Any]:
        return {"Contents": [{"Key": key} for key in self.store.list_keys(Prefix)]}


class FakeSecrets:
    def get_secret_value(self, SecretId: str) -> dict[str, Any]:
        return {"SecretString": json.dumps({"FRONTEND_URL": "https://dal-secret.example"})}


def _fake_boto3(monkeypatch: pytest.MonkeyPatch, store: InMemoryObjectStore) -> list[str]:
    made: list[str] = []

    def client(name: str, region_name: str | None = None) -> Any:
        made.append(name)
        return {"s3": FakeS3(store), "secretsmanager": FakeSecrets()}.get(name, object())

    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(client=client))
    return made


def test_the_service_starts_from_the_environment_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from cycle_validation.api.main import create_app_from_env

    made = _fake_boto3(monkeypatch, _published())
    environ = {
        "BUCKETNAME": "b",
        "REGION_NAME": "eu-south-1",
        "SECRET_NAME": "cv/prod",
        "CIVIL_KNOWLEDGE_POINTER": POINTER,
        "EJ200_KNOWLEDGE_POINTER": EJ200 + "current.json",
        "MACHINES_FILE": str(_machines(tmp_path)),
        "KNOWLEDGE_WORKDIR": str(tmp_path / "k"),
        "CLOUDWATCH_METRICS": "false",
    }
    app = create_app_from_env(environ)

    assert environ["FRONTEND_URL"] == "https://dal-secret.example"
    assert "cloudwatch" not in made
    with TestClient(app) as client:  # l'avvio scarica la conoscenza
        assert client.get("/cycle_validation/health").json()["status"] == "ok"
    assert (tmp_path / "k" / "civil" / "r1").is_dir()


def test_missing_boto3_is_explained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from cycle_validation.api.main import build_services

    monkeypatch.setitem(sys.modules, "boto3", None)
    with pytest.raises(ConfigError, match="--extra aws"):
        build_services(_app_config(), {"MACHINES_FILE": str(_machines(tmp_path))})
