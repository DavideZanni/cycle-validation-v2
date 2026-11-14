"""Esecuzione della pipeline per un profilo: costruisce le dipendenze e lancia il run."""

from collections.abc import Callable

from cycle_validation.domain.report import Report
from cycle_validation.pipeline import Dependencies, RunRequest, arun_validation


class PipelineRunner:
    """`deps_for(profile)` costruisce (o riusa) le dipendenze del profilo."""

    def __init__(self, deps_for: Callable[[str], Dependencies]) -> None:
        self._deps_for = deps_for

    async def run(self, profile: str, request: RunRequest) -> Report:
        return await arun_validation(request, self._deps_for(profile))
