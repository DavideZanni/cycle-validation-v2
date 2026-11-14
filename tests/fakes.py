"""Sessione finta: risponde secondo un copione, senza rete."""

from collections.abc import Callable
from typing import Any

from cycle_validation.agent.session import SessionOutcome, SessionRequest, SessionStatus
from cycle_validation.domain.check import Usage

Reply = SessionOutcome | Exception | dict[str, Any]
Script = Callable[[SessionRequest, int], Reply]

ONE_CALL = Usage(input_tokens=100, output_tokens=20, cost_usd=0.001, turns=1, sessions=1)


def ok(output: dict[str, Any]) -> SessionOutcome:
    return SessionOutcome(status=SessionStatus.OK, output=output, usage=ONE_CALL)


class ScriptedSession:
    """`script(request, attempt)` decide la risposta; `attempt` parte da 1 per ogni sessione."""

    def __init__(self, script: Script) -> None:
        self._script = script
        self.requests: list[SessionRequest] = []
        self.attempts: dict[str, int] = {}
        self.running = 0
        self.max_running = 0

    async def run(self, request: SessionRequest) -> SessionOutcome:
        import asyncio

        self.requests.append(request)
        attempt = self.attempts.get(request.session_id, 0) + 1
        self.attempts[request.session_id] = attempt
        self.running += 1
        self.max_running = max(self.max_running, self.running)
        try:
            await asyncio.sleep(0)
            reply = self._script(request, attempt)
        finally:
            self.running -= 1
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, dict):
            return ok(reply)
        return reply
