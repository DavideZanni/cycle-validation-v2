"""Controllo `dr_recommendation`: il serial number ha una recommendation applicabile.

È un controllo bloccante: se non passa, gli altri controlli del ciclo non partono.
"""

from cycle_validation.checks.base import CheckContext, guarded, make_result
from cycle_validation.checks.uncertainty import describe
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.kb.port import DocumentInfo, DrRecommendation, KnowledgeBase
from cycle_validation.resolve.civil import resolve_document
from cycle_validation.resolve.dr import (
    DrSelectors,
    is_not_applicable,
    match_recommendations,
    without_conditions,
)

CHECK = CheckName.DR_RECOMMENDATION


def _label(recommendation: DrRecommendation) -> str:
    return recommendation.reference or recommendation.serial_number


def applicable_recommendations(
    kb: KnowledgeBase, selectors: DrSelectors | None
) -> list[DrRecommendation]:
    """Recommendation su cui proseguire. Vuota se il controllo DR non passa."""
    if selectors is None:
        return []
    found = kb.find_dr_recommendations(selectors.serial_number)
    if without_conditions(found):
        return []
    matched = match_recommendations(found, selectors.conditions)
    return [] if any(is_not_applicable(item) for item in matched) else matched


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
    stopped = next((item for item in matched if is_not_applicable(item)), None)
    if stopped is not None:
        return make_result(
            CHECK,
            target,
            Reason.DR_NON_APPLICABILE,
            f"La recommendation {_label(stopped)} prevede '{stopped.procedure}': "
            "il ciclo propone riparazioni non applicabili.",
            evidence=evidence,
        )
    names = ", ".join(_label(item) for item in matched)
    # Controllo bloccante: un dubbio sui dati dell'indice non ferma il ciclo, si scrive.
    doubts = sorted({reason for item in matched for reason in item.uncertain})
    return make_result(
        CHECK,
        target,
        Reason.VERIFICATO,
        f"Recommendation applicabile per il serial number {selectors.serial_number}: {names}."
        + describe(doubts),
        evidence=evidence,
    )


def check_dr_recommendation(ctx: CheckContext) -> list[CheckResult]:
    target = Target.cycle()
    return [guarded(CHECK, target, lambda: _check(ctx, target))]
