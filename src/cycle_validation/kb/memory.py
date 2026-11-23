"""Knowledge base con indici in memoria. È l'implementazione usata dalla cartella locale
e dai test; un adattatore su sorgenti remote può riusarla dopo aver scaricato i dati."""

from collections.abc import Iterable, Mapping

from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.kb.task_text import find_task_in_text
from cycle_validation.text import normalize_code, sheet_key


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
        # Task trovati nel testo perché l'indice non li ha (anche i mancati: None).
        self._from_text: dict[tuple[str, str], TaskLocation | None] = {}
        self._tags = {normalize_code(entry.tag): entry for entry in machine_tags}
        self._sheets = {sheet_key(entry.code): entry for entry in process_sheets}
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
        return self._task_in(self.find_manuals(manual), task)

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None:
        return self._task_in(self.documents_of_kind(kind), task)

    def documents_of_kind(self, kind: str) -> list[DocumentInfo]:
        """I documenti di un tipo (`kind` del manifest, per esempio SPM)."""
        wanted = normalize_code(kind)
        return [d for d in self._documents if normalize_code(d.kind or "") == wanted]

    def _task_in(self, documents: list[DocumentInfo], task: str) -> TaskLocation | None:
        wanted = normalize_code(task)
        for document in documents:
            location = self._tasks.get((document.key, wanted))
            if location is not None:
                return location
        # L'indice non ha il task (titolo in una forma che non riconosce): si cerca il titolo
        # nel testo dei documenti, con la stessa regola dell'indice.
        for document in documents:
            location = self._task_from_text(document, task, wanted)
            if location is not None:
                return location
        return None

    def _task_from_text(
        self, document: DocumentInfo, task: str, wanted: str
    ) -> TaskLocation | None:
        key = (document.key, wanted)
        if key not in self._from_text:
            found = find_task_in_text(read_lines(document.path), task)
            self._from_text[key] = (
                None
                if found is None
                else TaskLocation(
                    manual_key=document.key,
                    task=task.strip(),
                    document=document,
                    line_start=found[0],
                    line_end=found[1],
                )
            )
        return self._from_text[key]

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        return self._tags.get(normalize_code(tag))

    def machine_tags(self) -> list[MachineTagEntry]:
        """Tutte le targhe: EJ200 le prende dalla conoscenza civile."""
        return list(self._tags.values())

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        return self._sheets.get(sheet_key(code))

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        return list(self._dr.get(normalize_code(serial_number), ()))

    def uncertain_counts(self) -> dict[str, int]:
        """Voci con almeno un motivo di incertezza dall'indice (per `kb-check`)."""
        return {
            "targhe_incerte": sum(1 for entry in self._tags.values() if entry.uncertain),
            "schede_incerte": sum(1 for entry in self._sheets.values() if entry.uncertain),
            "recommendation_dr_incerte": sum(
                1 for items in self._dr.values() for entry in items if entry.uncertain
            ),
        }

    def stats(self) -> dict[str, int]:
        return {
            "documenti": len(self._documents),
            "task": len(self._tasks),
            "targhe": len(self._tags),
            "schede": len(self._sheets),
            "recommendation_dr": sum(len(items) for items in self._dr.values()),
        }
