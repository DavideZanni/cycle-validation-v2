"""Hook PreToolUse: impone la lettura a paragrafo (GRASP) e confina l'agente nei file
ammessi per la sua sessione.

GRASP: dopo un Grep che restituisce `file:riga`, si legge solo una finestra attorno
alla riga, mai il file intero. Qui la regola non è un consiglio nel prompt: una Read
senza `limit`, o con `limit` oltre soglia, viene rifiutata con le istruzioni per rifarla.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeGuard

ALLOWED_TOOLS = ("Read", "Grep")
# Tool interno con cui l'SDK consegna l'output strutturato (`output_format`): non legge
# nulla, ma passa anch'esso dall'hook. Se lo si rifiuta la sessione non può rispondere.
OUTPUT_TOOL = "StructuredOutput"
_GREP_CONTEXT_KEYS = ("-A", "-B", "-C", "context")

PreToolUseHook = Callable[[Any, str | None, Any], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolPolicy:
    allowed_files: frozenset[Path]
    base_dir: Path
    read_limit: int = 40
    read_window: int = 30
    read_before: int = 15
    grep_max_context: int = 10

    @classmethod
    def for_files(cls, files: list[Path], base_dir: Path, **limits: int) -> "ToolPolicy":
        return cls(frozenset(path.resolve() for path in files), base_dir.resolve(), **limits)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""


_ALLOW = Decision(allowed=True)


def _deny(reason: str) -> Decision:
    return Decision(allowed=False, reason=reason)


def _is_positive_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _resolve(raw: object, policy: ToolPolicy) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw)
    resolved = (path if path.is_absolute() else policy.base_dir / path).resolve()
    return resolved if resolved in policy.allowed_files else None


def _files_hint(policy: ToolPolicy) -> str:
    names = ", ".join(sorted(path.name for path in policy.allowed_files))
    return f"File ammessi in questa sessione: {names}."


def _check_read(tool_input: dict[str, Any], policy: ToolPolicy) -> Decision:
    if _resolve(tool_input.get("file_path"), policy) is None:
        return _deny(f"Puoi leggere solo i file indicati nel messaggio. {_files_hint(policy)}")
    limit = tool_input.get("limit")
    if not _is_positive_int(limit) or limit > policy.read_limit:
        return _deny(
            "Lettura del file intero vietata (regola GRASP). Richiama Read con "
            f"offset = riga_del_match - {policy.read_before} e limit = {policy.read_window} "
            f"(massimo {policy.read_limit})."
        )
    return _ALLOW


def _check_grep(tool_input: dict[str, Any], policy: ToolPolicy) -> Decision:
    if _resolve(tool_input.get("path"), policy) is None:
        return _deny(
            "Grep va eseguito su un singolo file ammesso: imposta `path` al percorso "
            f"completo del file. {_files_hint(policy)}"
        )
    for key in _GREP_CONTEXT_KEYS:
        value = tool_input.get(key)
        if isinstance(value, int) and value > policy.grep_max_context:
            return _deny(
                f"Contesto del Grep troppo ampio: al massimo {policy.grep_max_context} righe. "
                "Per leggere di più usa Read con offset e limit."
            )
    return _ALLOW


def check_tool_call(tool_name: str, tool_input: dict[str, Any], policy: ToolPolicy) -> Decision:
    """Decide se una chiamata tool dell'agente è ammessa. Funzione pura."""
    if tool_name == "Read":
        return _check_read(tool_input, policy)
    if tool_name == "Grep":
        return _check_grep(tool_input, policy)
    if tool_name == OUTPUT_TOOL:
        return _ALLOW
    return _deny(f"Tool '{tool_name}' non consentito. Usa solo Read e Grep.")


def make_pre_tool_use_hook(policy: ToolPolicy) -> PreToolUseHook:
    """Adatta check_tool_call al formato degli hook del Claude Agent SDK."""

    async def hook(input_data: Any, tool_use_id: str | None, context: Any) -> dict[str, Any]:
        decision = check_tool_call(
            input_data["tool_name"], input_data.get("tool_input") or {}, policy
        )
        if decision.allowed:
            return {}
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }

    return hook
