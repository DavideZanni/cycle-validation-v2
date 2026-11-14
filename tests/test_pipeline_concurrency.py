"""Controlli deterministici e sessioni dell'agente procedono insieme; le ricerche bloccanti
non girano sul loop che serve le altre richieste."""

import asyncio
import gc
import threading
import warnings
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fakes import ok
from support import example_cycle, make_deps, scripted_judge, write_cycle_pdf

from cycle_validation.agent.session import SessionOutcome, SessionRequest
from cycle_validation.domain.check import CheckName, Reason
from cycle_validation.pipeline import RunRequest, arun_validation, run_validation


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    return write_cycle_pdf(tmp_path / "ciclo.pdf", example_cycle())


def test_sessions_start_while_a_slow_deterministic_check_is_still_running(pdf: Path) -> None:
    session_started = threading.Event()
    seen: dict[str, bool] = {}

    class SlowRegistry:
        """Come la prima query sul registro delle macchine: risponde dopo un po'."""

        def is_active(self, tag: str) -> bool:
            seen.setdefault("session_started_meanwhile", session_started.wait(2))
            return tag != "TM-3003"

    def script(request: SessionRequest, attempt: int) -> dict[str, Any]:
        session_started.set()
        return scripted_judge(request, attempt)

    deps, _ = make_deps(script=script)
    report = run_validation(RunRequest(pdf_path=pdf), replace(deps, machines=SlowRegistry()))

    assert seen["session_started_meanwhile"] is True
    machines = [r.reason for r in report.results if r.check is CheckName.MACHINE_TAG]
    assert machines == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.MACCHINA_NON_ATTIVA,
        Reason.CAMPO_ASSENTE,
    ]
    assert report.counts.errato == 2  # stessi esiti di test_mos_end_to_end


class RecordingKnowledge:
    """Inoltra tutto alla knowledge base vera e annota il thread di ogni ricerca di task."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.threads: list[int] = []

    def find_task(self, manual: str, task: str) -> Any:
        self.threads.append(threading.get_ident())
        return self._inner.find_task(manual, task)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def test_reference_lookups_never_run_on_the_event_loop(pdf: Path) -> None:
    deps, _ = make_deps()
    kb = RecordingKnowledge(deps.kb)

    async def main() -> int:
        await arun_validation(RunRequest(pdf_path=pdf), replace(deps, kb=kb))
        return threading.get_ident()

    loop_thread = asyncio.run(main())
    assert kb.threads and loop_thread not in kb.threads


def test_an_unexpected_failure_of_a_check_stops_the_run_and_its_sessions(pdf: Path) -> None:
    completed: list[str] = []

    class Broken:
        def is_active(self, tag: str) -> bool:
            raise RuntimeError("guasto imprevisto")

    class Session:
        async def run(self, request: SessionRequest) -> SessionOutcome:
            await asyncio.sleep(0.2)
            completed.append(request.session_id)
            return ok(scripted_judge(request, 1))

    deps, _ = make_deps()
    deps = replace(deps, machines=Broken(), session=Session())

    async def main() -> None:
        with pytest.raises(RuntimeError):
            await arun_validation(RunRequest(pdf_path=pdf), deps)
        await asyncio.sleep(0.4)  # una sessione lasciata correre finirebbe qui

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        asyncio.run(main())
        gc.collect()
    assert completed == []
    assert not [w for w in caught if "never awaited" in str(w.message)]
