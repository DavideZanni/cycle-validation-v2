"""Esecuzione della pipeline per un profilo: costruisce le dipendenze e lancia il run."""

from collections.abc import Callable, Iterable

from cycle_validation.domain.report import Report
from cycle_validation.pipeline import Dependencies, RunRequest, arun_validation


class PipelineRunner:
    """`deps_for(profile)` costruisce (o riusa) le dipendenze del profilo."""

    def __init__(self, deps_for: Callable[[str], Dependencies]) -> None:
        self._deps_for = deps_for

    def preload(self, profiles: Iterable[str]) -> None:
        """Costruisce le dipendenze dei profili e scarica la loro conoscenza, così la prima
        validazione dopo un riavvio non aspetta S3. Un file non valido ferma qui, con il nome."""
        for profile in profiles:
            preload = getattr(self._deps_for(profile).kb, "preload", None)
            if callable(preload):
                preload()

    async def run(self, profile: str, request: RunRequest) -> Report:
        return await arun_validation(request, self._deps_for(profile))
