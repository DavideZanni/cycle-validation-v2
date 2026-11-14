"""Macchine attive da un database SQL (in azienda Redshift).

Il modulo non apre connessioni da solo: riceve una funzione `connect()` che restituisce una
connessione DB-API (psycopg2, redshift_connector, o sqlite3 nei test). Le credenziali
restano a chi costruisce la connessione (per esempio da Secrets Manager).

La query reale sta in configurazione: la regola nota è `work_center_usage_cd = 'TO'`.
"""

import time
from collections.abc import Callable
from typing import Any

from cycle_validation.errors import SourceUnavailableError
from cycle_validation.services.machines import LazyMachineRegistry

DEFAULT_TTL_S = 900.0
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
