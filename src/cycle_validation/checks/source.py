"""Controllo `source`: manuale (o pubblicazione) e task citati esistono nella conoscenza."""

from functools import partial

from cycle_validation.checks.base import CheckContext, evidence_at, guarded, make_result
from cycle_validation.checks.uncertainty import describe
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.domain.cycle import Source
from cycle_validation.kb.port import DocumentInfo
from cycle_validation.resolve.civil import (
    cited_section,
    resolve_document,
    section_locations,
    version_key,
)

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
        newer = _newer_issue(ctx, document) if ctx.profile.reference_mode == "document" else None
        if newer is not None:
            return make_result(
                CHECK,
                target,
                Reason.VERSIONE_DIVERSA,
                f"Il ciclo cita la issue {document.version} di {document.code}; è disponibile "
                f"la issue {newer.version}, più recente. Il confronto si fa sulla issue citata.",
                evidence=[evidence],
            )
        return make_result(
            CHECK,
            target,
            Reason.VERIFICATO,
            f"Il documento {document.key} è disponibile.{describe(document.uncertain)}",
            evidence=[evidence],
        )
    assert source.task is not None
    location = ctx.kb.find_task(source.manual, source.task)
    section = cited_section(source.task)
    if location is None and section is not None:
        found = section_locations(ctx.kb, source.manual, section)
        if found:
            keys = ", ".join(dict.fromkeys(item.document.key for item in found))
            return make_result(
                CHECK,
                target,
                Reason.VERIFICATO,
                f"La sezione {section} è presente nel manuale ({keys}).",
                evidence=[evidence_at(found[0].document, found[0].line_start)],
            )
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
        # Il documento del task, non quello scelto come più recente: un manuale diviso in
        # capitoli ha lo stesso codice in più documenti.
        f"Il task {source.task} è presente nel manuale {location.document.key}."
        + describe(location.document.uncertain),
        evidence=[evidence_at(location.document, location.line_start)],
    )


def _newer_issue(ctx: CheckContext, document: DocumentInfo) -> DocumentInfo | None:
    """La issue pubblicata più recente della stessa pubblicazione, se è dopo quella citata.
    Solo per pubblicazioni intere (EJ200): nei manuali civili `version` è il capitolo."""
    if not document.code or document.version is None:
        return None
    issues = [
        other
        for other in ctx.kb.find_manuals(document.code)
        if other.published and other.code == document.code and other.version is not None
    ]
    latest = max(issues, key=version_key, default=None)
    if latest is None or version_key(latest) <= version_key(document):
        return None
    return latest


def check_sources(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, source in enumerate(ctx.cycle.sources):
        target = Target.source(index, source)
        results.append(guarded(CHECK, target, partial(_check_one, ctx, target, source)))
    return results
