"""CLI: `run`, `leggi`, `confronta`, `manuali`, `macchine`, `qa`, `golden`, `kb-check` ed `eval` (esperimenti: `eval esegui`,
`eval classifica`)."""

import asyncio
import difflib
import hashlib
import json
import os
import re
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml

from cycle_validation.agent.prompt import OPERATION_PROMPT_FILE, load_prompt, prompt_version
from cycle_validation.agent.sdk_session import SdkAgentSession
from cycle_validation.agent.session import AgentSession
from cycle_validation.checks.languages import language_parts, number_mismatches
from cycle_validation.config import AgentSettings, Settings, load_profile, load_settings
from cycle_validation.domain.check import CheckName
from cycle_validation.domain.cycle import Cycle
from cycle_validation.domain.report import Report
from cycle_validation.errors import CycleValidationError
from cycle_validation.evaluation.blind import DESCRIPTIONS as BLIND_DESCRIPTIONS
from cycle_validation.evaluation.blind import KINDS as BLIND_KINDS
from cycle_validation.evaluation.blind import blind_mutations
from cycle_validation.evaluation.draft import draft_case
from cycle_validation.evaluation.leaderboard import build_leaderboard, render_leaderboard
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.mutations import mutate_cases
from cycle_validation.evaluation.run import load_suites, run_variant
from cycle_validation.evaluation.snapshot import snapshot_version, take_snapshot
from cycle_validation.evaluation.trials import (
    TRIAL_REPORT,
    CycleScore,
    build_trial,
    failed_cycle,
    load_known_errors,
    load_trials,
    score_cycle,
    write_summary,
    write_trial,
)
from cycle_validation.evaluation.variant import load_variant
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.factory import make_pdf_extractor
from cycle_validation.extract.from_file import FileCycleExtractor
from cycle_validation.extract.pvrm320 import parse_pvrm320
from cycle_validation.extract.pvrm320_report import footer_oems, page_structure
from cycle_validation.golden import GoldenCase, load_cases, run_golden
from cycle_validation.ingest.pdf import read_pdf, read_pdf_bytes
from cycle_validation.ingest.transcribe import make_transcriber
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.module_kind import EJ200, detect_module_kind
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.report.manuals import (
    CycleSeen,
    cycle_coverage,
    explain_missing,
    file_lines,
    from_cycle,
    from_report,
    match_files,
    needed_manuals,
    parse_errors,
    screen_lines,
)
from cycle_validation.resolve.dr import SERIAL_IN_TEXT, parse_selectors, serials_in_text
from cycle_validation.services.machines import load_machine_registry
from cycle_validation.text import normalize_code

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


# Codice ATA scritto nella descrizione, con la parola prima (TASK, SUBTASK, il manuale...).
_ATA_REFERENCE = re.compile(
    r"(?:(?P<word>[A-Za-z][\w.]*)\s+)?(?P<code>\d{2}-\d{2}-\d{2}(?:(?:[-/]\d{3})+|\s*,?\s*[A-Z]+\s+\d{3})?)(?![\dA-Za-z])"
)


def _reference_shape(match: re.Match[str]) -> str:
    """Parola e codice: la sezione si vede, il resto del codice e la parola diventano forme."""
    code = match["code"]
    shown = code[:8] + _masked(code[8:]) if len(code) > 8 else code
    return f"{_masked(match['word'])} {shown}" if match["word"] else shown


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
    breve: Annotated[
        bool,
        typer.Option(help="Una riga per stampa: operazioni, pagine rimesse in ordine, parser."),
    ] = False,
    senza_riordino: Annotated[
        bool,
        typer.Option(
            help="Legge il testo nell'ordine del PDF, senza rimettere in ordine le righe."
        ),
    ] = False,
    struttura: Annotated[
        int | None,
        typer.Option(
            help="Stampa come il parser vede ogni riga di questa pagina (tipo di riga, numero "
            "di operazione, prima parola), senza il testo: per capire un errore di layout."
        ),
    ] = None,
    lingue: Annotated[
        bool,
        typer.Option(
            help="Stampa le operazioni in cui la descrizione italiana e quella inglese hanno "
            "numeri diversi (solo i numeri), e quante operazioni hanno le due lingue."
        ),
    ] = False,
    fonti: Annotated[
        bool,
        typer.Option(
            help="Stampa le fonti (task e riparazione, il manuale come M1, M2, ...) e le "
            "riparazioni delle operazioni, senza codici di manuali."
        ),
    ] = False,
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
            pdf = read_pdf(path, limits, reorder=not senza_riordino)
        except CycleValidationError as error:
            typer.echo(f"  non letto: {_masked_quotes(str(error))}")
            continue
        reordered = [str(page.number) for page in pdf.pages if page.reordered]
        if breve:
            try:
                parsed = parse_pvrm320(pdf)
                state = f"operazioni: {len(parsed.operations)} · parser: letto"
            except CycleValidationError as error:
                state = f"parser: NON LETTO ({_masked_quotes(str(error))})"
            typer.echo(f"  {state} · pagine rimesse in ordine: {', '.join(reordered) or 'nessuna'}")
            continue
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
        if lingue:
            try:
                cycle = parse_pvrm320(pdf)
            except CycleValidationError as error:
                typer.echo(f"  non letto dal parser: {_masked_quotes(str(error))}")
                continue
            both = [op for op in cycle.operations if language_parts(op.operation_description)]
            for op in both:
                if pairs := number_mismatches(op.operation_description):
                    shown = ", ".join(f"{a} → {b}" for a, b in pairs)
                    typer.echo(f"  op {op.operation_number}: italiano → inglese {shown}")
            typer.echo(f"  operazioni con le due lingue: {len(both)} su {len(cycle.operations)}")
            continue
        if fonti:
            try:
                cycle = parse_pvrm320(pdf)
            except CycleValidationError as error:
                typer.echo(f"  non letto dal parser: {_masked_quotes(str(error))}")
                continue
            names = list(dict.fromkeys(source.manual for source in cycle.sources))
            for source in cycle.sources:
                typer.echo(
                    f"  fonte M{names.index(source.manual) + 1} · task {source.task or '-'} · "
                    f"rc {source.repair_code or '-'}"
                )
            repairs = sorted({op.repair_code or "-" for op in cycle.operations})
            typer.echo(f"  rc delle operazioni: {' '.join(repairs)}")
            oems = [_masked(oem) for oem in footer_oems(pdf)]
            typer.echo(f"  OEM nel piè di pagina (forma): {', '.join(oems) or 'nessuno'}")
            for op in cycle.operations:
                cited = {normalize_code(code) for code in op.task_codes}
                others = [
                    _reference_shape(match)
                    for match in _ATA_REFERENCE.finditer(op.operation_description)
                    if normalize_code(match["code"]) not in cited
                ]
                if others:
                    typer.echo(
                        f"  op {op.operation_number} · rc {op.repair_code or '-'} · task "
                        f"{', '.join(op.task_codes) or '-'} · altri codici nel testo: "
                        f"{'; '.join(dict.fromkeys(others))}"
                    )
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
            typer.echo(f"  non letto dal parser: {_masked_quotes(str(error))}")
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
    primo_senza_riordino: Annotated[
        bool,
        typer.Option(
            help="Legge la prima stampa senza rimettere in ordine le righe: con la stessa stampa "
            "due volte mostra cosa cambia il riordino."
        ),
    ] = False,
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
    readings = (
        (
            "primo (senza riordino)" if primo_senza_riordino else "primo (giusto)",
            primo,
            not primo_senza_riordino,
        ),
        (
            "secondo (con riordino)" if primo_senza_riordino else "secondo (con errori)",
            secondo,
            True,
        ),
    )
    for which, path, reorder in readings:
        try:
            cycles.append(parse_pvrm320(read_pdf(path, limits, reorder=reorder)))
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


_SKIPPED_FOLDERS = frozenset({"node_modules", ".venv", "venv", ".git", "__pycache__"})


def _pdfs_in(folder: Path) -> list[Path]:
    """I PDF di una cartella e delle sottocartelle, saltando quelle di programmi e librerie."""
    found: list[Path] = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in _SKIPPED_FOLDERS)
        found.extend(Path(root) / name for name in sorted(files) if name.lower().endswith(".pdf"))
    return found


# una stampa di ciclo pesa poco: i PDF più grandi (manuali, scansioni lunghe) non si leggono
_CYCLE_MAX_BYTES = 20 * 1024 * 1024


def _read_cycles(
    pdfs: list[Path],
    settings: Settings,
    cycles: dict[str, CycleSeen],
    names: dict[str, list[str]],
    hash_of: dict[str, str],
) -> int:
    """Legge le stampe con il parser (zero token): `cycles` per impronta, `names` i nomi dei
    file di ogni impronta, `hash_of` l'impronta di ogni percorso. Ritorna i PDF non letti (non
    cicli PVRM320 o troppo grandi). Un'impronta già in `cycles` non si rilegge."""
    limits = load_profile("mos", settings.paths.profiles_dir).file_limits
    unread = 0
    for pdf_path in pdfs:
        try:
            if pdf_path.stat().st_size > (limits.max_bytes or _CYCLE_MAX_BYTES):
                unread += 1  # troppo grande per un ciclo (per esempio un manuale)
                continue
            data = pdf_path.read_bytes()
        except OSError:
            unread += 1
            continue
        name = hashlib.sha256(data).hexdigest()[:8]
        names.setdefault(name, []).append(pdf_path.name)
        hash_of[str(pdf_path)] = name
        if name in cycles:
            continue
        try:
            pdf = read_pdf_bytes(data, pdf_path.name, limits)
            military = detect_module_kind(pdf.text, settings.module_check) == EJ200
            cycles[name] = from_cycle(name, parse_pvrm320(pdf), military=military)
        except CycleValidationError:
            unread += 1
    return unread


@app.command("manuali")
def list_manuals(
    percorsi: Annotated[
        list[Path],
        typer.Argument(
            help="Stampe dei cicli (PDF), cartelle con stampe, o cartelle di prove già fatte "
            "(con report.json)."
        ),
    ],
    errori: Annotated[
        list[str] | None,
        typer.Option(help="Operazioni con un errore noto: impronta=op,op (si può ripetere)."),
    ] = None,
    conoscenza: Annotated[
        Path | None,
        typer.Option(help="Versione della conoscenza (cartella) con cui confrontare i manuali."),
    ] = None,
    out: Annotated[Path, typer.Option(help="File con i codici veri (resta sul PC).")] = Path(
        "runs/manuali-da-ingestionare.txt"
    ),
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
) -> None:
    """I manuali da mettere nella conoscenza per i cicli di prova (zero token). Le stampe si
    leggono con il parser; con `--conoscenza` dice quali manuali e task mancano. Sullo schermo
    M1, M2, ... e le impronte dei cicli; i codici veri, i capitoli e i task nel file `--out`."""
    try:
        errors = parse_errors(errori or [])
        settings = load_settings(config)
        load_profile("mos", settings.paths.profiles_dir)
        kb = load_local_knowledge(conoscenza) if conoscenza else None
    except CycleValidationError as error:
        raise _fail(error) from error
    cycles: dict[str, CycleSeen] = {}
    names: dict[str, list[str]] = {}
    pdfs: list[Path] = []
    hash_of: dict[str, str] = {}
    for path in percorsi:
        if path.is_dir() and (path / "report.json").is_file():
            try:
                report = json.loads((path / "report.json").read_text(encoding="utf-8"))
                cycles[path.name] = from_report(path.name, report)
            except (OSError, ValueError) as error:
                typer.echo(f"{path.name}: report.json non letto ({type(error).__name__}).")
        elif path.is_dir():
            pdfs.extend(_pdfs_in(path))
        elif path.suffix.lower() == ".pdf":
            pdfs.append(path)
    unread = _read_cycles(pdfs, settings, cycles, names, hash_of)
    if not cycles:
        raise _fail(CycleValidationError("Nessun ciclo letto: niente da elencare."))
    result = needed_manuals(list(cycles.values()), errors, kb)
    if kb is not None:
        explain_missing(result, kb)
    # i PDF che non sono cicli possono essere i file dei manuali: si collegano alla lista
    cycle_files = {str(path) for path in pdfs if hash_of.get(str(path)) in cycles}
    match_files(result, [str(path) for path in pdfs if str(path) not in cycle_files])
    out.parent.mkdir(parents=True, exist_ok=True)
    read = {name: files for name, files in names.items() if name in cycles}
    out.write_text("\n".join(file_lines(result, read)) + "\n", encoding="utf-8")
    if pdfs:
        typer.echo(
            f"Stampe: {len(pdfs)} file, {len(names)} diverse; cicli letti: "
            f"{len(cycles)}; non lette (non sono cicli PVRM320 o troppo grandi): {unread}."
        )
    needed = sum(need.needed for need in result.manuals)
    typer.echo(
        f"Manuali citati: {len(result.manuals)}; da ingestionare: {needed}"
        + ("" if kb else " (senza --conoscenza: stato dai report, se ci sono)")
        + "."
    )
    for line in screen_lines(result):
        typer.echo(line)
    for line in result.unmatched:
        typer.echo(f"senza manuale: {line}")
    typer.echo(f"Codici veri, capitoli e task: {out}")


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


DEFAULT_TRIAL_LIST = Path("runs/prove/cicli.txt")


@eval_app.command("scegli")
def eval_choose(
    percorsi: Annotated[list[Path], typer.Argument(help="Cartelle (o PDF) con le stampe.")],
    knowledge: Annotated[Path, typer.Option(help="Versione della conoscenza (cartella).")],
    quanti: Annotated[
        int, typer.Option(help="Cicli nella lista, compresi quelli noti. 0 = tutti.")
    ] = 30,
    copertura: Annotated[
        float, typer.Option(help="Parte minima delle operazioni confrontabili (0-1).")
    ] = 0.8,
    attesi: Annotated[Path, typer.Option(help="YAML degli errori noti.")] = Path(
        "eval/errori-noti.yaml"
    ),
    out: Annotated[Path, typer.Option(help="Lista dei PDF (resta sul PC).")] = DEFAULT_TRIAL_LIST,
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
) -> None:
    """Sceglie i cicli di una prova più grande (zero token): prima i cicli di `--attesi` (con
    errori e giusti), poi cicli veri civili con almeno `--copertura` delle operazioni
    confrontabili con la conoscenza, in ordine di impronta (sempre gli stessi), fino a
    `--quanti`. Scrive i percorsi in `--out`; sullo schermo solo impronte e numeri."""
    try:
        settings = load_settings(config)
        load_profile("mos", settings.paths.profiles_dir)
        known = load_known_errors(attesi)
        kb = load_local_knowledge(knowledge)
    except (CycleValidationError, OSError, ValueError) as error:
        raise _fail(error) from error
    pdfs: list[Path] = []
    for path in percorsi:
        pdfs.extend(_pdfs_in(path) if path.is_dir() else [path])
    cycles: dict[str, CycleSeen] = {}
    names: dict[str, list[str]] = {}
    hash_of: dict[str, str] = {}
    unread = _read_cycles(pdfs, settings, cycles, names, hash_of)
    first: dict[str, Path] = {}
    for pdf in pdfs:
        first.setdefault(hash_of.get(str(pdf), ""), pdf)
    noted = [name for name in sorted(cycles) if known.cycle(name) is not None]
    chosen = list(noted)
    skipped = Counter[str]()
    lines: list[str] = []
    for name in sorted(cycles):
        seen = cycles[name]
        if name in noted:
            continue
        if seen.military:
            skipped["EJ200 (la sua conoscenza resta su AWS)"] += 1
            continue
        covered, total = cycle_coverage(seen, kb)
        if not total or covered / total < copertura:
            skipped["poche operazioni confrontabili"] += 1
            continue
        if quanti and len(chosen) >= quanti:
            skipped["oltre il numero richiesto"] += 1
            continue
        chosen.append(name)
        lines.append(f"{name} vero: {covered} operazioni confrontabili su {total}")
    missing = [entry for entry in known.cicli if entry not in cycles]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(str(first[name]) for name in chosen) + "\n", encoding="utf-8")
    typer.echo(
        f"Stampe: {len(pdfs)} file, cicli letti {len(cycles)}, non letti {unread}. "
        f"Scelti {len(chosen)}: noti {len(noted)}, veri {len(chosen) - len(noted)}."
    )
    for line in lines:
        typer.echo(line)
    for reason, count in sorted(skipped.items()):
        typer.echo(f"lasciati fuori ({reason}): {count}")
    if missing:
        typer.echo(f"cicli di {attesi.name} non trovati: {', '.join(sorted(missing))}")
    typer.echo(f"Lista: {out}")


def _list_entries(lists: list[Path]) -> list[tuple[Path, Path | None]]:
    """Righe dei file `--lista`: `pdf`, oppure `pdf<TAB>ciclo.json` (copia con un errore
    cieco: si valida il ciclo del JSON, il PDF serve per la testata)."""
    entries: list[tuple[Path, Path | None]] = []
    for lista in lists:
        for line in lista.read_text(encoding="utf-8").splitlines():
            pdf, _, cycle = line.strip().partition("\t")
            if pdf:
                entries.append((Path(pdf), Path(cycle) if cycle else None))
    return entries


@eval_app.command("muta")
def eval_blind(
    lista: Annotated[Path, typer.Option(help="PDF dei cicli veri, uno per riga (eval scegli).")],
    knowledge: Annotated[Path, typer.Option(help="Versione della conoscenza (cartella).")],
    quanti: Annotated[int, typer.Option(help="Copie con un errore cieco.")] = 60,
    seme: Annotated[int, typer.Option(help="Seme: un seme nuovo dà errori nuovi.")] = 1,
    attesi: Annotated[Path, typer.Option(help="YAML degli errori noti.")] = Path(
        "eval/errori-noti.yaml"
    ),
    out: Annotated[Path, typer.Option(help="Cartella delle copie (resta sul PC).")] = Path(
        "runs/mutazioni"
    ),
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
) -> None:
    """Copie dei cicli veri con **un** errore messo dal programma (zero token): numero cambiato
    in una lingua, numero del manuale cambiato in tutte e due, negazione tolta in una lingua,
    codice di task che non esiste. Scrive in `--out` le copie (`<impronta>.json`), gli errori
    (`errori.yaml`, segnati come mai visti) e la lista per `eval prova` (`lista.txt`). Sullo
    schermo solo i conteggi per tipo: quali errori sono non si mostra."""
    try:
        settings = load_settings(config)
        limits = load_profile("mos", settings.paths.profiles_dir).file_limits
        known = load_known_errors(attesi)
        kb = load_local_knowledge(knowledge)
        entries = _list_entries([lista])
    except (CycleValidationError, OSError, ValueError) as error:
        raise _fail(error) from error
    cycles: list[tuple[str, Cycle]] = []
    pdf_of: dict[str, Path] = {}
    skipped = 0
    for pdf_path, _ in entries:
        try:
            data = pdf_path.read_bytes()
            name = hashlib.sha256(data).hexdigest()[:8]
            entry = known.cycle(name)
            if name in pdf_of or (entry is not None and not entry.giusto):
                continue  # doppione, o ciclo che ha già i suoi errori
            pdf = read_pdf_bytes(data, pdf_path.name, limits)
            if detect_module_kind(pdf.text, settings.module_check) == EJ200:
                skipped += 1
                continue
            cycles.append((name, parse_pvrm320(pdf)))
            pdf_of[name] = pdf_path
        except (CycleValidationError, OSError):
            skipped += 1
    mutations = blind_mutations(cycles, kb, count=quanti, seed=seme)
    out.mkdir(parents=True, exist_ok=True)
    errors: dict[str, Any] = {}
    lines: list[str] = []
    kinds: Counter[str] = Counter()
    for mutation in mutations:
        text = mutation.cycle.model_dump_json(indent=2)
        fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        path = out / f"{fingerprint}.json"
        path.write_text(text, encoding="utf-8")
        op = mutation.operation
        errors[fingerprint] = {
            "visto": False,
            "di": mutation.source,
            "errori": {op: f"[{mutation.kind}] {BLIND_DESCRIPTIONS[mutation.kind]}"},
        }
        lines.append(f"{pdf_of[mutation.source].resolve()}\t{path.resolve()}")
        kinds[mutation.kind] += 1
    (out / "errori.yaml").write_text(
        "# Errori ciechi (eval muta): non guardarli, servono a misurare la generalizzazione.\n"
        + yaml.safe_dump({"seme": seme, "cicli": errors}, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )
    (out / "lista.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    typer.echo(
        f"Cicli veri letti: {len(cycles)} (non letti o EJ200: {skipped}). Copie con un errore "
        f"cieco: {len(mutations)} su {quanti} chieste, seme {seme}."
    )
    for kind in BLIND_KINDS:
        typer.echo(f"  {kind}: {kinds.get(kind, 0)}")
    typer.echo(f"Lista: {out / 'lista.txt'} · errori: {out / 'errori.yaml'}")


@eval_app.command("prova")
def eval_trial(
    pdfs: Annotated[
        list[Path] | None, typer.Argument(help="PDF dei cicli (oppure --lista).")
    ] = None,
    knowledge: Annotated[Path | None, typer.Option(help="Cartella della knowledge base.")] = None,
    nome: Annotated[
        str | None, typer.Option(help="Nome della prova. Vuoto = nome della variante.")
    ] = None,
    variante: Annotated[
        Path | None, typer.Option(help="Variante (eval/varianti/...yaml) sopra --config.")
    ] = None,
    lista: Annotated[
        list[Path] | None,
        typer.Option(help="File con i PDF, uno per riga (eval scegli, eval muta). Ripetibile."),
    ] = None,
    attesi: Annotated[
        list[Path] | None,
        typer.Option(help="YAML degli errori noti (ripetibile). Vuoto = eval/errori-noti.yaml."),
    ] = None,
    config: Annotated[Path | None, typer.Option(help="settings.yaml.")] = None,
    profile: Annotated[str, typer.Option(help="mos | dr | ej200")] = "mos",
    cartella: Annotated[Path, typer.Option(help="Cartella delle prove.")] = Path("runs/prove"),
) -> None:
    """Valida i cicli, li confronta con gli errori noti e scrive il report della prova
    (`prestazioni.md`) e il riepilogo di tutte le prove (`riepilogo.md`). Con `--variante` le
    impostazioni sono quelle di `--config` più le modifiche della variante."""
    try:
        if knowledge is None:
            raise CycleValidationError("Manca --knowledge.")
        if variante is not None:
            loaded = load_variant(variante, config_override=config)
            settings = loaded.settings
            nome = nome or loaded.name
        else:
            settings = load_settings(config)
        if not nome:
            raise CycleValidationError("Manca --nome (o --variante).")
        known = load_known_errors(attesi or [Path("eval/errori-noti.yaml")])
        entries: list[tuple[Path, Path | None]] = []
        for path in pdfs or []:
            entries += [(pdf, None) for pdf in (_pdfs_in(path) if path.is_dir() else [path])]
        entries += _list_entries(lista or [])
        if not entries:
            raise CycleValidationError("Nessun PDF: dai i PDF o --lista.")
    except (CycleValidationError, OSError, ValueError) as error:
        raise _fail(error) from error
    started = datetime.now()
    safe = re.sub(r"[^\w.-]+", "-", nome).strip("-") or "prova"
    folder = cartella / f"{started:%Y%m%d-%H%M}-{safe}"
    reports: list[Report] = []
    scores: list[CycleScore] = []
    seen: set[str] = set()
    for pdf, cycle_file in entries:
        if not pdf.is_file() or (cycle_file is not None and not cycle_file.is_file()):
            typer.echo(f"File non trovato: {(cycle_file or pdf).name}")
            continue
        source = cycle_file if cycle_file is not None else pdf
        fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()[:8]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        out = folder / fingerprint
        extractor = FileCycleExtractor(cycle_file) if cycle_file is not None else None
        try:
            deps = build_dependencies(
                settings,
                profile,
                kb_dir=knowledge,
                machines_file=None,
                extractor=extractor,
                out_dir=out,
            )
            report = run_validation(RunRequest(pdf_path=pdf), deps, out)
        except CycleValidationError as error:
            scores.append(failed_cycle(fingerprint, known, str(error)))
            typer.echo(f"{fingerprint} non eseguito")
            continue
        reports.append(report)
        score = score_cycle(report, known, fingerprint)
        scores.append(score)
        if score.kind == "errori" and not score.seen:
            # mai visto: solo l'esito, non dove sta l'errore
            typer.echo(f"{fingerprint} mai visto: {'trovato' if score.found else 'mancato'}")
            continue
        typer.echo(
            f"{fingerprint} {score.kind}: trovati {', '.join(f.op for f in score.found) or '-'}"
            f" · mancati {', '.join(m.op for m in score.missed) or '-'}"
            f" · ERRATO in più {', '.join(f.op for f in score.extra) or '-'}"
        )
    trial = build_trial(nome, started, reports, scores)
    write_trial(trial, folder)
    summary = write_summary(cartella)
    typer.echo(
        f"Prova «{nome}»: errori noti trovati {trial.known_found} su {trial.known_total} "
        f"(visti {trial.seen_found} su {trial.seen_total}, mai visti {trial.unseen_found} su "
        f"{trial.unseen_total}) · falsi errori nei cicli giusti {trial.false_errors} · ERRATO in più "
        f"{trial.extra_errors} · costo {trial.cost_usd:.2f} $"
    )
    typer.echo(f"Report della prova: {folder / TRIAL_REPORT}")
    typer.echo(f"Riepilogo di tutte le prove: {summary}")


@eval_app.command("riepilogo")
def eval_trials_summary(
    cartella: Annotated[Path, typer.Option(help="Cartella delle prove.")] = Path("runs/prove"),
) -> None:
    """Riscrive `riepilogo.md` con tutte le prove della cartella e stampa la tabella."""
    trials = load_trials(cartella)
    summary = write_summary(cartella)
    for trial in trials:
        typer.echo(
            f"{trial.started_at:%d-%m %H:%M} {trial.name}: {trial.known_found} su "
            f"{trial.known_total} · falsi {trial.false_errors} · in più {trial.extra_errors} · "
            f"{trial.cost_usd:.2f} $"
        )
    typer.echo(f"Riepilogo: {summary}")


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


def _aws_client(service: str, region: str | None) -> Any:
    """Punto di sostituzione per i test."""
    import boto3

    return boto3.client(service, region_name=region)


def _aws_error(error: Exception) -> str:
    """Solo il codice dell'errore AWS: il messaggio può contenere ARN e numero di account."""
    response = getattr(error, "response", None)
    code = response.get("Error", {}).get("Code") if isinstance(response, dict) else None
    return code or type(error).__name__


def _field_names(values: dict[str, Any]) -> str:
    return ", ".join(sorted(key for key in values if not key.startswith("__"))) or "nessuno"


def _redshift_connector() -> Any:
    try:
        import redshift_connector  # type: ignore[import-not-found]
    except ImportError as error:
        raise CycleValidationError(
            "Per --diretto serve redshift_connector: lancia il comando con "
            "`uv run --with redshift_connector cycle-validation macchine ...`."
        ) from error
    return redshift_connector


def _direct_fetch(values: dict[str, Any], database: str | None, query: str) -> list[str]:
    """Come la v1 (`RedshiftConnector`): host, porta, utente e password dal secret."""
    from cycle_validation.services.redshift import fetch_active_machines, secret_connection

    if not database:
        raise CycleValidationError("Manca il nome del database: indicalo con --database.")
    return fetch_active_machines(
        secret_connection(lambda: values, _redshift_connector(), database), query
    )


_MASKED = ("CV_ENV_SECRET", "REDSHIFT_DATABASE", "MACHINES_QUERY")


@app.command("qa")
def prepare_qa(
    conoscenza_civile: Annotated[
        str | None, typer.Option(help="current.json della conoscenza civile su S3.")
    ] = None,
    v1: Annotated[Path, typer.Option(help="Cartella della v1.")] = Path("../app_cycle_validation"),
    impostazioni: Annotated[
        Path, typer.Option(help="Impostazioni provate in locale (copiate nell'immagine).")
    ] = Path("data/settings.yaml"),
    ej200: Annotated[bool, typer.Option(help="Cicli militari accesi nel servizio.")] = False,
    conoscenza_ej200: Annotated[
        str | None, typer.Option(help="current.json della conoscenza EJ200 su S3 (con --ej200).")
    ] = None,
    buildspec: Annotated[Path, typer.Option(help="buildspec.yml del repository aziendale.")] = Path(
        "../buildspec.yml"
    ),
    torna_alla_v1: Annotated[
        bool, typer.Option(help="Rimette nel buildspec la cartella della v1 e basta.")
    ] = False,
) -> None:
    """Prepara la v2 per QA sul PC aziendale: Dockerfile dalla v1 con i valori aziendali,
    libreria di accesso in vendor/, impostazioni nell'immagine, buildspec sulla v2."""
    import shutil

    from cycle_validation.deploy import (
        SETTINGS_FILE,
        V1_FOLDER,
        read_v1_image,
        read_v1_wheel,
        render_dockerfile,
        service_settings,
        switch_buildspec,
    )
    from cycle_validation.deploy import mentions as lines_with
    from cycle_validation.services.redshift import find_in_v1, machines_query

    try:
        if not buildspec.is_file():
            raise CycleValidationError(f"buildspec non trovato: {buildspec}")
        spec = buildspec.read_text(encoding="utf-8")
        if torna_alla_v1:
            back, count = switch_buildspec(spec, to_v2=False)
            if count:
                buildspec.write_text(back, encoding="utf-8")
            typer.echo(f"buildspec: percorsi rimessi sulla v1: {count}.")
            for line in lines_with(back, V1_FOLDER):
                typer.echo(f"  {line}")
            return
        if not conoscenza_civile:
            raise CycleValidationError("Manca --conoscenza-civile (current.json su S3).")
        if ej200 and not conoscenza_ej200:
            raise CycleValidationError("Con --ej200 serve anche --conoscenza-ej200.")
        image = read_v1_image((v1 / "Dockerfile").read_text(encoding="utf-8"))
        requirements = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(v1.glob("requirements*.txt"))
        )
        wheel, extras = read_v1_wheel(requirements)
        found = find_in_v1(v1)
        missing = [
            name
            for name, value in (
                ("secret di ambiente", found.env_secret),
                ("database", found.database),
                ("tabella delle macchine", found.table),
            )
            if not value
        ]
        if missing:
            raise CycleValidationError("Nel codice della v1 non trovo: " + ", ".join(missing) + ".")
        settings_text = service_settings(impostazioni.read_text(encoding="utf-8"))
        Path(SETTINGS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(SETTINGS_FILE).write_text(settings_text, encoding="utf-8")
        settings = load_settings(Path(SETTINGS_FILE))
        env = {
            "CV_ENV_SECRET": str(found.env_secret),
            "MACHINES_SOURCE": "diretta",
            "REDSHIFT_DATABASE": str(found.database),
            "MACHINES_QUERY": machines_query(str(found.table)),
            "CYCLE_VALIDATION_CONFIG": SETTINGS_FILE,
            "CIVIL_KNOWLEDGE_POINTER": conoscenza_civile,
            "EJ200_VALIDATION_ENABLED": "true" if ej200 else "false",
            **({"EJ200_KNOWLEDGE_POINTER": conoscenza_ej200} if conoscenza_ej200 else {}),
            "API_INCLUDE_TRACEBACK": "false",
        }
        dockerfile = render_dockerfile(image, wheel, extras, env)
        source = v1 / "vendor" / wheel
        if not source.is_file():
            raise CycleValidationError(f"Il .whl dei requirements non è in {v1 / 'vendor'}.")
        switched, count = switch_buildspec(spec)
        if not count and f"cd {V1_FOLDER}_v2" not in spec:
            raise CycleValidationError("Nel buildspec non trovo `cd app_cycle_validation`.")
    except (CycleValidationError, OSError) as error:
        raise _fail(error) from error
    Path("vendor").mkdir(exist_ok=True)
    shutil.copyfile(source, Path("vendor") / wheel)
    Path("Dockerfile").write_text(dockerfile, encoding="utf-8")
    if count:
        buildspec.write_text(switched, encoding="utf-8")
    typer.echo(
        f"Dalla v1: base e {len(image.certificates)} istruzioni sui certificati; libreria "
        f"{wheel}{extras} copiata in vendor; secret di ambiente, database e tabella trovati."
    )
    typer.echo(
        f"Impostazioni: {impostazioni} -> {SETTINGS_FILE} (modello {settings.agent.model}, "
        "testi delle sessioni su disco spenti)."
    )
    typer.echo(f"buildspec: percorsi spostati sulla v2: {count}.")
    for line in lines_with(switched, V1_FOLDER) + lines_with(switched, "ca-certificates"):
        typer.echo(f"  {line}")
    typer.echo("Dockerfile scritto (valori aziendali coperti):")
    shown = dockerfile
    for name in _MASKED:
        shown = re.sub(rf'({name}=)"(?:[^"\\]|\\.)*"', r'\1"…"', shown)
    for line in shown.splitlines():
        typer.echo(f"  {line}")


@app.command("macchine")
def export_machines(
    v1: Annotated[
        Path | None,
        typer.Option(help="Cartella della v1: da lì si prendono nome del secret e tabella."),
    ] = None,
    secret: Annotated[str | None, typer.Option(help="Nome o ARN del secret di Redshift.")] = None,
    tabella: Annotated[str | None, typer.Option(help="Tabella delle macchine.")] = None,
    regione: Annotated[
        str | None, typer.Option(help="Regione del secret. Vuoto = ambiente.")
    ] = None,
    database: Annotated[
        str | None, typer.Option(help="Database di Redshift. Vuoto = dalla v1 o dal secret.")
    ] = None,
    diretto: Annotated[
        bool,
        typer.Option(
            help="Connessione diretta come la v1 (redshift_connector, porta del secret) invece "
            "della Data API."
        ),
    ] = False,
    out: Annotated[Path, typer.Option(help="File da scrivere.")] = Path(
        "data/macchine_attive.json"
    ),
) -> None:
    """Scarica da Redshift l'elenco delle macchine attive (come la v1: `work_center_usage_cd =
    'TO'`) e lo scrive in un file JSON da passare a `run --machines`. Stampa solo il numero di
    macchine: niente nomi, host o valori del secret."""
    from cycle_validation.services.redshift import (
        cluster_database,
        data_api_target,
        fetch_with_data_api,
        find_in_v1,
        host_region,
        machines_query,
        secret_database,
    )

    found = find_in_v1(v1) if v1 is not None else None
    if found is not None:
        typer.echo(
            f"Dalla v1: nome del secret {'trovato' if found.secret else 'NON trovato'} nel "
            f"codice, secret di ambiente {'trovato' if found.env_secret else 'NON trovato'}, "
            f"tabella {'trovata' if found.table else 'NON trovata'}, database "
            + (
                f"letto dalla chiave {found.database_key} con {found.database_read}"
                if found.database_key
                else "scritto nel codice"
                if found.database
                else "NON trovato"
            )
            + "."
        )
    secrets = _aws_client("secretsmanager", regione)

    def read(name: str, what: str) -> dict[str, Any]:
        try:
            reply = secrets.get_secret_value(SecretId=name)
            values = json.loads(reply["SecretString"])
        except Exception as error:  # qualunque errore AWS diventa un messaggio corto
            raise _fail(CycleValidationError(f"{what} non letto: {_aws_error(error)}.")) from error
        if not isinstance(values, dict):
            raise _fail(CycleValidationError(f"{what}: non è un elenco di campi."))
        values["__arn__"] = reply.get("ARN", name)
        return values

    environment: dict[str, Any] = {}
    if (
        found is not None
        and found.env_secret
        and not (secret and (database or (found.database and not found.database_key)))
    ):
        # come la v1: SECRET_NAME (e a volte il database) stanno nel secret di ambiente
        environment = read(found.env_secret, "Secret di ambiente della v1")
    secret = secret or (found.secret if found else None)
    if not secret and environment:
        secret = str(environment.get("SECRET_NAME") or "") or None
        typer.echo(
            "Nel secret di ambiente: SECRET_NAME "
            + ("trovato." if secret else "NON trovato. Campi: " + _field_names(environment))
        )
    tabella = tabella or (found.table if found else None)
    if not secret or not tabella:
        raise _fail(CycleValidationError("Servono il nome del secret e la tabella delle macchine."))
    values = read(secret, "Secret di Redshift")
    arn = str(values.pop("__arn__"))
    if not database and found is not None:
        key = found.database_key
        from_key = (
            str(values.get(key) or environment.get(key) or os.environ.get(key) or "") or None
            if key
            else None
        )
        database = from_key or found.database
        if key:
            typer.echo(
                f"Chiave {key} del database: "
                + ("trovata." if from_key else "NON trovata nei due secret né nell'ambiente.")
                + (
                    " Uso il valore predefinito scritto nel codice."
                    if not from_key and database
                    else ""
                )
            )
    database = database or secret_database(values)
    host = str(values.get("host") or "")
    cluster = values.get("dbClusterIdentifier") or (
        host.split(".")[0] if host and "redshift-serverless" not in host else None
    )
    if not database and cluster:
        # la v1 non trova il database nei secret: si usa quello creato con il cluster
        try:
            client = _aws_client("redshift", host_region(host) or regione)
            database = cluster_database(client, str(cluster))
        except Exception as error:
            typer.echo(f"Database del cluster non letto: {_aws_error(error)}.")
        else:
            typer.echo("Database del cluster: " + ("trovato." if database else "NON trovato."))
    try:
        if diretto:
            kind = "connessione diretta"
            tags = sorted(set(_direct_fetch(values, database, machines_query(tabella))))
        else:
            region, parameters = data_api_target(values, arn, database)
            client = _aws_client("redshift-data", region or regione)
            tags = sorted(set(fetch_with_data_api(client, parameters, machines_query(tabella))))
            kind = "serverless" if "WorkgroupName" in parameters else "cluster"
    except CycleValidationError as error:
        raise _fail(error) from error
    except Exception as error:
        raise _fail(CycleValidationError(f"Redshift non letto: {_aws_error(error)}.")) from error
    if not tags:
        raise _fail(CycleValidationError("La query non ha restituito nessuna macchina attiva."))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tags, indent=0), encoding="utf-8")
    typer.echo(f"Macchine attive: {len(tags)} (Redshift {kind}). Scritte in {out}.")


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
