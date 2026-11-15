"""Guasti simulati: il modello che non risponde, risponde storto o finisce i passi, la conoscenza
che non si legge, un ritardo su ogni sessione.

Servono a verificare una regola, non a misurare la velocità: **un guasto dà WARNING, mai
ERRATO**. Una variante li dichiara così:

```yaml
nome: guasti
base: baseline
guasti:
  errore: 0.3          # quota di sessioni che falliscono (rete, throttling, servizio giù)
  risposta_storta: 0.2 # quota di risposte che non rispettano lo schema
  budget: 0.1          # quota di sessioni che finiscono i passi
  conoscenza: 0.1      # quota di letture della conoscenza che non riescono
  ritardo_s: 0         # attesa in più per ogni sessione
  seme: 1              # stessi guasti a ogni prova con lo stesso seme
```

Una sessione guasta non chiama il modello: la prova costa meno della baseline. I guasti
dipendono dal seme, dalla ripetizione, dalla richiesta e da quante volte è stata fatta, non
dall'ordine in cui le sessioni partono: con la concorrenza l'ordine cambia, i guasti no.

La lettura del ciclo non si guasta: se fallisce, il caso si ferma con un errore chiaro e senza
esito (lo provano i test di `extract`). Qui si provano i controlli, dove vale la regola.
"""

import asyncio
import random
from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cycle_validation.agent.session import (
    AgentSession,
    SessionOutcome,
    SessionRequest,
    SessionStatus,
)
from cycle_validation.errors import SourceUnavailableError
from cycle_validation.extract.llm import EXTRACTION_SESSION_ID
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    KnowledgeBase,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)


class Faults(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    errore: float = Field(default=0.0, ge=0, le=1)
    risposta_storta: float = Field(default=0.0, ge=0, le=1)
    budget: float = Field(default=0.0, ge=0, le=1)
    conoscenza: float = Field(default=0.0, ge=0, le=1)
    ritardo_s: float = Field(default=0.0, ge=0, le=60)
    seme: int = 0

    @model_validator(mode="after")
    def _shares_fit(self) -> "Faults":
        if self.errore + self.risposta_storta + self.budget > 1:
            raise ValueError("errore + risposta_storta + budget non può superare 1")
        return self


class _Dice:
    """Un numero tra 0 e 1 per ogni (chiave, volta): uguale a ogni prova con lo stesso seme."""

    def __init__(self, seed: int, repetition: int) -> None:
        self._seed = f"{seed}:r{repetition}"
        self._counts: Counter[str] = Counter()

    def roll(self, key: str) -> float:
        self._counts[key] += 1
        return random.Random(f"{self._seed}:{key}:{self._counts[key]}").random()


class FaultySession:
    """Una sessione che a volte si guasta prima di chiamare il modello."""

    def __init__(self, inner: AgentSession, faults: Faults, repetition: int = 1) -> None:
        self._inner = inner
        self._faults = faults
        self._dice = _Dice(faults.seme, repetition)

    async def run(self, request: SessionRequest) -> SessionOutcome:
        faults = self._faults
        if request.session_id == EXTRACTION_SESSION_ID:
            return await self._inner.run(request)
        if faults.ritardo_s:
            await asyncio.sleep(faults.ritardo_s)
        roll = self._dice.roll(request.session_id)
        if roll < faults.errore:
            return SessionOutcome(
                status=SessionStatus.ERROR, error="guasto simulato: il servizio non risponde"
            )
        roll -= faults.errore
        if roll < faults.risposta_storta:
            return SessionOutcome(status=SessionStatus.OK, output={"guasto": "risposta storta"})
        roll -= faults.risposta_storta
        if roll < faults.budget:
            return SessionOutcome(
                status=SessionStatus.MAX_TURNS, error="guasto simulato: passi finiti"
            )
        return await self._inner.run(request)


class FaultyKnowledge:
    """Una conoscenza che a volte non si legge, come un S3 o un Redshift irraggiungibile."""

    def __init__(self, inner: KnowledgeBase, faults: Faults, repetition: int = 1) -> None:
        self._inner = inner
        self._faults = faults
        self._dice = _Dice(faults.seme, repetition)

    def _maybe_fail(self, what: str, *args: Any) -> None:
        if self._dice.roll(f"{what}:{args}") < self._faults.conoscenza:
            raise SourceUnavailableError(f"guasto simulato: {what} non raggiungibile")

    @property
    def version(self) -> str:
        return self._inner.version

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        self._maybe_fail("manuali", manual)
        return self._inner.find_manuals(manual)

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        self._maybe_fail("task", manual, task)
        return self._inner.find_task(manual, task)

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        self._maybe_fail("targhe", tag)
        return self._inner.find_machine_tag(tag)

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        self._maybe_fail("schede", code)
        return self._inner.find_process_sheet(code)

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        self._maybe_fail("recommendation DR", serial_number)
        return self._inner.find_dr_recommendations(serial_number)

    def stats(self) -> dict[str, int]:
        return self._inner.stats()
