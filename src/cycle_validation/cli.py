"""CLI: `cycle-validation run` e `cycle-validation kb-check`."""

import asyncio
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from cycle_validation.agent.prompt import OPERATION_PROMPT_FILE, load_prompt, prompt_version
from cycle_validation.agent.sdk_session import SdkAgentSession
from cycle_validation.agent.session import AgentSession
from cycle_validation.config import AgentSettings, Settings, load_profile, load_settings
from cycle_validation.domain.check import CheckName
from cycle_validation.errors import CycleValidationError
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.composite import FallbackCycleExtractor
from cycle_validation.extract.from_file import FileCycleExtractor, load_cycle
from cycle_validation.extract.llm import LlmCycleExtractor
from cycle_validation.extract.pvrm320 import Pvrm320LayoutExtractor
from cycle_validation.golden import GoldenCase, load_cases, run_golden
from cycle_validation.ingest.transcribe import make_transcriber
from cycle_validation.kb.export import export_local_knowledge
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.manuals import IndexedManualSource
from cycle_validation.kb.remote import RemoteKnowledgeBase
from cycle_validation.kb.stores import LocalDirObjectStore, load_jsonl_index
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.resolve.dr import parse_selectors
from cycle_validation.services.machines import load_machine_registry

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Validazione dei cicli.")


def make_session(settings: AgentSettings, transcripts_dir: Path | None) -> AgentSession:
    """Punto di sostituzione: i test iniettano una sessione finta."""
    return SdkAgentSession(settings, transcripts_dir)


def _fail(error: Exception) -> typer.Exit:
    typer.echo(f"Errore: {error}", err=False)
    return typer.Exit(code=1)


@app.command("kb-check")
def kb_check(
    directory: Annotated[Path, typer.Argument(help="Cartella della knowledge base.")],
) -> None:
    """Carica una knowledge base locale e stampa i conteggi."""
    try:
        kb = load_local_knowledge(directory)
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(f"Knowledge base {kb.version}")
    for name, count in kb.stats().items():
        typer.echo(f"  {name}: {count}")


@app.command("kb-export")
def kb_export(
    structured_dir: Annotated[Path, typer.Option(help="Snapshot dei JSON S3 (TM, SP, DR).")],
    chunks: Annotated[Path, typer.Option(help="Snapshot JSONL dei chunk dei manuali.")],
    cycle_json: Annotated[Path, typer.Option(help="Ciclo: indica manuali e task da esportare.")],
    out: Annotated[Path, typer.Option(help="Cartella della knowledge base locale.")],
    version: Annotated[str, typer.Option(help="Versione da scrivere nel manifest.")] = "export",
) -> None:
    """Scrive una knowledge base locale a partire da snapshot delle sorgenti reali."""
    try:
        cycle = load_cycle(cycle_json)
        wanted: dict[str, list[str]] = {}
        for source in cycle.sources:
            wanted.setdefault(source.manual, [])
            if source.task:
                wanted[source.manual].append(source.task)
        for operation in cycle.operations:
            for source in cycle.sources:
                wanted.setdefault(source.manual, []).extend(operation.task_codes)
        with tempfile.TemporaryDirectory() as workdir:
            kb = RemoteKnowledgeBase(
                version,
                LocalDirObjectStore(structured_dir),
                IndexedManualSource(load_jsonl_index(chunks), Path(workdir)),
            )
            kb.preload()
            report = export_local_knowledge(
                kb, out, [(m, list(dict.fromkeys(t))) for m, t in wanted.items()], version=version
            )
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(f"{report.manuals} manuali e {report.tasks} task esportati in {out}")
    for item in report.missing:
        typer.echo(f"  non trovato: {item}")


@app.command()
def golden(
    directory: Annotated[
        Path, typer.Argument(help="Cartella del golden set (un caso per cartella).")
    ],
    knowledge: Annotated[Path | None, typer.Option(help="Cartella della knowledge base.")] = None,
    machines: Annotated[Path | None, typer.Option(help="JSON delle macchine attive.")] = None,
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
) -> None:
    """Esegue il golden set e stampa concordanza, costo, tempi e quota di sessioni in linea."""
    try:
        settings = load_settings(config)
        cases = load_cases(directory)
        if not cases:
            raise typer.BadParameter(f"Nessun caso in {directory}.")

        def deps_for(case: GoldenCase) -> Dependencies:
            return build_dependencies(
                settings,
                case.expected.profile,
                kb_dir=knowledge,
                machines_file=machines,
                extractor=FileCycleExtractor(case.cycle_path),
                out_dir=Path("runs") / "golden" / case.name,
            )

        summary = asyncio.run(run_golden(cases, deps_for))
    except (typer.BadParameter, CycleValidationError) as error:
        raise _fail(error) from error
    typer.echo(summary.render())
    if summary.concordance < 1.0:
        raise typer.Exit(code=1)


def _skip_checks(names: list[str]) -> frozenset[CheckName]:
    valid = {item.value: item for item in CheckName}
    unknown = [name for name in names if name not in valid]
    if unknown:
        raise typer.BadParameter(
            f"Controlli sconosciuti: {', '.join(unknown)}. Validi: {', '.join(valid)}."
        )
    return frozenset(valid[name] for name in names)


def build_dependencies(
    settings: Settings,
    profile_name: str,
    *,
    kb_dir: Path | None,
    machines_file: Path | None,
    extractor: CycleExtractor | None,
    out_dir: Path,
) -> Dependencies:
    """Senza `extractor` il ciclo si estrae dal PDF con una sessione LLM a output strutturato."""
    profile = load_profile(profile_name, settings.paths.profiles_dir)
    kb = load_local_knowledge(kb_dir or settings.paths.knowledge_dir)
    system_prompt = load_prompt(settings.paths.prompts_dir, OPERATION_PROMPT_FILE)
    session = make_session(settings.agent, out_dir / "transcripts")
    extraction_prompt = ""
    if extractor is None:
        extraction_prompt = load_prompt(settings.paths.prompts_dir, profile.extraction_prompt)
        extractor = LlmCycleExtractor(session, settings.agent, extraction_prompt)
        if profile.layout_extractor == "pvrm320":
            extractor = FallbackCycleExtractor(Pvrm320LayoutExtractor(), extractor)
    return Dependencies(
        settings=settings,
        profile=profile,
        kb=kb,
        machines=load_machine_registry(machines_file or settings.paths.machines_file),
        extractor=extractor,
        session=session,
        system_prompt=system_prompt,
        prompt_version=prompt_version(system_prompt, extraction_prompt),
        transcriber=make_transcriber(settings.agent),
    )


@app.command()
def run(
    pdf: Annotated[Path, typer.Argument(help="PDF del ciclo.")],
    profile: Annotated[str, typer.Option(help="mos | dr | ej200")] = "mos",
    cycle_json: Annotated[Path | None, typer.Option(help="Ciclo già estratto (JSON).")] = None,
    knowledge: Annotated[Path | None, typer.Option(help="Cartella della knowledge base.")] = None,
    machines: Annotated[Path | None, typer.Option(help="JSON delle macchine attive.")] = None,
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
    out: Annotated[Path, typer.Option(help="Cartella del run.")] = Path("runs/ultimo"),
    skip_check: Annotated[list[str] | None, typer.Option(help="Controllo da saltare.")] = None,
    serial_number: Annotated[str | None, typer.Option(help="DR: serial number.")] = None,
    condition: Annotated[
        str | None, typer.Option(help="DR: repair condition (1 oppure 1,2).")
    ] = None,
) -> None:
    """Valida un ciclo e scrive report.json, report.md e payload.json."""
    skipped = _skip_checks(skip_check or [])
    try:
        settings = load_settings(config)
        selectors = (
            parse_selectors(
                is_dr=profile == "dr", serial_number=serial_number, conditions=condition
            )
            if profile == "dr" or serial_number or condition
            else None
        )
        deps = build_dependencies(
            settings,
            profile,
            kb_dir=knowledge,
            machines_file=machines,
            extractor=FileCycleExtractor(cycle_json) if cycle_json else None,
            out_dir=out,
        )
        report = run_validation(
            RunRequest(pdf_path=pdf, selectors=selectors, skip_checks=skipped), deps, out
        )
    except typer.BadParameter as error:
        raise _fail(error) from error
    except CycleValidationError as error:
        raise _fail(error) from error
    counts = report.counts
    typer.echo(
        f"Ciclo {report.status.value}: {counts.corretto} corretti, {counts.warning} warning, "
        f"{counts.errato} errati, {counts.non_applicabile} non applicabili."
    )
    typer.echo(f"Risultati in {out}")
