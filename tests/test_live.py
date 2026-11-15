"""Prova con il modello vero (MIGLIORIE A5). Non parte con i test normali: `pytest -m live`.

Da lanciare a mano dopo ogni aggiornamento della libreria dell'agente o del modello: avrebbe
trovato subito l'errore A1 (strumento di risposta bloccato in modalità ricerca). Usa solo i casi
inventati di `eval/casi/sintetici` e costa pochi centesimi: tre sessioni.

Configurazione: `CV_LIVE_CONFIG`, se impostata, altrimenti `config/settings.yaml` (Bedrock).
Sul PC personale: una copia di settings con `agent.use_bedrock: false` (login Claude locale).
"""

import asyncio
import dataclasses
import json
import os
from pathlib import Path
from typing import Any

import pytest

from cycle_validation.agent.session import AgentSession, SessionOutcome, SessionRequest
from cycle_validation.cli import make_session
from cycle_validation.config import AgentSettings
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.run import load_suites, run_variant
from cycle_validation.evaluation.variant import Variant, load_variant

pytestmark = pytest.mark.live

ROOT = Path(__file__).resolve().parents[1]


class Watched:
    """La sessione vera, annotando se ha lavorato in linea o con la ricerca."""

    def __init__(self, inner: AgentSession, modes: list[bool]) -> None:
        self._inner = inner
        self._modes = modes

    async def run(self, request: SessionRequest) -> SessionOutcome:
        self._modes.append(request.use_tools)
        return await self._inner.run(request)


def _searching(variant: Variant) -> Variant:
    """Stessa variante, ma ogni testo va cercato con gli strumenti invece che nel messaggio."""
    agent = variant.settings.agent.model_copy(update={"inline_max_lines": 0})
    settings = variant.settings.model_copy(update={"agent": agent})
    return dataclasses.replace(variant, name=f"{variant.name}_ricerca", settings=settings)


def _run(variant: Variant, suites: list[Any], tmp_path: Path, modes: list[bool]) -> Any:
    def factory(settings: AgentSettings, transcripts: Path | None) -> AgentSession:
        return Watched(make_session(settings, transcripts), modes)

    path = asyncio.run(
        run_variant(
            variant,
            suites,
            repetitions=1,
            results_dir=tmp_path / variant.name / "risultati",
            session_factory=factory,
            project_root=ROOT,
            runs_dir=tmp_path / variant.name / "runs",
        )
    )
    return measure(json.loads(path.read_text(encoding="utf-8")))


def test_the_real_model_answers_inline_and_with_search(tmp_path: Path) -> None:
    config = Path(os.environ.get("CV_LIVE_CONFIG") or ROOT / "config" / "settings.yaml")
    variant = load_variant(ROOT / "eval" / "varianti" / "baseline.yaml", config_override=config)
    suites = {
        suite.name: dataclasses.replace(
            suite, cases=[case for case in suite.cases if case.name == "pulito"]
        )
        for suite in load_suites(ROOT / "eval" / "casi" / "sintetici")
    }
    modes: list[bool] = []
    runs = [
        _run(variant, [suites["mos"], suites["ej200"]], tmp_path, modes),
        _run(_searching(variant), [suites["mos"]], tmp_path, modes),
    ]
    assert False in modes and True in modes, f"modalità provate: {modes}"
    for metrics in runs:
        assert metrics.technical == 0, f"esiti tecnici: {metrics.mismatches}"
        assert metrics.false_errato == 0, metrics.mismatches
        assert metrics.concordance == 1.0, metrics.mismatches
