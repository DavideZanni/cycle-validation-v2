"""Knowledge base alimentata dalle sorgenti attuali: dati strutturati su un ObjectStore
(S3) e testo dei manuali da un ManualSource (cartella di markdown su S3). Implementa la porta
`KnowledgeBase`: i controlli non sanno da dove arriva la conoscenza."""

import threading

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.kb.snapshot import ManualSource
from cycle_validation.kb.stores import ObjectStore
from cycle_validation.kb.structured import StructuredData, StructuredLayout, load_structured


class RemoteKnowledgeBase:
    def __init__(
        self,
        version: str,
        store: ObjectStore,
        manuals: ManualSource,
        layout: StructuredLayout | None = None,
    ) -> None:
        self._version = version
        self._store = store
        self._manuals = manuals
        self._layout = layout or StructuredLayout()
        self._lock = threading.Lock()
        self._data: StructuredData | None = None
        # Gli stessi indici (e le stesse regole di ricerca) della conoscenza in memoria.
        self._index = IndexedKnowledgeBase(version)

    @property
    def version(self) -> str:
        return self._version

    def preload(self) -> None:
        """Carica i dati strutturati. Un oggetto mancante o non valido è un KnowledgeError:
        il run non deve partire con una knowledge base incompleta."""
        with self._lock:
            self._load()
        preload = getattr(self._manuals, "preload", None)
        if callable(preload):
            preload()

    def _load(self) -> StructuredData:
        if self._data is None:
            data = load_structured(self._store, self._layout)
            self._index = IndexedKnowledgeBase(
                self._version,
                machine_tags=data.machine_tags,
                process_sheets=data.process_sheets,
                dr_recommendations=data.dr_recommendations,
            )
            self._data = data
        return self._data

    def _ensure(self) -> IndexedKnowledgeBase:
        """Durante un controllo, un caricamento fallito è una sorgente non raggiungibile."""
        with self._lock:
            try:
                self._load()
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc
            return self._index

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        return self._manuals.find_manuals(manual)

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        return self._manuals.find_task(manual, task)

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None:
        return self._manuals.find_task_in_kind(kind, task)

    def documents_of_kind(self, kind: str) -> list[DocumentInfo]:
        return self._manuals.documents_of_kind(kind)

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        return self._ensure().find_machine_tag(tag)

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        return self._ensure().find_process_sheet(code)

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        return self._ensure().find_dr_recommendations(serial_number)

    def stats(self) -> dict[str, int]:
        data = self._load()
        return {
            "targhe": len(data.machine_tags),
            "schede": len(data.process_sheets),
            "recommendation_dr": len(data.dr_recommendations),
        }
