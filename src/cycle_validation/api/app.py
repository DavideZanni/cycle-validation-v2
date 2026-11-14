"""App FastAPI: stesse rotte, stessi modelli, stessi codici HTTP e stessa forma degli errori
del sistema attuale. La logica sta nella libreria; qui solo traduzione HTTP."""

import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Body, FastAPI, File, Form, Path, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from cycle_validation.api.auth import (
    PREFIX,
    SERVICE_ALL,
    SERVICE_EJ200,
    AuthBackend,
    AuthMiddleware,
    Identity,
)
from cycle_validation.api.models import (
    SESSION_ID,
    ChatSession,
    ConversationRequest,
    Ej200Feedback,
    Ej200Session,
)
from cycle_validation.api.settings import AppConfig
from cycle_validation.api.storage import CIVIL, EJ200, FeedbackStore, SessionStore
from cycle_validation.domain.report import Report
from cycle_validation.errors import (
    CycleValidationError,
    ExtractionError,
    IngestError,
    KnowledgeError,
    ProfileUnavailableError,
    SelectionError,
    SourceUnavailableError,
)
from cycle_validation.kb.stores import WritableObjectStore
from cycle_validation.pipeline import RunRequest
from cycle_validation.report.legacy_payload import build_legacy_payload
from cycle_validation.resolve.dr import SelectorError, parse_selectors
from cycle_validation.selection import MILITARY_PROFILE, resolve_profile, selection_options

DR_QUESTION = "Devi validare un ciclo DR (Departure Recommendation)?"
EJ200_START = "Ok. Carica il ciclo EJ200."


class ValidationRunner(Protocol):
    async def run(self, profile: str, request: RunRequest) -> Report: ...


class MetricsSink(Protocol):
    def llm_cost(self, usd: float) -> None: ...


class NullMetrics:
    def llm_cost(self, usd: float) -> None:
        return None


@dataclass
class ApiServices:
    config: AppConfig
    auth: AuthBackend
    store: WritableObjectStore
    runner: ValidationRunner
    metrics: MetricsSink = field(default_factory=NullMetrics)
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    new_id: Callable[[], str] = lambda: uuid.uuid4().hex


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _error(status: int, message: str, **extra: Any) -> JSONResponse:
    return JSONResponse(
        {"ok": False, "error": {"code": status, "message": message, **extra}}, status
    )


def _identity(request: Request) -> Identity:
    identity: Identity = request.state.identity
    return identity


def _check_session_id(value: str | None) -> None:
    if value is not None and not SESSION_ID.match(value):
        raise ApiError(422, "session_id non valido: ammessi lettere, cifre, - e _ (1-128).")


def _parse_bool(value: str) -> bool:
    lowered = value.strip().casefold()
    if lowered in ("true", "1", "yes", "sì", "si"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    raise ApiError(422, "is_dr deve essere true o false.")


_UPLOAD_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")


async def _read_pdf(file: UploadFile, max_bytes: int) -> bytes:
    name = file.filename or ""
    if not name.lower().endswith(_UPLOAD_EXTENSIONS):
        raise ApiError(415, "Il file deve essere un PDF (.pdf) o un'immagine (.jpg, .jpeg, .png).")
    # Si legge al massimo un byte oltre il tetto: un file enorme non entra mai in memoria.
    too_large = file.size is not None and file.size > max_bytes
    data = b"" if too_large else await file.read(max_bytes + 1)
    if too_large or len(data) > max_bytes:
        megabytes = max(max_bytes // (1024 * 1024), 1)
        raise ApiError(413, f"Il file supera il limite di caricamento di {megabytes} MB.")
    if not data:
        raise ApiError(400, "Il file è vuoto.")
    return data


def _envelope(services: ApiServices, report: Report, file_name: str) -> dict[str, Any]:
    services.metrics.llm_cost(report.usage.cost_usd)
    return {
        "state": "succeeded",
        "result": {"file_name": file_name, "payload": build_legacy_payload(report), "error": None},
        "error": None,
        "error_info": None,
    }


def _public_message(exc: BaseException) -> str:
    """Il messaggio degli errori previsti è scritto per chi usa lo strumento. Quello di ogni
    altra eccezione può riportare il valore che l'ha causata (testo del ciclo, di un manuale,
    di una sessione): al client va solo il tipo."""
    if isinstance(exc, CycleValidationError):
        return str(exc)
    return f"Errore interno ({type(exc).__name__})."


def _frames(exc: BaseException) -> str:
    """Catena delle eccezioni come tipo e posizioni nel codice: né i messaggi né le righe di
    sorgente, che possono contenere dati."""
    lines: list[str] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        lines.append(type(current).__name__)
        for frame in traceback.extract_tb(current.__traceback__):
            lines.append(f"  {frame.filename}:{frame.lineno} in {frame.name}")
        current = current.__cause__ or current.__context__
    return "\n".join(lines)


def _failed(services: ApiServices, exc: Exception) -> dict[str, Any]:
    message = _public_message(exc)
    info: dict[str, Any] = {"type": type(exc).__name__, "message": message}
    if services.config.include_traceback:
        info["traceback"] = _frames(exc)
    return {
        "state": "failed",
        "result": None,
        "error": message,
        "error_info": info,
    }


def _raise_for(exc: Exception) -> None:
    """Traduce gli errori della libreria nei codici HTTP del sistema attuale."""
    if isinstance(exc, IngestError):
        raise ApiError(exc.http_status, str(exc)) from exc
    if isinstance(exc, (SelectorError, SelectionError)):
        raise ApiError(422, str(exc)) from exc
    if isinstance(exc, (KnowledgeError, SourceUnavailableError, ProfileUnavailableError)):
        raise ApiError(503, str(exc)) from exc
    if isinstance(exc, ExtractionError):
        raise ApiError(422, str(exc)) from exc


def _sessions_router(
    store: SessionStore, feedback: FeedbackStore, *, ej200: bool, services: ApiServices
) -> APIRouter:
    router = APIRouter()
    base = "/ej200/sessions" if ej200 else "/sessions"
    model = Ej200Session if ej200 else ChatSession
    Sid = Annotated[str, Path(pattern=SESSION_ID.pattern)]

    @router.post(base)
    async def save_session(request: Request, session: Annotated[Any, Body()]) -> dict[str, Any]:
        data = model.model_validate(session).model_dump()
        sso = _identity(request).sso
        if ej200:
            data["track"] = "ej200"
            data["owner"] = sso
        store.save(sso, data["id"], data)
        return {"ok": True, "id": data["id"]}

    @router.get(base)
    async def list_own_sessions(request: Request) -> list[dict[str, Any]]:
        if not ej200:
            raise ApiError(404, "Percorso non trovato.")
        return store.list(_identity(request).sso)

    if not ej200:

        @router.get(f"{base}/{{username}}")
        async def list_sessions(request: Request, username: str) -> list[dict[str, Any]]:
            return store.list(_identity(request).sso)  # {username} non sceglie l'owner

        @router.get(f"{base}/{{username}}/{{session_id}}")
        async def get_civil(request: Request, username: str, session_id: Sid) -> dict[str, Any]:
            found = store.get(_identity(request).sso, session_id)
            if found is None:
                raise ApiError(404, "Sessione non trovata.")
            return found

    else:

        @router.get(f"{base}/{{session_id}}")
        async def get_ej200(request: Request, session_id: Sid) -> dict[str, Any]:
            found = store.get(_identity(request).sso, session_id)
            if found is None:
                raise ApiError(404, "Sessione non trovata.")
            return found

    @router.delete(f"{base}/{{session_id}}")
    async def delete_session(
        request: Request, session_id: Sid, username: str | None = None
    ) -> dict[str, Any]:
        store.delete(_identity(request).sso, session_id)
        return {"ok": True}

    feedback_path = "/ej200/feedback" if ej200 else "/feedback"

    @router.post(feedback_path)
    async def save_feedback(request: Request, body: Annotated[Any, Body()]) -> dict[str, Any]:
        sso = _identity(request).sso
        now = services.clock().isoformat()
        if ej200:
            record = Ej200Feedback.model_validate(body).model_dump()
            identifier = services.new_id()
            timestamp = str(record.get("timestamp") or now)
        else:
            if not isinstance(body, dict):
                raise ApiError(422, "Il feedback deve essere un oggetto JSON.")
            record = {
                "sessionId": body.get("sessionId"),
                "cycleId": body.get("cycleId"),
                "vote": "positive" if body.get("vote") == "up" else "negative",
                "feedbackText": body.get("feedbackText"),
                "timestamp": body.get("timestamp") or now,
                "messageId": body.get("messageId"),
            }
            identifier = str(body.get("messageId") or services.new_id())
            timestamp = str(record["timestamp"])
        record["sso"] = sso
        feedback.save(sso, timestamp, identifier, record)  # un errore di scrittura risale
        return {"ok": True}

    return router


def create_app(services: ApiServices) -> FastAPI:
    app = FastAPI(title="Cycle Validation", docs_url=None, redoc_url=None, openapi_url=None)
    civil_sessions = SessionStore(services.store, CIVIL)
    ej_sessions = SessionStore(services.store, EJ200)
    router = APIRouter(prefix=PREFIX)

    @router.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "code": 200}

    @router.get("/flow/start")
    async def flow_start(session_id: str | None = Query(None)) -> dict[str, str]:
        _check_session_id(session_id)
        return {"message": DR_QUESTION}

    @router.post("/conversation")
    async def conversation(body: ConversationRequest) -> dict[str, Any]:
        has_selectors = bool(body.dr_serial_number) or body.dr_condition not in (None, "", [])
        if body.is_yes is False:
            return {"is_dr": False, "next_message": "Ok. Carica il PDF del ciclo."}
        if has_selectors:
            try:
                parse_selectors(
                    is_dr=True, serial_number=body.dr_serial_number, conditions=body.dr_condition
                )
            except SelectorError as exc:
                raise ApiError(422, str(exc)) from exc
            return {"is_dr": True, "next_message": "Dati DR ricevuti. Carica il PDF del ciclo."}
        return {
            "is_dr": True,
            "next_message": "Indica il serial number e le repair condition del ciclo DR.",
        }

    @router.post("/upload")
    async def upload(
        file: Annotated[UploadFile, File()],
        is_dr: Annotated[str, Form()],
        dr_serial_number: Annotated[str | None, Form()] = None,
        dr_condition: Annotated[str | None, Form()] = None,
        session_id: str | None = Query(None),
    ) -> dict[str, Any]:
        _check_session_id(session_id)
        data = await _read_pdf(file, services.config.max_upload_bytes)
        dr = _parse_bool(is_dr)
        try:
            selectors = parse_selectors(
                is_dr=dr, serial_number=dr_serial_number, conditions=dr_condition
            )
        except SelectorError as exc:
            raise ApiError(422, str(exc)) from exc
        request = RunRequest(
            pdf_bytes=data, pdf_name=file.filename or "ciclo.pdf", selectors=selectors
        )
        try:
            report = await services.runner.run("dr" if dr else "mos", request)
        except (IngestError, SelectorError, KnowledgeError, ProfileUnavailableError) as exc:
            _raise_for(exc)
            raise
        except Exception as exc:  # il sistema attuale risponde 200 con state: failed
            return _failed(services, exc)
        return _envelope(services, report, request.pdf_name)

    @router.get("/validation/options")
    async def validation_options() -> dict[str, Any]:
        return selection_options(military_enabled=services.config.ej200_enabled)

    @router.post("/validation/upload")
    async def validation_upload(
        request: Request,
        file: Annotated[UploadFile, File()],
        domain: Annotated[str | None, Form()] = None,
        civil_type: Annotated[str | None, Form()] = None,
        dr_serial_number: Annotated[str | None, Form()] = None,
        dr_condition: Annotated[str | None, Form()] = None,
        session_id: str | None = Query(None),
    ) -> dict[str, Any]:
        """Caricamento con la scelta iniziale: civile (MOS o DR) oppure militare (EJ200).
        La scelta e i selettori si controllano prima di leggere il file."""
        _check_session_id(session_id)
        try:
            profile = resolve_profile(domain, civil_type)
            selectors = parse_selectors(
                is_dr=profile == "dr", serial_number=dr_serial_number, conditions=dr_condition
            )
        except (SelectionError, SelectorError) as exc:
            raise ApiError(422, str(exc)) from exc
        military = profile == MILITARY_PROFILE
        if military and not _identity(request).services & {SERVICE_EJ200, SERVICE_ALL}:
            raise ApiError(403, "Permesso insufficiente per i cicli militari.")
        if military and not services.config.ej200_enabled:
            raise ApiError(501, "La validazione dei cicli militari è disabilitata.")
        data = await _read_pdf(file, services.config.max_upload_bytes)
        run = RunRequest(pdf_bytes=data, pdf_name=file.filename or "ciclo.pdf", selectors=selectors)
        try:
            report = await services.runner.run(profile, run)
        except Exception as exc:
            if military or isinstance(
                exc, (IngestError, SelectorError, KnowledgeError, ProfileUnavailableError)
            ):
                _raise_for(exc)
                raise
            return _failed(services, exc)  # come il civile storico: 200 con state: failed
        envelope = _envelope(services, report, run.pdf_name)
        if military:
            envelope["job_id"] = services.new_id()
            envelope["finished_at"] = services.clock().astimezone(UTC).isoformat()
        return envelope

    router.include_router(
        _sessions_router(
            civil_sessions, FeedbackStore(services.store, CIVIL), ej200=False, services=services
        )
    )

    @router.get("/ej200/flow/start")
    async def ej200_flow_start(session_id: str | None = Query(None)) -> dict[str, str]:
        _check_session_id(session_id)
        return {"message": EJ200_START}

    @router.post("/ej200/upload")
    async def ej200_upload(
        file: Annotated[UploadFile, File()], session_id: str | None = Query(None)
    ) -> dict[str, Any]:
        if not services.config.ej200_enabled:
            raise ApiError(501, "La validazione EJ200 è disabilitata.")
        _check_session_id(session_id)
        data = await _read_pdf(file, services.config.max_upload_bytes)
        request = RunRequest(pdf_bytes=data, pdf_name=file.filename or "ciclo.pdf")
        try:
            report = await services.runner.run("ej200", request)
        except Exception as exc:
            _raise_for(exc)
            raise
        envelope = _envelope(services, report, request.pdf_name)
        envelope["job_id"] = services.new_id()
        envelope["finished_at"] = services.clock().astimezone(UTC).isoformat()
        return envelope

    router.include_router(
        _sessions_router(
            ej_sessions, FeedbackStore(services.store, EJ200), ej200=True, services=services
        )
    )
    app.include_router(router)

    app.add_middleware(AuthMiddleware, backend=services.auth)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[services.config.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _error(exc.status, exc.message)

    @app.exception_handler(SourceUnavailableError)
    async def unavailable(request: Request, exc: SourceUnavailableError) -> JSONResponse:
        return _error(503, str(exc))

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(part) for part in first.get("loc", ()))
        return _error(422, f"Richiesta non valida ({where}): {first.get('msg', '')}".strip())

    @app.exception_handler(ValidationError)
    async def invalid_model(request: Request, exc: ValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(part) for part in first.get("loc", ()))
        return _error(422, f"Richiesta non valida ({where}): {first.get('msg', '')}".strip())

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error(exc.status_code, str(exc.detail))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        if request.url.path.startswith(f"{PREFIX}/ej200") or not services.config.include_traceback:
            return _error(500, "Errore interno.")
        return _error(500, _public_message(exc), traceback=_frames(exc))

    return app
