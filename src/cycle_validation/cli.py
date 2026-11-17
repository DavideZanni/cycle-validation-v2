"""CLI: `run`, `golden`, `kb-check` ed `eval` (esperimenti: `eval esegui`, `eval classifica`)."""

import asyncio
import json
from collections import Counter
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
from cycle_validation.evaluation.draft import draft_case
from cycle_validation.evaluation.leaderboard import build_leaderboard, render_leaderboard
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.mutations import mutate_cases
from cycle_validation.evaluation.run import load_suites, run_variant
from cycle_validation.evaluation.snapshot import snapshot_version, take_snapshot
from cycle_validation.evaluation.variant import load_variant
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.factory import make_pdf_extractor
from cycle_validation.extract.from_file import FileCycleExtractor
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
    """Carica una knowledge base locale e stampa i conteggi, voci incerte comprese.
    Fallisce anche per un `uncertainty.json` incoerente, che il servizio tollererebbe."""
    problems: list[str] = []
    try:
        kb = load_local_knowledge(directory, problems=problems)
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(f"Knowledge base {kb.version}")
    for name, count in kb.stats().items():
        typer.echo(f"  {name}: {count}")
    for name, count in kb.uncertain_counts().items():
        typer.echo(f"  {name}: {count}")
    if problems:
        for problem in problems:
            typer.echo(f"Errore: {problem}")
        raise typer.Exit(code=1)


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
        extractor, extraction_prompt = make_pdf_extractor(
            profile, settings.agent, session, settings.paths.prompts_dir
        )
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


def _summary(name: str, path: Path) -> str:
    metrics = measure(json.loads(path.read_text(encoding="utf-8")))
    lines = [
        f"{name}: concordanza {metrics.concordance:.1%}".replace(".", ",")
        + f", ERRATO falsi {metrics.false_errato:g}, errori mancati {metrics.missed_errors:g}, "
        f"esiti tecnici {metrics.technical:g}, tempo mediano per ciclo "
        f"{metrics.time_median_ms / 1000:.1f} s, costo per ciclo {metrics.cost_per_cycle:.4f} USD"
        + (
            f", estrazione dal PDF {metrics.extraction_accuracy:.1%}".replace(".", ",")
            if metrics.extraction_accuracy is not None
            else ""
        )
    ]
    lines += [f"    {item}" for item in metrics.mismatches[:20]]
    if len(metrics.mismatches) > 20:
        lines.append(f"    ... e altre {len(metrics.mismatches) - 20} discordanze")
    lines.append(f"Risultati in {path}")
    return "\n".join(lines)


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
        summary = _summary(variant.name, path)
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(summary)


def _write_leaderboard(results_dir: Path, out: Path) -> str:
    text = render_leaderboard(build_leaderboard(results_dir))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    return text


@eval_app.command("classifica")
def eval_leaderboard(
    risultati: Annotated[Path, typer.Option(help="Cartella dei risultati.")] = Path(
        "eval/risultati"
    ),
    out: Annotated[
        Path | None,
        typer.Option(
            help="File della classifica. Vuoto = classifica.md nella cartella dei risultati."
        ),
    ] = None,
) -> None:
    """Mette in classifica le varianti, per ambiente, e scrive classifica.md accanto ai risultati."""
    try:
        text = _write_leaderboard(risultati, out or risultati / "classifica.md")
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(text)


@eval_app.command("fotografia")
def eval_snapshot(
    bucket: Annotated[str, typer.Option(help="Bucket S3 della conoscenza.")],
    prefisso: Annotated[list[str], typer.Option(help="Prefisso da copiare (ripetibile).")],
    out: Annotated[Path, typer.Option(help="Cartella nuova della fotografia.")],
    regione: Annotated[str | None, typer.Option(help="Regione AWS. Vuoto = ambiente.")] = None,
) -> None:
    """Copia i prefissi S3 della conoscenza in una cartella datata (credenziali dell'ambiente)."""
    try:
        import boto3
    except ImportError as error:
        raise _fail(
            CycleValidationError("Serve boto3: installare l'extra aws (uv sync --extra aws).")
        ) from error
    from cycle_validation.kb.stores import S3ObjectStore

    store = S3ObjectStore(boto3.client("s3", region_name=regione), bucket)
    try:
        count = take_snapshot(store, prefisso, out, source=f"s3://{bucket}")
    except CycleValidationError as error:
        raise _fail(error) from error
    typer.echo(f"Fotografia in {out}: {count} oggetti ({snapshot_version(out)}).")


@eval_app.command("mutazioni")
def eval_mutations(
    casi: Annotated[Path, typer.Option(help="Una suite o una cartella di suite.")] = Path(
        "eval/casi/aziendali"
    ),
    out: Annotated[Path, typer.Option(help="Dove scrivere le suite mutate.")] = Path(
        "eval/casi/mutazioni"
    ),
) -> None:
    """Copie dei casi rivisti con un difetto noto o una modifica innocua, con l'esito atteso."""
    try:
        made = mutate_cases(casi, out)
    except CycleValidationError as error:
        raise _fail(error) from error
    kinds = Counter(name.split("__", 1)[1] for name in made)
    detail = ", ".join(f"{kind} {count}" for kind, count in sorted(kinds.items()))
    typer.echo(f"{len(made)} mutazioni in {out} ({detail or 'nessuna'}).")
    if made:
        typer.echo(f"Per provarle: cycle-validation eval pipeline --casi {out}")


@eval_app.command("prepara")
def eval_draft(
    caso: Annotated[Path, typer.Argument(help="Cartella del caso, con ciclo.pdf.")],
    profilo: Annotated[
        str | None, typer.Option(help="mos | dr | ej200. Vuoto = quello della suite.")
    ] = None,
    variante: Annotated[Path, typer.Option(help="Variante con cui fare la bozza.")] = Path(
        "eval/varianti/baseline.yaml"
    ),
    config: Annotated[
        Path | None, typer.Option(help="Sostituisce il settings.yaml di partenza.")
    ] = None,
    serial_number: Annotated[str | None, typer.Option(help="DR: serial number.")] = None,
    condition: Annotated[
        str | None, typer.Option(help="DR: repair condition (1 oppure 1,2).")
    ] = None,
    sovrascrivi: Annotated[bool, typer.Option(help="Rifà anche una bozza già rivista.")] = False,
) -> None:
    """Scrive la bozza di expected.json (e ciclo.json) per un ciclo vero, da far rivedere."""
    try:
        variant = load_variant(variante, config_override=config)
        (suite,) = load_suites(caso.parent)
        selectors = None
        if serial_number or condition:
            parsed = parse_selectors(is_dr=True, serial_number=serial_number, conditions=condition)
            assert parsed is not None
            selectors = {
                "serial_number": parsed.serial_number,
                "conditions": list(parsed.conditions),
            }
        report = draft_case(
            caso,
            suite,
            variant,
            _session_for(variant.session),
            project_root=Path.cwd(),
            workdir=variant.settings.paths.runs_dir / "eval" / "prepara" / caso.name,
            profile=profilo,
            selectors=selectors,
            overwrite=sovrascrivi,
        )
    except (typer.BadParameter, CycleValidationError) as error:
        raise _fail(error) from error
    counts = report.counts
    typer.echo(
        f"Bozza scritta: {counts.corretto} corretti, {counts.warning} warning, "
        f"{counts.errato} errati, {counts.non_applicabile} non applicabili."
    )
    typer.echo(f'Da rivedere: {caso / "revisione.md"}, poi in expected.json "rivisto": true.')


CHECKS = (
    ("test", ["-m", "pytest", "-q", "-p", "no:cacheprovider"]),
    ("ruff", ["-m", "ruff", "check", "src", "tests"]),
    ("formato", ["-m", "ruff", "format", "--check", "src", "tests"]),
    ("mypy", ["-m", "mypy"]),
)


def run_code_checks(echo: Callable[[str], None]) -> bool:
    """Test, ruff e mypy con lo stesso Python del programma. Requisito, non punteggio."""
    import subprocess
    import sys

    ok = True
    for name, args in CHECKS:
        done = subprocess.run([sys.executable, *args], capture_output=True, text=True)
        last = (done.stdout.strip().splitlines() or [""])[-1]
        echo(f"  {name}: {'OK' if done.returncode == 0 else 'FALLITO'} {last}")
        if done.returncode != 0:
            ok = False
            echo(done.stdout[-3000:] + done.stderr[-2000:])
    return ok


def _variant_files(folder: Path, names: list[str] | None) -> list[Path]:
    files = sorted(folder.glob("*.yaml"))
    if names:
        wanted = set(names) | {"baseline"}
        unknown = wanted - {f.stem for f in files}
        if unknown:
            raise CycleValidationError(f"Varianti non trovate in {folder}: {', '.join(unknown)}.")
        files = [f for f in files if f.stem in wanted]
    if not any(f.stem == "baseline" for f in files):
        raise CycleValidationError(f"Manca {folder / 'baseline.yaml'}: serve come riferimento.")
    return sorted(files, key=lambda f: (f.stem != "baseline", f.stem))


@eval_app.command("pipeline")
def eval_pipeline(
    casi: Annotated[Path, typer.Option(help="Una suite o una cartella di suite.")] = Path(
        "eval/casi/sintetici"
    ),
    variante: Annotated[
        list[str] | None,
        typer.Option(help="Solo queste varianti (ripetibile). Vuoto = tutte. Baseline sempre."),
    ] = None,
    ripetizioni: Annotated[int, typer.Option(min=1, max=20, help="Volte per caso.")] = 3,
    config: Annotated[
        Path | None, typer.Option(help="Sostituisce il settings.yaml di partenza.")
    ] = None,
    ambiente: Annotated[
        str | None, typer.Option(help="Etichetta dell'ambiente. Vuoto = dedotta.")
    ] = None,
    varianti: Annotated[Path, typer.Option(help="Cartella delle varianti.")] = Path(
        "eval/varianti"
    ),
    risultati: Annotated[Path, typer.Option(help="Cartella dei risultati.")] = Path(
        "eval/risultati"
    ),
    salta_verifiche: Annotated[
        bool, typer.Option(help="Non lancia test, ruff e mypy prima delle prove.")
    ] = False,
    runs: Annotated[
        Path | None, typer.Option(help="Cartella di lavoro e transcript. Vuoto = paths.runs_dir.")
    ] = None,
) -> None:
    """Tutto in un comando: verifiche del codice, baseline e varianti sui casi, classifica."""
    echo = typer.echo
    if not salta_verifiche:
        echo("1. Verifiche del codice")
        if not run_code_checks(echo):
            raise _fail(CycleValidationError("verifiche del codice fallite: prove non lanciate."))
    try:
        files = _variant_files(varianti, variante)
        loaded = [load_variant(f, config_override=config) for f in files]
        suites = load_suites(casi)
        reviewed = sum(1 for s in suites for c in s.cases if c.expected.rivisto)
        if not reviewed:
            raise CycleValidationError(
                f"Nessun caso rivisto in {casi}: prima `eval prepara` e la revisione."
            )
        echo(
            f"2. Prove: {len(loaded)} varianti x {reviewed} casi x {ripetizioni} ripetizioni "
            f"({', '.join(v.name for v in loaded)})"
        )
        for number, variant in enumerate(loaded, 1):
            echo(f"--- variante {number}/{len(loaded)}: {variant.name} ({variant.description})")
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
                    progress=echo,
                )
            )
            echo(_summary(variant.name, path))
        echo("3. Classifica")
        out = risultati / "classifica.md"
        echo(_write_leaderboard(risultati, out))
    except CycleValidationError as error:
        raise _fail(error) from error
    echo(f"Classifica in {out}")
