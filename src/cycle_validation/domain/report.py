"""Report di un run: metadati, ciclo, esiti, conteggi, tempi, consumi, diagnostica."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cycle_validation.domain.check import CheckResult, Usage
from cycle_validation.domain.cycle import Cycle


class CycleStatus(StrEnum):
    COMPLETO = "completo"
    BLOCCATO = "bloccato"
    PARZIALE = "parziale"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PipelineError(_Strict):
    """Guasto tecnico non bloccante. Non contiene testo del ciclo né dei documenti."""

    stage: str
    target: str = ""
    message: str


class RunMeta(_Strict):
    run_id: str
    started_at: datetime
    pdf_name: str
    pdf_sha256: str
    profile: str
    selectors: dict[str, Any] = Field(default_factory=dict)
    knowledge_version: str
    model: str
    prompt_version: str
    tool_version: str


class Counts(_Strict):
    total: int = 0
    corretto: int = 0
    warning: int = 0
    errato: int = 0
    non_applicabile: int = 0
    errors_ratio: float = 0.0


class Report(_Strict):
    meta: RunMeta
    status: CycleStatus
    cycle: Cycle
    results: list[CheckResult]
    counts: Counts
    timings_ms: dict[str, int] = Field(default_factory=dict)
    usage: Usage = Field(default_factory=Usage)
    pipeline_errors: list[PipelineError] = Field(default_factory=list)
    session_modes: dict[str, int] = Field(default_factory=dict)
