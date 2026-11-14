"""Sessioni e feedback su S3, con le stesse chiavi del sistema attuale.

Due correzioni rispetto ad allora: il feedback civile è un oggetto per feedback (non più
un file condiviso in lettura-modifica-scrittura) e un errore di scrittura risale al chiamante.
"""

import json
from typing import Any

from cycle_validation.kb.stores import ObjectNotFoundError, WritableObjectStore

CIVIL = "Manufacturing AI/CycleValidationMemory"
EJ200 = f"{CIVIL}/EJ200"


class SessionStore:
    """Una sessione attiva e una copia completa (mirror) che l'eliminazione non tocca."""

    def __init__(self, store: WritableObjectStore, root: str) -> None:
        self._store = store
        self._root = root

    def _active(self, sso: str, session_id: str) -> str:
        return f"{self._root}/ChatSessions/{sso}/{session_id}.json"

    def _complete(self, sso: str, session_id: str) -> str:
        return f"{self._root}/ChatSessionsComplete/{sso}/{session_id}.json"

    def save(self, sso: str, session_id: str, session: dict[str, Any]) -> None:
        data = json.dumps(session, ensure_ascii=False).encode("utf-8")
        self._store.put_bytes(self._active(sso, session_id), data)
        self._store.put_bytes(self._complete(sso, session_id), data)

    def get(self, sso: str, session_id: str) -> dict[str, Any] | None:
        try:
            loaded: dict[str, Any] = json.loads(
                self._store.get_bytes(self._active(sso, session_id))
            )
            return loaded
        except ObjectNotFoundError:
            return None

    def list(self, sso: str) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for key in self._store.list_keys(f"{self._root}/ChatSessions/{sso}/"):
            if key.endswith(".json"):
                sessions.append(json.loads(self._store.get_bytes(key)))
        return sorted(
            sessions,
            key=lambda s: str(s.get("updatedAt") or s.get("createdAt") or ""),
            reverse=True,
        )

    def delete(self, sso: str, session_id: str) -> None:
        self._store.delete(self._active(sso, session_id))


class FeedbackStore:
    """Un oggetto per feedback: nessuna lettura-modifica-scrittura, nessuna perdita."""

    def __init__(self, store: WritableObjectStore, root: str) -> None:
        self._store = store
        self._root = root

    def save(self, sso: str, timestamp: str, identifier: str, feedback: dict[str, Any]) -> str:
        safe = "".join(c for c in f"{timestamp}_{identifier}" if c.isalnum() or c in "-_.:")
        key = f"{self._root}/Feedback/{sso}/{safe}.json"
        self._store.put_bytes(key, json.dumps(feedback, ensure_ascii=False).encode("utf-8"))
        return key
