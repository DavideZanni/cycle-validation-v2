"""Controllo `operation_description`: la descrizione dell'operazione è coerente con il
testo di riferimento. È l'unico controllo che usa il modello.

Il codice trova il dove (documenti e righe), l'agente confronta, il codice verifica le
citazioni e assegna l'esito. Un giudizio senza citazione verificata non diventa mai
né CORRETTO né ERRATO. Una contraddizione si rifà `confirm_contradiction` volte: resta
ERRATO solo se la ritrovano tutte (il modello, sullo stesso testo, può oscillare).
"""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import ValidationError

from cycle_validation.agent.prompt import (
    Judgement,
    OperationJudgement,
    build_operation_prompt,
    judgement_schema,
)
from cycle_validation.agent.runner import run_sessions
from cycle_validation.agent.session import (
    AgentSession,
    SessionOutcome,
    SessionRequest,
    SessionStatus,
)
from cycle_validation.checks.base import CheckContext, make_result
from cycle_validation.checks.dr_recommendation import dr_documents, dr_tasks
from cycle_validation.checks.languages import language_parts, number_mismatches
from cycle_validation.checks.process_sheet import engine_family, treatment_for_family
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Evidence,
    Reason,
    Target,
    TargetKind,
)
from cycle_validation.domain.cycle import Operation
from cycle_validation.domain.report import PipelineError
from cycle_validation.errors import SourceUnavailableError
from cycle_validation.kb.port import DocumentInfo, TaskLocation
from cycle_validation.resolve.civil import (
    cited_documents,
    context_locations,
    resolve_operation,
    whole_document,
)
from cycle_validation.verdict.citations import verify_citation

CHECK = CheckName.OPERATION_DESCRIPTION
STAGE = "operation_description"


@dataclass(frozen=True)
class OperationJob:
    index: int
    operation: Operation
    locations: tuple[TaskLocation, ...]
    request: SessionRequest

    @property
    def target(self) -> Target:
        return Target.operation(self.index, self.operation)

    @property
    def documents(self) -> list[DocumentInfo]:
        return list({item.document.key: item.document for item in self.locations}.values())


def _facts(ctx: CheckContext, operation: Operation) -> list[str]:
    """Fatti che il codice ha già risolto e che l'agente non deve cercare."""
    facts: list[str] = [
        f"Il ciclo cita {source.manual}, {source.section}."
        for source in ctx.cycle.sources
        if source.section
    ]
    try:
        if operation.machine_tag is not None:
            tag = ctx.kb.find_machine_tag(operation.machine_tag)
            if tag is not None and tag.function:
                facts.append(f"Macchina {tag.tag}: {tag.function}")
        if operation.process_sheet is not None:
            sheet = ctx.kb.find_process_sheet(operation.process_sheet.code)
            family = engine_family(ctx.cycle.engine_model, ctx.profile.engine_families)
            treatment = treatment_for_family(sheet.treatment, family) if sheet else None
            if sheet is not None and treatment:
                facts.append(f"Scheda {sheet.code}: {treatment}")
    except SourceUnavailableError:
        return facts
    return facts


def _locations(ctx: CheckContext, operation: Operation) -> tuple[TaskLocation, ...]:
    if ctx.profile.reference_mode == "document":
        documents = cited_documents(ctx.cycle, ctx.kb, ctx.profile.document_order)
        return tuple(whole_document(document) for document in documents)
    return context_locations(
        ctx.cycle,
        operation,
        ctx.kb,
        extra_tasks=dr_tasks(ctx.kb, ctx.selectors),
        extra_documents=dr_documents(ctx.kb, ctx.selectors),
    )


def _missing_tasks(ctx: CheckContext, operation: Operation, settings: AgentSettings) -> list[str]:
    """I task citati, se nessuno è nel manuale e il testo viene dalle fonti del ciclo. Si
    cercano solo se servono: per la nota al modello (A2) o per saltarlo (B6)."""
    wanted = settings.missing_task_note or settings.skip_missing_task
    if not wanted or ctx.profile.reference_mode == "document":
        return []
    if not operation.task_codes or resolve_operation(ctx.cycle, operation, ctx.kb).found:
        return []
    return list(operation.task_codes)


def plan_operation_checks(
    ctx: CheckContext, settings: AgentSettings, system_prompt: str
) -> tuple[list[OperationJob], list[CheckResult]]:
    """Decide per ogni operazione se serve una sessione e come costruirla."""
    jobs: list[OperationJob] = []
    immediate: list[CheckResult] = []
    schema = judgement_schema()
    for index, operation in enumerate(ctx.cycle.operations):
        target = Target.operation(index, operation)
        if not operation.operation_description:
            immediate.append(
                make_result(CHECK, target, Reason.CAMPO_ASSENTE, "Descrizione assente.")
            )
            continue
        if (CHECK, TargetKind.OPERATION, index) in ctx.unconfirmed:
            # il giudizio verrebbe comunque declassato: non si spende una sessione
            immediate.append(
                make_result(
                    CHECK,
                    target,
                    Reason.ESTRAZIONE_NON_CONFERMATA,
                    "La descrizione estratta non è confermata dal testo del PDF: "
                    "confronto con i documenti non eseguito.",
                )
            )
            continue
        if mismatches := number_mismatches(operation.operation_description):
            # una delle due lingue è sbagliata: si vede senza manuale e senza modello
            pairs = ", ".join(f"{a} → {b}" for a, b in mismatches)
            immediate.append(
                make_result(
                    CHECK,
                    target,
                    Reason.INCOERENZA_LINGUE,
                    "La descrizione italiana e quella inglese non dicono gli stessi numeri "
                    f"(italiano → inglese: {pairs}): una delle due è sbagliata.",
                )
            )
            continue
        try:
            locations = _locations(ctx, operation)
            missing_tasks = _missing_tasks(ctx, operation, settings)
        except SourceUnavailableError as exc:
            immediate.append(
                make_result(CHECK, target, Reason.ERRORE_TECNICO, f"Controllo non eseguito: {exc}")
            )
            continue
        if missing_tasks and settings.skip_missing_task:
            immediate.append(
                make_result(
                    CHECK,
                    target,
                    Reason.FONTE_ASSENTE,
                    f"I task citati ({', '.join(missing_tasks)}) non sono nel manuale: "
                    "descrizione non confrontata.",
                )
            )
            continue
        if not locations:
            immediate.append(
                make_result(
                    CHECK,
                    target,
                    Reason.FONTE_ASSENTE,
                    "Nessun riferimento dell'operazione è disponibile nella knowledge base: "
                    "descrizione non verificata.",
                )
            )
            continue
        inline = sum(item.n_lines for item in locations) <= settings.inline_max_lines
        prompt = build_operation_prompt(
            ctx.cycle,
            operation,
            _facts(ctx, operation),
            locations,
            inline=inline,
            settings=settings,
            missing_tasks=missing_tasks,
            languages=(
                language_parts(operation.operation_description)
                if settings.separate_languages
                else None
            ),
        )
        request = SessionRequest(
            session_id=f"op-{index:03d}-{operation.operation_number}",
            system_prompt=system_prompt,
            prompt=prompt,
            output_schema=schema,
            use_tools=not inline,
            allowed_files=tuple({item.document.path for item in locations}),
            max_turns=settings.inline_max_turns if inline else settings.max_turns,
        )
        jobs.append(OperationJob(index, operation, locations, request))
    return jobs, immediate


def _failure(
    job: OperationJob, outcome: SessionOutcome
) -> tuple[CheckResult, PipelineError | None]:
    if outcome.status is SessionStatus.MAX_TURNS:
        result = make_result(
            CHECK,
            job.target,
            Reason.BUDGET_ESAURITO,
            "La verifica non si è conclusa entro il numero massimo di passi.",
            decided_by="agent",
            usage=outcome.usage,
        )
        return result, None
    result = make_result(
        CHECK,
        job.target,
        Reason.ERRORE_TECNICO,
        "Controllo non eseguito per un errore tecnico: descrizione non verificata.",
        decided_by="agent",
        usage=outcome.usage,
    )
    detail = f"{outcome.status.value} dopo {outcome.attempts} tentativi: {outcome.error}"
    return result, PipelineError(stage=STAGE, target=job.target.label, message=detail)


def decide_operation(
    job: OperationJob, outcome: SessionOutcome, settings: AgentSettings
) -> tuple[CheckResult, PipelineError | None]:
    """Dal giudizio dell'agente all'esito: decide il codice, sulle citazioni verificate."""
    if outcome.status is not SessionStatus.OK or outcome.output is None:
        return _failure(job, outcome)
    try:
        judgement = OperationJudgement.model_validate(outcome.output)
    except ValidationError:
        invalid = outcome.model_copy(update={"status": SessionStatus.INVALID_OUTPUT})
        return _failure(job, invalid)

    evidence: list[Evidence] = []
    for citation in judgement.citations:
        try:
            verified = verify_citation(citation, job.documents, settings.citation_window)
        except SourceUnavailableError:
            verified = None
        if verified is not None and verified not in evidence:
            evidence.append(verified)

    if judgement.judgement is Judgement.NON_VERIFICABILE:
        reason = Reason.EVIDENZA_NON_TROVATA
        rationale = judgement.rationale
    elif not evidence:
        reason = Reason.CITAZIONE_NON_VERIFICATA
        rationale = (
            f"L'agente ha giudicato la descrizione '{judgement.judgement.value}', ma nessuna "
            f"citazione è stata ritrovata nei documenti. Motivazione: {judgement.rationale}"
        )
    elif judgement.judgement is Judgement.CONTRADDETTO:
        reason = Reason.CONTRADDIZIONE
        rationale = judgement.rationale
    else:
        reason = Reason.VERIFICATO
        rationale = judgement.rationale
    result = make_result(
        CHECK,
        job.target,
        reason,
        rationale,
        evidence=evidence,
        decided_by="agent",
        usage=outcome.usage,
    )
    return result, None


_DISAGREE = (Reason.VERIFICATO, Reason.EVIDENZA_NON_TROVATA, Reason.CITAZIONE_NON_VERIFICATA)


def confirm_contradiction(first: CheckResult, confirmations: Sequence[CheckResult]) -> CheckResult:
    """Un ERRATO resta tale solo se ogni verifica di conferma ritrova la contraddizione.
    Se una la smentisce: WARNING GIUDIZIO_INSTABILE, da guardare a mano. Se una conferma
    non si è potuta fare (guasto) e nessuna smentisce: WARNING per errore tecnico."""
    usage = first.usage
    for item in confirmations:
        usage = usage + item.usage
    if all(item.reason is Reason.CONTRADDIZIONE for item in confirmations):
        evidence = list(first.evidence)
        for item in confirmations:
            evidence += [proof for proof in item.evidence if proof not in evidence]
        return first.model_copy(update={"usage": usage, "evidence": tuple(evidence)})
    found = 1 + sum(1 for item in confirmations if item.reason is Reason.CONTRADDIZIONE)
    others = " ".join(
        f"Verifica {number}: {item.reason.value}. {item.rationale}"
        for number, item in enumerate(confirmations, start=2)
    )
    disagree = any(item.reason in _DISAGREE for item in confirmations)
    reason = Reason.GIUDIZIO_INSTABILE if disagree else Reason.ERRORE_TECNICO
    lead = (
        f"Giudizio non stabile: contraddizione ritrovata in {found} verifiche su "
        f"{1 + len(confirmations)}, da controllare a mano."
        if disagree
        else "Contraddizione non confermata per un errore tecnico, da controllare a mano."
    )
    rationale = f"{lead} Verifica 1: CONTRADDIZIONE. {first.rationale} {others}"
    return make_result(
        CHECK,
        first.target,
        reason,
        rationale,
        evidence=first.evidence,
        decided_by="agent",
        usage=usage,
    )


async def _run(
    session: AgentSession, requests: Sequence[SessionRequest], settings: AgentSettings
) -> Sequence[SessionOutcome]:
    return await run_sessions(
        session,
        requests,
        concurrency=settings.concurrency,
        retries=settings.retries,
        backoff_s=settings.retry_backoff_s,
        invalid_output_retries=settings.invalid_output_retries,
        validate=OperationJudgement.model_validate,
        timeout_s=settings.session_timeout_s,
    )


async def check_operations(
    ctx: CheckContext,
    session: AgentSession,
    settings: AgentSettings,
    system_prompt: str,
    stats: dict[str, int] | None = None,
) -> tuple[list[CheckResult], list[PipelineError]]:
    """`stats`, se dato, riceve il numero di sessioni "inline" e "search" pianificate e,
    se ce ne sono, quelle di "conferma" delle contraddizioni."""
    # La pianificazione interroga la knowledge base (rete, file): fuori dal loop degli eventi,
    # che nel servizio è lo stesso di tutte le altre richieste.
    jobs, results = await asyncio.to_thread(plan_operation_checks, ctx, settings, system_prompt)
    if stats is not None:
        stats["inline"] = sum(1 for job in jobs if not job.request.use_tools)
        stats["search"] = sum(1 for job in jobs if job.request.use_tools)
    outcomes = await _run(session, [job.request for job in jobs], settings)
    decided = [
        decide_operation(job, outcome, settings)
        for job, outcome in zip(jobs, outcomes, strict=True)
    ]
    errors = [error for _, error in decided if error is not None]

    repeats = settings.confirm_contradiction
    doubtful = [
        i for i, (result, _) in enumerate(decided) if result.reason is Reason.CONTRADDIZIONE
    ]
    if repeats and doubtful:
        requests = [
            jobs[i].request.model_copy(
                update={"session_id": f"{jobs[i].request.session_id}-conferma-{k}"}
            )
            for i in doubtful
            for k in range(1, repeats + 1)
        ]
        if stats is not None:
            stats["conferma"] = len(requests)
        confirmations = await _run(session, requests, settings)
        for n, i in enumerate(doubtful):
            checked = [
                decide_operation(jobs[i], outcome, settings)
                for outcome in confirmations[n * repeats : (n + 1) * repeats]
            ]
            errors += [error for _, error in checked if error is not None]
            decided[i] = (confirm_contradiction(decided[i][0], [r for r, _ in checked]), None)

    results += [result for result, _ in decided]
    results.sort(key=lambda item: item.target.index or 0)
    return results, errors
