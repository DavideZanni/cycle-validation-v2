"""Stadio 6b: regole finali (MG83, 28-11). Deterministiche, nessuna chiamata al modello.

Una regola finale lavora sugli esiti già fatti di un ciclo (per esempio un WARNING del modello
che il codice ha già deciso su quella operazione) e li cambia. Gira dopo tutti i controlli, nella
pipeline e nel servizio. Siccome usa solo quello che c'è nel `report.json`, si può **rigiocare**
sulle prove già fatte (`eval rigioca`, 0 $): si vede subito quanti WARNING toglie e se dà un
falso OK, sulle stesse risposte del modello delle prove di riferimento.

Le regole si accendono per nome con `agent.final_rules` (una variante per regola)."""

from collections.abc import Callable, Sequence
from decimal import Decimal

from cycle_validation.checks.base import make_result
from cycle_validation.checks.languages import (
    has_limit_word,
    language_blocks,
    limit_ways,
    values_in,
)
from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Reason,
    TargetKind,
    Verdict,
)
from cycle_validation.domain.cycle import Cycle
from cycle_validation.domain.report import Report
from cycle_validation.errors import ConfigError
from cycle_validation.verdict.consolidate import compute_counts

FinalRule = Callable[[Cycle, list[CheckResult]], list[CheckResult]]


def once_missing_source(cycle: Cycle, results: list[CheckResult]) -> list[CheckResult]:
    """MG83 (28-11): la fonte assente si dice una volta sola. Sul grande di `quasi_finale` due
    cicli veri con il manuale fuori dalla conoscenza davano un WARNING FONTE_ASSENTE per ogni
    operazione (16 e 21), più quelli dei task code sulle stesse operazioni: 4,5 WARNING per
    ciclo su 8,9. Resta un WARNING per ogni avviso diverso, con l'elenco delle operazioni; le
    altre righe diventano NON_APPLICABILE GIA_SEGNALATO e dicono dove guardare. Si uniscono
    i FONTE_ASSENTE della stessa operazione (controlli diversi) e quelli con la stessa
    spiegazione dello stesso controllo (operazioni diverse)."""
    out: list[CheckResult] = []
    by_op: dict[int, int] = {}
    by_text: dict[tuple[CheckName, str], int] = {}
    joined: dict[int, list[CheckResult]] = {}
    for result in results:
        index = result.target.index
        missing = result.reason is Reason.FONTE_ASSENTE
        if not missing or result.target.kind is not TargetKind.OPERATION or index is None:
            out.append(result)
            continue
        key = (result.check, result.rationale)
        first = by_op.get(index, by_text.get(key))
        by_op.setdefault(index, len(out) if first is None else first)
        by_text.setdefault(key, len(out) if first is None else first)
        if first is None:
            out.append(result)
            continue
        kept = out[first]
        joined.setdefault(first, []).append(result)
        out.append(
            make_result(
                result.check,
                result.target,
                Reason.GIA_SEGNALATO,
                f"Fonte assente, già nell'avviso dell'operazione {kept.target.label} "
                f"({kept.check}): {result.rationale}",
                usage=result.usage,
            )
        )
    for position, others in joined.items():
        kept = out[position]
        labels = sorted({o.target.label for o in others if o.target != kept.target})
        extra = sorted({o.rationale for o in others} - {kept.rationale})
        text = kept.rationale
        if labels:
            text += f" Stesso avviso anche per le operazioni {', '.join(labels)}."
        if extra:
            text += " Sulle stesse operazioni: " + " ".join(extra)
        out[position] = kept.model_copy(update={"rationale": text})
    return out


_WAY = {"giù": "al massimo", "su": "almeno"}


def _description_ways(description: str) -> dict[Decimal, set[str]]:
    """Valore → versi del limite nella descrizione, le due lingue insieme."""
    blocks = language_blocks(description)
    if blocks is None:
        return limit_ways(description, after=True)
    ways = limit_ways(blocks[0], "it", after=True)
    for value, found in limit_ways(blocks[1], "en", after=True).items():
        ways.setdefault(value, set()).update(found)
    return ways


def limit_against_quote(cycle: Cycle, results: list[CheckResult]) -> list[CheckResult]:
    """MG87 (28-11): il modello dice CORRETTO, ma la riga del manuale che lui stesso cita dà lo
    stesso valore con il limite al contrario («al massimo» contro «almeno»). Sulle prove di
    `quasi_finale` un limite invertito in tutte e due le lingue (copia cieca) usciva CORRETTO
    VERIFICATO: un falso OK a prova. Conta solo un valore con un verso solo nella descrizione
    (le due lingue d'accordo) e un verso solo nella riga citata."""
    out: list[CheckResult] = []
    for result in results:
        index = result.target.index
        if (
            result.check is not CheckName.OPERATION_DESCRIPTION
            or result.verdict is not Verdict.CORRETTO
            or index is None
            or not 0 <= index < len(cycle.operations)
        ):
            out.append(result)
            continue
        described = _description_ways(cycle.operations[index].operation_description)
        found: tuple[Decimal, str, str] | None = None
        for evidence in result.evidence:
            for value, ways in limit_ways(evidence.quote, after=True).items():
                mine = described.get(value, set())
                if len(mine) == 1 and len(ways) == 1 and mine != ways:
                    found = (value, next(iter(mine)), next(iter(ways)))
                    break
            if found:
                break
        if found is None:
            out.append(result)
            continue
        value, mine_way, quoted_way = found
        out.append(
            make_result(
                result.check,
                result.target,
                Reason.LIMITE_CONTRO_CITAZIONE,
                f"La descrizione dice {_WAY[mine_way]} {value}, la riga del manuale citata "
                f"dice {_WAY[quoted_way]} {value}: lo stesso limite al contrario. "
                f"(Il modello aveva detto: {result.rationale})",
                evidence=result.evidence,
                usage=result.usage,
            )
        )
    return out


def quote_diagnosis(cycle: Cycle, results: Sequence[CheckResult], op: str) -> str:
    """MG87, perché la regola non scatta: che cosa c'è nella riga citata dal modello per il
    CORRETTO della descrizione su `op`. Solo sì/no e conteggi, mai il testo (va a schermo)."""
    result = next(
        (
            r
            for r in results
            if r.check is CheckName.OPERATION_DESCRIPTION
            and r.verdict is Verdict.CORRETTO
            and r.target.label == op
            and r.target.index is not None
            and 0 <= r.target.index < len(cycle.operations)
        ),
        None,
    )
    if result is None or result.target.index is None:
        return "nessun CORRETTO della descrizione"
    described = _description_ways(cycle.operations[result.target.index].operation_description)
    limited = {value for value, ways in described.items() if len(ways) == 1}
    quotes = [e.quote for e in result.evidence]
    numbers = set().union(*(values_in(q) for q in quotes)) if quotes else set()
    near = {
        way
        for q in quotes
        for value, ways in limit_ways(q, after=True).items()
        if value in limited
        for way in ways
    }

    def yes(flag: bool) -> str:
        return "sì" if flag else "no"

    return (
        f"citazioni {len(quotes)} · limite letto nella descrizione {yes(bool(limited))} · "
        f"stesso numero nella riga citata {yes(bool(limited & numbers))} · parole di limite "
        f"nella riga {yes(any(has_limit_word(q) for q in quotes))} · verso letto vicino al "
        f"numero {', '.join(sorted(near)) or 'nessuno'}"
    )


# nome → regola, in `agent.final_rules` (una variante per regola).
RULES: dict[str, FinalRule] = {
    "fonte_assente_una_volta": once_missing_source,
    "limite_contro_citazione": limit_against_quote,
}


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
