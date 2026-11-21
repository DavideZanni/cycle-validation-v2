"""Stadio 6: consolidamento degli esiti. Deterministico, nessuna chiamata al modello.

Applica la verifica di integrità, propaga i blocchi, conta e dà lo stato del ciclo.
"""

from collections.abc import Collection, Sequence

from cycle_validation.checks.base import make_result
from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Reason,
    Target,
    TargetKind,
    Verdict,
)
from cycle_validation.domain.cycle import Cycle
from cycle_validation.domain.report import Counts, CycleStatus, PipelineError

_PROOF_VERDICTS = (Verdict.CORRETTO, Verdict.ERRATO)
_PARTIAL_REASONS = (Reason.ERRORE_TECNICO, Reason.BUDGET_ESAURITO)


def expected_rows(cycle: Cycle, checks: Collection[CheckName]) -> list[tuple[CheckName, Target]]:
    """Le righe che il report deve avere: un controllo per il suo oggetto (ciclo, fonte, operazione)."""
    rows: list[tuple[CheckName, Target]] = []
    for check in checks:
        if check is CheckName.EXTRACTION_INTEGRITY:
            continue
        if check is CheckName.DR_RECOMMENDATION:
            rows.append((check, Target.cycle()))
        elif check is CheckName.SOURCE:
            rows.extend((check, Target.source(i, s)) for i, s in enumerate(cycle.sources))
        else:
            rows.extend((check, Target.operation(i, o)) for i, o in enumerate(cycle.operations))
    return rows


def apply_integrity(
    results: Sequence[CheckResult], unconfirmed: Collection[tuple[CheckName, TargetKind, int]]
) -> list[CheckResult]:
    """Un esito CORRETTO o ERRATO su un valore non confermato dal PDF non è affidabile."""
    out: list[CheckResult] = []
    for item in results:
        key = (item.check, item.target.kind, item.target.index)
        if item.verdict in _PROOF_VERDICTS and key in unconfirmed:
            out.append(
                make_result(
                    item.check,
                    item.target,
                    Reason.ESTRAZIONE_NON_CONFERMATA,
                    "Il valore estratto non compare nel testo del PDF: esito non affidabile "
                    f"(era {item.verdict.value}: {item.rationale})",
                    usage=item.usage,
                )
            )
        else:
            out.append(item)
    return out


# WARNING di un controllo bloccante che non ferma gli altri: il dubbio è sul ciclo intero e
# gli altri controlli servono proprio a guardarlo (DR `Accept as is`).
_NOT_BLOCKING = (Reason.DR_SENZA_RIPARAZIONE,)


def is_blocking_failure(result: CheckResult) -> bool:
    if result.reason in _NOT_BLOCKING:
        return False
    return result.verdict not in (Verdict.CORRETTO, Verdict.NON_APPLICABILE)


def blocked_results(
    cycle: Cycle, checks: Collection[CheckName], blocked_by: CheckResult
) -> list[CheckResult]:
    """Righe dei controlli che non si sono eseguiti perché un controllo bloccante è fallito."""
    why = f"Controllo non eseguito: il controllo {blocked_by.check.value} è fallito."
    return [
        make_result(check, target, Reason.BLOCCATO_A_MONTE, why)
        for check, target in expected_rows(cycle, checks)
    ]


def compute_counts(results: Sequence[CheckResult]) -> Counts:
    rows = [item for item in results if item.check is not CheckName.EXTRACTION_INTEGRITY]
    tally = {verdict: sum(1 for item in rows if item.verdict is verdict) for verdict in Verdict}
    applicable = len(rows) - tally[Verdict.NON_APPLICABILE]
    wrong = tally[Verdict.ERRATO]
    return Counts(
        total=len(rows),
        corretto=tally[Verdict.CORRETTO],
        warning=tally[Verdict.WARNING],
        errato=wrong,
        non_applicabile=tally[Verdict.NON_APPLICABILE],
        errors_ratio=wrong / applicable if applicable else 0.0,
    )


def cycle_status(
    results: Sequence[CheckResult], *, blocked: bool, pipeline_errors: Sequence[PipelineError]
) -> CycleStatus:
    if blocked:
        return CycleStatus.BLOCCATO
    if pipeline_errors or any(item.reason in _PARTIAL_REASONS for item in results):
        return CycleStatus.PARZIALE
    return CycleStatus.COMPLETO
