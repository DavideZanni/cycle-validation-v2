"""Parser di layout del modulo PVRM320 (cicli EJ200): zero token, ripetibile.

Il layout reale dei PDF non è noto a questa macchina: le etichette e le espressioni
regolari stanno in `Pvrm320Layout` e si adattano senza toccare l'algoritmo. Quello qui
descritto è un layout di riferimento, a blocchi:

    PVRM320 ...                      intestazione (ripetuta a ogni pagina)
    CYCLE: <codice>   DESCRIPTION: <testo>   ENGINE: EJ200   REPAIR CODE: <codice>
    REFERENCES: RN-100 Issue 2; EF-200; RDR-300
    OP 0010 <descrizione, anche su più righe>
    MACHINE: <targa>
    DM: <data-module>, <data-module>
    NOTE: <testo>                    NON è un'operazione e non entra nelle descrizioni

Le operazioni ripetute su più pagine (stesso numero) si uniscono in una sola.
"""

import re
from dataclasses import dataclass
from typing import Any

from cycle_validation.domain.check import Usage
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.errors import ExtractionError
from cycle_validation.extract.pvrm320_report import is_pvrm320_report, parse_pvrm320_report
from cycle_validation.ingest.pdf import PdfDocument

_PAGE_MARKER_LINE = re.compile(r"^PVRM320\b", re.IGNORECASE)


@dataclass(frozen=True)
class Pvrm320Layout:
    marker: re.Pattern[str] = re.compile(r"PVRM320", re.IGNORECASE)
    cycle_code: re.Pattern[str] = re.compile(r"^CYCLE:\s*(.+)$", re.IGNORECASE)
    description: re.Pattern[str] = re.compile(r"^DESCRIPTION:\s*(.+)$", re.IGNORECASE)
    engine: re.Pattern[str] = re.compile(r"^ENGINE:\s*(.+)$", re.IGNORECASE)
    repair_code: re.Pattern[str] = re.compile(r"^REPAIR CODE:\s*(.+)$", re.IGNORECASE)
    references: re.Pattern[str] = re.compile(r"^REFERENCES:\s*(.+)$", re.IGNORECASE)
    operation: re.Pattern[str] = re.compile(
        r"^OP\s+(?P<number>\d+)\s*(?:\(cont\.?\))?\s*(?P<text>.*)$", re.IGNORECASE
    )
    machine: re.Pattern[str] = re.compile(r"^MACHINE:\s*(.+)$", re.IGNORECASE)
    data_modules: re.Pattern[str] = re.compile(r"^DM:\s*(.+)$", re.IGNORECASE)
    note: re.Pattern[str] = re.compile(r"^NOTE\b:?\s*(.*)$", re.IGNORECASE)
    issue: re.Pattern[str] = re.compile(
        r"^(?P<code>\S+)\s+(?:issue|iss\.?)\s+(?P<issue>\S+)$", re.IGNORECASE
    )


@dataclass
class _Op:
    number: str
    text: list[str]
    machine: str | None = None
    modules: list[str] | None = None
    page: int | None = None


def _sources(raw: str, layout: Pvrm320Layout) -> list[Source]:
    sources: list[Source] = []
    for part in (item.strip() for item in raw.split(";")):
        if not part:
            continue
        match = layout.issue.match(part)
        if match:
            sources.append(Source(manual=match["code"], issue=match["issue"]))
        else:
            sources.append(Source(manual=part))
    return sources


def parse_pvrm320(pdf: PdfDocument, layout: Pvrm320Layout | None = None) -> Cycle:
    if layout is None and is_pvrm320_report(pdf):
        return parse_pvrm320_report(pdf)
    layout = layout or Pvrm320Layout()
    if not layout.marker.search(pdf.text):
        raise ExtractionError("Il PDF non ha il layout PVRM320.")
    head: dict[str, Any] = {}
    sources: list[Source] = []
    operations: dict[str, _Op] = {}
    current: _Op | None = None
    in_note = False
    for page in pdf.pages:
        for raw in page.text.splitlines():
            line = raw.strip()
            if not line or _PAGE_MARKER_LINE.match(line):
                continue
            if layout.note.match(line):
                in_note = True
                continue
            if (m := layout.operation.match(line)) is not None:
                in_note = False
                current = operations.setdefault(m["number"], _Op(m["number"], [], page=page.number))
                if m["text"].strip():
                    current.text.append(m["text"].strip())
            elif (m := layout.machine.match(line)) is not None and current is not None:
                in_note = False
                current.machine = m[1].strip()
            elif (m := layout.data_modules.match(line)) is not None and current is not None:
                in_note = False
                found = [x.strip() for x in m[1].split(",") if x.strip()]
                current.modules = [*(current.modules or []), *found]
            elif (m := layout.cycle_code.match(line)) is not None:
                head["cycle_code"] = m[1].strip()
            elif (m := layout.description.match(line)) is not None:
                head["cycle_description"] = m[1].strip()
            elif (m := layout.engine.match(line)) is not None:
                head["engine_model"] = m[1].strip()
            elif (m := layout.repair_code.match(line)) is not None:
                head["repair_code"] = m[1].strip()
            elif (m := layout.references.match(line)) is not None:
                sources.extend(_sources(m[1], layout))
            elif current is not None and not in_note:
                current.text.append(line)
    if not operations:
        raise ExtractionError("Nessuna operazione trovata nel layout PVRM320.")
    return Cycle(
        **head,
        sources=sources,
        operations=[
            Operation(
                operation_number=op.number,
                operation_description=" ".join(op.text),
                machine_tag=op.machine,
                task_codes=op.modules or [],
                page=op.page,
            )
            for op in operations.values()
        ],
    )


class Pvrm320LayoutExtractor:
    def __init__(self, layout: Pvrm320Layout | None = None) -> None:
        self._layout = layout

    async def extract(self, pdf: PdfDocument) -> tuple[Cycle, Usage]:
        return parse_pvrm320(pdf, self._layout), Usage()
