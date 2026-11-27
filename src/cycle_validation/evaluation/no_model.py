"""Prova senza modello (27-11 notte): tutti i controlli del codice, a costo zero.

Al posto del modello una sessione finta risponde sempre «non verificabile» (e «le lingue sono
uguali»): restano solo gli esiti decisi dal codice (task, schede, macchine, numeri, limiti e
azioni tra le lingue, DR). Gli errori che trova questa prova li trova sempre, in ogni prova
con il modello: è il modo gratis di misurare una regola nuova del codice su piccolo e grande
prima di una campagna (`eval senza-modello`)."""

from typing import Any

from cycle_validation.agent.session import SessionOutcome, SessionRequest, SessionStatus
from cycle_validation.config import Settings

RATIONALE = "Prova senza modello: nessun giudizio del modello."


def _answer(schema: dict[str, Any]) -> dict[str, Any] | None:
    properties = schema.get("properties", {})
    if "languages" in properties:
        return {"languages": "uguali", "rationale": RATIONALE}
    if "judgement" in properties:
        return {"judgement": "non_verificabile", "rationale": RATIONALE, "citations": []}
    return None  # lettura del PDF con il modello: senza modello non si fa


class ModelFreeSession:
    """Una `AgentSession` che non chiama nessun modello e non costa niente."""

    def __init__(self) -> None:
        self.calls = 0

    async def run(self, request: SessionRequest) -> SessionOutcome:
        self.calls += 1
        output = _answer(request.output_schema)
        if output is None:
            return SessionOutcome(status=SessionStatus.ERROR, error="senza modello", attempts=1)
        return SessionOutcome(status=SessionStatus.OK, output=output, attempts=1)


def model_free_settings(settings: Settings) -> Settings:
    """Le stesse impostazioni, senza niente che chiami un modello o ripeta sessioni inutili:
    niente trascrizione delle pagine fotografate, niente seconda ricerca, niente conferme."""
    agent = settings.agent.model_copy(
        update={
            "transcribe_model": None,
            "search_when_unverifiable": False,
            "confirm_contradiction": 0,
        }
    )
    return settings.model_copy(update={"agent": agent})
