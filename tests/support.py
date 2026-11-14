"""Costruzioni condivise dai test di pipeline, CLI e API."""

import json
from pathlib import Path
from typing import Any

from fakes import ScriptedSession
from kb_fixtures import EXAMPLE_DIR, memory_knowledge, profile

from cycle_validation.agent.session import SessionRequest
from cycle_validation.config import ProfileConfig, Settings, load_settings
from cycle_validation.domain.cycle import Cycle
from cycle_validation.extract.from_file import FileCycleExtractor
from cycle_validation.pipeline import Dependencies
from cycle_validation.services.machines import StaticMachineRegistry
from cycle_validation.testing.pdf import build_pdf, cycle_pdf_text

QUOTE_110 = {
    "file": "MAN-DEMO-72.md",
    "line": 7,
    "quote": "Pulire il supporto con solvente tipo A.",
}
QUOTE_350 = {
    "file": "MAN-DEMO-72.md",
    "line": 18,
    "quote": "Rettificare la sede fino al diametro 45,00 mm",
}


def example_cycle() -> Cycle:
    return Cycle.model_validate(json.loads((EXAMPLE_DIR / "ciclo.json").read_text("utf-8")))


def write_cycle_pdf(path: Path, cycle: Cycle) -> Path:
    path.write_bytes(build_pdf([cycle_pdf_text(cycle)]))
    return path


def scripted_judge(request: SessionRequest, attempt: int) -> dict[str, Any]:
    """Giudizio finto: la rettifica a 46,00 mm contraddice il manuale (45,00 mm)."""
    if "46,00" in request.prompt:
        return {
            "judgement": "contraddetto",
            "rationale": "Valore diverso.",
            "citations": [QUOTE_350],
        }
    return {"judgement": "coerente", "rationale": "In linea.", "citations": [QUOTE_110]}


def make_deps(
    profile_name: str = "mos",
    *,
    script: Any = scripted_judge,
    cycle_path: Path | None = None,
    settings: Settings | None = None,
    profile_config: ProfileConfig | None = None,
) -> tuple[Dependencies, ScriptedSession]:
    session = ScriptedSession(script)
    deps = Dependencies(
        settings=settings or load_settings(None).model_copy(),
        profile=profile_config or profile(profile_name),
        kb=memory_knowledge(),
        machines=StaticMachineRegistry(["TM-1001", "TM-2002"]),
        extractor=FileCycleExtractor(cycle_path or EXAMPLE_DIR / "ciclo.json"),
        session=session,
        system_prompt="sistema",
        prompt_version="test",
    )
    return deps, session
