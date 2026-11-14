"""Modulo caricato da Gunicorn: costruisce l'app dall'ambiente al primo import."""

from cycle_validation.api.main import create_app_from_env

app = create_app_from_env()
