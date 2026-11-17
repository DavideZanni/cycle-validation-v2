"""Punto di avvio del servizio: `uvicorn cycle_validation.api.entry:app` (o Gunicorn).

`build_services` monta tutto dall'ambiente con i client boto3: S3, conoscenza pubblicata,
EJ200, macchine attive (file o Redshift Data API), CloudWatch. Le variabili sono in
`api/settings.py` e `api/production.py`. Con `SECRET_NAME` le variabili mancanti si leggono
prima da Secrets Manager. Per un montaggio diverso basta passare un'altra `factory`.
"""

import os
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any

from fastapi import FastAPI

from cycle_validation.api.app import ApiServices, create_app
from cycle_validation.api.aws import bootstrap_environment
from cycle_validation.api.production import assemble_services, load_production_config
from cycle_validation.api.settings import AppConfig, load_app_config
from cycle_validation.errors import ConfigError
from cycle_validation.kb.stores import S3ObjectStore

ServicesFactory = Callable[[AppConfig], ApiServices]


def _boto3() -> Any:
    try:
        import boto3
    except ImportError as exc:
        raise ConfigError(
            "boto3 non è installato: serve per S3. Installa con `uv sync --extra aws` "
            "(nel Dockerfile c'è già)."
        ) from exc
    return boto3


def build_services(config: AppConfig, environ: Mapping[str, str] | None = None) -> ApiServices:
    """Cablaggio di produzione dall'ambiente. Prima valida tutto, poi crea i client."""
    production = load_production_config(os.environ if environ is None else environ)
    boto3 = _boto3()
    region = config.region or None
    return assemble_services(
        config,
        production,
        store=S3ObjectStore(boto3.client("s3", region_name=region), config.bucket),
        cloudwatch=(
            boto3.client("cloudwatch", region_name=region)
            if production.cloudwatch_metrics
            else None
        ),
        redshift_data=(
            boto3.client("redshift-data", region_name=region) if production.redshift else None
        ),
    )


def create_app_from_env(
    environ: MutableMapping[str, str] | None = None, factory: ServicesFactory | None = None
) -> FastAPI:
    """Legge il secret (se c'è), valida la configurazione con messaggi chiari, poi costruisce
    l'app."""
    env: MutableMapping[str, str] = os.environ if environ is None else environ
    secret = (env.get("SECRET_NAME") or "").strip()
    if secret:
        region = (env.get("REGION_NAME") or "").strip() or None
        bootstrap_environment(_boto3().client("secretsmanager", region_name=region), secret, env)
    config = load_app_config(env)
    return create_app((factory or (lambda c: build_services(c, env)))(config))
