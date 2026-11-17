"""Macchine attive da un database SQL (in azienda Redshift).

Il modulo non apre connessioni da solo: riceve una funzione `connect()` che restituisce una
connessione DB-API (psycopg2, redshift_connector, o sqlite3 nei test). Le credenziali
restano a chi costruisce la connessione (per esempio da Secrets Manager).

La query reale sta in configurazione: la regola nota è `work_center_usage_cd = 'TO'`.

In alternativa `fetch_with_data_api` usa la Redshift Data API con un client boto3
`redshift-data`: nessun driver da installare, credenziali dal ruolo AWS.
"""

import time
from collections.abc import Callable
from typing import Any

from cycle_validation.errors import SourceUnavailableError
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
