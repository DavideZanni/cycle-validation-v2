"""Esecuzione di una variante sui casi: un file JSON di risultati grezzi per ogni prova.

Una suite è una cartella con `suite.yaml` (conoscenza, macchine, modo di estrazione) e un caso
per sottocartella, nel formato del golden set. Le misure si calcolano dopo, dai file grezzi
(`evaluation.metrics`), così si rifanno senza rilanciare.
"""

import json
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from cycle_validation import __version__
from cycle_validation.agent.prompt import OPERATION_PROMPT_FILE, load_prompt, prompt_version
from cycle_validation.agent.session import AgentSession
from cycle_validation.config import AgentSettings, Settings, load_profile
from cycle_validation.domain.check import Reason
from cycle_validation.domain.cycle import Cycle
from cycle_validation.domain.report import Report
from cycle_validation.errors import ConfigError, CycleValidationError
from cycle_validation.evaluation.faults import FaultyKnowledge, FaultySession
from cycle_validation.evaluation.snapshot import snapshot_version
from cycle_validation.evaluation.variant import Variant
from cycle_validation.extract.base import CycleExtractor
from cycle_validation.extract.factory import make_pdf_extractor
from cycle_validation.extract.from_file import FileCycleExtractor
from cycle_validation.golden import GoldenCase, case_request, load_cases
from cycle_validation.ingest.transcribe import make_transcriber
from cycle_validation.kb.ej200 import (
    DEFAULT_CATALOG_KEY,
    DEFAULT_TEXT_PREFIX,
    Ej200Catalog,
    Ej200KnowledgeBase,
)
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.port import KnowledgeBase
from cycle_validation.kb.published import PublishedKnowledgeBase
from cycle_validation.kb.remote import RemoteKnowledgeBase
from cycle_validation.kb.snapshot import SnapshotManualSource
from cycle_validation.kb.stores import LocalDirObjectStore
from cycle_validation.kb.structured import StructuredLayout
from cycle_validation.pipeline import Dependencies, arun_validation
from cycle_validation.services.machines import MachineRegistry, load_machine_registry
from cycle_validation.text import normalize_code

FORMAT = 1
SessionFactory = Callable[[AgentSettings, Path | None], AgentSession]


class SuiteConfig(BaseModel):
    """Percorsi relativi alla cartella della suite."""

    model_config = ConfigDict(extra="forbid")

    conoscenza: Path
    # locale = cartella nel formato di examples/sintetico/knowledge;
    # fotografia = copia delle chiavi S3 (manuali dell'ingestion + dati TM/SP/DR), letta con il
    # codice di produzione; ej200 = copia delle chiavi S3 delle pubblicazioni EJ200.
    tipo_conoscenza: Literal["locale", "fotografia", "ej200"] = "locale"
    macchine: Path | None = None
    versione: str | None = None
    # ciclo_json = il ciclo si legge da ciclo.json (si provano solo i controlli);
    # dal_pdf = si estrae da ciclo.pdf come in produzione (si prova anche l'estrazione).
    estrazione: Literal["ciclo_json", "dal_pdf"] = "ciclo_json"
    profilo: str | None = None
    # fotografia: prefisso dei manuali e dei tre insiemi di dati (null = non usato).
    manuali: str = ""
    targhe: str | None = "structured/TM/"
    schede: str | None = "structured/SP/"
    dr: str | None = "structured/DR/"
    # ej200: chiavi del catalogo e dei testi.
    catalogo: str = DEFAULT_CATALOG_KEY
    testi: str = DEFAULT_TEXT_PREFIX
    # Chiave di `current.json` pubblicato da knowledge-index. Con fotografia la conoscenza
    # civile intera (manuali, task, TM, SP, DR) viene dalla versione indicata e `manuali`,
    # `targhe`, `schede`, `dr` non servono; con ej200 il catalogo e i testi vengono da lì.
    puntatore: str | None = None
    # ej200: `current.json` della conoscenza civile, da cui leggere le targhe come nel
    # servizio. Senza, le targhe vengono dal prefisso `targhe` della fotografia.
    puntatore_civile: str | None = None


@dataclass(frozen=True)
class Suite:
    name: str
    directory: Path
    config: SuiteConfig
    cases: list[GoldenCase]

    def path(self, value: Path) -> Path:
        return value if value.is_absolute() else self.directory / value

    def knowledge(self, workdir: Path) -> KnowledgeBase:
        """Carica e controlla la conoscenza. Un difetto ferma la prova prima del modello."""
        folder = self.path(self.config.conoscenza)
        version = self.config.versione or snapshot_version(folder) or folder.name
        cfg = self.config
        try:
            if cfg.tipo_conoscenza == "locale":
                return load_local_knowledge(folder)
            if not folder.is_dir():
                raise ConfigError(f"cartella non trovata: {folder}")
            store = LocalDirObjectStore(folder)
            kb: Ej200KnowledgeBase | RemoteKnowledgeBase | PublishedKnowledgeBase
            if cfg.tipo_conoscenza == "ej200":
                civil = (
                    PublishedKnowledgeBase(store, cfg.puntatore_civile, workdir / "civile")
                    if cfg.puntatore_civile
                    else None
                )
                kb = Ej200KnowledgeBase(
                    version,
                    Ej200Catalog(store, cfg.catalogo, pointer_key=cfg.puntatore),
                    workdir / "ej200",
                    store,
                    StructuredLayout(tm=cfg.targhe, sp=None, dr=None),
                    text_prefix=cfg.testi,
                    tags=civil.machine_tags if civil else None,
                )
            elif cfg.puntatore:
                kb = PublishedKnowledgeBase(store, cfg.puntatore, workdir / "pubblicata")
            else:
                kb = RemoteKnowledgeBase(
                    version,
                    store,
                    SnapshotManualSource(store, cfg.manuali, workdir / "manuali"),
                    StructuredLayout(tm=cfg.targhe, sp=cfg.schede, dr=cfg.dr),
                )
            kb.preload()
            return kb
        except CycleValidationError as exc:
            raise ConfigError(f"Suite {self.name}: conoscenza non leggibile ({exc})") from exc

    def machines(self) -> MachineRegistry:
        return load_machine_registry(
            self.path(self.config.macchine) if self.config.macchine else None
        )


def _suite(directory: Path) -> Suite:
    path = directory / "suite.yaml"
    try:
        config = SuiteConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"{path}: suite non valida ({exc})") from exc
    return Suite(directory.name, directory, config, load_cases(directory))


def load_suites(path: Path) -> list[Suite]:
    """Una suite (cartella con `suite.yaml`) oppure una cartella che ne contiene più d'una."""
    if (path / "suite.yaml").is_file():
        return [_suite(path)]
    if not path.is_dir():
        raise ConfigError(f"Cartella dei casi non trovata: {path}")
    suites = [_suite(p) for p in sorted(path.iterdir()) if (p / "suite.yaml").is_file()]
    if not suites:
        raise ConfigError(f"Nessuna suite (cartella con suite.yaml) in {path}.")
    return suites


def environment_of(settings: Settings) -> str:
    agent = settings.agent
    if not agent.use_bedrock:
        return "login-locale"
    return f"bedrock-{agent.aws_region or 'regione-ambiente'}"


def _git(root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


@dataclass(frozen=True)
class Prompts:
    system: str
    prompts_dir: Path
    profiles_dir: Path


def load_prompts(variant: Variant, project_root: Path) -> Prompts:
    paths = variant.settings.paths
    prompts_dir = _resolve(project_root, paths.prompts_dir)
    return Prompts(
        load_prompt(prompts_dir, OPERATION_PROMPT_FILE),
        prompts_dir,
        _resolve(project_root, paths.profiles_dir),
    )


def case_dependencies(
    variant: Variant,
    suite: Suite,
    case: GoldenCase,
    kb: KnowledgeBase,
    session: AgentSession,
    prompts: Prompts,
    *,
    from_pdf: bool,
) -> Dependencies:
    """Le dipendenze della pipeline per un caso. `from_pdf`: il ciclo si estrae da ciclo.pdf."""
    settings = variant.settings
    profile = load_profile(case.expected.profile, prompts.profiles_dir)
    extractor: CycleExtractor
    extraction_prompt = ""
    if from_pdf:
        if case.pdf_path is None:
            raise ConfigError(f"{case.directory}: manca ciclo.pdf (estrazione: dal_pdf).")
        extractor, extraction_prompt = make_pdf_extractor(
            profile, settings.agent, session, prompts.prompts_dir
        )
    else:
        if case.cycle_json is None:
            raise ConfigError(f"{case.directory}: manca ciclo.json (estrazione: ciclo_json).")
        extractor = FileCycleExtractor(case.cycle_path)
    return Dependencies(
        settings=settings,
        profile=profile,
        kb=kb,
        machines=suite.machines(),
        extractor=extractor,
        session=session,
        system_prompt=prompts.system,
        prompt_version=prompt_version(prompts.system, extraction_prompt),
        transcriber=make_transcriber(settings.agent) if from_pdf else None,
    )


def _row(result: Any) -> dict[str, Any]:
    return {
        "check": result.check.value,
        "kind": result.target.kind.value,
        "index": result.target.index,
        "verdict": result.verdict.value,
        "reason": result.reason.value,
        "decided_by": result.decided_by,
        "prova": bool(result.evidence),
    }


def _codes(values: Sequence[str]) -> list[str]:
    return sorted(normalize_code(value) for value in values)


def compare_extraction(extracted: Cycle, reference: Cycle) -> dict[str, list[int]]:
    """Operazioni e fonti estratte uguali al riferimento, sui campi che i controlli usano.
    Le descrizioni non si confrontano: piccole differenze di trascrizione sono normali."""

    def operation(op: Any) -> tuple[Any, ...]:
        sheet = op.process_sheet.code if op.process_sheet else None
        return (
            normalize_code(op.operation_number),
            normalize_code(op.machine_tag or ""),
            tuple(_codes(op.task_codes)),
            normalize_code(sheet or ""),
        )

    def source(item: Any) -> tuple[str, str]:
        return (normalize_code(item.manual), normalize_code(item.task or ""))

    got_ops = {operation(op)[0]: operation(op) for op in extracted.operations}
    same_ops = sum(
        1 for op in reference.operations if got_ops.get(operation(op)[0]) == operation(op)
    )
    got_sources = {source(item) for item in extracted.sources}
    same_sources = sum(1 for item in reference.sources if source(item) in got_sources)
    return {
        "operazioni": [same_ops, len(reference.operations)],
        "fonti": [same_sources, len(reference.sources)],
    }


def _record(
    suite: Suite,
    case: GoldenCase,
    repetition: int,
    report: Report | None,
    failure: str | None,
    elapsed_ms: int,
    *,
    from_pdf: bool,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "suite": suite.name,
        "caso": case.name,
        "ripetizione": repetition,
        "profilo": case.expected.profile,
        "attesi": [row.model_dump(mode="json") for row in case.expected.rows],
        "stato_atteso": case.expected.status,
        "guasto": failure,
        "ottenuti": [],
        "stato": None,
        "tempi_ms": {"total": elapsed_ms},
        "consumi": {},
        "sessioni": {},
        "errori_pipeline": 0,
        "estrazione": None,
    }
    if report is not None:
        record.update(
            ottenuti=[_row(result) for result in report.results],
            stato=report.status.value,
            tempi_ms=report.timings_ms,
            consumi=report.usage.model_dump(),
            sessioni=report.session_modes,
            errori_pipeline=len(report.pipeline_errors),
        )
        if from_pdf and case.cycle_json is not None:
            reference = Cycle.model_validate_json(case.cycle_json.read_text(encoding="utf-8"))
            record["estrazione"] = compare_extraction(report.cycle, reference)
    return record


def _describe(error: Exception) -> str:
    """Tipo e messaggio, troncato: i messaggi del programma non portano testo dei documenti."""
    return f"{type(error).__name__}: {error}"[:300]


async def run_variant(
    variant: Variant,
    suites: Sequence[Suite],
    *,
    repetitions: int,
    results_dir: Path,
    session_factory: SessionFactory,
    project_root: Path,
    runs_dir: Path,
    environment: str | None = None,
    cases_label: str = "",
    progress: Callable[[str], None] | None = None,
) -> Path:
    """Esegue ogni caso `repetitions` volte, uno dopo l'altro, e scrive il file dei risultati.

    La conoscenza di ogni suite si carica una volta sola, prima di qualunque chiamata al
    modello: se non si legge, la prova si ferma subito e non si spende niente."""
    if repetitions < 1:
        raise ConfigError("Serve almeno una ripetizione.")
    say = progress or (lambda _: None)
    settings = variant.settings
    prompts = load_prompts(variant, project_root)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}_{variant.name}"
    base = runs_dir / "eval" / run_id
    knowledge = {suite.name: suite.knowledge(base / suite.name) for suite in suites}
    skipped = [f"{s.name}/{c.name}" for s in suites for c in s.cases if not c.expected.rivisto]
    for name in skipped:
        say(f'saltato {name}: esiti attesi da rivedere (expected.json ha "rivisto": false)')
    plan = [(s, c) for s in suites for c in s.cases if c.expected.rivisto]
    records: list[dict[str, Any]] = []
    total = repetitions * len(plan)
    for repetition in range(1, repetitions + 1):
        for suite, case in plan:
            work = base / f"{suite.name}-{case.name}-r{repetition}"
            from_pdf = suite.config.estrazione == "dal_pdf"
            report: Report | None = None
            failure: str | None = None
            began = time.perf_counter()
            try:
                session = session_factory(settings.agent, work / "transcripts")
                kb: KnowledgeBase = knowledge[suite.name]
                if variant.faults is not None:
                    session = FaultySession(session, variant.faults, repetition)
                    kb = FaultyKnowledge(kb, variant.faults, repetition)
                deps = case_dependencies(
                    variant,
                    suite,
                    case,
                    kb,
                    session,
                    prompts,
                    from_pdf=from_pdf,
                )
                report = await arun_validation(case_request(case), deps)
            except Exception as error:  # un caso rotto non ferma la prova
                failure = _describe(error)
            elapsed = int((time.perf_counter() - began) * 1000)
            record = _record(suite, case, repetition, report, failure, elapsed, from_pdf=from_pdf)
            records.append(record)
            say(_progress_line(len(records), total, record))
    commit = _git(project_root, "rev-parse", "--short", "HEAD")
    dirty = _git(project_root, "status", "--porcelain")
    data = {
        "formato": FORMAT,
        "variante": variant.name,
        "descrizione": variant.description,
        "ipotesi": variant.hypothesis,
        "atteso": variant.expected,
        "catena": variant.chain,
        "sessione": variant.session,
        "file_variante": variant.path.as_posix(),
        "ambiente": environment or environment_of(settings),
        "commit": commit or "sconosciuto",
        "working_tree_pulita": dirty == "" if dirty is not None else None,
        "data": datetime.now().isoformat(timespec="seconds"),
        "ripetizioni": repetitions,
        "casi": cases_label,
        "conoscenza": {name: kb.version for name, kb in knowledge.items()},
        "saltati": skipped,
        "guasti_simulati": variant.faults.model_dump() if variant.faults else None,
        "impostazioni": settings.model_dump(mode="json"),
        "prompt_version": prompt_version(prompts.system, ""),
        "tool_version": __version__,
        "esecuzioni": records,
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{run_id}.json"
    counter = 1
    while path.exists():
        counter += 1
        path = results_dir / f"{run_id}-{counter}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return path


_TECHNICAL = {
    Reason.ERRORE_TECNICO.value,
    Reason.BUDGET_ESAURITO.value,
    Reason.ESTRAZIONE_NON_CONFERMATA.value,
}


def _progress_line(done: int, total: int, record: dict[str, Any]) -> str:
    where = f"[{done}/{total}] rip. {record['ripetizione']} {record['suite']}/{record['caso']}"
    seconds = record["tempi_ms"].get("total", 0) / 1000
    if record["guasto"]:
        return f"{where}: GUASTO {record['guasto']}"
    technical = sum(1 for row in record["ottenuti"] if row["reason"] in _TECHNICAL)
    note = f", {technical} esiti tecnici" if technical else ""
    return f"{where}: {seconds:.1f} s{note}"
