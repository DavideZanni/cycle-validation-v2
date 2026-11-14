"""Porta verso la conoscenza: le sole domande che i controlli fanno.

Controlli, agente e report dipendono da questa interfaccia, non dalla sorgente.
Un adattatore nuovo (S3, OpenSearch, catalogo EJ200) deve solo implementarla
e superare la suite `tests/test_kb_contract.py`.
"""

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict


class _Entry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DocumentInfo(_Entry):
    """Documento di riferimento disponibile come file di testo a righe.

    `code` raggruppa più issue della stessa pubblicazione; `kind` è il tipo
    (per EJ200: RN, EF, RDR); `published` e `partial` descrivono lo stato.
    """

    key: str
    path: Path
    version: str | None = None
    title: str = ""
    code: str | None = None
    kind: str | None = None
    published: bool = True
    partial: bool = False


class TaskLocation(_Entry):
    """Dove sta un task dentro un documento: righe iniziale e finale, incluse, da 1."""

    manual_key: str
    task: str
    document: DocumentInfo
    line_start: int
    line_end: int

    @property
    def n_lines(self) -> int:
        return self.line_end - self.line_start + 1


class MachineTagEntry(_Entry):
    tag: str
    function: str | None = None


class ProcessSheetEntry(_Entry):
    code: str
    edition: str | None = None
    treatment: str | None = None
    engine_families: tuple[str, ...] = ()


class DrRecommendation(_Entry):
    serial_number: str
    conditions: tuple[int, ...]
    procedure: str
    reference: str | None = None
    manual: str | None = None
    tasks: tuple[str, ...] = ()


class KnowledgeBase(Protocol):
    """Ogni metodo può sollevare SourceUnavailableError se la sorgente non risponde."""

    @property
    def version(self) -> str:
        """Identificativo della conoscenza usata: finisce nel report."""
        ...

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        """Documenti che rispondono a un nome o a un codice. Più di un codice = ambiguo."""
        ...

    def find_task(self, manual: str, task: str) -> TaskLocation | None: ...

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None: ...

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None: ...

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]: ...

    def stats(self) -> dict[str, int]: ...
