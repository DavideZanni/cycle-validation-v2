"""Stadio 6b: regole finali (MG83, 28-11). Deterministiche, nessuna chiamata al modello.

Una regola finale lavora sugli esiti già fatti di un ciclo (per esempio un WARNING del modello
che il codice ha già deciso su quella operazione) e li cambia. Gira dopo tutti i controlli, nella
pipeline e nel servizio. Siccome usa solo quello che c'è nel `report.json`, si può **rigiocare**
sulle prove già fatte (`eval rigioca`, 0 $): si vede subito quanti WARNING toglie e se dà un
falso OK, sulle stesse risposte del modello delle prove di riferimento.

Le regole si accendono per nome con `agent.final_rules` (una variante per regola)."""

from collections.abc import Callable, Sequence

from cycle_validation.domain.check import CheckName, CheckResult
from cycle_validation.domain.cycle import Cycle
from cycle_validation.domain.report import Report
from cycle_validation.errors import ConfigError
from cycle_validation.verdict.consolidate import compute_counts

FinalRule = Callable[[Cycle, list[CheckResult]], list[CheckResult]]

# nome → regola. Le regole arrivano con MG83 (dopo la tabella «WARNING per operazione»).
RULES: dict[str, FinalRule] = {}


def check_rule_names(names: Sequence[str]) -> None:
    unknown = [name for name in names if name not in RULES]
    if unknown:
        known = ", ".join(sorted(RULES)) or "nessuna"
        raise ConfigError(f"Regole finali sconosciute: {', '.join(unknown)} (ci sono: {known}).")


def apply_final_rules(
    cycle: Cycle, results: Sequence[CheckResult], names: Sequence[str]
) -> list[CheckResult]:
    """Le regole `names`, in ordine. Le righe della verifica di integrità non si toccano."""
    if not names:
        return list(results)
    check_rule_names(names)
    integrity = [r for r in results if r.check is CheckName.EXTRACTION_INTEGRITY]
    out = [r for r in results if r.check is not CheckName.EXTRACTION_INTEGRITY]
    for name in names:
        out = RULES[name](cycle, out)
    return [*integrity, *out]


def replay_report(report: Report, names: Sequence[str]) -> Report:
    """Il report come sarebbe uscito con le regole `names` in più (`eval rigioca`)."""
    results = apply_final_rules(report.cycle, report.results, names)
    return report.model_copy(update={"results": results, "counts": compute_counts(results)})
