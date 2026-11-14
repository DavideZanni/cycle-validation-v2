"""Controllo `source`: manuale (o pubblicazione) e task citati esistono nella conoscenza."""

from functools import partial

from cycle_validation.checks.base import CheckContext, evidence_at, guarded, make_result
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.domain.cycle import Source
from cycle_validation.resolve.civil import resolve_document

CHECK = CheckName.SOURCE


def _check_one(ctx: CheckContext, target: Target, source: Source) -> CheckResult:
    resolution = resolve_document(source.manual, ctx.kb, source.issue)
    document = resolution.document
    if resolution.problem is not None or document is None:
        reason = resolution.problem or Reason.FONTE_ASSENTE
        return make_result(CHECK, target, reason, resolution.message)
    by_task = ctx.profile.reference_mode == "task" and source.task is not None
    if not by_task:
        evidence = Evidence(document_key=document.key, version=document.version)
        return make_result(
            CHECK,
            target,
            Reason.VERIFICATO,
            f"Il documento {document.key} è disponibile.",
            evidence=[evidence],
        )
    assert source.task is not None
    location = ctx.kb.find_task(source.manual, source.task)
    if location is None:
        return make_result(
            CHECK,
            target,
            Reason.FONTE_ASSENTE,
            f"Il task {source.task} non è stato trovato nel manuale {document.key}.",
        )
    return make_result(
        CHECK,
        target,
        Reason.VERIFICATO,
        f"Il task {source.task} è presente nel manuale {document.key}.",
        evidence=[evidence_at(location.document, location.line_start)],
    )


def check_sources(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, source in enumerate(ctx.cycle.sources):
        target = Target.source(index, source)
        results.append(guarded(CHECK, target, partial(_check_one, ctx, target, source)))
    return results
