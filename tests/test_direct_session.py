"""MG54-MG56-MG59: la sessione diretta su Bedrock, con un client finto (niente rete)."""

import asyncio
from pathlib import Path
from typing import Any

from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

from cycle_validation.agent.direct_session import (
    OUTPUT_TOOL,
    REMINDER,
    DirectBedrockSession,
    price_of,
)
from cycle_validation.agent.factory import make_agent_session
from cycle_validation.agent.sdk_session import SdkAgentSession
from cycle_validation.agent.session import SessionRequest, SessionStatus
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import Usage as OurUsage

SCHEMA = {
    "type": "object",
    "properties": {"judgement": {"type": "string"}},
    "required": ["judgement"],
}


def _message(*blocks: Any, stop: str = "tool_use") -> Message:
    return Message(
        id="m",
        type="message",
        role="assistant",
        model="finto",
        content=list(blocks),
        stop_reason=stop,  # type: ignore[arg-type]
        stop_sequence=None,
        usage=Usage(input_tokens=1000, output_tokens=100, cache_read_input_tokens=500),
    )


def _call(name: str, data: dict[str, Any], n: int = 1) -> ToolUseBlock:
    return ToolUseBlock(id=f"t{n}", type="tool_use", name=name, input=data)


class FakeClient:
    def __init__(self, replies: list[Any]) -> None:
        self.replies = replies
        self.calls: list[dict[str, Any]] = []
        self.messages = self
        self.closed = False

    async def create(self, **kwargs: Any) -> Message:
        import copy

        self.calls.append(copy.deepcopy(kwargs))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply  # type: ignore[no-any-return]

    async def close(self) -> None:
        self.closed = True


def _session(client: FakeClient, **changes: Any) -> DirectBedrockSession:
    settings = AgentSettings(model="eu.finto-haiku", session_backend="diretta", **changes)
    return DirectBedrockSession(settings, client_factory=lambda _: client)


def _request(**changes: Any) -> SessionRequest:
    return SessionRequest(
        session_id="op-001-010",
        system_prompt="sistema",
        prompt="domanda",
        output_schema=SCHEMA,
        **changes,
    )


def test_an_inline_session_answers_with_the_output_tool() -> None:
    client = FakeClient([_message(_call(OUTPUT_TOOL, {"judgement": "coerente"}))])
    outcome = asyncio.run(_session(client).run(_request()))
    assert outcome.status is SessionStatus.OK and outcome.output == {"judgement": "coerente"}
    (call,) = client.calls
    assert [tool["name"] for tool in call["tools"]] == [OUTPUT_TOOL]  # niente Read e Grep
    assert call["tools"][0]["input_schema"] == SCHEMA
    assert call["model"] == "eu.finto-haiku"
    assert call["output_config"] == {"effort": "low"}
    assert "cache_control" not in str(call)  # cache spenta
    assert outcome.usage.sessions == 1 and outcome.usage.turns == 1
    assert outcome.usage.cost_usd == price_of(outcome.usage, AgentSettings())
    assert client.closed


def test_read_and_grep_follow_the_same_rules_as_the_hook(tmp_path: Path) -> None:
    manual = tmp_path / "manuale.txt"
    manual.write_text("\n".join(f"riga {n}" for n in range(1, 101)), encoding="utf-8")
    other = tmp_path / "altro.txt"
    other.write_text("segreto\n", encoding="utf-8")
    client = FakeClient(
        [
            _message(_call("Grep", {"pattern": "riga 5[0-2]$", "path": str(manual)})),
            _message(_call("Read", {"file_path": str(manual), "offset": 1, "limit": 100}, 2)),
            _message(_call("Read", {"file_path": str(other), "offset": 1, "limit": 5}, 3)),
            _message(_call("Read", {"file_path": str(manual), "offset": 49, "limit": 3}, 4)),
            _message(_call(OUTPUT_TOOL, {"judgement": "coerente"}, 5)),
        ]
    )
    request = _request(use_tools=True, allowed_files=(manual,), max_turns=10)
    outcome = asyncio.run(_session(client).run(request))
    assert outcome.status is SessionStatus.OK
    assert [t["name"] for t in client.calls[0]["tools"]] == ["Read", "Grep", OUTPUT_TOOL]

    def last_result(n: int) -> dict[str, Any]:
        return client.calls[n]["messages"][-1]["content"][0]  # type: ignore[no-any-return]

    assert last_result(1)["content"] == "50: riga 50\n51: riga 51\n52: riga 52"
    assert last_result(2)["is_error"] and "GRASP" in last_result(2)["content"]
    assert last_result(3)["is_error"] and "segreto" not in str(last_result(3))
    assert last_result(4)["content"] == "49: riga 49\n50: riga 50\n51: riga 51"
    assert outcome.usage.turns == 5


def test_no_answer_gets_a_reminder_then_stops_at_max_turns() -> None:
    text = TextBlock(type="text", text="penso che sia coerente")
    client = FakeClient([_message(text, stop="end_turn"), _message(text, stop="end_turn")])
    outcome = asyncio.run(_session(client).run(_request(max_turns=2)))
    assert outcome.status is SessionStatus.MAX_TURNS
    assert client.calls[1]["messages"][-1]["content"][0]["text"] == REMINDER


def test_a_failure_keeps_only_the_error_type() -> None:
    client = FakeClient([RuntimeError("testo del ciclo che non deve uscire")])
    outcome = asyncio.run(_session(client).run(_request()))
    assert outcome.status is SessionStatus.ERROR and outcome.error == "RuntimeError"
    assert client.closed


def test_cache_points_and_shared_text() -> None:
    client = FakeClient(
        [
            _message(TextBlock(type="text", text="..."), stop="end_turn"),
            _message(_call(OUTPUT_TOOL, {"judgement": "coerente"})),
        ]
    )
    request = _request(shared_context="testo del manuale", max_turns=3)
    asyncio.run(_session(client, direct_cache=True).run(request))
    first, second = client.calls
    assert first["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert first["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    shared, question = first["messages"][0]["content"]
    assert shared == {
        "type": "text",
        "text": "testo del manuale",
        "cache_control": {"type": "ephemeral"},
    }
    assert question == {"type": "text", "text": "domanda"}
    # dal secondo turno anche la storia: punto di cache sull'ultimo messaggio
    assert second["messages"][-1]["content"][-1]["cache_control"] == {"type": "ephemeral"}


def test_the_price_uses_the_settings() -> None:
    usage = OurUsage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_tokens=1_000_000,
        cache_write_tokens=1_000_000,
    )
    assert round(price_of(usage, AgentSettings()), 6) == round(0.10 + 0.50 + 0.125 + 0.01, 6)


def test_the_backend_comes_from_the_settings() -> None:
    assert isinstance(make_agent_session(AgentSettings()), SdkAgentSession)
    direct = make_agent_session(AgentSettings(session_backend="diretta"))
    assert isinstance(direct, DirectBedrockSession)


def test_the_smoke_command_reports_the_call(monkeypatch: Any, tmp_path: Path) -> None:
    """`eval chiamata-diretta`: una domanda finta, per provare accesso e parametri."""
    from typer.testing import CliRunner

    from cycle_validation import cli
    from cycle_validation.agent import direct_session

    monkeypatch.chdir(tmp_path)
    client = FakeClient([_message(_call(OUTPUT_TOOL, {"risposta": "uguali"}))])
    monkeypatch.setattr(direct_session, "default_client", lambda _: client)
    result = CliRunner().invoke(cli.app, ["eval", "chiamata-diretta"])
    assert result.exit_code == 0, result.output
    assert "Chiamata diretta: ok" in result.output and "uguali" in result.output
    assert client.calls[0]["system"][0]["cache_control"] == {"type": "ephemeral"}
