"""CLI: `run`, `golden`, `kb-check` ed `eval` (esperimenti: `eval esegui`, `eval classifica`)."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from cycle_validation.agent.prompt import OPERATION_PROMPT_FILE, load_prompt, prompt_version
from cycle_validation.agent.sdk_session import SdkAgentSession
from cycle_validation.agent.session import AgentSession
from cycle_validation.config import AgentSettings, Settings, load_profile, load_settings
from cycle_validation.domain.check import CheckName
from cycle_validation.errors import CycleValidationError
from cycle_validation.evaluation.leaderboard import build_leaderboard, render_leaderboard
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.run import load_suites, run_variant
from cycle_validation.evaluation.variant import load_variant
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.composite import FallbackCycleExtractor
from cycle_validation.extract.from_file import FileCycleExtractor
from cycle_validation.extract.llm import LlmCycleExtractor
from cycle_validation.extract.pvrm320 import Pvrm320LayoutExtractor
from cycle_validation.golden import GoldenCase, load_cases, run_golden
from cycle_validation.ingest.transcribe import make_transcriber
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.resolve.dr import parse_selectors
from cycle_validation.services.machines import load_machine_registry

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Validazione dei cicli.")
eval_app = typer.Typer(
    no_args_is_help=True, help="Esperimenti: varianti provate sugli stessi casi e classifica."
)
app.add_typer(eval_app, name="eval")


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


def _session_for(name: str) -> Callable[[AgentSettings, Path | None], AgentSession]:
    """Implementazioni di AgentSession scelte per nome da una variante (`sessione:`)."""
    factories: dict[str, Callable[[AgentSettings, Path | None], AgentSession]] = {
        "sdk": lambda settings, transcripts: make_session(settings, transcripts),
    }
    return factories[name]


@eval_app.command("esegui")
def eval_run(
    variante: Annotated[Path, typer.Option(help="File YAML della variante.")],
    ripetizioni: Annotated[int, typer.Option(min=1, max=20, help="Volte per caso.")] = 3,
    casi: Annotated[Path, typer.Option(help="Una suite o una cartella di suite.")] = Path(
        "eval/casi/sintetici"
    ),
    config: Annotated[
        Path | None, typer.Option(help="Sostituisce il settings.yaml di partenza.")
    ] = None,
    ambiente: Annotated[
        str | None, typer.Option(help="Etichetta dell'ambiente. Vuoto = dedotta.")
    ] = None,
    risultati: Annotated[Path, typer.Option(help="Cartella dei risultati.")] = Path(
        "eval/risultati"
    ),
    runs: Annotated[
        Path | None, typer.Option(help="Cartella di lavoro e transcript. Vuoto = paths.runs_dir.")
    ] = None,
) -> None:
    """Esegue una variante su tutti i casi e scrive un file di risultati in eval/risultati."""
    try:
        variant = load_variant(variante, config_override=config)
        suites = load_suites(casi)
        path = asyncio.run(
            run_variant(
                variant,
                suites,
                repetitions=ripetizioni,
                results_dir=risultati,
                session_factory=_session_for(variant.session),
                project_root=Path.cwd(),
                runs_dir=runs or variant.settings.paths.runs_dir,
                environment=ambiente,
                cases_label=casi.as_posix(),
                progress=typer.echo,
            )
        )
        metrics = measure(json.loads(path.read_text(encoding="utf-8")))
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(
        f"{variant.name}: concordanza {metrics.concordance:.1%}".replace(".", ",")
        + f", ERRATO falsi {metrics.false_errato:g}, errori mancati {metrics.missed_errors:g}, "
        f"esiti tecnici {metrics.technical:g}, tempo mediano per ciclo "
        f"{metrics.time_median_ms / 1000:.1f} s, costo per ciclo {metrics.cost_per_cycle:.4f} USD"
    )
    for item in metrics.mismatches[:20]:
        typer.echo(f"    {item}")
    if len(metrics.mismatches) > 20:
        typer.echo(f"    ... e altre {len(metrics.mismatches) - 20} discordanze")
    typer.echo(f"Risultati in {path}")


@eval_app.command("classifica")
def eval_leaderboard(
    risultati: Annotated[Path, typer.Option(help="Cartella dei risultati.")] = Path(
        "eval/risultati"
    ),
    out: Annotated[Path, typer.Option(help="File della classifica.")] = Path("eval/classifica.md"),
) -> None:
    """Mette in classifica le varianti, per ambiente, e scrive eval/classifica.md."""
    try:
        text = render_leaderboard(build_leaderboard(risultati))
    except CycleValidationError as error:
        raise _fail(error) from error
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    typer.echo(text)
