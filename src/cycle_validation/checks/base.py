"""Mattoni comuni dei controlli: contesto, costruzione degli esiti, guasti delle sorgenti."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from cycle_validation.config import ProfileConfig
from cycle_validation.domain.check import (
    REASON_VERDICT,
    CheckName,
    CheckResult,
    Evidence,
    Reason,
    Target,
    TargetKind,
    Usage,
)
from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import SourceUnavailableError
from cycle_validation.kb.documents import page_at, read_lines
from cycle_validation.kb.port import DocumentInfo, KnowledgeBase
from cycle_validation.resolve.dr import DrSelectors
from cycle_validation.services.machines import MachineRegistry


@dataclass(frozen=True)
class CheckContext:
    cycle: Cycle
    kb: KnowledgeBase
    machines: MachineRegistry
    profile: ProfileConfig
    selectors: DrSelectors | None = None
    # Valori estratti che il PDF non conferma (controllo, tipo di oggetto, indice): un
    # controllo può evitare lavoro il cui esito verrebbe comunque declassato.
    unconfirmed: frozenset[tuple[CheckName, TargetKind, int]] = frozenset()


def make_result(
    check: CheckName,
    target: Target,
    reason: Reason,
    rationale: str,
    *,
    evidence: Sequence[Evidence] = (),
    decided_by: Literal["code", "agent"] = "code",
    usage: Usage | None = None,
) -> CheckResult:
    """L'esito discende dal motivo: non si può costruire una coppia incoerente."""
    return CheckResult(
        check=check,
        target=target,
        verdict=REASON_VERDICT[reason],
        reason=reason,
        rationale=rationale,
        evidence=tuple(evidence),
        decided_by=decided_by,
        usage=usage or Usage(),
    )


def evidence_at(document: DocumentInfo, line: int) -> Evidence:
    lines = read_lines(document.path)
    quote = lines[line - 1].strip() if 1 <= line <= len(lines) else ""
    return Evidence(
        document_key=document.key,
        version=document.version,
        page=page_at(document.path, line),
        line=line,
        quote=quote,
    )


def guarded(check: CheckName, target: Target, decide: Callable[[], CheckResult]) -> CheckResult:
    """Una sorgente che non risponde non è un errore del ciclo: diventa un warning."""
    try:
        return decide()
    except SourceUnavailableError as exc:
        return make_result(check, target, Reason.ERRORE_TECNICO, f"Controllo non eseguito: {exc}")
