"""MG58: stesso PDF, stessa richiesta e stessa conoscenza → il risultato già calcolato (dati
inventati, sessione finta)."""

import asyncio
import dataclasses
from typing import Any

from support import example_cycle, make_deps

from cycle_validation.agent.session import SessionRequest
from cycle_validation.api.runner import PipelineRunner, ResultCache
from cycle_validation.pipeline import RunRequest
from cycle_validation.testing.pdf import synthetic_cycle_pdf


def _request(pdf: bytes, name: str = "ciclo.pdf") -> RunRequest:
    return RunRequest(pdf_bytes=pdf, pdf_name=name)


def test_the_same_pdf_is_answered_from_the_saved_result() -> None:
    deps, session = make_deps()
    runner = PipelineRunner(lambda _: deps)
    pdf = synthetic_cycle_pdf(example_cycle())
    first = asyncio.run(runner.run("mos", _request(pdf)))
    calls = len(session.requests)
    assert calls > 0
    again = asyncio.run(runner.run("mos", _request(pdf, "copia.pdf")))
    assert len(session.requests) == calls  # il modello non lavora di nuovo
    assert [(r.verdict, r.reason) for r in again.results] == [
        (r.verdict, r.reason) for r in first.results
    ]
    assert again.meta.run_id != first.meta.run_id and again.meta.pdf_name == "copia.pdf"
    assert again.usage.cost_usd == 0
    # un altro PDF (anche solo un byte diverso): si valida di nuovo
    asyncio.run(runner.run("mos", _request(pdf + b"\n%altro\n")))
    assert len(session.requests) > calls


def test_new_knowledge_or_a_technical_error_is_not_reused() -> None:
    deps, session = make_deps()
    versions = iter(["v1", "v2"])

    def deps_for(_: str) -> Any:
        kb = deps.kb
        return dataclasses.replace(deps, kb=_Versioned(kb, next(versions, "v2")))

    runner = PipelineRunner(deps_for)
    pdf = synthetic_cycle_pdf(example_cycle())
    asyncio.run(runner.run("mos", _request(pdf)))
    calls = len(session.requests)
    asyncio.run(runner.run("mos", _request(pdf)))  # conoscenza nuova: si rifà
    assert len(session.requests) > calls

    def broken(request: SessionRequest, attempt: int) -> Any:
        raise TimeoutError("rete")

    deps2, session2 = make_deps(script=broken)
    runner2 = PipelineRunner(lambda _: deps2)
    asyncio.run(runner2.run("mos", _request(pdf)))
    calls = len(session2.requests)
    asyncio.run(runner2.run("mos", _request(pdf)))  # con un errore tecnico non si riusa
    assert len(session2.requests) > calls


def test_the_saved_results_expire_and_are_limited() -> None:
    deps, session = make_deps()
    pdf = synthetic_cycle_pdf(example_cycle())
    runner = PipelineRunner(lambda _: deps, ResultCache(seconds=0))
    asyncio.run(runner.run("mos", _request(pdf)))
    calls = len(session.requests)
    asyncio.run(runner.run("mos", _request(pdf)))
    assert len(session.requests) > calls
    off = PipelineRunner(lambda _: deps, ResultCache(max_items=0))
    asyncio.run(off.run("mos", _request(pdf)))
    calls = len(session.requests)
    asyncio.run(off.run("mos", _request(pdf)))
    assert len(session.requests) > calls


class _Versioned:
    """La stessa conoscenza con un'altra versione."""

    def __init__(self, kb: Any, version: str) -> None:
        self._kb = kb
        self.version = version

    def __getattr__(self, name: str) -> Any:
        return getattr(self._kb, name)
