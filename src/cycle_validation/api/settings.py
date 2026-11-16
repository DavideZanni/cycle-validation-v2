"""Impostazioni del servizio, lette dall'ambiente e validate all'avvio con messaggi chiari.

Oggi un valore numerico mancante impedisce l'avvio senza spiegazione: qui ogni problema
viene elencato con il nome della variabile.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from cycle_validation.errors import ConfigError
from cycle_validation.kb.pointer import DEFAULT_CIVIL_POINTER, DEFAULT_EJ200_POINTER

DEFAULT_EJ200_CATALOG_KEY = "Manufacturing AI/exports/ej200_publication/catalog.json"
_TRUE = {"1", "true", "yes", "on", "si", "sì"}
_FALSE = {"0", "false", "no", "off", ""}
_REQUIRED = ("BUCKETNAME", "REGION_NAME", "FRONTEND_URL")


@dataclass(frozen=True)
class AppConfig:
    bucket: str
    region: str
    frontend_url: str
    include_traceback: bool = True
    ej200_enabled: bool = True
    ej200_catalog_key: str = DEFAULT_EJ200_CATALOG_KEY
    # `current.json` pubblicati da knowledge-index (None = non usato, chiavi fisse).
    civil_knowledge_pointer: str | None = DEFAULT_CIVIL_POINTER
    ej200_knowledge_pointer: str | None = DEFAULT_EJ200_POINTER
    # Validazioni contemporanee (API_MAX_WORKERS); le altre aspettano il loro turno.
    max_workers: int = 6
    # Tetto del file caricato, per ogni rotta: i limiti del profilo (EJ200: 20 MB) valgono
    # dopo, e i profili civili non ne hanno uno proprio.
    max_upload_bytes: int = 50 * 1024 * 1024
    # Header con cui il frontend passa l'utente già verificato e i suoi servizi (vedi api/auth.py).
    user_header: str = "X-User"
    services_header: str = "X-Services"
    environment: str = "development"
    secret_name: str | None = None
    input_tokens_cost: float = 0.0
    output_tokens_cost: float = 0.0


def _flag(environ: Mapping[str, str], name: str, default: bool, problems: list[str]) -> bool:
    raw = environ.get(name)
    if raw is None:
        return default
    value = raw.strip().casefold()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    problems.append(f"{name}: valore booleano non valido ({raw!r}); usa true o false.")
    return default


def _number[T: (int, float)](
    environ: Mapping[str, str], name: str, kind: type[T], default: T, problems: list[str]
) -> T:
    raw = environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return kind(raw.strip())
    except ValueError:
        problems.append(f"{name}: atteso un numero ({kind.__name__}), trovato {raw!r}.")
        return default


def _optional(environ: Mapping[str, str], name: str, default: str) -> str | None:
    """Assente = valore standard; presente ma vuota = non usata."""
    raw = environ.get(name)
    if raw is None:
        return default
    return raw.strip() or None


def load_app_config(environ: Mapping[str, str]) -> AppConfig:
    """Raccoglie tutti i problemi e li riporta insieme, senza stampare valori di secret."""
    problems = [
        f"{name}: variabile obbligatoria mancante."
        for name in _REQUIRED
        if not environ.get(name, "").strip()
    ]
    config = AppConfig(
        bucket=environ.get("BUCKETNAME", "").strip(),
        region=environ.get("REGION_NAME", "").strip(),
        frontend_url=environ.get("FRONTEND_URL", "").strip(),
        include_traceback=_flag(environ, "API_INCLUDE_TRACEBACK", True, problems),
        ej200_enabled=_flag(environ, "EJ200_VALIDATION_ENABLED", True, problems),
        ej200_catalog_key=environ.get("EJ200_CATALOG_KEY", DEFAULT_EJ200_CATALOG_KEY).strip(),
        civil_knowledge_pointer=_optional(
            environ, "CIVIL_KNOWLEDGE_POINTER", DEFAULT_CIVIL_POINTER
        ),
        ej200_knowledge_pointer=_optional(
            environ, "EJ200_KNOWLEDGE_POINTER", DEFAULT_EJ200_POINTER
        ),
        max_workers=_number(environ, "API_MAX_WORKERS", int, 6, problems),
        max_upload_bytes=_number(environ, "API_MAX_UPLOAD_MB", int, 50, problems) * 1024 * 1024,
        user_header=environ.get("API_USER_HEADER", "").strip() or "X-User",
        services_header=environ.get("API_SERVICES_HEADER", "").strip() or "X-Services",
        environment=environ.get("ENVIRONMENT", "development").strip() or "development",
        secret_name=environ.get("SECRET_NAME") or None,
        input_tokens_cost=_number(environ, "INPUT_TOKENS_COST", float, 0.0, problems),
        output_tokens_cost=_number(environ, "OUTPUT_TOKENS_COST", float, 0.0, problems),
    )
    if config.max_workers < 1:
        problems.append("API_MAX_WORKERS: almeno 1, altrimenti nessuna validazione parte.")
    if problems:
        raise ConfigError("Configurazione del servizio non valida:\n  - " + "\n  - ".join(problems))
    return config
