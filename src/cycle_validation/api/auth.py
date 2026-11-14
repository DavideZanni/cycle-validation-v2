"""Autenticazione e autorizzazione per servizio.

Nel sistema attuale la verifica è dell'SDK condiviso (`chatbot_ai_sdk.auth`: introspezione
del token e permessi letti da S3). Qui sta dietro `AuthBackend`: l'adattatore sull'SDK
si scrive dove l'SDK è disponibile; `StaticAuthBackend` serve ai test. L'identità viene
sempre dal backend, mai da un header `sso` passato dal chiamante.
"""

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from cycle_validation.errors import SourceUnavailableError

PREFIX = "/cycle_validation"
EJ200_PREFIX = f"{PREFIX}/ej200"
PUBLIC_PATHS = frozenset({f"{PREFIX}/health"})
SERVICE_CIVIL = "cv"
SERVICE_EJ200 = "cv_ej200"
SERVICE_ALL = "all"


@dataclass(frozen=True)
class Identity:
    sso: str
    services: frozenset[str]


class AuthBackend(Protocol):
    def authenticate(self, headers: Mapping[str, str]) -> Identity | None:
        """None se il token manca o non è valido. SourceUnavailableError se l'IdP non risponde."""
        ...


class StaticAuthBackend:
    def __init__(self, tokens: Mapping[str, Identity]) -> None:
        self._tokens = dict(tokens)

    def authenticate(self, headers: Mapping[str, str]) -> Identity | None:
        authorization = headers.get("authorization", "")
        token = authorization.removeprefix("Bearer ").strip() if authorization else ""
        return self._tokens.get(token)


def required_services(path: str) -> frozenset[str]:
    """Servizi che aprono la rotta: EJ200 è più restrittivo del civile."""
    if path == EJ200_PREFIX or path.startswith(f"{EJ200_PREFIX}/"):
        return frozenset({SERVICE_EJ200, SERVICE_ALL})
    return frozenset({SERVICE_CIVIL, SERVICE_EJ200, SERVICE_ALL})


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, backend: AuthBackend) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._backend = backend

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if request.method == "OPTIONS" or path in PUBLIC_PATHS or not path.startswith(PREFIX):
            return await call_next(request)
        try:
            identity = self._backend.authenticate(request.headers)
        except SourceUnavailableError:
            return JSONResponse({"detail": "Servizio di autenticazione non disponibile."}, 503)
        if identity is None:
            return JSONResponse({"detail": "Autenticazione richiesta."}, 401)
        if not identity.services & required_services(path):
            return JSONResponse({"detail": "Permesso insufficiente per il servizio."}, 403)
        request.state.identity = identity
        return await call_next(request)
