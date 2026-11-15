import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from fakes import ScriptedSession

from cycle_validation.agent.session import SessionOutcome, SessionStatus
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import Usage
from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import ExtractionError
from cycle_validation.extract.composite import FallbackCycleExtractor
from cycle_validation.extract.llm import LlmCycleExtractor, cycle_schema
from cycle_validation.ingest.pdf import PdfDocument, PdfPage

SETTINGS = AgentSettings(retry_backoff_s=0)
PDF = PdfDocument(
    name="c.pdf",
    sha256="x",
    size_bytes=1,
    pages=(PdfPage(number=1, text="CICLO C-1"), PdfPage(number=2, text="OPERAZIONE 0010")),
)
GOOD: dict[str, Any] = {
    "cycle_code": "C-1",
    "cycle_description": None,
    "engine_model": "GENX-1B",
    "operation_type": None,
    "repair_code": None,
    "sources": [{"manual": "M1", "task": None, "repair_code": None, "issue": None}],
    "operations": [
        {
            "operation_number": "0010",
            "operation_description": "Pulire",
            "repair_code": None,
            "machine_tag": "TM-1",
            "task_codes": ["T1"],
            "process_sheet": {"code": "SP-1"},
        },
        {
            "operation_number": "0020",
            "operation_description": "Ispezionare",
            "repair_code": None,
            "machine_tag": None,
            "task_codes": [],
            "process_sheet": None,
        },
    ],
}


def extract(script: Any) -> tuple[Cycle, Usage]:
    session = ScriptedSession(script)
    return asyncio.run(LlmCycleExtractor(session, SETTINGS, "sistema").extract(PDF))


def test_schema_is_closed_with_required_fields() -> None:
    schema = cycle_schema()
    assert schema["additionalProperties"] is False
    operation = schema["properties"]["operations"]["items"]
    assert operation["additionalProperties"] is False
    assert set(operation["required"]) == set(operation["properties"])
    assert Cycle.model_validate(GOOD).operations[1].process_sheet is None


def test_extraction_returns_cycle_and_usage() -> None:
    cycle, usage = extract(lambda r, a: GOOD)
    assert cycle.cycle_code == "C-1"
    assert cycle.operations[0].process_sheet is not None
    assert usage.sessions == 1


def test_prompt_carries_the_pages_and_no_tools() -> None:
    session = ScriptedSession(lambda r, a: GOOD)
    asyncio.run(LlmCycleExtractor(session, SETTINGS, "sistema").extract(PDF))
    request = session.requests[0]
    assert "<!-- page 2 -->\nOPERAZIONE 0010" in request.prompt
    assert not request.use_tools
    assert request.max_turns == SETTINGS.extraction_max_turns


def test_invalid_output_is_retried_then_reported() -> None:
    calls: list[int] = []

    def script(request: Any, attempt: int) -> Any:
        calls.append(attempt)
        return {"operations": "no"} if attempt == 1 else GOOD

    assert extract(script)[0].cycle_code == "C-1"
    assert calls == [1, 2]
    with pytest.raises(ExtractionError, match="invalid_output"):
        extract(lambda r, a: {"operations": "no"})


def test_technical_failure_is_an_extraction_error() -> None:
    with pytest.raises(ExtractionError, match="error"):
        extract(lambda r, a: SessionOutcome(status=SessionStatus.ERROR, error="throttling"))


class _Fixed:
    def __init__(self, cycle: Cycle | None, usage: Usage | None = None) -> None:
        self.cycle, self.usage, self.calls = cycle, usage or Usage(), 0

    async def extract(self, pdf: PdfDocument) -> tuple[Cycle, Usage]:
        self.calls += 1
        if self.cycle is None:
            raise ExtractionError("no")
        return self.cycle, self.usage


def test_fallback_is_used_only_when_primary_fails_or_is_empty() -> None:
    good = Cycle.model_validate(GOOD)
    primary, backup = _Fixed(good), _Fixed(good)
    chain = FallbackCycleExtractor(primary, backup)
    assert asyncio.run(chain.extract(PDF))[0] is good
    assert (chain.last_used, backup.calls) == ("primary", 0)
    for broken in (_Fixed(None), _Fixed(Cycle())):
        backup = _Fixed(good, Usage(sessions=1))
        chain = FallbackCycleExtractor(broken, backup)
        cycle, usage = asyncio.run(chain.extract(PDF))
        assert cycle is good and chain.last_used == "fallback" and usage.sessions == 1


# --- ciclo da file -------------------------------------------------------------------------


def test_an_invalid_cycle_file_is_reported_without_quoting_its_content(tmp_path: Path) -> None:
    from cycle_validation.extract.from_file import load_cycle

    path = tmp_path / "ciclo.json"
    path.write_text(
        json.dumps({"operations": [{"operation_number": ["Rettificare a 46,00 mm"]}]}),
        encoding="utf-8",
    )
    with pytest.raises(ExtractionError) as caught:
        load_cycle(path)
    message = str(caught.value)
    assert "46,00" not in message
    assert "operations.0.operation_number" in message  # dove, non che cosa


def test_a_missing_or_malformed_cycle_file_is_an_extraction_error(tmp_path: Path) -> None:
    from cycle_validation.extract.from_file import load_cycle

    with pytest.raises(ExtractionError, match="Impossibile leggere"):
        load_cycle(tmp_path / "manca.json")
    broken = tmp_path / "rotto.json"
    broken.write_text("{non json", encoding="utf-8")
    with pytest.raises(ExtractionError, match="Impossibile leggere"):
        load_cycle(broken)


def test_extraction_can_reason_more_than_the_checks() -> None:
    # Si può risparmiare sul ragionamento dei controlli senza rischiare la lettura del PDF.
    session = ScriptedSession(lambda r, a: GOOD)
    settings = AgentSettings(retry_backoff_s=0, effort="low", extraction_effort="high")
    asyncio.run(LlmCycleExtractor(session, settings, "sistema").extract(PDF))
    assert session.requests[0].effort == "high"
    asyncio.run(LlmCycleExtractor(session, SETTINGS, "sistema").extract(PDF))
    assert session.requests[1].effort is None
