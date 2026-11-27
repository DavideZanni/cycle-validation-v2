"""Adattatore tra AgentSession e Claude Agent SDK. Unico modulo che importa l'SDK.

Ogni sessione è isolata: nessuna impostazione dell'utente, nessun server MCP, nessun
tool oltre a Read e Grep, e solo sui file ammessi per quella sessione. Le credenziali
AWS non passano da qui: l'SDK usa quelle dell'ambiente (ruolo, profilo, variabili).
"""

import dataclasses
import json
import os
import re
import time
from pathlib import Path
from typing import Any, cast

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ProcessError, ResultMessage, query
from claude_agent_sdk.types import HookCallback

from cycle_validation.agent.hooks import ALLOWED_TOOLS, ToolPolicy, make_pre_tool_use_hook
from cycle_validation.agent.session import SessionOutcome, SessionRequest, SessionStatus
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import Usage

_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def usage_from_result(result: ResultMessage) -> Usage:
    raw = result.usage or {}
    return Usage(
        input_tokens=int(raw.get("input_tokens") or 0),
        output_tokens=int(raw.get("output_tokens") or 0),
        cache_read_tokens=int(raw.get("cache_read_input_tokens") or 0),
        cache_write_tokens=int(raw.get("cache_creation_input_tokens") or 0),
        cost_usd=float(result.total_cost_usd or 0.0),
        duration_ms=int(result.duration_ms or 0),
        api_duration_ms=int(result.duration_api_ms or 0),
        turns=int(result.num_turns or 0),
        sessions=1,
    )


def _is_max_turns(subtype: object, terminal_reason: object) -> bool:
    return subtype == "error_max_turns" or terminal_reason == "max_turns"


def _error_detail(subtype: object, terminal_reason: object, status: object) -> str:
    """Che cosa è fallito, dai soli campi che non portano contenuto. `result` ed `errors`
    possono contenere testo del modello o del processo e non si copiano: stanno nel transcript."""
    detail = str(subtype or "errore")
    if terminal_reason:
        detail = f"{detail} ({terminal_reason})"
    return detail if status is None else f"HTTP {status}: {detail}"


def outcome_from_process_error(error: ProcessError) -> SessionOutcome:
    """Il processo è uscito con errore senza consegnare un risultato. Un `ResultError`
    (SDK ≥ 0.2.181) porta sottotipo, motivo e codice HTTP; altrimenti resta il codice d'uscita."""
    subtype = getattr(error, "subtype", None)
    terminal_reason = getattr(error, "terminal_reason", None)
    if _is_max_turns(subtype, terminal_reason):
        return SessionOutcome(status=SessionStatus.MAX_TURNS)
    if subtype is not None:
        detail = _error_detail(subtype, terminal_reason, getattr(error, "api_error_status", None))
    else:
        detail = type(error).__name__
        if error.exit_code is not None:
            detail = f"{detail} (exit code {error.exit_code})"
    return SessionOutcome(status=SessionStatus.ERROR, error=detail)


def outcome_from_result(result: ResultMessage | None) -> SessionOutcome:
    """Traduce il messaggio finale dell'SDK nell'esito della sessione."""
    if result is None:
        return SessionOutcome(
            status=SessionStatus.ERROR, error="La sessione è terminata senza un risultato."
        )
    usage = usage_from_result(result)
    terminal_reason = getattr(result, "terminal_reason", None)
    if _is_max_turns(result.subtype, terminal_reason):
        return SessionOutcome(status=SessionStatus.MAX_TURNS, usage=usage)
    if result.is_error:
        detail = _error_detail(
            result.subtype, terminal_reason, getattr(result, "api_error_status", None)
        )
        return SessionOutcome(status=SessionStatus.ERROR, usage=usage, error=detail)
    output = getattr(result, "structured_output", None)
    if not isinstance(output, dict):
        return SessionOutcome(
            status=SessionStatus.INVALID_OUTPUT,
            usage=usage,
            error="La sessione non ha restituito un output strutturato.",
        )
    return SessionOutcome(status=SessionStatus.OK, output=output, usage=usage)


def _to_jsonable(message: object) -> dict[str, Any]:
    if dataclasses.is_dataclass(message) and not isinstance(message, type):
        body = dataclasses.asdict(message)
    else:
        body = {"repr": repr(message)}
    return {"type": type(message).__name__, **body}


class SdkAgentSession:
    """Una sessione del Claude Agent SDK per richiesta."""

    def __init__(self, settings: AgentSettings, transcripts_dir: Path | None = None) -> None:
        self._settings = settings
        self._transcripts_dir = transcripts_dir if settings.save_transcripts else None

    def _environment(self) -> dict[str, str]:
        env: dict[str, str] = {}
        if self._settings.use_bedrock:
            env["CLAUDE_CODE_USE_BEDROCK"] = "1"
        if self._settings.aws_region:
            env["AWS_REGION"] = self._settings.aws_region
        return env

    def build_options(self, request: SessionRequest) -> ClaudeAgentOptions:
        settings = self._settings
        files = list(request.allowed_files)
        # i tool solo con dei file ammessi: senza, mancherebbe l'hook che limita Read e Grep a
        # quei file (27-11, revisione del codice; oggi ogni sessione con i tool ha dei file)
        tools = list(ALLOWED_TOOLS) if request.use_tools and files else []
        cwd = Path(os.path.commonpath([str(path.parent) for path in files])) if files else None
        hooks: dict[str, list[HookMatcher]] = {}
        if request.use_tools and cwd is not None:
            policy = ToolPolicy.for_files(
                files,
                cwd,
                read_limit=settings.read_limit,
                read_window=settings.read_window,
                read_before=settings.read_before,
                grep_max_context=settings.grep_max_context,
            )
            hook = make_pre_tool_use_hook(policy)
            hooks = {"PreToolUse": [HookMatcher(hooks=[cast(HookCallback, hook)])]}
        options = ClaudeAgentOptions(
            tools=tools,
            allowed_tools=tools,
            system_prompt=request.system_prompt,
            model=settings.model,
            max_turns=request.max_turns,
            cwd=cwd,
            permission_mode="dontAsk",
            setting_sources=[],
            strict_mcp_config=True,
            hooks=cast(Any, hooks) or None,
            output_format={"type": "json_schema", "schema": request.output_schema},
            env=self._environment(),
            # niente chat salvate in ~/.claude/projects: ogni sessione è usa e getta e i testi
            # dei manuali non restano sul disco (si vedrebbero tra le chat di Claude in VS Code)
            extra_args={"no-session-persistence": None},
        )
        effort = request.effort or settings.effort
        if effort is not None:
            options.effort = effort
        return options

    async def run(self, request: SessionRequest) -> SessionOutcome:
        began = time.perf_counter()
        outcome = await self._run(request)
        wall_ms = int((time.perf_counter() - began) * 1000)
        return outcome.model_copy(
            update={"usage": outcome.usage.model_copy(update={"wall_ms": wall_ms})}
        )

    async def _run(self, request: SessionRequest) -> SessionOutcome:
        result: ResultMessage | None = None
        transcript = None
        if self._transcripts_dir is not None:
            self._transcripts_dir.mkdir(parents=True, exist_ok=True)
            name = _UNSAFE.sub("_", request.session_id)
            transcript = (self._transcripts_dir / f"{name}.jsonl").open("a", encoding="utf-8")
        try:
            async for message in query(prompt=request.prompt, options=self.build_options(request)):
                if transcript is not None:
                    line = json.dumps(_to_jsonable(message), ensure_ascii=False, default=str)
                    transcript.write(line + "\n")
                if isinstance(message, ResultMessage):
                    result = message
        except ProcessError as error:
            # Dopo un risultato d'errore il processo esce con codice non nullo e l'SDK solleva:
            # il risultato già ricevuto (esito e consumi) vale più dell'eccezione.
            if result is None:
                return outcome_from_process_error(error)
        finally:
            if transcript is not None:
                transcript.close()
        return outcome_from_result(result)
