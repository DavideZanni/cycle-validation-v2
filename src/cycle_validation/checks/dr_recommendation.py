"""Controllo `dr_recommendation`: il serial number ha una recommendation di riparazione.

È un controllo bloccante: se fallisce, gli altri controlli del ciclo non partono.

Le regole (confermate dall'utente il 22-11-2026, come nella v1):

- `Repair`: la riparazione si fa. CORRETTO, e i task e la procedura del DR fanno da
  riferimento per le operazioni.
- `Reject` (il pezzo si scarta) o `Accept as is` (il pezzo va bene così): un ciclo di
  riparazione non dovrebbe esistere. ERRATO e ciclo bloccato.
- `Repair` e `Accept as is` per condition diverse richieste insieme: si salta la parte
  `Accept as is` e si prosegue con la `Repair`.

Serial number e condition sono facoltativi. Senza serial number (né dato né scritto nella
stampa), o senza la condition quando serve per scegliere, WARNING `DR_NON_VERIFICATA`: gli
altri controlli proseguono e la recommendation si guarda a mano.
"""

from dataclasses import dataclass, field

from cycle_validation.checks.base import CheckContext, guarded, make_result
from cycle_validation.checks.uncertainty import describe
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.kb.port import DocumentInfo, DrRecommendation, KnowledgeBase
from cycle_validation.resolve.civil import resolve_document
from cycle_validation.resolve.dr import (
    DrSelectors,
    is_accept_as_is,
    is_reject,
    match_recommendations,
    without_conditions,
)

CHECK = CheckName.DR_RECOMMENDATION


def _label(recommendation: DrRecommendation) -> str:
    return recommendation.reference or recommendation.serial_number


def _is_repair(recommendation: DrRecommendation) -> bool:
    return not is_reject(recommendation) and not is_accept_as_is(recommendation)


def _show(item: DrRecommendation) -> str:
    return f"{_label(item)} ({item.procedure}, condition {list(item.conditions)})"


@dataclass(frozen=True)
class _Decision:
    reason: Reason
    text: str
    shown: list[DrRecommendation] = field(default_factory=list)
    # recommendation di riparazione che fanno da riferimento per le operazioni
    context: list[DrRecommendation] = field(default_factory=list)


def _decide(kb: KnowledgeBase, selectors: DrSelectors | None) -> _Decision:
    if selectors is None or not selectors.serial_number:
        return _Decision(
            Reason.DR_NON_VERIFICATA,
            "Serial number non indicato e non scritto nella stampa: recommendation DR non "
            "verificata, da guardare a mano. Gli altri controlli proseguono senza la "
            "procedura DR come riferimento.",
        )
    serial = selectors.serial_number
    found = kb.find_dr_recommendations(serial)
    if not found:
        return _Decision(
            Reason.DR_NESSUNA_CORRISPONDENZA,
            f"Nessuna recommendation per il serial number {serial}.",
        )
    unclear = without_conditions(found)
    if unclear:
        names = ", ".join(_label(item) for item in unclear)
        return _Decision(
            Reason.RIFERIMENTO_AMBIGUO,
            f"Il serial number {serial} ha {len(found)} recommendation e {names} non indica le "
            "repair condition: non si può scegliere quella giusta, va controllato a mano.",
            unclear,
        )
    if not selectors.conditions and len(found) > 1:
        return _without_condition(serial, found)
    conditions = ", ".join(str(value) for value in selectors.conditions)
    matched = match_recommendations(found, selectors.conditions)
    if not matched:
        return _Decision(
            Reason.DR_NESSUNA_CORRISPONDENZA,
            f"Il serial number {serial} ha {len(found)} recommendation, nessuna per le repair "
            f"condition {conditions}.",
        )
    return _with_matches(serial, matched)


def _not_applicable(item: DrRecommendation) -> str:
    what = "va scartato" if is_reject(item) else "si accetta così com'è"
    return (
        f"La recommendation {_label(item)} prevede '{item.procedure}': il pezzo {what}, "
        "quindi un ciclo di riparazione non dovrebbe esistere."
    )


def _with_matches(serial: str, matched: list[DrRecommendation]) -> _Decision:
    rejected = next((item for item in matched if is_reject(item)), None)
    if rejected is not None:
        return _Decision(Reason.DR_NON_APPLICABILE, _not_applicable(rejected), matched)
    repairs = [item for item in matched if _is_repair(item)]
    if not repairs:
        return _Decision(Reason.DR_NON_APPLICABILE, _not_applicable(matched[0]), matched)
    names = ", ".join(_label(item) for item in repairs)
    text = f"Recommendation di riparazione per il serial number {serial}: {names}."
    accepted = [item for item in matched if is_accept_as_is(item)]
    if accepted:
        others = ", ".join(_show(item) for item in accepted)
        text += f" Saltata la parte senza riparazione: {others}."
    return _Decision(Reason.VERIFICATO, text, matched, repairs)


def _without_condition(serial: str, found: list[DrRecommendation]) -> _Decision:
    """Più recommendation e nessuna condition indicata."""
    repairs = [item for item in found if _is_repair(item)]
    listing = "; ".join(_show(item) for item in found)
    if len(repairs) == len(found):
        names = ", ".join(_label(item) for item in repairs)
        return _Decision(
            Reason.VERIFICATO,
            f"Condition non indicata: il serial number {serial} ha {len(found)} recommendation, "
            f"tutte di riparazione ({names}). Valgono tutte come riferimento.",
            found,
            repairs,
        )
    if not repairs:
        return _Decision(Reason.DR_NON_APPLICABILE, _not_applicable(found[0]), found)
    return _Decision(
        Reason.DR_NON_VERIFICATA,
        f"Condition non indicata e il serial number {serial} ha recommendation diverse: "
        f"{listing}. Non si sa se il pezzo va riparato: da guardare a mano (oppure indicare "
        "la condition). Gli altri controlli proseguono con le recommendation di riparazione "
        "come riferimento.",
        found,
        repairs,
    )


def applicable_recommendations(
    kb: KnowledgeBase, selectors: DrSelectors | None
) -> list[DrRecommendation]:
    """Recommendation di riparazione che fanno da riferimento per le operazioni. Vuota se il
    controllo DR non passa."""
    return _decide(kb, selectors).context


def dr_tasks(kb: KnowledgeBase, selectors: DrSelectors | None) -> list[tuple[str | None, str]]:
    """Coppie (manuale, task) indicate dalle recommendation: contesto per le operazioni.
    Manuale `None` quando la DR non ne ha uno affidabile (l'indice toglie quello
    contraddetto dai task): il task si cerca allora nei manuali citati dal ciclo."""
    return [
        (item.manual, task)
        for item in applicable_recommendations(kb, selectors)
        for task in item.tasks
    ]


# Tipo del documento della procedura DR nel manifest dell'indice.
DR_PROCEDURE_KIND = "DR_PROC"


def dr_documents(kb: KnowledgeBase, selectors: DrSelectors | None) -> list[DocumentInfo]:
    """Procedure DR indicate dalle recommendation applicabili, intere: il contesto quando
    nessun task si trova (la procedura spesso non ha task con codice). La procedura si cerca
    con il manuale della recommendation e, se manca, con il codice del DR (`reference`):
    l'indice lascia il manuale vuoto quando i task non lo indicano. Solo documenti di tipo
    procedura DR: un manuale intero sarebbe troppo grande e poco mirato."""
    out: dict[str, DocumentInfo] = {}
    for item in applicable_recommendations(kb, selectors):
        for name in (item.manual, item.reference):
            if not name or not name.strip():
                continue
            document = resolve_document(name, kb).document
            if document is not None and (document.kind or "").upper() == DR_PROCEDURE_KIND:
                out.setdefault(document.key, document)
                break
    return list(out.values())


def _check(ctx: CheckContext, target: Target) -> CheckResult:
    decision = _decide(ctx.kb, ctx.selectors)
    # Controllo bloccante: un dubbio sui dati dell'indice non ferma il ciclo, si scrive.
    doubts = describe(sorted({reason for item in decision.shown for reason in item.uncertain}))
    evidence = [
        Evidence(document_key=_label(item), quote=f"{item.procedure} (condition {item.conditions})")
        for item in decision.shown
    ]
    return make_result(CHECK, target, decision.reason, decision.text + doubts, evidence=evidence)


def check_dr_recommendation(ctx: CheckContext) -> list[CheckResult]:
    target = Target.cycle()
    return [guarded(CHECK, target, lambda: _check(ctx, target))]
