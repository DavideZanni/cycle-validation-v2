"""Chi è l'utente e quali servizi può usare.

L'accesso lo verifica il **frontend**: il backend non legge token. Il frontend, dopo aver
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

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

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
