"""Stadio 6b: regole finali (MG83, 28-11). Deterministiche, nessuna chiamata al modello.

Una regola finale lavora sugli esiti già fatti di un ciclo (per esempio un WARNING del modello
che il codice ha già deciso su quella operazione) e li cambia. Gira dopo tutti i controlli, nella
pipeline e nel servizio. Siccome usa solo quello che c'è nel `report.json`, si può **rigiocare**
sulle prove già fatte (`eval rigioca`, 0 $): si vede subito quanti WARNING toglie e se dà un
falso OK, sulle stesse risposte del modello delle prove di riferimento.

Le regole si accendono per nome con `agent.final_rules` (una variante per regola)."""

import re
from collections.abc import Callable, Sequence
from decimal import Decimal

from cycle_validation.checks.base import make_result
from cycle_validation.checks.languages import (
    extreme_word,
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


# MG87b: la parola di limite della riga citata, al massimo così lontana da un numero in comune
_NEAR = 25


def _quote_extreme(quote: str, shared: set[Decimal]) -> str | None:
    """`max` o `min` se la riga citata ha una sola delle due parole, vicina a un numero che c'è
    anche nella descrizione; altrimenti None."""
    kinds = {kind for lang in ("en", "it") if (kind := extreme_word(quote, lang))}
    if len(kinds) != 1:
        return None
    kind = next(iter(kinds))
    for match in _NUMBER_IN_QUOTE.finditer(quote):
        if Decimal(match.group().replace(",", ".")) not in shared:
            continue
        around = quote[max(0, match.start() - _NEAR) : match.end() + _NEAR]
        if extreme_word(around, "en") == kind or extreme_word(around, "it") == kind:
            return kind
    return None


def limit_word_against_quote(cycle: Cycle, results: list[CheckResult]) -> list[CheckResult]:
    """MG87b (28-11, passo 4l): il modello dice CORRETTO, ma la descrizione dice «massimo» (in
    tutte e due le lingue, e nessun «minimo») e la riga del manuale che lui stesso cita dice
    «minimum» vicino a un numero che c'è anche nella descrizione (o il contrario). La forma del
    falso OK di 9ccfacac 030: «... MASSIMO ...» / «... MAXIMUM ...» senza un numero vicino, la
    riga citata «... a minimum of 99 ...»; per questo `limite_contro_citazione`, che guarda il
    verso sul numero, non scattava."""
    out: list[CheckResult] = []
    names = {"max": "massimo", "min": "minimo"}
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
        description = cycle.operations[index].operation_description
        blocks = language_blocks(description)
        mine = None
        if blocks is not None:
            italian, english = extreme_word(blocks[0], "it"), extreme_word(blocks[1], "en")
            mine = italian if italian is not None and italian == english else None
        shared_values = values_in(description)
        quoted = next(
            (
                kind
                for evidence in result.evidence
                if (kind := _quote_extreme(evidence.quote, shared_values)) is not None
            ),
            None,
        )
        if mine is None or quoted is None or quoted == mine:
            out.append(result)
            continue
        out.append(
            make_result(
                result.check,
                result.target,
                Reason.LIMITE_CONTRO_CITAZIONE,
                f"La descrizione dice «{names[mine]}» in tutte e due le lingue, la riga del "
                f"manuale citata dice «{names[quoted]}» vicino a un numero della descrizione: "
                f"il limite al contrario. (Il modello aveva detto: {result.rationale})",
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

    common = limited & numbers
    described_way = {way for value in common for way in described[value]}

    def yes(flag: bool) -> str:
        return "sì" if flag else "no"

    return (
        f"citazioni {len(quotes)} · limite letto nella descrizione {yes(bool(limited))} · "
        f"stesso numero nella riga citata {yes(bool(common))} · parole di limite "
        f"nella riga {yes(any(has_limit_word(q) for q in quotes))} · verso letto vicino al "
        f"numero {', '.join(sorted(near)) or 'nessuno'} · verso nella descrizione sullo "
        f"stesso numero {', '.join(sorted(described_way)) or 'nessuno'}"
    )


# Le parole che restano leggibili nella «forma» di un testo: limiti e negazioni, generiche.
_KEPT_WORDS = frozenset(
    [
        "al",
        "massimo",
        "massima",
        "massimi",
        "massime",
        "minimo",
        "minima",
        "minimi",
        "minime",
        "max",
        "min",
        "maximum",
        "minimum",
        "almeno",
        "at",
        "most",
        "least",
        "non",
        "not",
        "no",
        "oltre",
        "sopra",
        "sotto",
        "fino",
        "up",
        "to",
        "less",
        "more",
        "than",
        "above",
        "below",
        "over",
        "under",
        "superiore",
        "superiori",
        "inferiore",
        "inferiori",
        "exceed",
        "exceeds",
        "exceeding",
        "meno",
        "più",
        "di",
        "a",
        "mm",
    ]
)
_WORD_OR_DIGIT = re.compile(r"[^\W\d_]+|\d")
# le parole che scambia la copia cieca «limite invertito» (evaluation/blind.py)
_SWAPPED = re.compile(
    r"(?<![\w.])(?:al massimo|almeno|massimo|minimo|at most|at least|maximum|minimum|max|min)"
    r"(?!\w)",
    re.IGNORECASE,
)


def text_shape(text: str, start: int, end: int, width: int = 30) -> str:
    """La «forma» del testo intorno a [start, end): lettere → x, cifre → 9; restano leggibili
    solo le parole di limite e di negazione. Niente codici né parole del manuale (va a schermo)."""

    def mask(match: re.Match[str]) -> str:
        word = match.group()
        if word.isdigit():
            return "9"
        return word if word.casefold() in _KEPT_WORDS else "x" * len(word)

    window = text[max(0, start - width) : end + width]
    return " ".join(_WORD_OR_DIGIT.sub(mask, window).split())


def _shape_at_limit(text: str) -> str:
    match = _SWAPPED.search(text)
    return text_shape(text, match.start(), match.end()) if match else "nessuna parola di limite"


def quote_shapes(cycle: Cycle, results: Sequence[CheckResult], op: str) -> str:
    """MG87, secondo giro (28-11): la forma della descrizione intorno alla prima parola di
    limite, per lingua (è quella che scambia la copia cieca), e della riga citata intorno al
    numero in comune. Così si vede se il limite scambiato sta vicino a un numero."""
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
    description = cycle.operations[result.target.index].operation_description
    blocks = language_blocks(description)
    parts = [("it", blocks[0]), ("en", blocks[1])] if blocks else [("testo", description)]
    shapes = [f"{name} «{_shape_at_limit(text)}»" for name, text in parts]
    described = _description_ways(description)
    for number, evidence in enumerate(result.evidence[:2], start=1):
        quote = evidence.quote
        hit = next(
            (
                m
                for m in _NUMBER_IN_QUOTE.finditer(quote)
                if Decimal(m.group().replace(",", ".")) in described
            ),
            None,
        )
        shape = text_shape(quote, hit.start(), hit.end()) if hit else _shape_at_limit(quote)
        shapes.append(f"riga {number} «{shape}»")
    return " · ".join(shapes)


_NUMBER_IN_QUOTE = re.compile(r"(?<![\w.,/-])\d+(?:[.,]\d+)?(?![\w/-]|[.,]\d)")


# nome → regola, in `agent.final_rules` (una variante per regola).
RULES: dict[str, FinalRule] = {
    "fonte_assente_una_volta": once_missing_source,
    "limite_contro_citazione": limit_against_quote,
    "parola_limite_contro_citazione": limit_word_against_quote,
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
