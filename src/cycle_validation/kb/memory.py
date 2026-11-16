"""Knowledge base con indici in memoria. È l'implementazione usata dalla cartella locale
e dai test; un adattatore su sorgenti remote può riusarla dopo aver scaricato i dati."""

from collections.abc import Iterable, Mapping

from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.text import normalize_code


class IndexedKnowledgeBase:
    def __init__(
        self,
        version: str,
        *,
        documents: Iterable[DocumentInfo] = (),
        aliases: Mapping[str, Iterable[str]] | None = None,
        tasks: Iterable[TaskLocation] = (),
        machine_tags: Iterable[MachineTagEntry] = (),
        process_sheets: Iterable[ProcessSheetEntry] = (),
        dr_recommendations: Iterable[DrRecommendation] = (),
    ) -> None:
        self._version = version
        self._documents = list(documents)
        self._by_name: dict[str, list[DocumentInfo]] = {}
        for document in self._documents:
            names = {document.key, *(aliases or {}).get(document.key, ())}
            if document.code:
                names.add(document.code)
            for name in {normalize_code(name) for name in names}:
                self._by_name.setdefault(name, []).append(document)
        self._tasks = {
            (location.document.key, normalize_code(location.task)): location for location in tasks
        }
        self._tags = {normalize_code(entry.tag): entry for entry in machine_tags}
        self._sheets = {normalize_code(entry.code): entry for entry in process_sheets}
        self._dr: dict[str, list[DrRecommendation]] = {}
        for recommendation in dr_recommendations:
            key = normalize_code(recommendation.serial_number)
            self._dr.setdefault(key, []).append(recommendation)

    @property
    def version(self) -> str:
        return self._version

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        return list(self._by_name.get(normalize_code(manual), ()))

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        wanted = normalize_code(task)
        for document in self.find_manuals(manual):
            location = self._tasks.get((document.key, wanted))
            if location is not None:
                return location
        return None

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        return self._tags.get(normalize_code(tag))

    def machine_tags(self) -> list[MachineTagEntry]:
        """Tutte le targhe: EJ200 le prende dalla conoscenza civile."""
        return list(self._tags.values())

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        return self._sheets.get(normalize_code(code))

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        return list(self._dr.get(normalize_code(serial_number), ()))

    def stats(self) -> dict[str, int]:
        return {
            "documenti": len(self._documents),
            "task": len(self._tasks),
            "targhe": len(self._tags),
            "schede": len(self._sheets),
            "recommendation_dr": sum(len(items) for items in self._dr.values()),
        }
