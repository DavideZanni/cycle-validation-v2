"""Esecuzione delle sessioni: in parallelo con un tetto, con nuovi tentativi sui guasti
tecnici e sugli output non conformi. Un guasto resta confinato alla sua sessione.

Una sessione che supera il tempo massimo è un errore tecnico e non si riprova: riprovare
raddoppierebbe proprio l'attesa che il limite serve a togliere."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from cycle_validation.agent.session import (
    AgentSession,
    SessionOutcome,
    SessionRequest,
    SessionStatus,
)
from cycle_validation.domain.check import Usage

Validator = Callable[[dict[str, Any]], object]
# MG53 (27-11 notte): la validazione ha un tempo massimo (`agent.validation_timeout_s`), sotto i
# 600 s del backend. Le sessioni che non finiscono in tempo chiudono come errore tecnico: il
# report esce con quello che c'è.
DEADLINE_ERROR = "tempo massimo della validazione superato"
Sleep = Callable[[float], Awaitable[None]]


def _validated(outcome: SessionOutcome, validate: Validator | None) -> SessionOutcome:
    if outcome.status is not SessionStatus.OK:
        return outcome
    if outcome.output is None:
        return outcome.model_copy(
            update={"status": SessionStatus.INVALID_OUTPUT, "error": "Nessun output strutturato."}
        )
    if validate is None:
        return outcome
    try:
        validate(outcome.output)
    except ValueError as exc:  # pydantic.ValidationError è un ValueError
        return outcome.model_copy(
            update={
                "status": SessionStatus.INVALID_OUTPUT,
                "error": f"Output non conforme allo schema: {type(exc).__name__}",
            }
        )
    return outcome


async def _run_one(
    session: AgentSession,
    request: SessionRequest,
    *,
    retries: int,
    backoff_s: float,
    invalid_output_retries: int,
    validate: Validator | None,
    sleep: Sleep,
    timeout_s: float | None,
    deadline: float | None = None,
) -> SessionOutcome:
    usage = Usage()
    errors_left = retries
    invalid_left = invalid_output_retries
    attempts = 0
    loop = asyncio.get_running_loop()
    while True:
        attempts += 1
        limit = timeout_s
        if deadline is not None:
            left = deadline - loop.time()
            if left <= 0:
                return SessionOutcome(
                    status=SessionStatus.ERROR,
                    error=DEADLINE_ERROR,
                    usage=usage,
                    attempts=attempts - 1,
                )
            limit = left if limit is None else min(limit, left)
        try:
            outcome = _validated(await asyncio.wait_for(session.run(request), limit), validate)
        except TimeoutError:
            ended = deadline is not None and loop.time() >= deadline
            return SessionOutcome(
                status=SessionStatus.ERROR,
                error=DEADLINE_ERROR if ended else f"tempo massimo superato ({timeout_s:g} s)",
                usage=usage,
                attempts=attempts,
            )
        except Exception as exc:
            # solo il tipo: il messaggio di un'eccezione può riportare testo del ciclo o dei
            # documenti, e questo campo finisce in _pipeline_errors, nel payload e nei log
            outcome = SessionOutcome(status=SessionStatus.ERROR, error=type(exc).__name__)
        usage = usage + outcome.usage
        final = outcome.model_copy(update={"usage": usage, "attempts": attempts})
        if outcome.status is SessionStatus.ERROR and errors_left > 0:
            errors_left -= 1
            await sleep(backoff_s * 2 ** (retries - errors_left - 1))
            continue
        if outcome.status is SessionStatus.INVALID_OUTPUT and invalid_left > 0:
            invalid_left -= 1
            continue
        return final


async def run_sessions(
    session: AgentSession,
    requests: Sequence[SessionRequest],
    *,
    concurrency: int,
    retries: int,
    backoff_s: float,
    invalid_output_retries: int,
    validate: Validator | None = None,
    sleep: Sleep = asyncio.sleep,
    timeout_s: float | None = None,
    deadline: float | None = None,
) -> list[SessionOutcome]:
    """Esegue le richieste e restituisce gli esiti nello stesso ordine.

    `timeout_s` vale per ogni tentativo di ogni sessione. None = nessun limite. `deadline`
    (orologio del loop, `loop.time()`) vale per tutte: dopo, nessuna sessione parte più e
    quelle in corso si fermano (MG53)."""
    gate = asyncio.Semaphore(concurrency)

    async def guarded(request: SessionRequest) -> SessionOutcome:
        async with gate:
            return await _run_one(
                session,
                request,
                retries=retries,
                backoff_s=backoff_s,
                invalid_output_retries=invalid_output_retries,
                validate=validate,
                sleep=sleep,
                timeout_s=timeout_s,
                deadline=deadline,
            )

    return list(await asyncio.gather(*(guarded(request) for request in requests)))
