"""Knowledge base alimentata dalle sorgenti attuali: dati strutturati su un ObjectStore
(S3) e testo dei manuali da un ManualSource (cartella di markdown su S3). Implementa la porta
`KnowledgeBase`: i controlli non sanno da dove arriva la conoscenza."""

import threading

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
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
from cycle_validation.text import normalize_code, sheet_key


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
        self._tags: dict[str, MachineTagEntry] = {}
        self._sheets: dict[str, ProcessSheetEntry] = {}
        self._dr: dict[str, list[DrRecommendation]] = {}

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
            self._tags = {normalize_code(item.tag): item for item in data.machine_tags}
            self._sheets = {sheet_key(item.code): item for item in data.process_sheets}
            self._dr = {}
            for item in data.dr_recommendations:
                self._dr.setdefault(normalize_code(item.serial_number), []).append(item)
            self._data = data
        return self._data

    def _ensure(self) -> None:
        """Durante un controllo, un caricamento fallito è una sorgente non raggiungibile."""
        with self._lock:
            try:
                self._load()
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        return self._manuals.find_manuals(manual)

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        return self._manuals.find_task(manual, task)

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None:
        return self._manuals.find_task_in_kind(kind, task)

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        self._ensure()
        return self._tags.get(normalize_code(tag))

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        self._ensure()
        return self._sheets.get(sheet_key(code))

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        self._ensure()
        return list(self._dr.get(normalize_code(serial_number), ()))

    def stats(self) -> dict[str, int]:
        data = self._load()
        return {
            "targhe": len(data.machine_tags),
            "schede": len(data.process_sheets),
            "recommendation_dr": len(data.dr_recommendations),
        }
