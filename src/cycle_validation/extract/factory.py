"""Estrattore del ciclo dal PDF per un profilo: parser di layout, se c'è, poi il modello."""

from pathlib import Path

from cycle_validation.agent.prompt import load_prompt
from cycle_validation.agent.session import AgentSession
from cycle_validation.config import AgentSettings, ProfileConfig
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.composite import FallbackCycleExtractor
from cycle_validation.extract.llm import LlmCycleExtractor
from cycle_validation.extract.pvrm320 import Pvrm320LayoutExtractor


def make_pdf_extractor(
    profile: ProfileConfig, settings: AgentSettings, session: AgentSession, prompts_dir: Path
) -> tuple[CycleExtractor, str]:
    """L'estrattore e il testo del prompt di estrazione (entra nella versione dei prompt)."""
    prompt = load_prompt(prompts_dir, profile.extraction_prompt)
    extractor: CycleExtractor = LlmCycleExtractor(session, settings, prompt)
    if profile.layout_extractor == "pvrm320":
        extractor = FallbackCycleExtractor(Pvrm320LayoutExtractor(), extractor)
    return extractor, prompt
