"""Servizi API di test: autenticazione statica, store in memoria, pipeline con sessione finta."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ej200_fixtures import judge, make_kb, pvrm320_pages
from fakes import ScriptedSession
from fastapi.testclient import TestClient
from support import example_cycle, make_deps, scripted_judge

from cycle_validation.api.app import ApiServices, create_app
from cycle_validation.api.auth import Identity, StaticAuthBackend
from cycle_validation.api.runner import PipelineRunner
from cycle_validation.api.settings import AppConfig
from cycle_validation.extract.pvrm320 import Pvrm320LayoutExtractor
from cycle_validation.kb.stores import InMemoryObjectStore
from cycle_validation.pipeline import Dependencies
from cycle_validation.services.machines import StaticMachineRegistry
from cycle_validation.testing.pdf import build_pdf

CONTRACT = Path(__file__).parent / "contract"
TOKENS = {
    "civile": Identity("sso-civile", frozenset({"cv"})),
    "ej200": Identity("sso-ej", frozenset({"cv_ej200"})),
    "tutto": Identity("sso-all", frozenset({"all"})),
    "altro": Identity("sso-altro", frozenset({"altro"})),
}


class RecordingMetrics:
    def __init__(self) -> None:
        self.costs: list[float] = []

    def llm_cost(self, usd: float) -> None:
        self.costs.append(usd)


class FailingStore(InMemoryObjectStore):
    def put_bytes(self, key: str, data: bytes) -> None:
        from cycle_validation.errors import SourceUnavailableError

        raise SourceUnavailableError("scrittura non riuscita")


def config(**changes: Any) -> AppConfig:
    base = AppConfig(bucket="b", region="eu-south-1", frontend_url="https://frontend.example")
    return AppConfig(**{**base.__dict__, **changes})


def civil_deps(profile: str, tmp_path: Path, script: Any = scripted_judge) -> Dependencies:
    return make_deps(profile, script=script)[0]


def ej200_deps(tmp_path: Path) -> Dependencies:
    deps, _ = make_deps("ej200", script=judge)
    kb, _ = make_kb(tmp_path / "work")
    return Dependencies(
        **{
            **deps.__dict__,
            "kb": kb,
            "machines": StaticMachineRegistry(["TM-1001", "TM-2002"]),
            "extractor": Pvrm320LayoutExtractor(),
        }
    )


class Env:
    def __init__(self, tmp_path: Path, **changes: Any) -> None:
        self.store = changes.pop("store", InMemoryObjectStore())
        self.metrics = RecordingMetrics()
        self.session = ScriptedSession(scripted_judge)
        runner_override = changes.pop("runner", None)
        self.deps_for = lambda profile: (
            ej200_deps(tmp_path) if profile == "ej200" else civil_deps(profile, tmp_path)
        )
        self.services = ApiServices(
            config=config(**changes),
            auth=StaticAuthBackend(TOKENS),
            store=self.store,
            runner=runner_override or PipelineRunner(self.deps_for),
            metrics=self.metrics,
            clock=lambda: datetime(2026, 11, 13, 12, 0, tzinfo=UTC),
            new_id=iter(f"id{n}" for n in range(1000)).__next__,
        )
        self.client = TestClient(create_app(self.services), raise_server_exceptions=False)

    def auth(self, who: str = "tutto") -> dict[str, str]:
        return {"Authorization": f"Bearer {who}"}


def civil_pdf() -> bytes:
    from cycle_validation.testing.pdf import synthetic_cycle_pdf

    return synthetic_cycle_pdf(example_cycle())


def ej200_pdf() -> bytes:
    return build_pdf(pvrm320_pages())


def recorded(name: str) -> Any:
    return json.loads((CONTRACT / name).read_text(encoding="utf-8"))


def same_shape(actual: Any, expected: Any, path: str = "$") -> list[str]:
    """Differenze di forma: chiavi mancanti o tipi diversi. I valori non contano."""
    problems: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: atteso oggetto"]
        for key, value in expected.items():
            if key not in actual:
                problems.append(f"{path}.{key}: chiave mancante")
            else:
                problems += same_shape(actual[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: attesa lista"]
    elif (
        expected is not None
        and actual is not None
        and type(actual) is not type(expected)
        and not (isinstance(expected, (int, float)) and isinstance(actual, (int, float)))
    ):
        problems.append(f"{path}: tipo {type(actual).__name__} invece di {type(expected).__name__}")
    return problems
