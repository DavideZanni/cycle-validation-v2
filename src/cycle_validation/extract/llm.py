"""Estrattore con output strutturato: una sessione senza tool, schema chiuso di `Cycle`."""

from typing import Any

from cycle_validation.agent.runner import run_sessions
from cycle_validation.agent.session import AgentSession, SessionRequest, SessionStatus
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import Usage
from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import ExtractionError
from cycle_validation.ingest.pdf import PdfDocument

EXTRACTION_SESSION_ID = "extract"


def _nullable(kind: str) -> dict[str, Any]:
    return {"type": [kind, "null"]}


def cycle_schema() -> dict[str, Any]:
    """Schema JSON chiuso, con tutti i campi richiesti e null per i dati assenti."""

    def obj(properties: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": list(properties),
            "properties": properties,
        }

    source = obj(
        {
            "manual": {"type": "string"},
            "task": _nullable("string"),
            "repair_code": _nullable("string"),
            "issue": _nullable("string"),
            "section": _nullable("string"),
        }
    )
    sheet = {
        "type": ["object", "null"],
        "additionalProperties": False,
        "required": ["code"],
        "properties": {"code": {"type": "string"}},
    }
    operation = obj(
        {
            "operation_number": {"type": "string"},
            "operation_description": {"type": "string"},
            "repair_code": _nullable("string"),
            "machine_tag": _nullable("string"),
            "task_codes": {"type": "array", "items": {"type": "string"}},
            "process_sheet": sheet,
        }
    )
    return obj(
        {
            "cycle_code": _nullable("string"),
            "cycle_description": _nullable("string"),
            "engine_model": _nullable("string"),
            "operation_type": _nullable("string"),
            "repair_code": _nullable("string"),
            "sources": {"type": "array", "items": source},
            "operations": {"type": "array", "items": operation},
        }
    )


def pdf_prompt(pdf: PdfDocument) -> str:
    pages = "\n".join(f"<!-- page {page.number} -->\n{page.text}" for page in pdf.pages)
    return f"Testo del PDF {pdf.name}:\n\n{pages}"


class LlmCycleExtractor:
    def __init__(self, session: AgentSession, settings: AgentSettings, system_prompt: str) -> None:
        self._session = session
        self._settings = settings
        self._system_prompt = system_prompt

    async def extract(self, pdf: PdfDocument) -> tuple[Cycle, Usage]:
        request = SessionRequest(
            session_id=EXTRACTION_SESSION_ID,
            system_prompt=self._system_prompt,
            prompt=pdf_prompt(pdf),
            output_schema=cycle_schema(),
            use_tools=False,
            max_turns=self._settings.extraction_max_turns,
            effort=self._settings.extraction_effort,
        )
        (outcome,) = await run_sessions(
            self._session,
            [request],
            concurrency=1,
            retries=self._settings.retries,
            backoff_s=self._settings.retry_backoff_s,
            invalid_output_retries=self._settings.invalid_output_retries,
            validate=Cycle.model_validate,
            timeout_s=self._settings.extraction_timeout_s,
        )
        if outcome.status is not SessionStatus.OK or outcome.output is None:
            raise ExtractionError(
                f"Estrazione del ciclo non riuscita ({outcome.status.value}): {outcome.error}"
            )
        return Cycle.model_validate(outcome.output), outcome.usage
