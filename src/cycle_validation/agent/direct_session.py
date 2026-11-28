"""Sessione diretta su Bedrock (MG54, 28-11): l'SDK `anthropic` chiama il modello senza avviare
Claude Code per ogni sessione. Stesso contratto di `SdkAgentSession` (una richiesta, un esito).

- Read e Grep li esegue questo modulo, solo sui file ammessi e con le stesse regole dell'hook
  (`hooks.check_tool_call`: lettura a paragrafo, niente file interi).
- La risposta arriva con lo strumento `StructuredOutput` (schema = `output_schema`), come fa
  Claude Code: il modello lo chiama per consegnare il giudizio.
- Il costo si calcola dai token con i prezzi delle impostazioni (`AgentSettings.direct_*`).
- MG56 (`direct_cache`): punti di cache sul testo fisso (istruzioni, strumenti) e sulla storia
  della sessione, così i turni dopo il primo pagano la storia un decimo. MG59
  (`SessionRequest.shared_context`): il testo di riferimento in un blocco a sé, prima della
  domanda, con un punto di cache: le operazioni che citano lo stesso task lo pagano una volta.

Le credenziali AWS non passano da qui: si usano quelle dell'ambiente.

Il trasporto (28-11, dopo la prima prova sul PC: `APIConnectionError` con il client HTTP
dell'SDK) è predefinito su **boto3** (`agent.direct_transport`): `invoke_model` di
`bedrock-runtime`, con la stessa rete (proxy, certificati con `AWS_CA_BUNDLE`, credenziali) che
sul PC già funziona per S3. Il corpo è quello della Messages API, come lo manda l'SDK per
Bedrock. `httpx` resta: il client `AsyncAnthropicBedrock` dell'SDK, con il certificato di
`AWS_CA_BUNDLE` se c'è.
"""

import asyncio
import json
import os
import re
import ssl
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from cycle_validation.agent.hooks import OUTPUT_TOOL, ToolPolicy, check_tool_call
from cycle_validation.agent.session import SessionOutcome, SessionRequest, SessionStatus
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import Usage
from cycle_validation.kb.documents import read_lines

_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")
# Righe al massimo in una risposta di Grep: oltre, il modello deve cercare meglio.
GREP_MAX_MATCHES = 40
MAX_TOKENS = 8000
ANSWER_NOTE = (
    f"Quando hai deciso, consegna la risposta chiamando lo strumento `{OUTPUT_TOOL}`: è l'unico "
    "modo di rispondere."
)
REMINDER = f"Rispondi adesso chiamando lo strumento `{OUTPUT_TOOL}` con l'oggetto richiesto."

READ_TOOL: dict[str, Any] = {
    "name": "Read",
    "description": (
        "Legge alcune righe di un file ammesso. `offset` è la prima riga (da 1), `limit` quante "
        "righe. Ogni riga esce con il suo numero: `numero: testo`."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "percorso completo del file"},
            "offset": {"type": "integer", "minimum": 1},
            "limit": {"type": "integer", "minimum": 1},
        },
        "required": ["file_path", "offset", "limit"],
    },
}
GREP_TOOL: dict[str, Any] = {
    "name": "Grep",
    "description": (
        "Cerca un'espressione regolare in un file ammesso. Restituisce le righe trovate con il "
        "loro numero (`numero: testo`). `-i` ignora maiuscole e minuscole; `-C` aggiunge righe "
        "di contesto prima e dopo."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string", "description": "percorso completo del file"},
            "-i": {"type": "boolean"},
            "-C": {"type": "integer", "minimum": 0},
        },
        "required": ["pattern", "path"],
    },
}


def price_of(usage: Usage, settings: AgentSettings) -> float:
    """Il costo in dollari dei token, con i prezzi delle impostazioni (per milione)."""
    per_million = 1_000_000
    return (
        usage.input_tokens * settings.direct_input_price
        + usage.output_tokens * settings.direct_output_price
        + usage.cache_write_tokens * settings.direct_input_price * 1.25
        + usage.cache_read_tokens * settings.direct_input_price * 0.1
    ) / per_million


def run_read(tool_input: dict[str, Any], policy: ToolPolicy) -> str:
    path = Path(str(tool_input["file_path"]))
    resolved = (path if path.is_absolute() else policy.base_dir / path).resolve()
    lines = read_lines(resolved)
    first = max(int(tool_input.get("offset") or 1), 1)
    last = min(first + int(tool_input["limit"]) - 1, len(lines))
    if first > len(lines):
        return f"Il file ha solo {len(lines)} righe."
    return "\n".join(f"{n}: {lines[n - 1]}" for n in range(first, last + 1))


def run_grep(tool_input: dict[str, Any], policy: ToolPolicy) -> str:
    path = Path(str(tool_input["path"]))
    resolved = (path if path.is_absolute() else policy.base_dir / path).resolve()
    flags = re.IGNORECASE if tool_input.get("-i") else 0
    try:
        pattern = re.compile(str(tool_input["pattern"]), flags)
    except re.error as exc:
        raise ValueError(f"Espressione regolare non valida: {exc}") from exc
    lines = read_lines(resolved)
    context = max(int(tool_input.get("-C") or 0), 0)
    hits = [n for n, line in enumerate(lines, start=1) if pattern.search(line)]
    if not hits:
        return "Nessuna riga trovata."
    shown: list[int] = []
    for n in hits[:GREP_MAX_MATCHES]:
        for m in range(max(n - context, 1), min(n + context, len(lines)) + 1):
            if not shown or shown[-1] < m:
                shown.append(m)
    text = "\n".join(f"{n}: {lines[n - 1]}" for n in shown)
    if len(hits) > GREP_MAX_MATCHES:
        text += (
            f"\n(altre {len(hits) - GREP_MAX_MATCHES} righe: cerca con un'espressione più precisa)"
        )
    return text


def _usage_of(raw: Any) -> Usage:
    return Usage(
        input_tokens=int(getattr(raw, "input_tokens", 0) or 0),
        output_tokens=int(getattr(raw, "output_tokens", 0) or 0),
        cache_read_tokens=int(getattr(raw, "cache_read_input_tokens", 0) or 0),
        cache_write_tokens=int(getattr(raw, "cache_creation_input_tokens", 0) or 0),
    )


def _cached(block: dict[str, Any]) -> dict[str, Any]:
    return {**block, "cache_control": {"type": "ephemeral"}}


def _block_dict(block: Any) -> dict[str, Any]:
    """Un blocco della risposta come dizionario, da rimandare uguale (pensiero compreso)."""
    if isinstance(block, dict):
        return block
    dumped: dict[str, Any] = block.model_dump(mode="json", exclude_none=True)
    return dumped


ClientFactory = Callable[[AgentSettings], Any]


BEDROCK_VERSION = "bedrock-2023-05-31"
_BOTO_CLIENTS: dict[tuple[str | None, float | None, int], Any] = {}
_BOTO_LOCK = threading.Lock()


def _boto_client(settings: AgentSettings) -> Any:
    """Un client `bedrock-runtime` per processo (i client di boto3 si possono usare da più
    thread; crearne uno per sessione costa)."""
    key = (settings.aws_region, settings.session_timeout_s, settings.concurrency)
    with _BOTO_LOCK:
        if key not in _BOTO_CLIENTS:
            import boto3
            from botocore.config import Config

            config = Config(
                # i nuovi tentativi li fa già `agent/runner.py`
                retries={"max_attempts": 1, "mode": "standard"},
                read_timeout=int(settings.session_timeout_s or 300),
                connect_timeout=20,
                max_pool_connections=max(10, 2 * settings.concurrency),
            )
            _BOTO_CLIENTS[key] = boto3.client(
                "bedrock-runtime", region_name=settings.aws_region, config=config
            )
        return _BOTO_CLIENTS[key]


def _plain(value: Any) -> Any:
    """I blocchi dell'SDK (pydantic) come JSON, solo i campi arrivati dal servizio."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_unset=True)
    raise TypeError(type(value).__name__)


class BotoBedrockClient:
    """Lo stesso `messages.create` del client dell'SDK, ma con `invoke_model` di boto3."""

    def __init__(self, settings: AgentSettings, boto_client: Any | None = None) -> None:
        self._client = boto_client if boto_client is not None else _boto_client(settings)
        self.messages = self

    async def create(self, **kwargs: Any) -> Any:
        from anthropic.types import Message

        model = kwargs.pop("model")
        body = json.dumps({"anthropic_version": BEDROCK_VERSION, **kwargs}, default=_plain)
        raw = await asyncio.to_thread(
            self._client.invoke_model,
            modelId=model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        data = await asyncio.to_thread(raw["body"].read)
        return Message.model_validate(json.loads(data))

    async def close(self) -> None:
        return None  # il client di boto3 resta per le sessioni dopo


def _ca_context() -> ssl.SSLContext | None:
    """Il certificato del filtro di rete, se l'ambiente lo dà (COPILOT.md, riga Zscaler)."""
    for name in ("AWS_CA_BUNDLE", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        path = os.environ.get(name)
        if path and os.path.isfile(path):
            return ssl.create_default_context(cafile=path)
    return None


def default_client(settings: AgentSettings) -> Any:
    if settings.direct_transport == "boto3":
        return BotoBedrockClient(settings)
    from anthropic import AsyncAnthropicBedrock, DefaultAsyncHttpxClient

    context = _ca_context()
    http_client = DefaultAsyncHttpxClient(verify=context) if context is not None else None
    # i nuovi tentativi li fa già `agent/runner.py`: qui nessuno, per non raddoppiare l'attesa
    return AsyncAnthropicBedrock(
        aws_region=settings.aws_region, max_retries=0, http_client=http_client
    )


# Parole del messaggio di un errore di rete → una causa da mostrare. Del messaggio non si
# mostra niente (può contenere indirizzi, account o testo del ciclo): solo tipi e codici.
_CAUSES = (
    (("certificate", "ssl"), "certificato (filtro di rete?)"),
    (("expired", "sso", "token"), "accesso AWS scaduto?"),
    (("credential",), "credenziali AWS"),
    (("timed out", "timeout"), "tempo scaduto"),
    (("proxy",), "proxy"),
    (("getaddrinfo", "name or service", "nodename", "name resolution"), "nome del servizio"),
    (("refused",), "connessione rifiutata"),
    (("reset", "closed", "eof"), "connessione chiusa"),
)


def describe_error(exc: BaseException) -> str:
    """Il tipo dell'errore, le sue cause (solo i tipi), il codice di AWS e una causa probabile:
    `APIConnectionError ← ConnectError · certificato (filtro di rete?)`."""
    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and len(chain) < 5:
        chain.append(current)
        current = current.__cause__ or current.__context__
    names = " ← ".join(type(item).__name__ for item in chain)
    code = ""
    for item in chain:
        response = getattr(item, "response", None)
        if isinstance(response, dict):
            code = str(response.get("Error", {}).get("Code", ""))
            if code:
                break
    text = " ".join(str(item) for item in chain).lower()
    # con un codice di AWS il codice basta (per esempio `ExpiredTokenException`)
    cause = (
        ""
        if code
        else next((label for words, label in _CAUSES if any(w in text for w in words)), "")
    )
    return " · ".join(part for part in (names, code, cause) if part)


class DirectBedrockSession:
    """Una sessione per richiesta, con un client per richiesta (il client è legato al loop
    degli eventi in cui nasce: le prove ne aprono uno per ciclo)."""

    def __init__(
        self,
        settings: AgentSettings,
        transcripts_dir: Path | None = None,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._settings = settings
        self._transcripts_dir = transcripts_dir if settings.save_transcripts else None
        # cercato a ogni sessione: i test sostituiscono `default_client`
        self._client_factory = client_factory or (lambda settings: default_client(settings))

    def _model(self) -> str:
        return self._settings.direct_model or self._settings.model

    def _tools(self, request: SessionRequest) -> list[dict[str, Any]]:
        answer = {
            "name": OUTPUT_TOOL,
            "description": "Consegna la risposta finale, con l'oggetto richiesto.",
            "input_schema": request.output_schema,
        }
        tools = [READ_TOOL, GREP_TOOL, answer] if request.use_tools else [answer]
        if self._settings.direct_cache:
            tools[-1] = _cached(tools[-1])
        return tools

    def _system(self, request: SessionRequest) -> list[dict[str, Any]]:
        block = {"type": "text", "text": f"{request.system_prompt}\n\n{ANSWER_NOTE}"}
        return [_cached(block) if self._settings.direct_cache else block]

    def _first_message(self, request: SessionRequest) -> dict[str, Any]:
        content: list[dict[str, Any]] = []
        if request.shared_context:
            shared = {"type": "text", "text": request.shared_context}
            content.append(_cached(shared) if self._settings.direct_cache else shared)
        content.append({"type": "text", "text": request.prompt})
        return {"role": "user", "content": content}

    def _with_history_cache(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Con `direct_cache`, un punto di cache sull'ultimo blocco dell'ultimo messaggio: il
        turno dopo rilegge tutta la storia dalla cache. Al massimo 4 punti per richiesta:
        istruzioni, strumenti, testo comune, storia."""
        if not self._settings.direct_cache or len(messages) < 2:
            return messages
        last = messages[-1]
        content = list(last["content"])
        content[-1] = _cached(content[-1])
        return [*messages[:-1], {**last, "content": content}]

    def _policy(self, request: SessionRequest) -> ToolPolicy | None:
        files = list(request.allowed_files)
        if not request.use_tools or not files:
            return None
        import os

        base = Path(os.path.commonpath([str(path.parent) for path in files]))
        s = self._settings
        return ToolPolicy.for_files(
            files,
            base,
            read_limit=s.read_limit,
            read_window=s.read_window,
            read_before=s.read_before,
            grep_max_context=s.grep_max_context,
        )

    def _run_tool(self, block: dict[str, Any], policy: ToolPolicy | None) -> dict[str, Any]:
        name, tool_input = block["name"], block.get("input") or {}
        result: dict[str, Any] = {"type": "tool_result", "tool_use_id": block["id"]}
        if policy is None:
            return {**result, "content": "Nessun file da leggere.", "is_error": True}
        decision = check_tool_call(name, tool_input, policy)
        if not decision.allowed:
            return {**result, "content": decision.reason, "is_error": True}
        try:
            text = run_read(tool_input, policy) if name == "Read" else run_grep(tool_input, policy)
        except (KeyError, TypeError, ValueError, OSError) as exc:
            return {**result, "content": f"Richiesta non valida: {exc}", "is_error": True}
        return {**result, "content": text}

    async def run(self, request: SessionRequest) -> SessionOutcome:
        began = time.perf_counter()
        outcome = await self._run(request)
        wall_ms = int((time.perf_counter() - began) * 1000)
        usage = outcome.usage.model_copy(
            update={
                "wall_ms": wall_ms,
                "duration_ms": wall_ms,
                "cost_usd": price_of(outcome.usage, self._settings),
                "sessions": 1,
            }
        )
        return outcome.model_copy(update={"usage": usage})

    async def _run(self, request: SessionRequest) -> SessionOutcome:
        settings = self._settings
        policy = self._policy(request)
        tools = self._tools(request)
        system = self._system(request)
        messages: list[dict[str, Any]] = [self._first_message(request)]
        usage = Usage()
        transcript: list[dict[str, Any]] = []
        effort = request.effort or settings.effort
        extra: dict[str, Any] = {"thinking": {"type": "adaptive"}}
        if effort is not None:
            extra["output_config"] = {"effort": effort}
        client = self._client_factory(settings)
        try:
            for turn in range(1, request.max_turns + 1):
                began = time.perf_counter()
                response = await client.messages.create(
                    model=self._model(),
                    max_tokens=MAX_TOKENS,
                    system=system,
                    tools=tools,
                    messages=self._with_history_cache(messages),
                    **extra,
                )
                api_ms = int((time.perf_counter() - began) * 1000)
                usage = usage + _usage_of(response.usage).model_copy(
                    update={"api_duration_ms": api_ms, "turns": 1}
                )
                blocks = [_block_dict(block) for block in response.content]
                transcript.append({"turno": turn, "risposta": blocks, "stop": response.stop_reason})
                answer = next(
                    (b for b in blocks if b.get("type") == "tool_use" and b["name"] == OUTPUT_TOOL),
                    None,
                )
                if answer is not None:
                    output = answer.get("input")
                    if not isinstance(output, dict):
                        return SessionOutcome(
                            status=SessionStatus.INVALID_OUTPUT,
                            usage=usage,
                            error="Risposta senza un oggetto.",
                        )
                    return SessionOutcome(status=SessionStatus.OK, output=output, usage=usage)
                if response.stop_reason == "refusal":
                    return SessionOutcome(status=SessionStatus.ERROR, usage=usage, error="refusal")
                # i blocchi come sono arrivati (il pensiero va rimandato uguale)
                messages.append({"role": "assistant", "content": list(response.content)})
                calls = [b for b in blocks if b.get("type") == "tool_use"]
                if calls:
                    results = [self._run_tool(call, policy) for call in calls]
                    messages.append({"role": "user", "content": results})
                else:
                    messages.append(
                        {"role": "user", "content": [{"type": "text", "text": REMINDER}]}
                    )
            return SessionOutcome(status=SessionStatus.MAX_TURNS, usage=usage)
        except Exception as exc:
            # solo tipi, codice e causa: il messaggio può riportare testo del ciclo
            return SessionOutcome(
                status=SessionStatus.ERROR, usage=usage, error=describe_error(exc)
            )
        finally:
            close = getattr(client, "close", None)
            if close is not None:
                await close()
            self._save(request, messages, transcript)

    def _save(
        self,
        request: SessionRequest,
        messages: list[dict[str, Any]],
        transcript: list[dict[str, Any]],
    ) -> None:
        if self._transcripts_dir is None:
            return
        self._transcripts_dir.mkdir(parents=True, exist_ok=True)
        name = _UNSAFE.sub("_", request.session_id)
        with (self._transcripts_dir / f"{name}.jsonl").open("a", encoding="utf-8") as out:
            for line in [{"richiesta": messages[0]}, *transcript]:
                out.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
