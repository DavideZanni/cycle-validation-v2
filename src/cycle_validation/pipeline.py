"""Orchestrazione degli stadi: ingest → extract → integrity → check → consolidate → report."""

import asyncio
import uuid
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from cycle_validation import __version__
from cycle_validation.agent.session import AgentSession
from cycle_validation.checks.base import CheckContext
from cycle_validation.checks.dr_recommendation import check_dr_recommendation
from cycle_validation.checks.machine_tag import check_machine_tags
from cycle_validation.checks.operation import check_operations
from cycle_validation.checks.process_sheet import check_process_sheets
from cycle_validation.checks.source import check_sources
from cycle_validation.checks.task_code import check_task_codes
from cycle_validation.config import ModuleCheckSettings, ProfileConfig, Settings
from cycle_validation.domain.check import CheckName, CheckResult, Usage
from cycle_validation.domain.report import PipelineError, Report, RunMeta
from cycle_validation.errors import ExtractionError, ProfileUnavailableError
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.integrity import check_extraction_integrity
from cycle_validation.ingest.document import read_document, read_document_bytes
from cycle_validation.ingest.pdf import PdfDocument, check_required_text
from cycle_validation.ingest.transcribe import PageTranscriber
from cycle_validation.kb.port import KnowledgeBase
from cycle_validation.module_kind import check_module_kind
from cycle_validation.report.builder import build_report, write_outputs
from cycle_validation.resolve.dr import DrSelectors, SelectorError
from cycle_validation.services.machines import MachineRegistry
from cycle_validation.verdict.consolidate import (
    apply_integrity,
    blocked_results,
    is_blocking_failure,
)

SyncCheck = Callable[[CheckContext], list[CheckResult]]

SYNC_CHECKS: dict[CheckName, SyncCheck] = {
    CheckName.DR_RECOMMENDATION: check_dr_recommendation,
    CheckName.SOURCE: check_sources,
    CheckName.TASK_CODE: check_task_codes,
    CheckName.MACHINE_TAG: check_machine_tags,
    CheckName.PROCESS_SHEET: check_process_sheets,
}


@dataclass(frozen=True)
class RunRequest:
    """Il PDF arriva da file (CLI) oppure in memoria (API)."""

    pdf_path: Path | None = None
    pdf_bytes: bytes | None = None
    pdf_name: str = "ciclo.pdf"
    selectors: DrSelectors | None = None
    skip_checks: frozenset[CheckName] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Dependencies:
    settings: Settings
    profile: ProfileConfig
    kb: KnowledgeBase
    machines: MachineRegistry
    extractor: CycleExtractor
    session: AgentSession
    system_prompt: str
    prompt_version: str
    # Per immagini e PDF senza testo. None = solo PDF con testo (PDFium).
    transcriber: PageTranscriber | None = None


def _ms(start: float) -> int:
    return round((perf_counter() - start) * 1000)


def _read(
    request: RunRequest,
    profile: ProfileConfig,
    transcriber: PageTranscriber | None,
    module_check: ModuleCheckSettings,
) -> tuple[PdfDocument, Usage]:
    # Il testo richiesto dal profilo si controlla dopo il tipo di modulo: a chi carica un
    # ciclo di un altro tipo va detto quale ha caricato, non quale parola manca.
    limits = profile.file_limits.model_copy(update={"required_text": []})
    if request.pdf_bytes is not None:
        pdf, usage = read_document_bytes(request.pdf_bytes, request.pdf_name, limits, transcriber)
    elif request.pdf_path is not None:
        pdf, usage = read_document(request.pdf_path, limits, transcriber)
    else:
        raise ExtractionError("Nessun PDF indicato.")
    check_module_kind(pdf.text, profile.name, module_check)
    check_required_text(pdf, profile.file_limits)
    return pdf, usage


def _check_selectors(profile: ProfileConfig, selectors: DrSelectors | None) -> None:
    if profile.requires_selectors and selectors is None:
        raise SelectorError(f"Il profilo {profile.name} richiede serial number e repair condition.")
    if not profile.requires_selectors and selectors is not None:
        raise SelectorError(f"Il profilo {profile.name} non ammette selettori DR.")


async def _run_sync(checks: Collection[CheckName], ctx: CheckContext) -> list[CheckResult]:
    batches = await asyncio.gather(
        *(asyncio.to_thread(SYNC_CHECKS[check], ctx) for check in checks)
    )
    return [item for batch in batches for item in batch]


async def arun_validation(
    request: RunRequest, deps: Dependencies, run_dir: Path | None = None
) -> Report:
    started = datetime.now(UTC)
    began = perf_counter()
    timings: dict[str, int] = {}
    profile = deps.profile
    if not profile.enabled:
        raise ProfileUnavailableError(
            f"Il profilo {profile.name} non è attivo: {profile.disabled_reason or 'disabilitato'}."
        )
    _check_selectors(profile, request.selectors)

    mark = perf_counter()
    pdf, ingest_usage = await asyncio.to_thread(
        _read, request, profile, deps.transcriber, deps.settings.module_check
    )
    timings["ingest"] = _ms(mark)

    mark = perf_counter()
    cycle, extraction_usage = await deps.extractor.extract(pdf)
    if not cycle.operations:
        raise ExtractionError("Il ciclo estratto non contiene operazioni.")
    if request.selectors is not None:
        record = {
            **(cycle.dr_record or {}),
            "serial_number": request.selectors.serial_number,
            "conditions": list(request.selectors.conditions),
        }
        cycle = cycle.model_copy(update={"dr_record": record})
    timings["extract"] = _ms(mark)

    integrity = check_extraction_integrity(cycle, pdf)
    ctx = CheckContext(
        cycle, deps.kb, deps.machines, profile, request.selectors, integrity.unconfirmed
    )
    active = [check for check in profile.checks if check not in request.skip_checks]
    results: list[CheckResult] = []
    pipeline_errors: list[PipelineError] = []
    blocked = False
    session_modes: dict[str, int] = {}

    mark = perf_counter()
    first = [c for c in active if c in profile.blocking_checks and c in SYNC_CHECKS]
    rest = [c for c in active if c not in first]
    results.extend(await _run_sync(first, ctx))
    cause = next((item for item in results if is_blocking_failure(item)), None)
    if cause is not None:
        blocked = True
        results.extend(blocked_results(cycle, rest, cause))
    else:
        # I controlli deterministici (knowledge base, registro macchine) e le sessioni
        # dell'agente non dipendono gli uni dalle altre: procedono insieme.
        sync_rest = [c for c in rest if c in SYNC_CHECKS]
        sync_task = asyncio.ensure_future(_run_sync(sync_rest, ctx))
        operation_task: asyncio.Future[tuple[list[CheckResult], list[PipelineError]]] | None
        operation_task = None
        if CheckName.OPERATION_DESCRIPTION in rest:
            operation_task = asyncio.ensure_future(
                check_operations(
                    ctx, deps.session, deps.settings.agent, deps.system_prompt, session_modes
                )
            )
        try:
            results.extend(await sync_task)
            if operation_task is not None:
                op_results, op_errors = await operation_task
                results.extend(op_results)
                pipeline_errors.extend(op_errors)
        except BaseException:
            # il run è fallito: le sessioni ancora in corso non devono continuare a spendere
            for task in (sync_task, operation_task):
                if task is not None:
                    task.cancel()
            await asyncio.gather(
                *(task for task in (sync_task, operation_task) if task is not None),
                return_exceptions=True,
            )
            raise
    timings["checks"] = _ms(mark)

    results = apply_integrity(results, integrity.unconfirmed)
    timings["total"] = _ms(began)
    meta = RunMeta(
        run_id=uuid.uuid4().hex[:12],
        started_at=started,
        pdf_name=pdf.name,
        pdf_sha256=pdf.sha256,
        profile=profile.name,
        selectors=(
            {
                "serial_number": request.selectors.serial_number,
                "conditions": list(request.selectors.conditions),
            }
            if request.selectors
            else {}
        ),
        knowledge_version=deps.kb.version,
        model=deps.settings.agent.model,
        prompt_version=deps.prompt_version,
        tool_version=__version__,
    )
    report = build_report(
        meta,
        cycle,
        [*integrity.results, *results],
        timings_ms=timings,
        pipeline_errors=pipeline_errors,
        blocked=blocked,
        extra_usage=extraction_usage + ingest_usage,
        session_modes=session_modes,
    )
    if run_dir is not None:
        await asyncio.to_thread(write_outputs, report, run_dir)
    return report


def run_validation(request: RunRequest, deps: Dependencies, run_dir: Path | None = None) -> Report:
    """Versione sincrona per CLI e script."""
    return asyncio.run(arun_validation(request, deps, run_dir))
