"""Registro delle macchine attive. In azienda la sorgente autorevole è Redshift
(`work_center_usage_cd = 'TO'`); in locale un file JSON con l'elenco delle targhe attive."""

import json
import threading
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Protocol

from cycle_validation.errors import CheckDisabledError, ConfigError, SourceUnavailableError
from cycle_validation.text import normalize_code


class MachineRegistry(Protocol):
    def is_active(self, tag: str) -> bool:
        """True se la macchina è attiva. Solleva SourceUnavailableError se non si può sapere."""
        ...


class StaticMachineRegistry:
    def __init__(self, active: Iterable[str]) -> None:
        self._active = frozenset(normalize_code(tag) for tag in active)

    def is_active(self, tag: str) -> bool:
        return normalize_code(tag) in self._active

    def __len__(self) -> int:
        return len(self._active)


class UnavailableMachineRegistry:
    """Registro che non risponde. `disabled`: non è un guasto, è spento per configurazione
    (nessun registro sul PC): il controllo delle targhe esce N/A invece di WARNING."""

    def __init__(self, reason: str, *, disabled: bool = False) -> None:
        self._reason = reason
        self._disabled = disabled

    def is_active(self, tag: str) -> bool:
        if self._disabled:
            raise CheckDisabledError(self._reason)
        raise SourceUnavailableError(self._reason)


class LazyMachineRegistry:
    """Carica l'elenco alla prima domanda e lo tiene in memoria per `ttl_s` secondi
    (None = per sempre: adatto a un run da CLI, non a un servizio).

    `fetch` restituisce le targhe attive: in azienda è la query su Redshift.
    Un errore di caricamento non viene memorizzato: la domanda successiva riprova.
    Un elenco vuoto è trattato come errore di caricamento: non dimostra che ogni macchina
    è inattiva, e un guasto tecnico non deve diventare un esito ERRATO.
    """

    def __init__(
        self,
        fetch: Callable[[], Iterable[str]],
        ttl_s: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetch = fetch
        self._ttl = ttl_s
        self._clock = clock
        self._loaded: StaticMachineRegistry | None = None
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def is_active(self, tag: str) -> bool:
        with self._lock:
            return self._current().is_active(tag)

    def _current(self) -> StaticMachineRegistry:
        expired = self._ttl is not None and self._clock() - self._loaded_at >= self._ttl
        if self._loaded is None or expired:
            try:
                loaded = StaticMachineRegistry(self._fetch())
            except SourceUnavailableError:
                raise
            except Exception as exc:
                raise SourceUnavailableError(
                    f"Registro macchine non raggiungibile: {type(exc).__name__}"
                ) from exc
            if not len(loaded):
                # nessuna macchina attiva è un guasto della sorgente, non una prova di inattività
                raise SourceUnavailableError(
                    "Il registro delle macchine attive è vuoto: stato non verificabile."
                )
            self._loaded = loaded
            self._loaded_at = self._clock()
        return self._loaded


def load_machine_registry(path: Path | None) -> MachineRegistry:
    """File JSON: una lista di targhe, oppure `{"active": [...]}`."""
    if path is None:
        return UnavailableMachineRegistry(
            "Registro delle macchine attive non configurato.", disabled=True
        )
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Registro macchine non leggibile ({path}): {exc}") from exc
    if isinstance(loaded, dict):
        loaded = loaded.get("active")
    if not isinstance(loaded, list) or not all(isinstance(item, str) for item in loaded):
        raise ConfigError(f"{path}: attesa una lista di targhe oppure {{'active': [...]}}.")
    return StaticMachineRegistry(loaded)
