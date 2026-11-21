"""Conoscenza civile pubblicata con un puntatore (`current.json`), aggiornata senza riavvio.

Ogni `check_every_s` secondi si rilegge il puntatore. Se indica una versione nuova, la si
scarica in `workdir/<versione>` e, solo se è valida, diventa quella corrente. Mentre scarica,
chi chiede risponde con la versione corrente: aspetta solo la richiesta che ha fatto partire
il controllo. Se qualcosa va storto (puntatore illeggibile, file non validi) si resta sulla
versione che c'era.

Una validazione chiama `current()` all'inizio e usa quella versione fino alla fine, anche se
nel frattempo ne arriva una nuova: le cartelle delle ultime `keep` versioni restano su disco.
`workdir` è dedicata: le cartelle che non sono tra quelle tenute si cancellano.
"""

import logging
import shutil
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.pointer import Pointer, read_pointer
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.kb.snapshot import sync_snapshot
from cycle_validation.kb.stores import ObjectStore

log = logging.getLogger(__name__)

COMPLETE = ".completo"
_DOWNLOADING = ".scarico-"


def rename_when_free(
    source: Path,
    target: Path,
    *,
    attempts: int = 6,
    pause_s: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Rinomina una cartella appena scritta. Su Windows l'antivirus o l'indicizzatore possono
    tenere aperti per un attimo i file nuovi e la rinomina fallisce con "Accesso negato"
    (WinError 5): si riprova con attese crescenti, poi si rinuncia con l'errore vero."""
    for attempt in range(attempts):
        try:
            source.rename(target)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            sleep(pause_s * 2**attempt)


class PublishedKnowledgeBase:
    def __init__(
        self,
        store: ObjectStore,
        pointer_key: str,
        workdir: Path,
        *,
        check_every_s: float = 300.0,
        keep: int = 3,
        workers: int = 8,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._store = store
        self._pointer_key = pointer_key
        self._workdir = workdir
        self._check_every = check_every_s
        self._keep = max(1, keep)
        self._workers = workers
        self._clock = clock
        self._lock = threading.Lock()  # protegge lo stato qui sotto
        self._refreshing = threading.Lock()  # un solo download alla volta
        self._kb: IndexedKnowledgeBase | None = None
        self._checked_at = 0.0
        self._recent: list[str] = []  # versioni tenute su disco, la corrente per prima

    # ------------------------------------------------------------ versione corrente

    def current(self) -> IndexedKnowledgeBase:
        """La versione da usare adesso. Senza alcuna versione: SourceUnavailableError."""
        with self._lock:
            kb = self._kb
            due = kb is None or self._clock() - self._checked_at >= self._check_every
        if kb is not None and not due:
            return kb
        if kb is None:
            with self._refreshing:
                with self._lock:
                    if self._kb is not None:
                        return self._kb
                try:
                    return self._refresh()
                except KnowledgeError as exc:
                    raise SourceUnavailableError(str(exc)) from exc
        assert kb is not None
        if not self._refreshing.acquire(blocking=False):
            return kb  # un altro sta già controllando o scaricando
        try:
            return self._refresh()
        except (KnowledgeError, SourceUnavailableError) as exc:
            log.warning("Conoscenza non aggiornata, resta la versione %s: %s", kb.version, exc)
            with self._lock:
                self._checked_at = self._clock()
            return kb
        finally:
            self._refreshing.release()

    def preload(self) -> None:
        """All'avvio: senza una versione valida il servizio non parte."""
        try:
            self.current()
        except SourceUnavailableError as exc:
            raise KnowledgeError(str(exc)) from exc

    def _refresh(self) -> IndexedKnowledgeBase:
        """Da chiamare con `_refreshing` preso."""
        pointer = read_pointer(self._store, self._pointer_key)
        with self._lock:
            kb = self._kb
        if kb is not None and kb.version == pointer.version:
            with self._lock:
                self._checked_at = self._clock()
            return kb
        fresh = self._open(pointer)
        with self._lock:
            self._kb = fresh
            self._checked_at = self._clock()
            self._recent = [pointer.version, *(v for v in self._recent if v != pointer.version)]
            self._recent = self._recent[: self._keep]
            kept = set(self._recent)
        log.info("Conoscenza alla versione %s", pointer.version)
        self._prune(kept)
        return fresh

    def _open(self, pointer: Pointer) -> IndexedKnowledgeBase:
        folder = self._workdir / pointer.version
        if (folder / COMPLETE).is_file():
            return load_local_knowledge(folder, version=pointer.version)
        self._workdir.mkdir(parents=True, exist_ok=True)
        staging = self._workdir / f"{_DOWNLOADING}{uuid.uuid4().hex[:8]}"
        try:
            sync_snapshot(self._store, pointer.prefix, staging, workers=self._workers)
            load_local_knowledge(staging, version=pointer.version)  # valida prima di spostare
            (staging / COMPLETE).write_text(pointer.version + "\n", encoding="utf-8")
            if folder.exists():
                shutil.rmtree(folder)  # download interrotto in un giro precedente
            rename_when_free(staging, folder)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        return load_local_knowledge(folder, version=pointer.version)

    def _prune(self, kept: set[str]) -> None:
        for path in self._workdir.iterdir():
            if path.is_dir() and path.name not in kept and not path.name.startswith(_DOWNLOADING):
                shutil.rmtree(path, ignore_errors=True)

    # ------------------------------------------------------------ KnowledgeBase

    @property
    def version(self) -> str:
        return self.current().version

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        return self.current().find_manuals(manual)

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        return self.current().find_task(manual, task)

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None:
        return self.current().find_task_in_kind(kind, task)

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        return self.current().find_machine_tag(tag)

    def machine_tags(self) -> list[MachineTagEntry]:
        return self.current().machine_tags()

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        return self.current().find_process_sheet(code)

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        return self.current().find_dr_recommendations(serial_number)

    def stats(self) -> dict[str, int]:
        return self.current().stats()
