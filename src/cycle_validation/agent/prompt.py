"""Prompt e schema dell'output per il giudizio su un'operazione."""

import hashlib
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cycle_validation.config import AgentSettings
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.errors import ConfigError
from cycle_validation.kb.documents import numbered_lines
from cycle_validation.kb.port import TaskLocation
from cycle_validation.verdict.citations import Citation

OPERATION_PROMPT_FILE = "operation_check.md"


class Judgement(StrEnum):
    COERENTE = "coerente"
    CONTRADDETTO = "contraddetto"
    NON_VERIFICABILE = "non_verificabile"


class OperationJudgement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    judgement: Judgement
    rationale: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)


def judgement_schema() -> dict[str, Any]:
    """Schema JSON dell'output: chiuso, senza campi opzionali, adatto all'output strutturato."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["judgement", "rationale", "citations"],
        "properties": {
            "judgement": {"type": "string", "enum": [item.value for item in Judgement]},
            "rationale": {"type": "string"},
            "citations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["file", "line", "quote"],
                    "properties": {
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "quote": {"type": "string"},
                    },
                },
            },
        },
    }


def load_prompt(prompts_dir: Path, name: str) -> str:
    path = prompts_dir / name
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ConfigError(f"Prompt non trovato: {path} ({exc})") from exc


def prompt_version(*texts: str) -> str:
    """Impronta dei prompt usati: entra nel report e rende confrontabili i run."""
    digest = hashlib.sha256("\n---\n".join(texts).encode("utf-8"))
    return digest.hexdigest()[:12]


def _header(cycle: Cycle, operation: Operation, facts: Sequence[str]) -> list[str]:
    lines = [
        f"Operazione {operation.operation_number}",
        f"Descrizione nel ciclo: {operation.operation_description}",
    ]
    if operation.task_codes:
        lines.append(f"Task code citati: {', '.join(operation.task_codes)}")
    if cycle.engine_model:
        lines.append(f"Motore: {cycle.engine_model}")
    if facts:
        lines.append("Fatti già verificati dal codice (non vanno cercati):")
        lines.extend(f"- {fact}" for fact in facts)
    return lines


def _where(location: TaskLocation) -> str:
    label = f"task {location.task}" if location.task else "documento intero"
    return f"{location.document.path} ({label}, righe {location.line_start}-{location.line_end})"


def build_operation_prompt(
    cycle: Cycle,
    operation: Operation,
    facts: Sequence[str],
    locations: Sequence[TaskLocation],
    *,
    inline: bool,
    settings: AgentSettings,
) -> str:
    lines = _header(cycle, operation, facts)
    lines.append("")
    if inline:
        lines.append("Testo di riferimento, con il numero di riga di ciascun file:")
        for location in locations:
            lines.append("")
            lines.append(f"File: {_where(location)}")
            lines.extend(
                numbered_lines(location.document.path, location.line_start, location.line_end)
            )
        lines.append("")
        lines.append("Non hai tool: giudica sul testo qui sopra.")
    else:
        lines.append("Documenti di riferimento, da consultare con Grep e Read:")
        lines.extend(f"- {_where(location)}" for location in locations)
        lines.append("")
        lines.append(
            "Cerca con Grep (path = file), poi leggi con Read solo il paragrafo: "
            f"offset = riga del match - {settings.read_before}, limit = {settings.read_window}."
        )
    lines.append("Nelle citazioni usa il percorso del file così come è scritto qui.")
    return "\n".join(lines)
