import json
from typing import Any

import pytest

from cycle_validation.api.aws import CloudWatchMetrics, bootstrap_environment
from cycle_validation.api.settings import load_app_config
from cycle_validation.errors import ConfigError
from cycle_validation.kb.pointer import DEFAULT_CIVIL_POINTER, DEFAULT_EJ200_POINTER

ENV = {"BUCKETNAME": "b", "REGION_NAME": "eu-south-1", "FRONTEND_URL": "https://fe.example"}


def test_valid_environment_with_defaults() -> None:
    config = load_app_config(ENV)
    assert (config.bucket, config.region) == ("b", "eu-south-1")
    assert config.ej200_enabled and config.include_traceback
    assert config.ej200_catalog_key.endswith("ej200_publication/catalog.json")


def test_every_problem_is_listed_with_the_variable_name() -> None:
    with pytest.raises(ConfigError) as info:
        load_app_config({"API_MAX_WORKERS": "molti", "EJ200_VALIDATION_ENABLED": "forse"})
    text = str(info.value)
    for name in (
        "BUCKETNAME",
        "REGION_NAME",
        "FRONTEND_URL",
        "API_MAX_WORKERS",
        "EJ200_VALIDATION_ENABLED",
    ):
        assert name in text


def test_flags_and_numbers_are_parsed() -> None:
    config = load_app_config(
        ENV
        | {
            "EJ200_VALIDATION_ENABLED": "false",
            "API_INCLUDE_TRACEBACK": "0",
            "API_MAX_WORKERS": "4",
            "INPUT_TOKENS_COST": "0.25",
        }
    )
    assert not config.ej200_enabled and not config.include_traceback
    assert config.max_workers == 4 and config.input_tokens_cost == 0.25


def test_cloudwatch_metric_and_failure_isolation() -> None:
    sent: list[dict[str, Any]] = []

    class Client:
        def put_metric_data(self, **args: Any) -> None:
            sent.append(args)

    CloudWatchMetrics(Client()).llm_cost(0.5)
    assert sent[0]["Namespace"] == "Chatbot/CV"
    assert sent[0]["MetricData"][0]["MetricName"] == "llmInvokationCost"

    class Down:
        def put_metric_data(self, **_: Any) -> None:
            raise TimeoutError

    metrics = CloudWatchMetrics(Down())
    metrics.llm_cost(1.0)  # non solleva
    assert metrics.failures == 1


def test_bootstrap_imports_missing_variables_only_and_never_returns_values() -> None:
    class Secrets:
        def get_secret_value(self, SecretId: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"NUOVA": "v1", "ESISTENTE": "v2"})}

    environ = {"ESISTENTE": "originale"}
    names = bootstrap_environment(Secrets(), "nome-secret", environ)
    assert names == ["NUOVA"] and environ == {"ESISTENTE": "originale", "NUOVA": "v1"}


def test_bootstrap_errors_do_not_leak_content() -> None:
    class Broken:
        def get_secret_value(self, **_: Any) -> Any:
            raise PermissionError("AccessDenied sul secret")

    with pytest.raises(ConfigError, match="nome-secret"):
        bootstrap_environment(Broken(), "nome-secret", {})

    class NotObject:
        def get_secret_value(self, **_: Any) -> dict[str, str]:
            return {"SecretString": "[1, 2]"}

    with pytest.raises(ConfigError, match="oggetto JSON"):
        bootstrap_environment(NotObject(), "s", {})


def test_app_from_env_validates_first_then_needs_the_machines_source() -> None:
    from cycle_validation.api.main import create_app_from_env

    with pytest.raises(ConfigError, match="BUCKETNAME"):
        create_app_from_env({})
    with pytest.raises(ConfigError, match="MACHINES_FILE"):
        create_app_from_env(dict(ENV))


def test_app_from_env_uses_the_given_factory(tmp_path: Any) -> None:
    from api_support import Env

    from cycle_validation.api.main import create_app_from_env

    env = Env(tmp_path)
    app = create_app_from_env(ENV, lambda config: env.services)
    assert app.title == "Cycle Validation"


def test_upload_limit_defaults_to_50_mb_and_reads_megabytes_from_the_environment() -> None:
    base = {"BUCKETNAME": "b", "REGION_NAME": "r", "FRONTEND_URL": "https://f.example"}
    assert load_app_config(base).max_upload_bytes == 50 * 1024 * 1024
    assert load_app_config({**base, "API_MAX_UPLOAD_MB": "8"}).max_upload_bytes == 8 * 1024 * 1024


def test_zero_simultaneous_validations_would_block_the_service() -> None:
    with pytest.raises(ConfigError, match="API_MAX_WORKERS"):
        load_app_config({**ENV, "API_MAX_WORKERS": "0"})


def test_the_identity_headers_can_be_renamed() -> None:
    config = load_app_config(ENV)
    assert (config.user_header, config.services_header) == ("X-User", "X-Services")
    config = load_app_config({**ENV, "API_USER_HEADER": "X-Utente", "API_SERVICES_HEADER": "X-G"})
    assert (config.user_header, config.services_header) == ("X-Utente", "X-G")


def test_knowledge_pointers_have_standard_keys_and_can_be_turned_off() -> None:
    config = load_app_config(ENV)
    assert config.civil_knowledge_pointer == DEFAULT_CIVIL_POINTER
    assert config.ej200_knowledge_pointer == DEFAULT_EJ200_POINTER

    changed = load_app_config(
        ENV | {"CIVIL_KNOWLEDGE_POINTER": " altro/current.json ", "EJ200_KNOWLEDGE_POINTER": ""}
    )
    assert changed.civil_knowledge_pointer == "altro/current.json"
    assert changed.ej200_knowledge_pointer is None  # vuoto = catalogo a chiave fissa
