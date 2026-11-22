"""Accesso come la v1 (`API_AUTH=sdk`): token e permessi li controlla la libreria interna
`chatbot_ai_sdk`, qui sostituita da una finta con lo stesso comportamento visto nella v1
(risposte C17, C19, C21): 401 senza token valido, 403 senza il servizio, `current_user(request)`
con il campo `sso`."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from api_support import Env, civil_pdf
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from test_api import session_body

from cycle_validation.api.settings import load_app_config
from cycle_validation.errors import ConfigError

BASE = "/cycle_validation"
# token -> (sso, servizi in permissions.json)
USERS = {
    "t-civile": ("anna", {"cv"}),
    "t-ej200": ("bruno", {"cv_ej200"}),
    "t-altro": ("carla", {"altro"}),
}
CALLS: dict[str, Any] = {}


@dataclass(frozen=True)
class VerifiedUser:
    sso: str
    client_id: str = "frontend"


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app: Any, validator: Any, public_paths: set[str], allowed_origins: list[str]
    ) -> None:
        super().__init__(app)
        CALLS["auth"] = {"public": public_paths, "origins": allowed_origins}
        self.public = public_paths

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS" or request.url.path in self.public:
            return await call_next(request)
        token = request.cookies.get("session") or ""
        if token not in USERS:
            return JSONResponse({"detail": "token"}, 401)
        request.state.user = VerifiedUser(USERS[token][0])
        return await call_next(request)


class ServiceAccessMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        service_keys: set[str],
        path_service_keys: dict[str, set[str]],
        permissions: Any,
    ) -> None:
        super().__init__(app)
        CALLS["access"] = {"keys": service_keys, "paths": path_service_keys}
        self.keys, self.paths = service_keys, path_service_keys

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        user = getattr(request.state, "user", None)
        if user is None:
            return await call_next(request)
        needed = next(
            (keys for path, keys in self.paths.items() if request.url.path.startswith(path)),
            self.keys,
        )
        granted = next(services for sso, services in USERS.values() if sso == user.sso)
        if not granted & (needed | {"all"}):
            return JSONResponse({"detail": "permesso"}, 403)
        return await call_next(request)


def current_user(request: Request) -> VerifiedUser:
    user: VerifiedUser = request.state.user
    return user


LIBRARY = SimpleNamespace(
    AuthMiddleware=AuthMiddleware,
    ServiceAccessMiddleware=ServiceAccessMiddleware,
    IntrospectionValidator=lambda settings: object(),
    AuthSettings=SimpleNamespace(from_env=lambda: object()),
    S3PermissionsSource=SimpleNamespace(from_env=lambda: object()),
    current_user=current_user,
)


def _env(tmp_path: Path) -> Env:
    env = Env(tmp_path, auth="sdk", auth_library=LIBRARY)
    return env


def test_the_middlewares_are_set_up_like_the_v1(tmp_path: Path) -> None:
    _env(tmp_path).client.get(f"{BASE}/health")  # Starlette li crea alla prima richiesta
    assert CALLS["auth"] == {
        "public": {f"{BASE}/health"},
        "origins": ["https://frontend.example"],
    }
    assert CALLS["access"] == {
        "keys": {"cv", "cv_ej200"},
        "paths": {f"{BASE}/ej200": {"cv_ej200"}},
    }


def test_without_a_valid_token_it_is_401_and_health_stays_public(tmp_path: Path) -> None:
    client = _env(tmp_path).client
    assert client.get(f"{BASE}/health").status_code == 200
    assert client.get(f"{BASE}/flow/start").status_code == 401
    # gli header della modalità di prova non valgono più
    headers = {"X-User": "anna", "X-Services": "all"}
    assert client.get(f"{BASE}/flow/start", headers=headers).status_code == 401


def test_the_user_comes_from_the_token_and_the_sessions_are_theirs(tmp_path: Path) -> None:
    env = _env(tmp_path)
    env.client.cookies.set("session", "t-civile")
    assert env.client.get(f"{BASE}/flow/start").status_code == 200
    created = env.client.post(f"{BASE}/sessions", json=session_body())
    assert created.status_code == 200, created.text
    assert any("ChatSessions/anna/s1.json" in key for key in env.store.list_keys(""))


def test_ej200_needs_the_military_service(tmp_path: Path) -> None:
    env = _env(tmp_path)
    env.client.cookies.set("session", "t-civile")
    assert env.client.get(f"{BASE}/ej200/flow/start").status_code == 403
    env.client.cookies.set("session", "t-ej200")
    assert env.client.get(f"{BASE}/ej200/flow/start").status_code == 200
    env.client.cookies.set("session", "t-altro")
    assert env.client.get(f"{BASE}/flow/start").status_code == 403


def test_military_cycles_go_through_the_ej200_routes_only(tmp_path: Path) -> None:
    """I servizi dell'utente non arrivano alle rotte: sulla rotta nuova il militare è spento."""
    env = _env(tmp_path)
    env.client.cookies.set("session", "t-ej200")
    options = env.client.get(f"{BASE}/validation/options").json()
    domains = [option["value"] for option in options["steps"][0]["options"]]
    assert domains == ["civil"]
    files = {"file": ("ciclo.pdf", civil_pdf(), "application/pdf")}
    response = env.client.post(
        f"{BASE}/validation/upload", data={"domain": "military"}, files=files
    )
    assert response.status_code == 403


def test_the_mode_is_chosen_from_the_v1_secret() -> None:
    env = {"BUCKETNAME": "b", "REGION_NAME": "r", "FRONTEND_URL": "https://f.example"}
    assert load_app_config(env).auth == "header"
    assert load_app_config({**env, "AUTH_INTROSPECT_URL": "https://idp.example"}).auth == "sdk"
    assert load_app_config({**env, "API_AUTH": "header", "AUTH_INTROSPECT_URL": "x"}).auth == (
        "header"
    )
    with pytest.raises(ConfigError, match="API_AUTH"):
        load_app_config({**env, "API_AUTH": "forse"})


def test_sdk_mode_without_the_library_does_not_start(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    try:
        import chatbot_ai_sdk  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        with pytest.raises(ConfigError, match="chatbot_ai_sdk"):
            Env(tmp_path, auth="sdk")
    else:
        pytest.skip("la libreria è installata")


def test_the_environment_secret_name_comes_from_cv_env_secret() -> None:
    from cycle_validation.api import main

    read: list[str] = []

    class Secrets:
        def get_secret_value(self, SecretId: str) -> dict[str, str]:
            read.append(SecretId)
            return {"SecretString": '{"BUCKETNAME": "b", "SECRET_NAME": "redshift"}'}

    class Boto3:
        @staticmethod
        def client(service: str, region_name: str | None = None) -> Secrets:
            return Secrets()

    env = {"CV_ENV_SECRET": "ambiente", "REGION_NAME": "r", "FRONTEND_URL": "https://f.example"}
    original = main._boto3
    main._boto3 = lambda: Boto3
    try:
        main.create_app_from_env(env, lambda config: _raise(config))
    except _Built as built:
        assert built.config.bucket == "b"
    finally:
        main._boto3 = original
    assert read == ["ambiente"]
    assert env["SECRET_NAME"] == "redshift"  # come nella v1: il secret di Redshift


class _Built(Exception):
    def __init__(self, config: Any) -> None:
        self.config = config


def _raise(config: Any) -> Any:
    raise _Built(config)
