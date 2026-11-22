"""Macchine attive da un database SQL (in azienda Redshift).

Il modulo non apre connessioni da solo: riceve una funzione `connect()` che restituisce una
connessione DB-API (psycopg2, redshift_connector, o sqlite3 nei test). Le credenziali
restano a chi costruisce la connessione (per esempio da Secrets Manager).

La query reale sta in configurazione: la regola nota è `work_center_usage_cd = 'TO'`.

In alternativa `fetch_with_data_api` usa la Redshift Data API con un client boto3
`redshift-data`: nessun driver da installare, credenziali dal ruolo AWS.
"""

import ast
import contextlib
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cycle_validation.errors import CycleValidationError, SourceUnavailableError
from cycle_validation.services.machines import LazyMachineRegistry

DEFAULT_TTL_S = 900.0
_FAILED = {"FAILED", "ABORTED"}
DEFAULT_QUERY = "SELECT DISTINCT work_center_cd FROM work_centers WHERE work_center_usage_cd = 'TO'"


def fetch_active_machines(connect: Callable[[], Any], query: str = DEFAULT_QUERY) -> list[str]:
    """Esegue la query e restituisce le targhe della prima colonna."""
    try:
        connection = connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                return [str(row[0]).strip() for row in cursor.fetchall() if row[0] is not None]
            finally:
                cursor.close()
        finally:
            connection.close()
    except Exception as exc:
        raise SourceUnavailableError(
            f"Registro macchine non raggiungibile ({type(exc).__name__})."
        ) from exc


def redshift_machine_registry(
    connect: Callable[[], Any],
    query: str = DEFAULT_QUERY,
    *,
    ttl_s: float | None = DEFAULT_TTL_S,
    clock: Callable[[], float] = time.monotonic,
) -> LazyMachineRegistry:
    """Registro che interroga il database alla prima domanda e rinnova l'elenco ogni `ttl_s`
    secondi: in un servizio che resta acceso una macchina attivata o dismessa dopo l'avvio
    non deve produrre un esito su dati vecchi."""
    return LazyMachineRegistry(lambda: fetch_active_machines(connect, query), ttl_s, clock)


def _first_column(record: list[dict[str, Any]]) -> str | None:
    if not record or record[0].get("isNull"):
        return None
    value = next(iter(record[0].values()), None)
    return None if value is None else str(value).strip() or None


def fetch_with_data_api(
    client: Any,
    parameters: dict[str, str],
    query: str,
    *,
    poll_s: float = 0.5,
    timeout_s: float = 60.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[str]:
    """Esegue la query con la Data API, aspetta la fine e legge tutte le pagine.
    `parameters`: Database e WorkgroupName, oppure ClusterIdentifier con DbUser o SecretArn."""
    try:
        statement = client.execute_statement(**parameters, Sql=query)["Id"]
        waited = 0.0
        while True:
            status = client.describe_statement(Id=statement)
            state = status.get("Status")
            if state == "FINISHED":
                break
            if state in _FAILED:
                raise SourceUnavailableError(
                    f"Query delle macchine attive {state}: {status.get('Error', '')}"
                )
            if waited >= timeout_s:
                raise SourceUnavailableError(
                    f"Query delle macchine attive oltre il tempo massimo ({timeout_s:.0f} s)."
                )
            sleep(poll_s)
            waited += poll_s
        tags: list[str] = []
        token: str | None = None
        while True:
            page = client.get_statement_result(
                Id=statement, **({"NextToken": token} if token else {})
            )
            tags += [tag for record in page.get("Records", []) if (tag := _first_column(record))]
            token = page.get("NextToken")
            if not token:
                return tags
    except SourceUnavailableError:
        raise
    except Exception as exc:
        raise SourceUnavailableError(
            f"Registro macchine non raggiungibile ({type(exc).__name__})."
        ) from exc


def data_api_registry(
    client: Any,
    parameters: dict[str, str],
    query: str = DEFAULT_QUERY,
    *,
    ttl_s: float | None = DEFAULT_TTL_S,
    clock: Callable[[], float] = time.monotonic,
) -> LazyMachineRegistry:
    """Come `redshift_machine_registry`, ma con la Data API."""
    return LazyMachineRegistry(lambda: fetch_with_data_api(client, parameters, query), ttl_s, clock)


# --- elenco delle macchine attive per le prove sul PC ------------------------------------------
# La v1 legge Redshift con `redshift_connector` e le credenziali di un secret (`SECRET_NAME`
# in `config.py`). Per le prove sul PC la v2 prende dalla v1 il nome del secret e la tabella,
# legge host e database dal secret e fa la query con la Data API (HTTPS: niente porta 5439).

_SECRET_NAME = re.compile(
    r"""SECRET_NAME\s*[:=]\s*(?:[\w.]+\(\s*["']\w+["']\s*,\s*)?["']([^"']+)["']"""
)
# la v1 legge all'avvio un secret «di ambiente» che mette le sue chiavi (SECRET_NAME compreso)
# nelle variabili d'ambiente: `load_secrets("<nome>")` in app_backend.py
_LOAD_SECRETS = re.compile(r"""load_secrets\(\s*["']([^"']+)["']""")
_FROM = re.compile(r"""\bFROM\s+([A-Za-z_"][\w."]*)""", re.IGNORECASE)
_TABLE = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*){0,2}$")
_SKIP = {".venv", "venv", "node_modules", "__pycache__", ".git"}
# il database della connessione: nella v1 `RedshiftConnector(database=REDSHIFT_DBNAME)`, con
# `..., REDSHIFT_DBNAME = get_db_credentials()` definita in un altro file. Si segue il valore
# nel codice (assegnazioni, tuple restituite da una funzione) fino a un testo scritto nel codice
# o a una chiave letta da un secret o dall'ambiente (`x["K"]`, `.get("K")`, `getenv("K")`).
_DB_ARGS = {"database", "dbname", "db_name"}


@dataclass(frozen=True)
class V1Redshift:
    secret: str | None
    table: str | None
    env_secret: str | None = None
    database: str | None = None
    database_key: str | None = None


def find_in_v1(folder: Path) -> V1Redshift:
    """Nome del secret e tabella delle macchine, cercati nei file Python della v1."""
    secret: str | None = None
    table: str | None = None
    env_secret: str | None = None
    trees: list[ast.Module] = []
    for path in sorted(folder.rglob("*.py")):
        if _SKIP & set(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if secret is None and (match := _SECRET_NAME.search(text)) is not None:
            secret = match[1]
        if env_secret is None and (match := _LOAD_SECRETS.search(text)) is not None:
            env_secret = match[1]
        at = text.find("work_center_usage_cd")
        if table is None and at >= 0:
            before = _FROM.findall(text[max(0, at - 800) : at])
            after = _FROM.findall(text[at : at + 400])
            found = before[-1] if before else (after[0] if after else None)
            table = found.replace('"', "") if found else None
        with contextlib.suppress(SyntaxError, ValueError):
            trees.append(ast.parse(text))
    database, database_key = _database_in(trees)
    return V1Redshift(secret, table, env_secret, database, database_key)


type _Found = tuple[str | None, str | None]


def _database_in(trees: list[ast.Module]) -> _Found:
    """(testo nel codice, chiave): la chiave, se c'è, vale più del testo (che è il suo valore
    predefinito, come in `.get("K", "predefinito")`)."""
    functions = {
        node.name: node
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    for tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg in _DB_ARGS:
                    found = _resolve(keyword.value, tree, functions, 0)
                    if found != (None, None):
                        return found
    return None, None


def _text(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _resolve(node: ast.AST, scope: ast.AST, functions: dict[str, Any], depth: int) -> _Found:
    if depth > 6:
        return None, None
    if (literal := _text(node)) is not None:
        return literal, None
    if isinstance(node, ast.Subscript) and (key := _text(node.slice)) is not None:
        return None, key
    if isinstance(node, ast.Call) and node.args and (key := _text(node.args[0])) is not None:
        name = (
            node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        )
        if name in {"get", "getenv"}:
            return (_text(node.args[1]) if len(node.args) > 1 else None), key
    if isinstance(node, ast.Name):
        for assign in ast.walk(scope):
            targets = (
                assign.targets
                if isinstance(assign, ast.Assign)
                else [assign.target]
                if isinstance(assign, ast.AnnAssign) and assign.value is not None
                else []
            )
            value = getattr(assign, "value", None)
            for target in targets:
                if isinstance(target, ast.Name) and target.id == node.id and value is not None:
                    return _resolve(value, scope, functions, depth + 1)
                if isinstance(target, ast.Tuple) and value is not None:
                    names = [getattr(item, "id", None) for item in target.elts]
                    if node.id in names:
                        return _from_tuple(value, names.index(node.id), scope, functions, depth)
    return None, None


def _from_tuple(
    value: ast.AST, index: int, scope: ast.AST, functions: dict[str, Any], depth: int
) -> _Found:
    """L'elemento `index` di una tupla scritta o restituita da una funzione della v1."""
    if isinstance(value, ast.Tuple) and index < len(value.elts):
        return _resolve(value.elts[index], scope, functions, depth + 1)
    if isinstance(value, ast.Call):
        name = (
            value.func.attr
            if isinstance(value.func, ast.Attribute)
            else getattr(value.func, "id", "")
        )
        function = functions.get(name)
        if function is not None:
            for node in ast.walk(function):
                if isinstance(node, ast.Return) and node.value is not None:
                    found = _from_tuple(node.value, index, function, functions, depth + 1)
                    if found != (None, None):
                        return found
    return None, None


def machines_query(table: str) -> str:
    if not _TABLE.fullmatch(table):
        raise CycleValidationError("Nome della tabella delle macchine non valido.")
    return f"SELECT DISTINCT work_center_cd FROM {table} WHERE work_center_usage_cd = 'TO'"


def data_api_target(
    values: Mapping[str, Any], secret_arn: str, database: str | None = None
) -> tuple[str | None, dict[str, str]]:
    """Regione e parametri della Data API dai campi del secret della v1 (host e database).
    `database` vale più del secret (la v1 può averlo nel codice o nel secret di ambiente).
    I valori non si stampano mai: nell'errore ci sono solo i nomi dei campi."""
    host = str(values.get("host") or values.get("hostname") or "")
    database = database or next(
        (
            str(values[key])
            for key in ("dbname", "database", "db_name", "dbName")
            if values.get(key)
        ),
        None,
    )
    fields = ", ".join(sorted(values)) or "nessuno"
    if not host:
        raise CycleValidationError(f"Nel secret manca host. Campi presenti: {fields}.")
    if not database:
        raise CycleValidationError(
            f"Manca il nome del database: non è nel secret (campi presenti: {fields}) né "
            "nel codice della v1. Indicalo con --database."
        )
    region = re.search(r"\.([a-z]{2}(?:-[a-z]+)+-\d)\.redshift", host)
    parameters = {"Database": database, "SecretArn": secret_arn}
    if "redshift-serverless" in host:
        parameters["WorkgroupName"] = host.split(".")[0]
    else:
        cluster = values.get("dbClusterIdentifier") or host.split(".")[0]
        parameters["ClusterIdentifier"] = str(cluster)
    return (region[1] if region else None), parameters
