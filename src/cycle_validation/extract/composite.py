"""Estrazione a cascata: un estrattore principale (per esempio il parser di layout, zero
token) e uno di riserva (LLM) se il principale non riesce o non trova operazioni."""

from cycle_validation.domain.check import Usage
from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import ExtractionError
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.ingest.pdf import PdfDocument


class FallbackCycleExtractor:
    def __init__(self, primary: CycleExtractor, fallback: CycleExtractor) -> None:
        self._primary = primary
        self._fallback = fallback
        self.last_used: str = ""

    async def extract(self, pdf: PdfDocument) -> tuple[Cycle, Usage]:
        usage = Usage()
        try:
            cycle, usage = await self._primary.extract(pdf)
            if cycle.operations:
                self.last_used = "primary"
                return cycle, usage
        except ExtractionError:
            pass
        self.last_used = "fallback"
        fallback_cycle, fallback_usage = await self._fallback.extract(pdf)
        return fallback_cycle, usage + fallback_usage
