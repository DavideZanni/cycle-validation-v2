"""Ciclo già estratto, letto da un file JSON. Serve per test, golden set e confronti:
toglie l'estrazione dall'equazione quando si vuole misurare solo la validazione."""

import json
from pathlib import Path

from pydantic import ValidationError

from cycle_validation.domain.check import Usage
from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import ExtractionError
from cycle_validation.ingest.pdf import PdfDocument


def load_cycle(path: Path) -> Cycle:
    try:
        return Cycle.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"Impossibile leggere il ciclo da {path}: {exc}") from exc
    except ValidationError as exc:
        # dove e che tipo di errore, non il valore rifiutato: è testo del ciclo
        first = exc.errors(include_input=False, include_url=False)[0]
        where = ".".join(str(part) for part in first["loc"])
        raise ExtractionError(
            f"Il ciclo in {path} non è valido ({exc.error_count()} errori). "
            f"Il primo: {where} ({first['type']})."
        ) from exc


class FileCycleExtractor:
    def __init__(self, path: Path) -> None:
        self._path = path

    async def extract(self, pdf: PdfDocument) -> tuple[Cycle, Usage]:
        return load_cycle(self._path), Usage()
