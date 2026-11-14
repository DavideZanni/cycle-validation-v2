"""Punto di avvio del servizio: `uvicorn cycle_validation.api.main:app` (o Gunicorn).

Il cablaggio con le sorgenti aziendali è `build_services`, da completare dove ci sono
credenziali e client (S3, OpenSearch, Redshift, CloudWatch, SDK di autenticazione): ogni
punto è una porta con la sua implementazione di prova, vedi docs/superpowers/COMPLETION_REPORT.md.
"""

import os
from collections.abc import Callable, Mapping

from fastapi import FastAPI

from cycle_validation.api.app import ApiServices, create_app
from cycle_validation.api.settings import AppConfig, load_app_config
from cycle_validation.errors import ConfigError

ServicesFactory = Callable[[AppConfig], ApiServices]


def build_services(config: AppConfig) -> ApiServices:
    """Cablaggio di produzione. Non è disponibile senza i client aziendali."""
    raise ConfigError(
        "Il cablaggio di produzione non è configurato: registrare una factory con "
        "`create_app_from_env(environ, factory)` che costruisca S3, OpenSearch, Redshift e "
        "l'autenticazione con i client aziendali."
    )


def create_app_from_env(
    environ: Mapping[str, str] | None = None, factory: ServicesFactory | None = None
) -> FastAPI:
    """Valida la configurazione con messaggi chiari, poi costruisce l'app."""
    config = load_app_config(os.environ if environ is None else environ)
    return create_app((factory or build_services)(config))
