"""Esecuzione della pipeline per un profilo: costruisce le dipendenze e lancia il run."""

import logging
import threading
from collections.abc import Callable, Iterable

from cycle_validation.domain.report import Report
from cycle_validation.errors import KnowledgeError, ProfileUnavailableError, SourceUnavailableError
from cycle_validation.pipeline import Dependencies, RunRequest, arun_validation

logger = logging.getLogger(__name__)


class PipelineRunner:
    """`deps_for(profile)` costruisce (o riusa) le dipendenze del profilo."""

    def __init__(self, deps_for: Callable[[str], Dependencies]) -> None:
        self._deps_for = deps_for
        # profili facoltativi con la conoscenza non valida all'avvio (MG44): profilo → motivo
        self._broken: dict[str, str] = {}
        self._lock = threading.Lock()

    def _preload_one(self, profile: str) -> None:
        preload = getattr(self._deps_for(profile).kb, "preload", None)
        if callable(preload):
            preload()

    def preload(self, profiles: Iterable[str], optional: Iterable[str] = ()) -> None:
        """Costruisce le dipendenze dei profili e scarica la loro conoscenza, così la prima
        validazione dopo un riavvio non aspetta S3. Un file non valido ferma qui, con il nome.

        MG44 (27-11 notte): per i profili `optional` (EJ200) una conoscenza non valida non ferma
        il servizio: quel profilo si spegne e MOS e DR partono lo stesso. Si riprova alla prima
        richiesta di quel profilo (la conoscenza può essere stata ripubblicata)."""
        skip = set(optional)
        for profile in profiles:
            try:
                self._preload_one(profile)
            except (KnowledgeError, SourceUnavailableError) as exc:
                if profile not in skip:
                    raise
                with self._lock:
                    self._broken[profile] = type(exc).__name__
                logger.warning("Profilo %s spento: conoscenza non valida all'avvio", profile)

    def _check_available(self, profile: str) -> None:
        with self._lock:
            broken = self._broken.get(profile)
        if broken is None:
            return
        try:
            self._preload_one(profile)
        except (KnowledgeError, SourceUnavailableError) as exc:
            raise ProfileUnavailableError(
                f"Profilo '{profile}' spento: la sua conoscenza non è valida "
                f"({type(exc).__name__}). Gli altri profili funzionano."
            ) from exc
        with self._lock:
            self._broken.pop(profile, None)
        logger.warning("Profilo %s di nuovo attivo", profile)

    @property
    def broken(self) -> dict[str, str]:
        """I profili spenti all'avvio (profilo → tipo di errore)."""
        with self._lock:
            return dict(self._broken)

    async def run(self, profile: str, request: RunRequest) -> Report:
        self._check_available(profile)
        return await arun_validation(request, self._deps_for(profile))
