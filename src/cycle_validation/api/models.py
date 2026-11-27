"""Modelli di richiesta e di risposta: stessi campi e stessi vincoli del sistema attuale."""

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
YES = {"sì", "si", "yes", "true", "1", "y", "s"}
NO = {"no", "false", "0", "n"}


class ConversationRequest(BaseModel):
    """`answer` sì/no, oppure i selettori DR del passaggio successivo."""

    model_config = ConfigDict(extra="ignore")

    answer: str | None = None
    dr_serial_number: str | None = None
    dr_condition: Any = None

    @field_validator("answer")
    @classmethod
    def _known_answer(cls, value: str | None) -> str | None:
        if value is not None and value.strip().casefold() not in YES | NO:
            raise ValueError("La risposta deve essere sì o no.")
        return value

    @property
    def is_yes(self) -> bool | None:
        if self.answer is None:
            return None
        return self.answer.strip().casefold() in YES

    @property
    def has_selectors(self) -> bool:
        """Almeno uno dei selettori DR ha un valore."""
        return bool(self.dr_serial_number) or self.dr_condition not in (None, "", [])

    @model_validator(mode="after")
    def _selectors_need_dr(self) -> "ConversationRequest":
        if self.is_yes is False and self.has_selectors:
            raise ValueError("Con risposta no i selettori DR non sono ammessi.")
        # Serial number e condition sono facoltativi: il passo DR può arrivare con i due campi
        # vuoti (il frontend li manda anche così, se si toglie l'obbligo). Serve però che ci
        # siano almeno i nomi dei campi, altrimenti la richiesta non dice niente.
        dr_step = {"dr_serial_number", "dr_condition"} & self.model_fields_set
        if self.answer is None and not self.has_selectors and not dr_step:
            raise ValueError("Serve una risposta oppure i campi DR (anche vuoti).")
        return self


class ChatSession(BaseModel):
    """Sessione civile: `username` del body viene ricevuto ma l'owner è l'SSO verificato."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(pattern=SESSION_ID.pattern)
    name: str
    username: str
    createdAt: str
    updatedAt: str
    useCase: str = "cv"
    messages: list[Any] = Field(default_factory=list)
    file_key: str | None = None


class Ej200Session(BaseModel):
    """Sessione EJ200: campi extra (`username`, `track`, ...) ignorati; li imposta il server."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(pattern=SESSION_ID.pattern)
    name: str
    createdAt: str
    updatedAt: str
    useCase: str = "ej200"
    messages: list[Any] = Field(default_factory=list)


class Ej200Feedback(BaseModel):
    model_config = ConfigDict(extra="allow")

    sessionId: str = Field(pattern=SESSION_ID.pattern)
    vote: Literal["up", "down"]
