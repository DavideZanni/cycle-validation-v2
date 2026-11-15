import asyncio
from typing import Any

import pytest
from fakes import ONE_CALL, ScriptedSession, ok

from cycle_validation.agent.runner import run_sessions
from cycle_validation.agent.session import SessionOutcome, SessionRequest, SessionStatus

SCHEMA: dict[str, Any] = {"type": "object"}


def req(name: str) -> SessionRequest:
    return SessionRequest(session_id=name, system_prompt="s", prompt="p", output_schema=SCHEMA)


async def no_sleep(_: float) -> None:
    return None


def run(session: ScriptedSession, names: list[str], **kw: Any) -> list[SessionOutcome]:
    options: dict[str, Any] = {
        "concurrency": 4,
        "retries": 2,
        "backoff_s": 1.0,
        "invalid_output_retries": 1,
        "sleep": no_sleep,
    }
    options.update(kw)
    return asyncio.run(run_sessions(session, [req(n) for n in names], **options))


def test_results_keep_request_order() -> None:
    session = ScriptedSession(lambda r, a: {"id": r.session_id})
    outcomes = run(session, ["a", "b", "c"])
    assert [o.output for o in outcomes] == [{"id": "a"}, {"id": "b"}, {"id": "c"}]


def test_concurrency_is_capped() -> None:
    session = ScriptedSession(lambda r, a: {"ok": 1})
    run(session, [str(i) for i in range(10)], concurrency=3)
    assert 1 < session.max_running <= 3


def test_error_is_retried_with_growing_backoff() -> None:
    delays: list[float] = []

    async def sleep(seconds: float) -> None:
        delays.append(seconds)

    def script(r: SessionRequest, attempt: int) -> Any:
        if attempt < 3:
            return SessionOutcome(status=SessionStatus.ERROR, error="throttling", usage=ONE_CALL)
        return {"ok": 1}

    outcomes = run(ScriptedSession(script), ["a"], sleep=sleep)
    assert outcomes[0].status is SessionStatus.OK
    assert outcomes[0].attempts == 3
    assert delays == [1.0, 2.0]


def test_exception_counts_as_error_and_gives_up_after_retries() -> None:
    session = ScriptedSession(lambda r, a: RuntimeError("boom"))
    outcome = run(session, ["a"])[0]
    assert outcome.status is SessionStatus.ERROR
    assert outcome.error == "RuntimeError"
    assert outcome.attempts == 3


def test_the_text_of_an_exception_never_reaches_the_outcome() -> None:
    # il messaggio di un'eccezione dell'SDK può contenere righe dell'output del modello
    # (per esempio CLIJSONDecodeError riporta i primi 100 caratteri): finirebbe in
    # _pipeline_errors, nel payload e nei log
    session = ScriptedSession(lambda r, a: ValueError("Failed to decode JSON: RETTIFICARE LA SEDE"))
    outcome = run(session, ["a"])[0]
    assert outcome.error == "ValueError"


def test_invalid_output_is_retried_once() -> None:
    def script(r: SessionRequest, attempt: int) -> Any:
        return {"x": 1} if attempt == 1 else {"good": True}

    def validate(output: dict[str, Any]) -> None:
        if "good" not in output:
            raise ValueError("no")

    outcome = run(ScriptedSession(script), ["a"], validate=validate)[0]
    assert outcome.status is SessionStatus.OK
    assert outcome.attempts == 2


def test_invalid_output_after_retries_is_reported() -> None:
    def validate(output: dict[str, Any]) -> None:
        raise ValueError("no")

    outcome = run(ScriptedSession(lambda r, a: {"x": 1}), ["a"], validate=validate)[0]
    assert outcome.status is SessionStatus.INVALID_OUTPUT
    assert outcome.attempts == 2


def test_max_turns_is_not_retried() -> None:
    session = ScriptedSession(
        lambda r, a: SessionOutcome(status=SessionStatus.MAX_TURNS, usage=ONE_CALL)
    )
    outcome = run(session, ["a"])[0]
    assert outcome.status is SessionStatus.MAX_TURNS
    assert outcome.attempts == 1


def test_usage_of_all_attempts_is_summed() -> None:
    def script(r: SessionRequest, attempt: int) -> Any:
        if attempt == 1:
            return SessionOutcome(status=SessionStatus.ERROR, error="x", usage=ONE_CALL)
        return ok({"ok": 1})

    outcome = run(ScriptedSession(script), ["a"])[0]
    assert outcome.usage.sessions == 2
    assert outcome.usage.input_tokens == 200


def test_a_failure_does_not_touch_other_sessions() -> None:
    def script(r: SessionRequest, attempt: int) -> Any:
        if r.session_id == "bad":
            return RuntimeError("boom")
        return {"ok": 1}

    outcomes = run(ScriptedSession(script), ["a", "bad", "c"])
    assert [o.status for o in outcomes] == [
        SessionStatus.OK,
        SessionStatus.ERROR,
        SessionStatus.OK,
    ]


@pytest.mark.parametrize("output", [None])
def test_ok_without_output_is_invalid(output: None) -> None:
    session = ScriptedSession(lambda r, a: SessionOutcome(status=SessionStatus.OK, output=output))
    assert run(session, ["a"], invalid_output_retries=0)[0].status is SessionStatus.INVALID_OUTPUT


class _Stuck:
    """Una sessione che non risponde mai, tranne quelle il cui id è in `quick`."""

    def __init__(self, quick: set[str]) -> None:
        self.quick = quick
        self.calls = 0

    async def run(self, request: SessionRequest) -> SessionOutcome:
        self.calls += 1
        if request.session_id not in self.quick:
            await asyncio.sleep(60)
        return ok({"id": request.session_id})


def test_a_stuck_session_stops_at_the_time_limit_without_retrying() -> None:
    session = _Stuck(quick={"b"})
    outcomes = asyncio.run(
        run_sessions(
            session,
            [req("a"), req("b")],
            concurrency=2,
            retries=2,
            backoff_s=0,
            invalid_output_retries=1,
            timeout_s=0.05,
        )
    )
    assert outcomes[0].status is SessionStatus.ERROR
    assert outcomes[0].error is not None and "tempo massimo" in outcomes[0].error
    assert outcomes[0].attempts == 1  # riprovare raddoppierebbe l'attesa
    assert outcomes[1].status is SessionStatus.OK
    assert session.calls == 2


def test_without_a_time_limit_sessions_are_awaited() -> None:
    session = ScriptedSession(lambda r, a: {"ok": 1})
    (outcome,) = run(session, ["a"], timeout_s=None)
    assert outcome.status is SessionStatus.OK
