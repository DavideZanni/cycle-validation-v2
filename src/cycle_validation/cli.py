"""CLI: `run`, `leggi`, `confronta`, `golden`, `kb-check` ed `eval` (esperimenti: `eval esegui`,
`eval classifica`)."""

import asyncio
import difflib
import json
import re
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
from cycle_validation.domain.cycle import Cycle
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
from cycle_validation.extract.pvrm320 import parse_pvrm320
from cycle_validation.extract.pvrm320_report import page_structure
from cycle_validation.golden import GoldenCase, load_cases, run_golden
from cycle_validation.ingest.pdf import read_pdf
from cycle_validation.ingest.transcribe import make_transcriber
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.resolve.dr import SERIAL_IN_TEXT, parse_selectors, serials_in_text
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


# Caso DR scritto nel testo della stampa: "D.R. CASE #00000000". Il serial number
# ("APPLY ON S/N XXXX0000") si cerca con `SERIAL_IN_TEXT`, lo stesso della validazione.
_DR_CASE = re.compile(r"D\.\s*R\.\s*CASE\s*#?\s*(\d{6,})", re.IGNORECASE)


_CODE_TOKEN = re.compile(r"\S*\d\S*")


def _masked_quotes(text: str) -> str:
    """Un messaggio del programma: si mascherano solo i pezzi di documento tra « »."""
    return re.sub(r"«([^»]*)»", lambda m: f"«{_masked(m[1])}»", text)


def _masked(text: str) -> str:
    """Le parole con almeno una cifra diventano forme: «AB12-3C» → «AA99-9A». Le altre restano."""

    def shape(match: re.Match[str]) -> str:
        return re.sub(r"\d", "9", re.sub(r"[A-Za-z]", "A", match.group()))

    return _CODE_TOKEN.sub(shape, text)


@app.command("leggi")
def read_cycles(
    pdfs: Annotated[list[Path], typer.Argument(help="PDF dei cicli.")],
    profile: Annotated[str, typer.Option(help="mos | dr | ej200")] = "mos",
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
    pagina: Annotated[
        int | None, typer.Option(help="Stampa anche il testo di questa pagina, riga per riga.")
    ] = None,
    cerca: Annotated[
        str | None,
        typer.Option(
            help="Stampa solo le righe che contengono questo testo, con i codici mascherati "
            "(lettere → A, cifre → 9), e i serial number trovati, mascherati."
        ),
    ] = None,
    struttura: Annotated[
        int | None,
        typer.Option(
            help="Stampa come il parser vede ogni riga di questa pagina (tipo di riga, numero "
            "di operazione, prima parola), senza il testo: per capire un errore di layout."
        ),
    ] = None,
) -> None:
    """Legge i cicli con il parser di layout, senza modello né conoscenza (zero token), e
    stampa riparazione, fonti e task citati: serve a scegliere quali cicli provare. Con
    `--pagina` stampa il testo di quella pagina com'è letto dal PDF, per capire un errore."""
    try:
        settings = load_settings(config)
        limits = load_profile(profile, settings.paths.profiles_dir).file_limits
    except CycleValidationError as error:
        raise _fail(error) from error
    for path in pdfs:
        typer.echo(path.name)
        try:
            pdf = read_pdf(path, limits)
        except CycleValidationError as error:
            typer.echo(f"  non letto: {error}")
            continue
        reordered = [str(page.number) for page in pdf.pages if page.reordered]
        if reordered:
            typer.echo(f"  pagine rimesse nell'ordine della pagina: {', '.join(reordered)}")
        if struttura is not None:
            if not 1 <= struttura <= len(pdf.pages):
                typer.echo(f"  pagina {struttura} non c'è (pagine: {len(pdf.pages)})")
                continue
            if pdf.pages[struttura - 1].reordered:
                typer.echo("  (righe rimesse nell'ordine della pagina: stampa modificata a mano)")
            for number, shape in enumerate(page_structure(pdf.pages[struttura - 1].text), 1):
                # solo la parola tra « » viene dal documento: si maschera quella
                typer.echo(f"  {number:3} | {_masked_quotes(shape)}")
            try:
                parse_pvrm320(pdf)
                typer.echo("  parser: letto")
            except CycleValidationError as error:
                typer.echo(f"  parser: {_masked_quotes(str(error))}")
            continue
        if cerca:
            # per capire cosa c'è nella stampa senza far vedere codici veri nelle foto
            for page in pdf.pages:
                for line in page.text.splitlines():
                    if cerca.casefold() in line.casefold():
                        typer.echo(f"  p.{page.number} | {_masked(line.strip())}")
            serials = [_masked(serial) for serial in serials_in_text(pdf.text)]
            typer.echo(f"  serial number trovati: {len(serials)} ({', '.join(serials) or '-'})")
            continue
        if pagina is not None and 1 <= pagina <= len(pdf.pages):
            for number, line in enumerate(pdf.pages[pagina - 1].text.splitlines(), 1):
                typer.echo(f"  {number:3} | {line}")
        # caso DR e serial number si cercano nel testo, anche se il parser non lo legge
        cases = list(dict.fromkeys(_DR_CASE.findall(pdf.text)))
        serials = list(dict.fromkeys(SERIAL_IN_TEXT.findall(pdf.text)))
        if cases or serials:
            typer.echo(f"  dr: caso {', '.join(cases) or '-'} · S/N {', '.join(serials) or '-'}")
        try:
            cycle = parse_pvrm320(pdf)
        except CycleValidationError as error:
            typer.echo(f"  non letto dal parser: {error}")
            continue
        sources = ", ".join(
            source.manual + (f" {source.task}" if source.task else "") for source in cycle.sources
        )
        tasks = list(dict.fromkeys(code for op in cycle.operations for code in op.task_codes))
        typer.echo(
            f"  riparazione: {cycle.repair_code or '-'} · fonti: {sources or '-'} · "
            f"operazioni: {len(cycle.operations)}"
        )
        typer.echo(f"  task: {', '.join(tasks) or '-'}")


def _changed(first: str, second: str, quote: str = "") -> str:
    """Due valori diversi, con i codici mascherati. Se la forma mascherata è la stessa lo dice:
    vuol dire che cambia solo qualche lettera o cifra di un codice."""
    a, b = _masked(first) or "-", _masked(second) or "-"
    if quote:
        a, b = f"«{a}»", f"«{b}»"
    same_shape = " (stessa forma: cambia qualche lettera o cifra)" if a == b else ""
    return f"{a} → {b}{same_shape}"


def _word_changes(first: str, second: str, limit: int = 5) -> list[str]:
    """I pezzi di testo che cambiano tra due descrizioni, mascherati e corti: dicono dove è la
    differenza senza stampare la descrizione."""
    words_a, words_b = first.split(), second.split()
    matcher = difflib.SequenceMatcher(a=words_a, b=words_b, autojunk=False)
    changes = [
        _changed(" ".join(words_a[i1:i2]), " ".join(words_b[j1:j2]), quote="«")
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]
    extra = len(changes) - limit
    return changes[:limit] + ([f"... e altre {extra}"] if extra > 0 else [])


def _cycle_differences(first: Cycle, second: Cycle) -> list[str]:
    lines: list[str] = []
    for name in (
        "cycle_code",
        "cycle_description",
        "engine_model",
        "operation_type",
        "repair_code",
    ):
        a, b = getattr(first, name) or "", getattr(second, name) or ""
        if a != b:
            lines.append(f"  ciclo, {name}: {_changed(a, b)}")
    for index in range(max(len(first.sources), len(second.sources))):
        a = first.sources[index] if index < len(first.sources) else None
        b = second.sources[index] if index < len(second.sources) else None
        label = f"  fonte {index + 1}"
        if a is None or b is None:
            lines.append(f"{label}: c'è solo nel {'secondo' if a is None else 'primo'}")
            continue
        for name in ("manual", "task", "repair_code", "issue"):
            value_a, value_b = getattr(a, name) or "", getattr(b, name) or ""
            if value_a != value_b:
                lines.append(f"{label}, {name}: {_changed(value_a, value_b)}")
    ops_a = {op.operation_number: op for op in first.operations}
    ops_b = {op.operation_number: op for op in second.operations}
    for number in dict.fromkeys([*ops_a, *ops_b]):
        a_op, b_op = ops_a.get(number), ops_b.get(number)
        label = f"  op {number}"
        if a_op is None or b_op is None:
            lines.append(f"{label}: c'è solo nel {'secondo' if a_op is None else 'primo'}")
            continue
        if a_op.operation_description != b_op.operation_description:
            lines.append(f"{label}, descrizione:")
            lines += [
                f"      {item}"
                for item in _word_changes(a_op.operation_description, b_op.operation_description)
            ]
        pairs = {
            "task code": (", ".join(a_op.task_codes), ", ".join(b_op.task_codes)),
            "targa": (a_op.machine_tag or "", b_op.machine_tag or ""),
            "scheda": (
                a_op.process_sheet.code if a_op.process_sheet else "",
                b_op.process_sheet.code if b_op.process_sheet else "",
            ),
            "riparazione": (a_op.repair_code or "", b_op.repair_code or ""),
        }
        for name, (value_a, value_b) in pairs.items():
            if value_a != value_b:
                lines.append(f"{label}, {name}: {_changed(value_a, value_b)}")
    return lines


@app.command("confronta")
def compare_cycles(
    primo: Annotated[Path, typer.Argument(help="PDF del ciclo giusto.")],
    secondo: Annotated[Path, typer.Argument(help="PDF dello stesso ciclo con errori.")],
    profile: Annotated[str, typer.Option(help="mos | dr | ej200")] = "mos",
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
) -> None:
    """Confronta due stampe dello stesso ciclo (la giusta e quella «con errori») con il parser
    di layout, senza modello (zero token): dice in quali operazioni e in quali campi sono
    diverse. I codici escono mascherati (lettere → A, cifre → 9), così si possono mandare foto
    senza codici veri; delle descrizioni stampa solo i pezzi che cambiano."""
    try:
        settings = load_settings(config)
        limits = load_profile(profile, settings.paths.profiles_dir).file_limits
    except CycleValidationError as error:
        raise _fail(error) from error
    cycles: list[Cycle] = []
    for which, path in (("primo (giusto)", primo), ("secondo (con errori)", secondo)):
        try:
            cycles.append(parse_pvrm320(read_pdf(path, limits)))
        except CycleValidationError as error:
            typer.echo(f"il {which} non è letto dal parser: {_masked_quotes(str(error))}")
    if len(cycles) < 2:
        return
    lines = _cycle_differences(*cycles)
    typer.echo(
        f"operazioni: {len(cycles[0].operations)} e {len(cycles[1].operations)} · "
        f"differenze: {len(lines) - sum(line.startswith('      ') for line in lines)}"
    )
    for line in lines:
        typer.echo(line)


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
        done = subprocess.run(
            [sys.executable, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
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
