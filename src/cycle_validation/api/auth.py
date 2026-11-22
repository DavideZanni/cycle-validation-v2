"""Chi è l'utente e quali servizi può usare. Due modi (`API_AUTH`):

- `sdk`, come la v1 e come serve in azienda: token e permessi controllati dalla libreria interna
  `chatbot_ai_sdk` (in fondo al file). Si sceglie da solo se c'è `AUTH_INTROSPECT_URL`;
- `header`, per le prove: l'accesso lo verifica il **frontend**: il backend non legge token. Il frontend, dopo aver
riconosciuto l'utente, mette nella richiesta due header (nomi in `AppConfig`, di solito `X-User`
e `X-Services`): l'utente e i suoi servizi separati da virgole. Il backend se ne fida, quindi
**deve essere raggiungibile solo dal frontend** (rete privata o gateway): chi arrivasse diretto
potrebbe presentarsi come un altro.

L'utente finisce nel percorso S3 delle sessioni e dei feedback: si accettano solo lettere,
cifre e `.`, `_`, `@`, `-`, così nessuno può puntare ai file di un altro.
"""

import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from cycle_validation.errors import ConfigError

PREFIX = "/cycle_validation"
EJ200_PREFIX = f"{PREFIX}/ej200"
PUBLIC_PATHS = frozenset({f"{PREFIX}/health"})

SERVICE_CIVIL = "cv"
SERVICE_EJ200 = "cv_ej200"
SERVICE_ALL = "all"

_USER = re.compile(r"[A-Za-z0-9._@-]{1,128}")


@dataclass(frozen=True)
class Identity:
    sso: str
    services: frozenset[str]


def identity_from_headers(
    headers: Mapping[str, str], user_header: str, services_header: str
) -> Identity | None:
    """None se l'utente manca o ha una forma che potrebbe uscire dalla sua cartella."""
    user = headers.get(user_header, "").strip()
    if not _USER.fullmatch(user) or set(user) == {"."}:
        return None
    raw = headers.get(services_header, "")
    services = frozenset(part.strip() for part in raw.split(",") if part.strip())
    return Identity(user, services)


def required_services(path: str) -> frozenset[str]:
    """Servizi che aprono la rotta: EJ200 è più restrittivo del civile."""
    if path == EJ200_PREFIX or path.startswith(f"{EJ200_PREFIX}/"):
        return frozenset({SERVICE_EJ200, SERVICE_ALL})
    return frozenset({SERVICE_CIVIL, SERVICE_EJ200, SERVICE_ALL})


class IdentityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, user_header: str, services_header: str) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._user_header = user_header
        self._services_header = services_header

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if request.method == "OPTIONS" or path in PUBLIC_PATHS or not path.startswith(PREFIX):
            return await call_next(request)
        identity = identity_from_headers(request.headers, self._user_header, self._services_header)
        if identity is None:
            return JSONResponse({"detail": "Utente mancante o non valido."}, 401)
        if not identity.services & required_services(path):
            return JSONResponse({"detail": "Permesso insufficiente per il servizio."}, 403)
        request.state.identity = identity
        return await call_next(request)


# --- accesso come la v1: libreria interna `chatbot_ai_sdk` --------------------------------------
# La v1 (risposte C17, C19, C21) controlla il token del cookie con `AuthMiddleware` e
# `IntrospectionValidator`, e i permessi di `permissions.json` su S3 con
# `ServiceAccessMiddleware`: servizi `cv` e `cv_ej200`, sotto `/cycle_validation/ej200` solo
# `cv_ej200`. Le rotte leggono soltanto `current_user(request).sso`: i servizi dell'utente non
# arrivano alle rotte. Per questo qui i servizi si deducono dal percorso, che la libreria ha già
# controllato: le rotte EJ200 hanno `cv_ej200`, le altre solo il civile. Il pulsante militare
# della rotta nuova `validation/options` resta spento e `validation/upload` militare risponde
# 403: i cicli militari passano dalle rotte `/cycle_validation/ej200`, come nel frontend di oggi.


def _sdk() -> Any:
    try:
        import chatbot_ai_sdk.auth as library  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ConfigError(
            "API_AUTH=sdk ma la libreria chatbot_ai_sdk non è installata (è il .whl in vendor/ "
            "della v1)."
        ) from exc
    return library


class SdkIdentityMiddleware(BaseHTTPMiddleware):
    """Dopo i controlli della libreria: mette nella richiesta l'utente verificato."""

    def __init__(self, app: object, current_user: Callable[[Request], Any]) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._current_user = current_user

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if request.method == "OPTIONS" or path in PUBLIC_PATHS or not path.startswith(PREFIX):
            return await call_next(request)
        sso = str(getattr(self._current_user(request), "sso", "") or "").strip()
        if not _USER.fullmatch(sso) or set(sso) == {"."}:
            return JSONResponse({"detail": "Utente non valido."}, 403)
        ej200 = path == EJ200_PREFIX or path.startswith(f"{EJ200_PREFIX}/")
        request.state.identity = Identity(
            sso, frozenset({SERVICE_EJ200} if ej200 else {SERVICE_CIVIL})
        )
        return await call_next(request)


def install_sdk_auth(app: Any, frontend_url: str, library: Any = None) -> None:
    """Gli stessi middleware della v1. Starlette: l'ultimo aggiunto è il più esterno, quindi
    prima il token (AuthMiddleware), poi i permessi, poi l'utente per le rotte."""
    sdk = library if library is not None else _sdk()
    app.add_middleware(SdkIdentityMiddleware, current_user=sdk.current_user)
    app.add_middleware(
        sdk.ServiceAccessMiddleware,
        service_keys={SERVICE_CIVIL, SERVICE_EJ200},
        path_service_keys={EJ200_PREFIX: {SERVICE_EJ200}},
        permissions=sdk.S3PermissionsSource.from_env(),
    )
    app.add_middleware(
        sdk.AuthMiddleware,
        validator=sdk.IntrospectionValidator(sdk.AuthSettings.from_env()),
        public_paths=set(PUBLIC_PATHS),
        allowed_origins=[frontend_url],
    )
