"""Controllo `dr_recommendation`: il serial number ha una recommendation applicabile.

È un controllo bloccante: se non passa, gli altri controlli del ciclo non partono.

Disposizioni del DR. `Repair`: la riparazione si fa, con i task e la procedura del DR come
contesto delle operazioni. `Reject`: il pezzo si scarta, ERRATO e ciclo bloccato.
`Accept as is`: il pezzo si accetta senza riparazione; il ciclo può avere comunque ispezioni e
registrazioni, quindi WARNING `DR_SENZA_RIPARAZIONE` senza blocco, e la procedura DR (che nei
documenti veri è solo la procedura di riparazione) non fa da contesto: una raccordatura nel
ciclo non deve sembrare giusta perché la procedura la descrive (domanda 17).
"""

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


def applicable_recommendations(
    kb: KnowledgeBase, selectors: DrSelectors | None
) -> list[DrRecommendation]:
    """Recommendation di riparazione su cui proseguire: il contesto delle operazioni.
    Vuota se il controllo DR non passa; senza le `Accept as is`, che non prevedono
    riparazione."""
    if selectors is None:
        return []
    found = kb.find_dr_recommendations(selectors.serial_number)
    if without_conditions(found):
        return []
    matched = match_recommendations(found, selectors.conditions)
    if any(is_reject(item) for item in matched):
        return []
    return [item for item in matched if not is_accept_as_is(item)]


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
    selectors = ctx.selectors
    if selectors is None:
        return make_result(
            CHECK,
            target,
            Reason.ERRORE_TECNICO,
            "Serial number e repair condition mancanti: recommendation non verificabile.",
        )
    conditions = ", ".join(str(value) for value in selectors.conditions)
    found = ctx.kb.find_dr_recommendations(selectors.serial_number)
    if not found:
        return make_result(
            CHECK,
            target,
            Reason.DR_NESSUNA_CORRISPONDENZA,
            f"Nessuna recommendation per il serial number {selectors.serial_number}.",
        )
    unclear = without_conditions(found)
    if unclear:
        names = ", ".join(_label(item) for item in unclear)
        return make_result(
            CHECK,
            target,
            Reason.RIFERIMENTO_AMBIGUO,
            f"Il serial number {selectors.serial_number} ha {len(found)} recommendation e "
            f"{names} non indica le repair condition: non si può scegliere quella giusta, "
            "va controllato a mano.",
            evidence=[
                Evidence(document_key=_label(item), quote=f"{item.procedure} (condition [])")
                for item in unclear
            ],
        )
    matched = match_recommendations(found, selectors.conditions)
    if not matched:
        return make_result(
            CHECK,
            target,
            Reason.DR_NESSUNA_CORRISPONDENZA,
            f"Il serial number {selectors.serial_number} ha {len(found)} recommendation, "
            f"nessuna per le repair condition {conditions}.",
        )
    evidence = [
        Evidence(document_key=_label(item), quote=f"{item.procedure} (condition {item.conditions})")
        for item in matched
    ]
    # Controllo bloccante: un dubbio sui dati dell'indice non ferma il ciclo, si scrive.
    doubts = describe(sorted({reason for item in matched for reason in item.uncertain}))
    stopped = next((item for item in matched if is_reject(item)), None)
    if stopped is not None:
        return make_result(
            CHECK,
            target,
            Reason.DR_NON_APPLICABILE,
            f"La recommendation {_label(stopped)} prevede '{stopped.procedure}': il pezzo va "
            "scartato, il ciclo di riparazione non si applica.",
            evidence=evidence,
        )
    accepted = [item for item in matched if is_accept_as_is(item)]
    repairs = [item for item in matched if not is_accept_as_is(item)]
    if not repairs:
        names = ", ".join(_label(item) for item in accepted)
        return make_result(
            CHECK,
            target,
            Reason.DR_SENZA_RIPARAZIONE,
            f"La recommendation {names} per le repair condition {conditions} prevede "
            f"'{accepted[0].procedure}': il pezzo si accetta senza riparazione. Da controllare "
            "a mano che il ciclo non contenga le lavorazioni della procedura di riparazione "
            "(per esempio raccordatura o attacco chimico); ispezioni e registrazioni possono "
            "restare. Gli altri controlli proseguono senza la procedura DR come riferimento."
            + doubts,
            evidence=evidence,
        )
    names = ", ".join(_label(item) for item in repairs)
    note = ""
    if accepted:
        others = ", ".join(_label(item) for item in accepted)
        note = f" Per {others} la recommendation è '{accepted[0].procedure}': nessuna riparazione."
    return make_result(
        CHECK,
        target,
        Reason.VERIFICATO,
        f"Recommendation applicabile per il serial number {selectors.serial_number}: {names}."
        + note
        + doubts,
        evidence=evidence,
    )


def check_dr_recommendation(ctx: CheckContext) -> list[CheckResult]:
    target = Target.cycle()
    return [guarded(CHECK, target, lambda: _check(ctx, target))]
