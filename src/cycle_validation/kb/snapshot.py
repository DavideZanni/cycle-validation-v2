"""Testo dei manuali da una cartella dello store (S3) nel formato della knowledge base locale.

L'ingestion pubblica markdown e JSON (`manifest.json`, `documents/*.md`, `tasks.json`):
qui si scaricano una volta in una cartella di lavoro e si leggono con lo stesso lettore della
cartella locale. Nessun indice di ricerca: il codice sa già in quale file e a quali righe
sta ogni task, e l'agente legge quel file a paragrafo.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import DocumentInfo, TaskLocation
from cycle_validation.kb.stores import ObjectNotFoundError, ObjectStore

MANIFEST = "manifest.json"


class ManualSource(Protocol):
    def find_manuals(self, manual: str) -> list[DocumentInfo]: ...

    def find_task(self, manual: str, task: str) -> TaskLocation | None: ...

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None: ...


def sync_snapshot(store: ObjectStore, prefix: str, dest: Path, *, workers: int = 8) -> int:
    """Copia in `dest` ogni oggetto sotto `prefix`. Restituisce quanti ne ha copiati.

    Le chiavi si controllano tutte prima di scaricare; poi i download vanno in parallelo
    (con 2000 documenti, uno alla volta sarebbe lento)."""
    root_prefix = prefix.rstrip("/") + "/"
    keys = [key for key in store.list_keys(root_prefix) if not key.endswith("/")]
    if root_prefix + MANIFEST not in keys:
        raise KnowledgeError(f"{MANIFEST} non trovato sotto '{root_prefix}'.")
    root = dest.resolve()
    targets: list[tuple[str, Path]] = []
    for key in keys:
        target = (root / key[len(root_prefix) :]).resolve()
        if not target.is_relative_to(root):
            raise KnowledgeError(
                f"La chiave '{key}' esce dalla cartella: ignorata, snapshot rifiutato."
            )
        targets.append((key, target))

    def copy(item: tuple[str, Path]) -> None:
        key, target = item
        try:
            data = store.get_bytes(key)
        except ObjectNotFoundError as exc:
            raise KnowledgeError(f"Oggetto '{key}' sparito durante il download.") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for _ in pool.map(copy, targets):
            pass
    return len(keys)


class SnapshotManualSource:
    """Scarica lo snapshot alla prima richiesta (o a `preload`) e risponde dalla cartella."""

    def __init__(self, store: ObjectStore, prefix: str, workdir: Path) -> None:
        self._store = store
        self._prefix = prefix
        self._workdir = workdir
        self._lock = threading.Lock()
        self._kb: IndexedKnowledgeBase | None = None

    def preload(self) -> None:
        """Scarica e valida. Un difetto è un KnowledgeError: il run non deve partire."""
        with self._lock:
            self._load()

    def _load(self) -> IndexedKnowledgeBase:
        if self._kb is None:
            sync_snapshot(self._store, self._prefix, self._workdir)
            self._kb = load_local_knowledge(self._workdir)
        return self._kb

    def _ready(self) -> IndexedKnowledgeBase:
        """Durante un controllo, uno snapshot non valido è una sorgente non raggiungibile."""
        with self._lock:
            try:
                return self._load()
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        return self._ready().find_manuals(manual)

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        return self._ready().find_task(manual, task)

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None:
        return self._ready().find_task_in_kind(kind, task)
