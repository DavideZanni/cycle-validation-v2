"""Impostazioni e profili, validati al caricamento con messaggi che dicono cosa correggere."""

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from cycle_validation.domain.check import CheckName
from cycle_validation.errors import ConfigError


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentSettings(_Strict):
    """Sessioni dell'agente. `model` è un alias o l'id completo del profilo di inferenza."""

    model: str = "haiku"
    # Ragionamento dei controlli. None = predefinito del modello. low: circa -30% di costo a
    # parità di esiti sui casi di prova (MIGLIORIE B2, da confermare su Bedrock).
    effort: Literal["low", "medium", "high"] | None = "low"
    # Ragionamento per la lettura del PDF. None = come `effort`. high: con low la lettura era
    # peggiore.
    extraction_effort: Literal["low", "medium", "high"] | None = "high"
    use_bedrock: bool = True
    aws_region: str | None = None
    # Modello Bedrock che trascrive immagini e PDF senza testo. None = disattivato.
    transcribe_model: str | None = None
    # Pagine scansionate mandate insieme al trascrittore (MIGLIORIE B3). Il limite vero sono le
    # quote Bedrock: con molti utenti insieme le chiamate sono API_MAX_WORKERS per questo.
    transcribe_concurrency: int = Field(default=4, ge=1, le=16)
    max_turns: int = Field(default=10, ge=1, le=50)
    inline_max_turns: int = Field(default=3, ge=1, le=10)
    extraction_max_turns: int = Field(default=3, ge=1, le=10)
    concurrency: int = Field(default=6, ge=1, le=32)
    retries: int = Field(default=2, ge=0, le=5)
    retry_backoff_s: float = Field(default=2.0, ge=0)
    invalid_output_retries: int = Field(default=1, ge=0, le=3)
    # Tempo massimo di una sessione dei controlli e della lettura del PDF (MIGLIORIE A4).
    # Oltre, WARNING per errore tecnico invece di un'attesa senza fine. None = nessun limite.
    session_timeout_s: float | None = Field(default=90, gt=0, le=600)
    extraction_timeout_s: float | None = Field(default=300, gt=0, le=1800)
    read_limit: int = Field(default=40, ge=5, le=200)
    read_window: int = Field(default=30, ge=5, le=200)
    read_before: int = Field(default=15, ge=0, le=100)
    grep_max_context: int = Field(default=10, ge=0, le=50)
    inline_max_lines: int = Field(default=150, ge=0, le=2000)
    citation_window: int = Field(default=3, ge=0, le=20)
    # Dire al modello che i task citati non sono nel manuale e che il testo è quello delle
    # fonti del ciclo (MIGLIORIE A2). Vale solo con `skip_missing_task` spento: variante
    # `prompt_task_mancante`.
    missing_task_note: bool = False
    # Task citato che il manuale non ha: WARNING subito, senza chiamare il modello (MIGLIORIE
    # B6, scelta il 20-11-2026 al posto di A2). Una sessione in meno.
    skip_missing_task: bool = True
    # Descrizione in due lingue: il modello confronta con il testo di riferimento l'italiano e
    # l'inglese separatamente; se una sola delle due dice altro, è una contraddizione. Variante
    # `lingue_separate` (24-11-2026): la base, spenta, mancava 18 negazioni tolte su 21.
    separate_languages: bool = False
    # Prima di giudicare il modello scompone la descrizione in elementi tecnici (lavorazione,
    # valori, limiti, divieti, materiali) e li controlla uno per uno. Variante
    # `elementi_uno_per_uno` (24-11-2026).
    itemized_check: bool = False
    # Se il primo giudizio è «non verificabile» (WARNING EVIDENZA_NON_TROVATA), una seconda
    # sessione cerca con Grep e Read in tutti i documenti citati dal ciclo, non solo nel task
    # dell'operazione. Variante `seconda_ricerca` (25-11-2026): i due errori noti sempre
    # mancati uscivano in tutte le 36 prove del 24-11 con EVIDENZA_NON_TROVATA. Costa solo
    # sulle operazioni non verificabili.
    search_when_unverifiable: bool = False
    # Una contraddizione (ERRATO) si conferma con altrettante sessioni uguali: resta ERRATO
    # solo se la ritrovano tutte, altrimenti WARNING GIUDIZIO_INSTABILE. Su un ciclo DR vero
    # lo stesso confronto dava ERRATO 3 volte su 6 (21-11-2026). Costa solo sugli ERRATO.
    # 0 = nessuna conferma.
    confirm_contradiction: int = Field(default=2, ge=0, le=5)
    # Testo delle sessioni su disco: contiene cicli e manuali. Spento nel servizio, acceso
    # negli esperimenti (eval/varianti/baseline.yaml).
    save_transcripts: bool = False


class PathSettings(_Strict):
    """Percorsi relativi alla cartella da cui si lancia lo strumento."""

    profiles_dir: Path = Path("config/profiles")
    prompts_dir: Path = Path("prompts")
    knowledge_dir: Path = Path("data/knowledge")
    runs_dir: Path = Path("runs")
    machines_file: Path | None = None


class ModuleCheckSettings(_Strict):
    """Riconoscimento del tipo di ciclo dalla testata, per rifiutare il modulo sbagliato."""

    enabled: bool = True
    # Valori del campo PROGETTO che identificano un ciclo militare e uno civile.
    military_projects: list[str] = Field(default_factory=lambda: ["EJ200"])
    civil_projects: list[str] = Field(default_factory=lambda: ["GENX", "LEAP"])
    # Espressioni regolari che, in testata, identificano un ciclo DR. Vuoto = MOS e DR
    # non vengono distinti. Sull'unica stampa DR reale vista (16/11/2026) la testata non dice
    # "DR": lo distingue il numero di segnalazione difetti in NOTE (`Saa/nnnnn-...`), dove
    # un MOS porta il task del manuale. Da riconfermare su altri DR.
    dr_markers: list[str] = Field(
        default_factory=lambda: [
            r"\bDR\b",
            r"DEPARTURE\s+RECOMMENDATION",
            r"\bS\d{2}/\d{4,6}\b",
        ]
    )

    @field_validator("dr_markers")
    @classmethod
    def _valid_patterns(cls, value: list[str]) -> list[str]:
        for pattern in value:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"espressione regolare non valida '{pattern}': {exc}") from exc
        return value


class Settings(_Strict):
    agent: AgentSettings = Field(default_factory=AgentSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    module_check: ModuleCheckSettings = Field(default_factory=ModuleCheckSettings)


class FileLimits(_Strict):
    require_pdf_header: bool = True
    max_bytes: int | None = Field(default=None, ge=1)
    max_pages: int | None = Field(default=None, ge=1)
    # Tetto delle pagine da trascrivere con il modello (scansioni): vale anche per i profili
    # senza `max_pages`, perché ogni pagina è un rendering e una chiamata a pagamento.
    max_transcribed_pages: int = Field(default=60, ge=1)
    min_chars: int = Field(default=100, ge=0)
    required_text: list[str] = Field(default_factory=list)


class ProfileConfig(_Strict):
    """Un profilo dichiara limiti sul file, controlli attivi e regole di dominio."""

    name: str
    enabled: bool = True
    disabled_reason: str = ""
    file_limits: FileLimits = Field(default_factory=FileLimits)
    checks: list[CheckName]
    blocking_checks: list[CheckName] = Field(default_factory=list)
    requires_selectors: bool = False
    reference_mode: Literal["task", "document"] = "task"
    document_order: list[str] = Field(default_factory=list)
    verify_process_sheet: bool = True
    excluded_sheet_prefixes: list[str] = Field(default_factory=list)
    engine_families: list[str] = Field(default_factory=list)
    extraction_prompt: str = "extract_cycle.md"
    layout_extractor: Literal["none", "pvrm320"] = "none"


def _describe(error: ValidationError, origin: Path) -> str:
    lines = [f"Configurazione non valida in {origin}:"]
    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"]) or "(radice)"
        lines.append(f"  - {field}: {item['msg']}")
    return "\n".join(lines)


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Impossibile leggere {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML non valido in {path}: {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} deve contenere una mappa chiave: valore.")
    return loaded


def load_settings(path: Path | None = None) -> Settings:
    """Carica le impostazioni. Senza file valgono i valori predefiniti."""
    if path is None:
        return Settings()
    if not path.is_file():
        raise ConfigError(f"File di configurazione non trovato: {path}")
    try:
        return Settings.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ConfigError(_describe(exc, path)) from exc


def available_profiles(profiles_dir: Path) -> list[str]:
    return sorted(item.stem for item in profiles_dir.glob("*.yaml"))


def load_profile(name: str, profiles_dir: Path) -> ProfileConfig:
    path = profiles_dir / f"{name}.yaml"
    if not path.is_file():
        known = ", ".join(available_profiles(profiles_dir)) or "nessuno"
        raise ConfigError(f"Profilo '{name}' non trovato in {profiles_dir}. Disponibili: {known}.")
    try:
        profile = ProfileConfig.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ConfigError(_describe(exc, path)) from exc
    unknown = [check for check in profile.blocking_checks if check not in profile.checks]
    if unknown:
        names = ", ".join(unknown)
        raise ConfigError(f"{path}: blocking_checks cita controlli non attivi: {names}.")
    return profile
