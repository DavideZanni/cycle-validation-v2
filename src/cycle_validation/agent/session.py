"""Porta verso il modello: una richiesta, un esito. Tutto il resto del codice dipende
da questa interfaccia, non dal Claude Agent SDK, e si testa senza rete."""

from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from cycle_validation.domain.check import Usage


class SessionStatus(StrEnum):
    OK = "ok"
    MAX_TURNS = "max_turns"
    ERROR = "error"
    INVALID_OUTPUT = "invalid_output"


class SessionRequest(BaseModel):
    """Una sessione isolata. `allowed_files` sono i soli file che l'agente può aprire."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str
    system_prompt: str
    prompt: str
    output_schema: dict[str, Any]
    use_tools: bool = False
    allowed_files: tuple[Path, ...] = ()
    max_turns: int = 3


class SessionOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SessionStatus
    output: dict[str, Any] | None = None
    error: str = ""
    usage: Usage = Field(default_factory=Usage)
    attempts: int = 1


class AgentSession(Protocol):
    async def run(self, request: SessionRequest) -> SessionOutcome: ...
