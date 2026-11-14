"""Porta dell'estrazione: dal PDF letto al ciclo strutturato."""

from typing import Protocol

from cycle_validation.domain.check import Usage
from cycle_validation.domain.cycle import Cycle
from cycle_validation.ingest.pdf import PdfDocument


class CycleExtractor(Protocol):
    async def extract(self, pdf: PdfDocument) -> tuple[Cycle, Usage]:
        """Solleva ExtractionError se il ciclo non è interpretabile."""
        ...
