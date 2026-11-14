"""Esecuzione di una variante sui casi: un file JSON di risultati grezzi per ogni prova.

Una suite è una cartella con `suite.yaml` (conoscenza e macchine) e un caso per sottocartella,
nel formato del golden set (`ciclo.json`, `expected.json`, `ciclo.pdf` facoltativo). Le misure
si calcolano dopo, dai file grezzi (`evaluation.metrics`), così si rifanno senza rilanciare.
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
from cycle_validation.domain.report import Report
from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.variant import Variant
from cycle_validation.extract.from_file import FileCycleExtractor
from cycle_validation.golden import GoldenCase, case_request, load_cases
from cycle_validation.kb.ej200 import Ej200Catalog, Ej200KnowledgeBase
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.port import KnowledgeBase
from cycle_validation.kb.stores import LocalDirObjectStore
from cycle_validation.kb.structured import StructuredLayout
from cycle_validation.pipeline import Dependencies, arun_validation
from cycle_validation.services.machines import load_machine_registry

FORMAT = 1
SessionFactory = Callable[[AgentSettings, Path | None], AgentSession]


class SuiteConfig(BaseModel):
    """Percorsi relativi alla cartella della suite."""

    model_config = ConfigDict(extra="forbid")

    conoscenza: Path
    tipo_conoscenza: Literal["locale", "ej200"] = "locale"
    macchine: Path | None = None
    versione: str | None = None


@dataclass(frozen=True)
class Suite:
    name: str
    directory: Path
    config: SuiteConfig
    cases: list[GoldenCase]

    def path(self, value: Path) -> Path:
        return value if value.is_absolute() else self.directory / value

    def knowledge(self, workdir: Path) -> KnowledgeBase:
        folder = self.path(self.config.conoscenza)
        if self.config.tipo_conoscenza == "locale":
            return load_local_knowledge(folder)
        store = LocalDirObjectStore(folder)
        return Ej200KnowledgeBase(
            self.config.versione or f"{self.name}-locale",
            Ej200Catalog(store),
            workdir,
            store,
            StructuredLayout(sp=None, dr=None),
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
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=10, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


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


def _record(
    suite: Suite,
    case: GoldenCase,
    repetition: int,
    report: Report | None,
    failure: str | None,
    elapsed_ms: int,
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
    """Esegue ogni caso `repetitions` volte, uno dopo l'altro, e scrive il file dei risultati."""
    if repetitions < 1:
        raise ConfigError("Serve almeno una ripetizione.")
    settings = variant.settings
    prompts_dir = _resolve(project_root, settings.paths.prompts_dir)
    profiles_dir = _resolve(project_root, settings.paths.profiles_dir)
    system_prompt = load_prompt(prompts_dir, OPERATION_PROMPT_FILE)
    version = prompt_version(system_prompt, "")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}_{variant.name}"
    records: list[dict[str, Any]] = []
    total = repetitions * sum(len(suite.cases) for suite in suites)
    for repetition in range(1, repetitions + 1):
        for suite in suites:
            for case in suite.cases:
                work = runs_dir / "eval" / run_id / f"{suite.name}-{case.name}-r{repetition}"
                report: Report | None = None
                failure: str | None = None
                began = time.perf_counter()
                try:
                    deps = Dependencies(
                        settings=settings,
                        profile=load_profile(case.expected.profile, profiles_dir),
                        kb=suite.knowledge(work / "work"),
                        machines=load_machine_registry(
                            suite.path(suite.config.macchine) if suite.config.macchine else None
                        ),
                        extractor=FileCycleExtractor(case.cycle_path),
                        session=session_factory(settings.agent, work / "transcripts"),
                        system_prompt=system_prompt,
                        prompt_version=version,
                    )
                    report = await arun_validation(case_request(case), deps)
                except Exception as error:  # un caso rotto non ferma la prova
                    failure = _describe(error)
                elapsed = int((time.perf_counter() - began) * 1000)
                record = _record(suite, case, repetition, report, failure, elapsed)
                records.append(record)
                if progress is not None:
                    progress(_progress_line(len(records), total, record))
    commit = _git(project_root, "rev-parse", "--short", "HEAD")
    dirty = _git(project_root, "status", "--porcelain")
    data = {
        "formato": FORMAT,
        "variante": variant.name,
        "descrizione": variant.description,
        "catena": variant.chain,
        "sessione": variant.session,
        "file_variante": variant.path.as_posix(),
        "ambiente": environment or environment_of(settings),
        "commit": commit or "sconosciuto",
        "working_tree_pulita": dirty == "" if dirty is not None else None,
        "data": datetime.now().isoformat(timespec="seconds"),
        "ripetizioni": repetitions,
        "casi": cases_label,
        "impostazioni": settings.model_dump(mode="json"),
        "prompt_version": version,
        "tool_version": __version__,
        "esecuzioni": records,
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{run_id}.json"
    counter = 1
    while path.exists():
        counter += 1
        path = results_dir / f"{run_id}-{counter}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
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
