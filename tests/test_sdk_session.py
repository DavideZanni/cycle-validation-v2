import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from claude_agent_sdk import ProcessError, ResultError, ResultMessage

from cycle_validation.agent import sdk_session
from cycle_validation.agent.sdk_session import SdkAgentSession, outcome_from_result
from cycle_validation.agent.session import SessionRequest, SessionStatus
from cycle_validation.config import AgentSettings

FILE = Path(__file__).resolve()


def result(**fields: Any) -> ResultMessage:
    base: dict[str, Any] = {
        "subtype": "success",
        "duration_ms": 1200,
        "duration_api_ms": 1000,
        "is_error": False,
        "num_turns": 2,
        "session_id": "s",
        "total_cost_usd": 0.002,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_read_input_tokens": 3,
            "cache_creation_input_tokens": 1,
        },
        "result": "",
        "structured_output": {"judgement": "coerente"},
    }
    base.update(fields)
    return ResultMessage(**base)


def request(**fields: Any) -> SessionRequest:
    base: dict[str, Any] = {
        "session_id": "op/001",
        "system_prompt": "sys",
        "prompt": "p",
        "output_schema": {"type": "object"},
    }
    base.update(fields)
    return SessionRequest(**base)


def test_success_is_translated_with_usage() -> None:
    outcome = outcome_from_result(result())
    assert outcome.status is SessionStatus.OK
    assert outcome.output == {"judgement": "coerente"}
    assert (outcome.usage.input_tokens, outcome.usage.cache_write_tokens) == (10, 1)
    assert outcome.usage.turns == 2
    assert outcome.usage.sessions == 1


def test_max_turns() -> None:
    assert outcome_from_result(result(subtype="error_max_turns")).status is SessionStatus.MAX_TURNS


def test_error_result() -> None:
    outcome = outcome_from_result(result(is_error=True, subtype="error_during_execution"))
    assert outcome.status is SessionStatus.ERROR


def test_missing_structured_output() -> None:
    outcome = outcome_from_result(result(structured_output=None))
    assert outcome.status is SessionStatus.INVALID_OUTPUT


def test_no_result_is_an_error() -> None:
    assert outcome_from_result(None).status is SessionStatus.ERROR


def test_options_without_tools_have_no_tools_and_no_hooks() -> None:
    options = SdkAgentSession(AgentSettings()).build_options(request())
    assert options.tools == []
    assert options.allowed_tools == []
    assert not options.hooks
    assert options.setting_sources == []
    assert options.strict_mcp_config is True
    assert options.permission_mode == "dontAsk"
    assert options.extra_args == {"no-session-persistence": None}  # nessuna chat su disco
    assert options.output_format == {"type": "json_schema", "schema": {"type": "object"}}


def test_options_with_tools_are_restricted_and_hooked() -> None:
    settings = AgentSettings(model="haiku", aws_region="eu-south-1", effort="low")
    options = SdkAgentSession(settings).build_options(
        request(use_tools=True, allowed_files=(FILE,), max_turns=7)
    )
    assert options.tools == ["Read", "Grep"]
    assert options.max_turns == 7
    assert options.model == "haiku"
    assert options.cwd == FILE.parent
    assert options.hooks and "PreToolUse" in options.hooks
    assert options.env["CLAUDE_CODE_USE_BEDROCK"] == "1"
    assert options.env["AWS_REGION"] == "eu-south-1"
    assert options.effort == "low"
    assert not any("KEY" in name or "SECRET" in name for name in options.env)


def test_run_writes_transcript_and_returns_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_query(*, prompt: str, options: Any):  # type: ignore[no-untyped-def]
        yield SimpleNamespace(kind="progress")
        yield result()

    monkeypatch.setattr(sdk_session, "query", fake_query)
    session = SdkAgentSession(AgentSettings(save_transcripts=True), tmp_path / "t")
    outcome = asyncio.run(session.run(request()))
    assert outcome.status is SessionStatus.OK
    assert (tmp_path / "t" / "op_001.jsonl").read_text(encoding="utf-8").count("\n") == 2


def test_error_detail_names_the_failure_without_copying_the_result_text() -> None:
    outcome = outcome_from_result(
        result(
            is_error=True,
            subtype="error_during_execution",
            result="La sede va rettificata a 45,00 mm",
            errors=["testo riportato dal processo"],
            api_error_status=429,
            terminal_reason="api_error",
        )
    )
    assert outcome.status is SessionStatus.ERROR
    assert outcome.error == "HTTP 429: error_during_execution (api_error)"


def _failing_query(*messages: Any, error: Exception):  # type: ignore[no-untyped-def]
    async def fake_query(*, prompt: str, options: Any):  # type: ignore[no-untyped-def]
        for message in messages:
            yield message
        raise error

    return fake_query


def test_max_turns_reported_before_the_process_exits_is_still_max_turns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # l'SDK consegna il risultato e poi solleva ResultError perché il processo esce con errore:
    # l'esito e i consumi del risultato non vanno persi, e MAX_TURNS non va ritentato
    data = {"subtype": "error_max_turns", "is_error": True}
    monkeypatch.setattr(
        sdk_session,
        "query",
        _failing_query(
            result(subtype="error_max_turns", is_error=True, structured_output=None),
            error=ResultError("Command failed", data=data, exit_code=1),
        ),
    )
    outcome = asyncio.run(SdkAgentSession(AgentSettings()).run(request()))
    assert outcome.status is SessionStatus.MAX_TURNS
    assert outcome.usage.input_tokens == 10


def test_a_result_error_without_a_result_message_is_read_from_the_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = {"subtype": "success", "is_error": True, "api_error_status": 529, "result": "API Error"}
    error = ResultError("Command failed", data=data, exit_code=1)
    monkeypatch.setattr(sdk_session, "query", _failing_query(error=error))
    outcome = asyncio.run(SdkAgentSession(AgentSettings()).run(request()))
    assert outcome.status is SessionStatus.ERROR
    assert outcome.error == "HTTP 529: success"


def test_a_process_failure_reports_its_exit_code_but_not_its_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = ProcessError("Command failed", exit_code=2, stderr="RETTIFICARE LA SEDE a 46,00 mm")
    monkeypatch.setattr(sdk_session, "query", _failing_query(error=error))
    outcome = asyncio.run(SdkAgentSession(AgentSettings()).run(request()))
    assert outcome.status is SessionStatus.ERROR
    assert outcome.error == "ProcessError (exit code 2)"


def test_usage_carries_model_time_separately_from_session_time() -> None:
    usage = outcome_from_result(result()).usage
    assert (usage.duration_ms, usage.api_duration_ms) == (1200, 1000)


def test_run_measures_the_wall_time_of_the_whole_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def slow_query(*, prompt: str, options: Any):  # type: ignore[no-untyped-def]
        await asyncio.sleep(0.05)
        yield result()

    monkeypatch.setattr(sdk_session, "query", slow_query)
    outcome = asyncio.run(SdkAgentSession(AgentSettings(save_transcripts=False)).run(request()))
    assert outcome.usage.wall_ms >= 50


def test_wall_time_is_measured_also_when_the_process_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sdk_session, "query", _failing_query(error=ProcessError("x", exit_code=1)))
    outcome = asyncio.run(SdkAgentSession(AgentSettings(save_transcripts=False)).run(request()))
    assert outcome.status is SessionStatus.ERROR
    assert outcome.usage.wall_ms >= 0


def test_a_request_can_ask_for_its_own_effort() -> None:
    session = SdkAgentSession(AgentSettings(effort="low"))
    assert session.build_options(request(effort="high")).effort == "high"
    assert session.build_options(request()).effort == "low"


def test_tools_without_allowed_files_are_switched_off() -> None:
    """27-11 (revisione del codice): senza file ammessi mancherebbe l'hook che limita Read e
    Grep a quei file. Oggi non succede, ma la sessione non deve avere i tool liberi."""
    options = SdkAgentSession(AgentSettings()).build_options(request(use_tools=True))
    assert options.tools == []
    assert not options.hooks
