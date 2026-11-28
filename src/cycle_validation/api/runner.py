"""Esecuzione della pipeline per un profilo: costruisce le dipendenze e lancia il run."""

import asyncio
import hashlib
import logging
import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from time import monotonic, perf_counter

from cycle_validation import __version__
from cycle_validation.domain.check import Reason, Usage
from cycle_validation.domain.report import Report
from cycle_validation.errors import KnowledgeError, ProfileUnavailableError, SourceUnavailableError
from cycle_validation.pipeline import Dependencies, RunRequest, arun_validation

logger = logging.getLogger(__name__)

# MG58 (28-11): risultati già calcolati. Quanti se ne tengono e per quanto: le macchine attive
# (registro) possono cambiare durante il giorno, quindi un risultato vale al massimo 6 ore.
REUSE_MAX = 200
REUSE_SECONDS = 6 * 3600


class ResultCache:
    """Gli ultimi risultati, in memoria, per chiave (PDF, profilo, richiesta, conoscenza,
    modello, prompt, versione della v2). Si perdono a ogni riavvio: va bene, è solo un
    risparmio. Si tengono solo i risultati senza errori tecnici."""

    def __init__(self, max_items: int = REUSE_MAX, seconds: float = REUSE_SECONDS) -> None:
        self._items: OrderedDict[tuple[str, ...], tuple[float, Report]] = OrderedDict()
        self._max = max_items
        self._seconds = seconds
        self._lock = threading.Lock()

    def get(self, key: tuple[str, ...]) -> Report | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            if monotonic() - item[0] > self._seconds:
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return item[1]

    def put(self, key: tuple[str, ...], report: Report) -> None:
        if self._max <= 0:
            return
        with self._lock:
            self._items[key] = (monotonic(), report)
            self._items.move_to_end(key)
            while len(self._items) > self._max:
                self._items.popitem(last=False)


def _reusable(report: Report) -> bool:
    """Un risultato con un errore tecnico (rete, servizio) non si riusa: la volta dopo il
    modello potrebbe rispondere."""
    return not report.pipeline_errors and all(
        r.reason is not Reason.ERRORE_TECNICO for r in report.results
    )


class PipelineRunner:
    """`deps_for(profile)` costruisce (o riusa) le dipendenze del profilo."""

    def __init__(
        self, deps_for: Callable[[str], Dependencies], cache: ResultCache | None = None
    ) -> None:
        self._deps_for = deps_for
        self._cache = cache if cache is not None else ResultCache()
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

    def _key(self, profile: str, request: RunRequest, deps: Dependencies) -> tuple[str, ...] | None:
        """La chiave del risultato: None se la richiesta non si può riusare (PDF da file)."""
        if request.pdf_bytes is None:
            return None
        current = getattr(type(deps.kb), "current", None)
        kb = deps.kb.current() if callable(current) else deps.kb  # type: ignore[attr-defined]
        selectors = request.selectors
        return (
            profile,
            hashlib.sha256(request.pdf_bytes).hexdigest(),
            repr(selectors.serial_number if selectors else None),
            repr(list(selectors.conditions) if selectors else None),
            ",".join(sorted(str(c) for c in request.skip_checks)),
            str(request.check_integrity),
            kb.version,
            deps.settings.agent.model,
            deps.prompt_version,
            __version__,
        )

    async def run(self, profile: str, request: RunRequest) -> Report:
        self._check_available(profile)
        deps = self._deps_for(profile)
        began = perf_counter()
        key = await asyncio.to_thread(self._key, profile, request, deps)
        saved = self._cache.get(key) if key is not None else None
        if saved is not None:
            # MG58: stesso PDF, stessa richiesta e stessa conoscenza. Stessi esiti; il run è
            # nuovo (id, ora, nome del file) e non costa niente.
            reused = saved.model_copy(
                update={
                    "meta": saved.meta.model_copy(
                        update={
                            "run_id": uuid.uuid4().hex[:12],
                            "started_at": datetime.now(UTC),
                            "pdf_name": request.pdf_name,
                        }
                    ),
                    "usage": Usage(),
                    "timings_ms": {"total": round((perf_counter() - began) * 1000)},
                }
            )
            logger.info(
                "Risultato riusato (MG58): run %s uguale a %s",
                reused.meta.run_id,
                saved.meta.run_id,
            )
            return reused
        report = await arun_validation(request, deps)
        if key is not None and report.meta.knowledge_version == key[6] and _reusable(report):
            self._cache.put(key, report)
        return report
