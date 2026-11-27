"""Montaggio di produzione: dall'ambiente ai servizi, senza codice da scrivere in azienda.

Oltre alle variabili di `api/settings.py` servono solo queste:

| Variabile | Se manca | Cosa fa |
|---|---|---|
| `MACHINES_SOURCE` | dedotta | `diretta`, `data_api`, `file` o `nessuna` (sotto) |
| `MACHINES_FILE` | — | JSON delle macchine attive (lista di targhe o `{"active": [...]}`) |
| `REDSHIFT_DATABASE` | — | il database di Redshift (con `diretta` e `data_api`) |
| `REDSHIFT_SECRET_NAME` | `SECRET_NAME` | con `diretta`: il secret di Redshift della v1 |
| `REDSHIFT_WORKGROUP` | — | Redshift Serverless; oppure `REDSHIFT_CLUSTER_ID` per un cluster |
| `REDSHIFT_DB_USER`, `REDSHIFT_SECRET_ARN` | — | per un cluster: utente (credenziali IAM) o secret |
| `MACHINES_QUERY` | query standard | la query, prima colonna = targa |
| `MACHINES_TTL_S` | 900 | ogni quanti secondi si rilegge l'elenco da Redshift |
| `CYCLE_VALIDATION_CONFIG` | `config/settings.yaml` | il file delle impostazioni |
| `KNOWLEDGE_WORKDIR` | cartella temporanea | dove si scarica la conoscenza pubblicata |
| `CLOUDWATCH_METRICS` | attivo | costo di ogni validazione su CloudWatch |

Una sola sorgente delle macchine, obbligatoria: senza, ogni targa uscirebbe WARNING.

- `diretta`: come la v1. Connessione a Redshift con `redshift_connector` e host, porta, utente
  e password del secret (lo stesso `SECRET_NAME` della v1). Va bene dove gira la v1 (su AWS):
  dal PC Redshift non si raggiunge.
- `data_api`: Redshift Data API (HTTPS), con `REDSHIFT_WORKGROUP` o `REDSHIFT_CLUSTER_ID`.
- `file`: `MACHINES_FILE`.
- `nessuna`: solo per le prove in locale. Ogni targa esce WARNING «non verificabile».

Senza `MACHINES_SOURCE` vale `file` se c'è `MACHINES_FILE`, altrimenti `data_api` se c'è
`REDSHIFT_DATABASE`.
"""

import json
import tempfile
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cycle_validation.agent.prompt import OPERATION_PROMPT_FILE, load_prompt, prompt_version
from cycle_validation.agent.sdk_session import SdkAgentSession
from cycle_validation.agent.session import AgentSession
from cycle_validation.api.app import ApiServices, NullMetrics
from cycle_validation.api.aws import CloudWatchMetrics
from cycle_validation.api.runner import PipelineRunner
from cycle_validation.api.settings import AppConfig
from cycle_validation.config import AgentSettings, Settings, load_profile, load_settings
from cycle_validation.errors import ConfigError
from cycle_validation.extract.factory import make_pdf_extractor
from cycle_validation.ingest.transcribe import make_transcriber
from cycle_validation.kb.ej200 import Ej200Catalog, Ej200KnowledgeBase
from cycle_validation.kb.port import KnowledgeBase
from cycle_validation.kb.published import PublishedKnowledgeBase
from cycle_validation.kb.stores import WritableObjectStore
from cycle_validation.pipeline import Dependencies
from cycle_validation.services.machines import (
    MachineRegistry,
    UnavailableMachineRegistry,
    load_machine_registry,
)
from cycle_validation.services.redshift import (
    DEFAULT_QUERY,
    DEFAULT_TTL_S,
    data_api_registry,
    redshift_machine_registry,
    secret_connection,
)

SessionFactory = Callable[[AgentSettings, Path | None], AgentSession]
_TRUE = {"1", "true", "yes", "on", "si", "sì"}
_FALSE = {"0", "false", "no", "off"}
SOURCES = ("diretta", "data_api", "file", "nessuna")
NO_MACHINES = (
    "Registro delle macchine attive non collegato (MACHINES_SOURCE=nessuna, solo per le prove "
    "in locale): stato non verificabile."
)


@dataclass(frozen=True)
class RedshiftTarget:
    database: str
    workgroup: str | None = None
    cluster: str | None = None
    db_user: str | None = None
    secret_arn: str | None = None
    query: str = DEFAULT_QUERY
    ttl_s: float = DEFAULT_TTL_S

    def parameters(self) -> dict[str, str]:
        """I parametri di `execute_statement`, senza la query."""
        names = {
            "Database": self.database,
            "WorkgroupName": self.workgroup,
            "ClusterIdentifier": self.cluster,
            "DbUser": self.db_user,
            "SecretArn": self.secret_arn,
        }
        return {name: value for name, value in names.items() if value}


@dataclass(frozen=True)
class DirectRedshift:
    """Come la v1: connessione diretta con le credenziali del secret di Redshift."""

    database: str
    secret_name: str
    query: str = DEFAULT_QUERY
    ttl_s: float = DEFAULT_TTL_S


@dataclass(frozen=True)
class ProductionConfig:
    settings_file: Path | None = Path("config/settings.yaml")
    knowledge_workdir: Path = Path(tempfile.gettempdir()) / "cycle-validation" / "knowledge"
    machines_file: Path | None = None
    redshift: RedshiftTarget | None = None
    direct: DirectRedshift | None = None
    no_machines: bool = False
    cloudwatch_metrics: bool = True


def _text(environ: Mapping[str, str], name: str) -> str | None:
    return (environ.get(name) or "").strip() or None


def _ttl(environ: Mapping[str, str], problems: list[str]) -> float:
    raw_ttl = _text(environ, "MACHINES_TTL_S")
    if raw_ttl is None:
        return DEFAULT_TTL_S
    try:
        return float(raw_ttl)
    except ValueError:
        problems.append(f"MACHINES_TTL_S: atteso un numero di secondi, trovato {raw_ttl!r}.")
        return DEFAULT_TTL_S


def _redshift(environ: Mapping[str, str], problems: list[str]) -> RedshiftTarget | None:
    database = _text(environ, "REDSHIFT_DATABASE")
    if database is None:
        return None
    workgroup = _text(environ, "REDSHIFT_WORKGROUP")
    cluster = _text(environ, "REDSHIFT_CLUSTER_ID")
    user = _text(environ, "REDSHIFT_DB_USER")
    secret = _text(environ, "REDSHIFT_SECRET_ARN")
    if (workgroup is None) == (cluster is None):
        problems.append(
            "REDSHIFT_WORKGROUP o REDSHIFT_CLUSTER_ID: serve uno dei due (Serverless o cluster)."
        )
    if cluster and not (user or secret):
        problems.append("REDSHIFT_CLUSTER_ID: serve anche REDSHIFT_DB_USER o REDSHIFT_SECRET_ARN.")
    return RedshiftTarget(
        database=database,
        workgroup=workgroup,
        cluster=cluster,
        db_user=user,
        secret_arn=secret,
        query=_text(environ, "MACHINES_QUERY") or DEFAULT_QUERY,
        ttl_s=_ttl(environ, problems),
    )


def _direct(environ: Mapping[str, str], problems: list[str]) -> DirectRedshift | None:
    database = _text(environ, "REDSHIFT_DATABASE")
    secret = _text(environ, "REDSHIFT_SECRET_NAME") or _text(environ, "SECRET_NAME")
    if database is None:
        problems.append("MACHINES_SOURCE=diretta: serve REDSHIFT_DATABASE.")
    if secret is None:
        problems.append(
            "MACHINES_SOURCE=diretta: serve il secret di Redshift (REDSHIFT_SECRET_NAME, oppure "
            "SECRET_NAME come nella v1)."
        )
    if database is None or secret is None:
        return None
    return DirectRedshift(
        database=database,
        secret_name=secret,
        query=_text(environ, "MACHINES_QUERY") or DEFAULT_QUERY,
        ttl_s=_ttl(environ, problems),
    )


def _source(environ: Mapping[str, str], problems: list[str]) -> str | None:
    given = _text(environ, "MACHINES_SOURCE")
    if given is None:
        if _text(environ, "MACHINES_FILE"):
            return "file"
        return "data_api" if _text(environ, "REDSHIFT_DATABASE") else None
    source = given.casefold()
    if source not in SOURCES:
        problems.append(f"MACHINES_SOURCE: usa {', '.join(SOURCES)}; trovato {given!r}.")
        return None
    return source


def load_production_config(environ: Mapping[str, str]) -> ProductionConfig:
    """Come `load_app_config`: tutti i problemi insieme, con il nome della variabile."""
    problems: list[str] = []
    source = _source(environ, problems)
    machines_file = _text(environ, "MACHINES_FILE")
    redshift = _redshift(environ, problems) if source == "data_api" else None
    direct = _direct(environ, problems) if source == "diretta" else None
    if source is None and not problems:
        problems.append(
            "Macchine attive: imposta MACHINES_SOURCE (diretta come la v1), oppure MACHINES_FILE "
            "o REDSHIFT_DATABASE con REDSHIFT_WORKGROUP o REDSHIFT_CLUSTER_ID."
        )
    database = _text(environ, "REDSHIFT_DATABASE")
    if source and ((machines_file and source != "file") or (database and source == "file")):
        problems.append(
            f"MACHINES_SOURCE={source} ma c'è anche "
            f"{'MACHINES_FILE' if source != 'file' else 'REDSHIFT_DATABASE'}: "
            "una sola sorgente delle macchine."
        )
    if source == "file" and not machines_file:
        problems.append("MACHINES_SOURCE=file: serve MACHINES_FILE.")
    given = environ.get("CLOUDWATCH_METRICS")
    flag = (given or "").strip().casefold()
    metrics = True
    if flag in _FALSE:
        metrics = False
    elif flag and flag not in _TRUE:
        problems.append(f"CLOUDWATCH_METRICS: usa true o false, trovato {given!r}.")
    if problems:
        raise ConfigError(
            "Configurazione di produzione non valida:\n  - " + "\n  - ".join(problems)
        )
    default = ProductionConfig()
    settings_file = _text(environ, "CYCLE_VALIDATION_CONFIG")
    workdir = _text(environ, "KNOWLEDGE_WORKDIR")
    return ProductionConfig(
        settings_file=Path(settings_file) if settings_file else default.settings_file,
        knowledge_workdir=Path(workdir) if workdir else default.knowledge_workdir,
        machines_file=Path(machines_file) if machines_file else None,
        redshift=redshift,
        direct=direct,
        no_machines=source == "nessuna",
        cloudwatch_metrics=metrics,
    )


def _profile_dependencies(
    name: str,
    settings: Settings,
    kb: KnowledgeBase,
    machines: MachineRegistry,
    session: AgentSession,
) -> Dependencies:
    profile = load_profile(name, settings.paths.profiles_dir)
    system_prompt = load_prompt(settings.paths.prompts_dir, OPERATION_PROMPT_FILE)
    extractor, extraction_prompt = make_pdf_extractor(
        profile, settings.agent, session, settings.paths.prompts_dir
    )
    return Dependencies(
        settings=settings,
        profile=profile,
        kb=kb,
        machines=machines,
        extractor=extractor,
        session=session,
        system_prompt=system_prompt,
        prompt_version=prompt_version(system_prompt, extraction_prompt),
        transcriber=make_transcriber(settings.agent),
    )


def _machines(
    production: ProductionConfig,
    redshift_data: Any | None,
    secrets: Any | None,
    redshift_driver: Any | None,
) -> MachineRegistry:
    if production.no_machines:
        return UnavailableMachineRegistry(NO_MACHINES, disabled=True)
    if production.direct is not None:
        if secrets is None or redshift_driver is None:
            raise ConfigError(
                "MACHINES_SOURCE=diretta ma manca il client secretsmanager o redshift_connector."
            )
        direct = production.direct

        def read_secret() -> dict[str, Any]:
            loaded = json.loads(
                secrets.get_secret_value(SecretId=direct.secret_name)["SecretString"]
            )
            return loaded if isinstance(loaded, dict) else {}

        return redshift_machine_registry(
            secret_connection(read_secret, redshift_driver, direct.database),
            direct.query,
            ttl_s=direct.ttl_s,
        )
    if production.redshift is not None:
        if redshift_data is None:
            raise ConfigError("REDSHIFT_DATABASE impostata ma nessun client redshift-data.")
        target = production.redshift
        return data_api_registry(
            redshift_data, target.parameters(), target.query, ttl_s=target.ttl_s
        )
    return load_machine_registry(production.machines_file)


def assemble_services(
    config: AppConfig,
    production: ProductionConfig,
    *,
    store: WritableObjectStore,
    cloudwatch: Any | None = None,
    redshift_data: Any | None = None,
    secrets: Any | None = None,
    redshift_driver: Any | None = None,
    session_factory: SessionFactory = SdkAgentSession,
) -> ApiServices:
    """I servizi con client già costruiti: qui nessun accesso alla rete. La conoscenza si
    scarica nel `warmup`, all'avvio: un file pubblicato non valido ferma lì il servizio (per
    EJ200 spegne solo EJ200, MG44)."""
    if config.civil_knowledge_pointer is None:
        raise ConfigError(
            "CIVIL_KNOWLEDGE_POINTER vuota: il servizio legge la conoscenza pubblicata da "
            "knowledge-index (current.json)."
        )
    settings = load_settings(production.settings_file)
    session = session_factory(settings.agent, settings.paths.runs_dir / "transcripts")
    machines = _machines(production, redshift_data, secrets, redshift_driver)
    civil = PublishedKnowledgeBase(
        store, config.civil_knowledge_pointer, production.knowledge_workdir / "civil"
    )
    knowledge: dict[str, KnowledgeBase] = {"mos": civil, "dr": civil}
    if config.ej200_enabled:
        catalog = (
            Ej200Catalog(store, pointer_key=config.ej200_knowledge_pointer)
            if config.ej200_knowledge_pointer
            else Ej200Catalog(store, key=config.ej200_catalog_key)
        )
        knowledge["ej200"] = Ej200KnowledgeBase(
            "ej200",
            catalog,
            production.knowledge_workdir / "ej200",
            store,
            tags=civil.machine_tags,
        )
    built: dict[str, Dependencies] = {}
    lock = threading.Lock()

    def deps_for(profile: str) -> Dependencies:
        if profile not in knowledge:
            raise ConfigError(f"Profilo '{profile}' non attivo in questo servizio.")
        with lock:
            if profile not in built:
                built[profile] = _profile_dependencies(
                    profile, settings, knowledge[profile], machines, session
                )
            return built[profile]

    runner = PipelineRunner(deps_for)
    metrics = (
        CloudWatchMetrics(cloudwatch)
        if cloudwatch is not None and production.cloudwatch_metrics
        else NullMetrics()
    )
    return ApiServices(
        config=config,
        store=store,
        runner=runner,
        metrics=metrics,
        warmup=lambda: runner.preload(list(knowledge), optional=("ej200",)),
    )
