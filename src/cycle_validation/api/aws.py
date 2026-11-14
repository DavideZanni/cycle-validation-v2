"""Adattatori AWS del livello API. Ricevono client già costruiti (boto3 non è importato qui):
metrica di costo su CloudWatch e bootstrap delle variabili da Secrets Manager.
Nessun valore di secret viene mai scritto nei log o negli errori."""

import json
import os
from collections.abc import MutableMapping
from typing import Any

from cycle_validation.errors import ConfigError

METRIC_NAMESPACE = "Chatbot/CV"
METRIC_NAME = "llmInvokationCost"


class CloudWatchMetrics:
    """Pubblica il costo LLM di un run. Un errore di metrica non deve far fallire la validazione."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self.failures = 0

    def llm_cost(self, usd: float) -> None:
        try:
            self._client.put_metric_data(
                Namespace=METRIC_NAMESPACE,
                MetricData=[{"MetricName": METRIC_NAME, "Value": float(usd), "Unit": "None"}],
            )
        except Exception:
            self.failures += 1


def bootstrap_environment(
    client: Any, secret_name: str, environ: MutableMapping[str, str] | None = None
) -> list[str]:
    """Legge un secret JSON `{NOME: valore}` e lo porta nell'ambiente, senza sovrascrivere
    le variabili già impostate. Restituisce i NOMI importati (mai i valori)."""
    target = os.environ if environ is None else environ
    try:
        raw = client.get_secret_value(SecretId=secret_name)["SecretString"]
        values = json.loads(raw)
    except Exception as exc:
        raise ConfigError(
            f"Secret '{secret_name}' non leggibile o non valido ({type(exc).__name__})."
        ) from exc
    if not isinstance(values, dict):
        raise ConfigError(f"Secret '{secret_name}': atteso un oggetto JSON {{NOME: valore}}.")
    imported: list[str] = []
    for name, value in values.items():
        if name not in target:
            target[str(name)] = str(value)
            imported.append(str(name))
    return imported
