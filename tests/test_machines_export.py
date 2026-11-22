"""Elenco delle macchine attive da Redshift per le prove sul PC (comando `macchine`)."""

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.errors import CycleValidationError
from cycle_validation.services.redshift import data_api_target, find_in_v1, machines_query

V1_CONFIG = 'import os\n# Redshift Configuration\nSECRET_NAME = os.getenv("SECRET_NAME", "nome/del-secret")\n'
V1_QUERY = (
    "def verify_active_TM(tags):\n"
    '    sql = """SELECT work_center_cd\n'
    "             FROM schema_x.tabella_y\n"
    '             WHERE work_center_usage_cd = \'TO\'"""\n'
)


def _v1(tmp_path: Path) -> Path:
    (tmp_path / "config.py").write_text(V1_CONFIG, encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "machines.py").write_text(V1_QUERY, encoding="utf-8")
    return tmp_path


def test_secret_name_and_table_come_from_the_v1_code(tmp_path: Path) -> None:
    found = find_in_v1(_v1(tmp_path))
    assert found.secret == "nome/del-secret"
    assert found.table == "schema_x.tabella_y"


def test_query_is_the_v1_rule_and_refuses_odd_table_names() -> None:
    assert machines_query("s.t") == (
        "SELECT DISTINCT work_center_cd FROM s.t WHERE work_center_usage_cd = 'TO'"
    )
    with pytest.raises(CycleValidationError):
        machines_query("t; DROP TABLE x")


def test_cluster_and_region_come_from_the_secret_host() -> None:
    values = {"host": "mio-cluster.abc.eu-west-1.redshift.amazonaws.com", "dbname": "db"}
    region, parameters = data_api_target(values, "arn:secret")
    assert region == "eu-west-1"
    assert parameters == {
        "Database": "db",
        "SecretArn": "arn:secret",
        "ClusterIdentifier": "mio-cluster",
    }


def test_serverless_host_gives_the_workgroup() -> None:
    values = {"host": "wg.123.eu-south-1.redshift-serverless.amazonaws.com", "database": "db"}
    _, parameters = data_api_target(values, "arn")
    assert parameters["WorkgroupName"] == "wg"


def test_missing_fields_are_named_without_values() -> None:
    with pytest.raises(CycleValidationError) as error:
        data_api_target({"username": "u", "password": "segretissima"}, "arn")
    assert "password, username" in str(error.value)
    assert "segretissima" not in str(error.value)


class FakeSecrets:
    def get_secret_value(self, SecretId: str) -> dict[str, str]:
        assert SecretId == "nome/del-secret"
        values = {"host": "c1.x.eu-south-1.redshift.amazonaws.com", "dbname": "db", "password": "p"}
        return {"SecretString": json.dumps(values), "ARN": "arn:secret"}


class FakeDataApi:
    def __init__(self) -> None:
        self.sql = ""

    def execute_statement(self, **kwargs: Any) -> dict[str, str]:
        self.sql = kwargs["Sql"]
        assert kwargs["ClusterIdentifier"] == "c1"
        return {"Id": "q1"}

    def describe_statement(self, Id: str) -> dict[str, str]:
        return {"Status": "FINISHED"}

    def get_statement_result(self, Id: str, **_: Any) -> dict[str, Any]:
        rows = ["TM-2", "TM-1", "TM-2"]
        return {"Records": [[{"stringValue": tag}] for tag in rows]}


def test_macchine_writes_the_active_machines_and_prints_only_the_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_api = FakeDataApi()
    clients: dict[str, Any] = {"secretsmanager": FakeSecrets(), "redshift-data": data_api}
    monkeypatch.setattr(cli, "_aws_client", lambda service, region: clients[service])
    out = tmp_path / "data" / "macchine_attive.json"
    result = CliRunner().invoke(
        cli.app, ["macchine", "--v1", str(_v1(tmp_path)), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(out.read_text(encoding="utf-8")) == ["TM-1", "TM-2"]
    assert "tabella_y" in data_api.sql
    assert "Macchine attive: 2 (Redshift cluster)" in result.output
    assert "c1" not in result.output and "nome/del-secret" not in result.output


def test_macchine_prints_only_the_aws_error_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Denied(Exception):
        def __init__(self, message: str) -> None:
            super().__init__(message)
            self.response = {"Error": {"Code": "AccessDeniedException", "Message": message}}

    class NoSecrets:
        def get_secret_value(self, SecretId: str) -> None:
            raise Denied("arn:aws:iam::123:x")

    monkeypatch.setattr(cli, "_aws_client", lambda service, region: NoSecrets())
    result = CliRunner().invoke(cli.app, ["macchine", "--v1", str(_v1(tmp_path))])
    assert result.exit_code != 0
    assert "AccessDeniedException" in result.output
    assert "123" not in result.output


def test_the_redshift_secret_name_can_come_from_the_v1_environment_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Come la v1: `SECRET_NAME = os.getenv("SECRET_NAME")` senza valore nel codice, e
    `load_secrets("<ambiente>")` all'avvio mette SECRET_NAME nelle variabili d'ambiente."""
    (tmp_path / "config.py").write_text('SECRET_NAME = os.getenv("SECRET_NAME")\n', "utf-8")
    (tmp_path / "app_backend.py").write_text('load_secrets("ambiente/v1")\n', "utf-8")
    (tmp_path / "machines.py").write_text(V1_QUERY, encoding="utf-8")
    found = find_in_v1(tmp_path)
    assert (found.secret, found.env_secret) == (None, "ambiente/v1")

    class Secrets:
        def get_secret_value(self, SecretId: str) -> dict[str, str]:
            if SecretId == "ambiente/v1":
                values = {"SECRET_NAME": "nome/del-secret", "ALTRO": "x"}
                return {"SecretString": json.dumps(values), "ARN": "arn:env"}
            return FakeSecrets().get_secret_value(SecretId)

    clients: dict[str, Any] = {"secretsmanager": Secrets(), "redshift-data": FakeDataApi()}
    monkeypatch.setattr(cli, "_aws_client", lambda service, region: clients[service])
    out = tmp_path / "m.json"
    result = CliRunner().invoke(cli.app, ["macchine", "--v1", str(tmp_path), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert "Nel secret di ambiente: SECRET_NAME trovato." in result.output
    assert json.loads(out.read_text(encoding="utf-8")) == ["TM-1", "TM-2"]
    assert "nome/del-secret" not in result.output


def test_the_database_can_be_written_in_the_v1_connection(tmp_path: Path) -> None:
    (tmp_path / "tm.py").write_text(
        "import redshift_connector\n"
        "conn = redshift_connector.connect(host=h, database='db_v1', port=5439)\n",
        "utf-8",
    )
    found = find_in_v1(tmp_path)
    assert (found.database, found.database_key) == ("db_v1", None)


def test_the_database_can_be_a_key_read_by_the_v1(tmp_path: Path) -> None:
    (tmp_path / "tm.py").write_text(
        "import redshift_connector\n"
        'conn = redshift_connector.connect(host=h, database=os.getenv("REDSHIFT_DB"))\n',
        "utf-8",
    )
    assert find_in_v1(tmp_path).database_key == "REDSHIFT_DB"
    (tmp_path / "tm.py").write_text(
        "import redshift_connector\nc = redshift_connector.connect(database=config.DB_NAME)\n",
        "utf-8",
    )
    assert find_in_v1(tmp_path).database_key is None  # attributo di un modulo: non si segue


def test_a_missing_database_asks_for_the_option() -> None:
    values = {"host": "c.x.eu-west-1.redshift.amazonaws.com", "password": "segretissima"}
    with pytest.raises(CycleValidationError) as error:
        data_api_target(values, "arn")
    assert "--database" in str(error.value) and "segretissima" not in str(error.value)
    _, parameters = data_api_target(values, "arn", "db")
    assert parameters["Database"] == "db"


def test_secret_without_database_takes_it_from_the_v1_environment_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Come al PC aziendale: il secret di Redshift ha dbClusterIdentifier, host, porta e
    credenziali ma non il database, che la v1 legge da una chiave del secret di ambiente."""
    (tmp_path / "app_backend.py").write_text('load_secrets("ambiente/v1")\n', "utf-8")
    (tmp_path / "machines.py").write_text(
        V1_QUERY
        + 'import redshift_connector\nc = redshift_connector.connect(database=os.getenv("RS_DB"))\n',
        "utf-8",
    )

    class Secrets:
        def get_secret_value(self, SecretId: str) -> dict[str, str]:
            if SecretId == "ambiente/v1":
                values = {"SECRET_NAME": "nome/del-secret", "RS_DB": "db"}
            else:
                values = {
                    "dbClusterIdentifier": "c1",
                    "engine": "redshift",
                    "host": "c1.x.eu-south-1.redshift.amazonaws.com",
                    "password": "p",
                    "port": "5439",
                    "username": "u",
                }
            return {"SecretString": json.dumps(values), "ARN": "arn:" + SecretId}

    data_api = FakeDataApi()
    clients: dict[str, Any] = {"secretsmanager": Secrets(), "redshift-data": data_api}
    monkeypatch.setattr(cli, "_aws_client", lambda service, region: clients[service])
    out = tmp_path / "m.json"
    result = CliRunner().invoke(cli.app, ["macchine", "--v1", str(tmp_path), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert "database letto dalla chiave RS_DB con .getenv()" in result.output
    assert "Chiave RS_DB del database: trovata." in result.output
    assert json.loads(out.read_text(encoding="utf-8")) == ["TM-1", "TM-2"]


def test_the_database_is_followed_through_a_credentials_function(tmp_path: Path) -> None:
    """Come la v1: la connessione riceve `self.database`, che viene da
    `RedshiftConnector(database=REDSHIFT_DBNAME)` e da `get_db_credentials()` in un altro file."""
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "credentials.py").write_text(
        "def get_db_credentials():\n"
        "    secret = load(SECRET_NAME)\n"
        "    dbname = secret.get('db_x', 'predefinito')\n"
        "    return secret['host'], secret['username'], secret['password'], dbname\n",
        "utf-8",
    )
    (tmp_path / "tm.py").write_text(
        "import redshift_connector\n"
        "class RedshiftConnector:\n"
        "    def extract_data(self):\n"
        "        with redshift_connector.connect(host=self.host, database=self.database):\n"
        "            pass\n"
        "def verify_active_TM(tags):\n"
        "    H, U, P, REDSHIFT_DBNAME = get_db_credentials()\n"
        "    redshift = RedshiftConnector(host=H, port=5439, database=REDSHIFT_DBNAME)\n",
        "utf-8",
    )
    found = find_in_v1(tmp_path)
    assert (found.database, found.database_key) == ("predefinito", "db_x")


def test_without_the_key_the_database_comes_from_the_cluster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prova del 22-11: la v1 legge la chiave `database`, che non c'è in nessun secret."""
    (tmp_path / "app_backend.py").write_text('load_secrets("ambiente/v1")\n', "utf-8")
    (tmp_path / "machines.py").write_text(
        V1_QUERY
        + "import redshift_connector\n"
        + "c = redshift_connector.connect(database=secret.get('database'))\n",
        "utf-8",
    )

    class Secrets:
        def get_secret_value(self, SecretId: str) -> dict[str, str]:
            if SecretId == "ambiente/v1":
                values = {"SECRET_NAME": "nome/del-secret"}
            else:
                values = {
                    "dbClusterIdentifier": "c1",
                    "host": "c1.x.eu-south-1.redshift.amazonaws.com",
                }
            return {"SecretString": json.dumps(values), "ARN": "arn:" + SecretId}

    class Redshift:
        def describe_clusters(self, ClusterIdentifier: str) -> dict[str, Any]:
            assert ClusterIdentifier == "c1"
            return {"Clusters": [{"DBName": "db_cluster"}]}

    class DataApi(FakeDataApi):
        def execute_statement(self, **kwargs: Any) -> dict[str, str]:
            assert kwargs["Database"] == "db_cluster"
            return super().execute_statement(**kwargs)

    clients: dict[str, Any] = {
        "secretsmanager": Secrets(),
        "redshift": Redshift(),
        "redshift-data": DataApi(),
    }
    monkeypatch.setattr(cli, "_aws_client", lambda service, region: clients[service])
    out = tmp_path / "m.json"
    result = CliRunner().invoke(cli.app, ["macchine", "--v1", str(tmp_path), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert "database letto dalla chiave database con .get()" in result.output
    assert "Database del cluster: trovato." in result.output
    assert "db_cluster" not in result.output
