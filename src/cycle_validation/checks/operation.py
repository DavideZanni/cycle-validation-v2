"""Controllo `operation_description`: la descrizione dell'operazione è coerente con il
testo di riferimento. È l'unico controllo che usa il modello.

Il codice trova il dove (documenti e righe), l'agente confronta, il codice verifica le
citazioni e assegna l'esito. Un giudizio senza citazione verificata non diventa mai
né CORRETTO né ERRATO. Una contraddizione si rifà `confirm_contradiction` volte: resta
ERRATO solo se la ritrovano tutte (il modello, sullo stesso testo, può oscillare).

Con `agent.compare_languages` (variante `lingue_tra_loro`, 26-11 sera) il modello confronta
anche la parte italiana e quella inglese tra loro, senza manuale: se una dice altro, con le due
citazioni ritrovate nel testo e confermato come gli altri ERRATO, l'operazione è ERRATO
INCOERENZA_LINGUE al posto dell'esito del confronto con il manuale.
"""

import asyncio
import re
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import ValidationError

from cycle_validation.agent.prompt import (
    LANGUAGES_SYSTEM_PROMPT,
    Judgement,
    LanguagesJudgement,
    LanguagesVerdict,
    OperationJudgement,
    build_languages_prompt,
    build_operation_prompt,
    build_strict_languages_prompt,
    judgement_schema,
    languages_schema,
)
from cycle_validation.agent.runner import run_sessions
from cycle_validation.agent.session import (
    AgentSession,
    SessionOutcome,
    SessionRequest,
    SessionStatus,
)
from cycle_validation.checks.base import CheckContext, make_result
from cycle_validation.checks.dr_recommendation import (
    DR_PROCEDURE_KIND,
    dr_documents,
    dr_tasks,
)
from cycle_validation.checks.languages import (
    language_parts,
    number_mismatches,
    strict_difference,
)
from cycle_validation.checks.process_sheet import engine_family, treatment_for_family
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Evidence,
    Reason,
    Target,
    TargetKind,
    Usage,
)
from cycle_validation.domain.cycle import Operation
from cycle_validation.domain.report import PipelineError
from cycle_validation.errors import SourceUnavailableError
from cycle_validation.kb.port import DocumentInfo, TaskLocation
from cycle_validation.resolve.civil import (
    cited_documents,
    context_locations,
    inspection_locations,
    is_inspection_task,
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


@dataclass(frozen=True)
class LanguageJob:
    """Il confronto tra le due lingue di un'operazione (`agent.compare_languages`)."""

    index: int
    italian: str
    english: str
    request: SessionRequest
    # versione stretta (`agent.compare_languages_strict`): vale solo quello che il codice
    # ritrova nelle parole copiate
    strict: bool = False


# esiti dopo i quali il confronto tra le due lingue non serve: le lingue sono già diverse nei
# numeri, oppure la descrizione non c'è o non è sicura
_NO_LANGUAGE_CHECK = (
    Reason.INCOERENZA_LINGUE,
    Reason.CAMPO_ASSENTE,
    Reason.ESTRAZIONE_NON_CONFERMATA,
)


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
        pass  # una sorgente che non risponde: restano i fatti trovati fin qui
    return facts


def _locations(
    ctx: CheckContext, operation: Operation, settings: AgentSettings
) -> tuple[TaskLocation, ...]:
    if ctx.profile.reference_mode == "document":
        documents = cited_documents(ctx.cycle, ctx.kb, ctx.profile.document_order)
        return tuple(whole_document(document) for document in documents)
    procedures = dr_documents(ctx.kb, ctx.selectors)
    locations = context_locations(
        ctx.cycle,
        operation,
        ctx.kb,
        extra_tasks=dr_tasks(ctx.kb, ctx.selectors),
        extra_documents=procedures,
    )
    if settings.dr_procedure_always and locations:
        # la procedura della D.R. anche quando i task si trovano: per quel pezzo vale di più
        present = {item.document.key for item in locations}
        locations += tuple(
            whole_document(document) for document in procedures if document.key not in present
        )
    if settings.inspection_source and locations and is_inspection(operation):
        # la sezione d'ispezione del manuale del motore: per i criteri vale più dell'SPM (I8)
        present_lines = {(item.document.key, item.line_start) for item in locations}
        locations += tuple(
            item
            for item in inspection_locations(ctx.cycle, ctx.kb)
            if (item.document.key, item.line_start) not in present_lines
        )
    return locations


# Operazioni d'ispezione e di controllo, in italiano o in inglese (I8).
_INSPECTION = re.compile(
    r"ispezion\w*|controll[oi]\s+(?:visiv|dimensional|penetrant|non\s+distruttiv)\w*"
    r"|esame\s+visivo|liquidi\s+penetranti|magnetoscop\w*|penetrant\w*|inspect\w*|\bFPI\b",
    re.IGNORECASE,
)


def is_inspection(operation: Operation) -> bool:
    """L'operazione è un'ispezione o un controllo (dalla descrizione)."""
    return _INSPECTION.search(operation.operation_description or "") is not None


def _has_inspection(locations: Sequence[TaskLocation]) -> bool:
    return any(is_inspection_task(item.task) for item in locations)


def _languages(operation: Operation, settings: AgentSettings) -> tuple[str, str] | None:
    """Le due parti della descrizione, se vanno giudicate separatamente."""
    return language_parts(operation.operation_description) if settings.separate_languages else None


def _has_dr_procedure(locations: Sequence[TaskLocation]) -> bool:
    return any((item.document.kind or "").upper() == DR_PROCEDURE_KIND for item in locations)


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
    schema = judgement_schema(settings.out_of_scope)
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
            locations = _locations(ctx, operation, settings)
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
            languages=_languages(operation, settings),
            dr_procedure=settings.dr_procedure_always and _has_dr_procedure(locations),
            inspection=settings.inspection_source and _has_inspection(locations),
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


def plan_language_checks(
    ctx: CheckContext, settings: AgentSettings, skip: set[int]
) -> list[LanguageJob]:
    """Una sessione corta per ogni operazione scritta in due lingue, tranne quelle in `skip`."""
    jobs: list[LanguageJob] = []
    strict = settings.compare_languages_strict
    schema = languages_schema(strict)
    build = build_strict_languages_prompt if strict else build_languages_prompt
    for index, operation in enumerate(ctx.cycle.operations):
        if index in skip or not operation.operation_description:
            continue
        parts = language_parts(operation.operation_description)
        if parts is None:
            continue
        italian, english = parts
        request = SessionRequest(
            session_id=f"op-{index:03d}-{operation.operation_number}-lingue",
            system_prompt=LANGUAGES_SYSTEM_PROMPT,
            prompt=build(italian, english),
            output_schema=schema,
            use_tools=False,
            max_turns=settings.inline_max_turns,
        )
        jobs.append(LanguageJob(index, italian, english, request, strict))
    return jobs


def _plain(text: str) -> str:
    """Testo per ritrovare una citazione: minuscolo, spazi singoli, senza virgolette."""
    for mark in '«»"“”':
        text = text.replace(mark, "")
    return " ".join(text.split()).casefold()


def decide_languages(job: LanguageJob, outcome: SessionOutcome) -> LanguagesJudgement | None:
    """Il giudizio, solo se dice `diverse` e le due citazioni si ritrovano ognuna nella sua
    lingua. Altrimenti None: il confronto non cambia l'esito dell'operazione."""
    if outcome.status is not SessionStatus.OK or outcome.output is None:
        return None
    try:
        judgement = LanguagesJudgement.model_validate(outcome.output)
    except ValidationError:
        return None
    if judgement.languages is not LanguagesVerdict.DIVERSE:
        return None
    italian, english = _plain(judgement.italian_quote), _plain(judgement.english_quote)
    if not italian or not english:
        return None
    if italian not in _plain(job.italian) or english not in _plain(job.english):
        return None
    if job.strict and not strict_difference(
        judgement.kind, judgement.italian_quote, judgement.english_quote
    ):
        # il modello dice «diverse», ma nelle parole copiate il codice non ritrova né una
        # negazione in una lingua sola né due limiti al contrario: traduzione libera
        return None
    return judgement


def wider_job(
    ctx: CheckContext, job: OperationJob, settings: AgentSettings, system_prompt: str
) -> OperationJob | None:
    """La seconda ricerca di un'operazione «non verificabile»: con Grep e Read in tutti i
    documenti citati dal ciclo (più quelli del task e, per DR, quelli del profilo). Nessuna
    se non c'è niente di nuovo da cercare: stessi documenti e la prima aveva già i tool."""
    documents = {location.document.key: location.document for location in job.locations}
    try:
        for document in cited_documents(ctx.cycle, ctx.kb, ctx.profile.document_order):
            documents.setdefault(document.key, document)
        for document in dr_documents(ctx.kb, ctx.selectors):
            documents.setdefault(document.key, document)
        locations = tuple(whole_document(document) for document in documents.values())
    except SourceUnavailableError:
        return None
    if job.request.use_tools and {d.key for d in documents.values()} == {
        location.document.key for location in job.locations
    }:
        return None
    operation = job.operation
    prompt = build_operation_prompt(
        ctx.cycle,
        operation,
        _facts(ctx, operation),
        locations,
        inline=False,
        settings=settings,
        missing_tasks=_missing_tasks(ctx, operation, settings),
        languages=_languages(operation, settings),
        second_search=True,
    )
    request = SessionRequest(
        session_id=f"{job.request.session_id}-ricerca",
        system_prompt=system_prompt,
        prompt=prompt,
        output_schema=job.request.output_schema,
        use_tools=True,
        allowed_files=tuple(location.document.path for location in locations),
        max_turns=settings.max_turns,
    )
    return OperationJob(job.index, operation, locations, request)


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

    rationale = judgement.rationale
    if judgement.judgement is Judgement.FUORI_TEMA and settings.out_of_scope:
        reason = Reason.FUORI_TEMA
        rationale = f"Niente da confrontare: {judgement.rationale}"
    elif judgement.judgement in (Judgement.NON_VERIFICABILE, Judgement.FUORI_TEMA):
        reason = Reason.EVIDENZA_NON_TROVATA
    elif not evidence:
        reason = Reason.CITAZIONE_NON_VERIFICATA
        rationale = (
            f"L'agente ha giudicato la descrizione '{judgement.judgement.value}', ma nessuna "
            f"citazione è stata ritrovata nei documenti. Motivazione: {judgement.rationale}"
        )
    elif judgement.judgement is Judgement.CONTRADDETTO:
        reason = Reason.CONTRADDIZIONE
    else:
        reason = Reason.VERIFICATO
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


def _repeated(request: SessionRequest, repeats: int) -> list[SessionRequest]:
    """Le copie di una sessione per le verifiche di conferma: `<id>-conferma-1`, `-2`, ..."""
    return [
        request.model_copy(update={"session_id": f"{request.session_id}-conferma-{k}"})
        for k in range(1, repeats + 1)
    ]


def _validate(output: dict[str, object]) -> object:
    """Le sessioni del confronto con il manuale e quelle del confronto tra le lingue girano
    insieme: ognuna con il suo schema."""
    if "languages" in output:
        return LanguagesJudgement.model_validate(output)
    return OperationJudgement.model_validate(output)


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
        validate=_validate,
        timeout_s=settings.session_timeout_s,
    )


async def _second_search(
    ctx: CheckContext,
    session: AgentSession,
    settings: AgentSettings,
    system_prompt: str,
    jobs: list[OperationJob],
    decided: list[tuple[CheckResult, PipelineError | None]],
    stats: dict[str, int] | None,
) -> list[PipelineError]:
    """Le operazioni «non verificabili» si rifanno cercando in tutti i documenti del ciclo. Un
    giudizio nuovo (CORRETTO o ERRATO, con citazione verificata) prende il posto del primo e la
    sua sessione diventa quella dell'operazione (le conferme di un ERRATO si rifanno su questa);
    altrimenti resta il primo. Il costo delle due sessioni si somma."""
    unclear = [
        i for i, (result, _) in enumerate(decided) if result.reason is Reason.EVIDENZA_NON_TROVATA
    ]
    if not unclear:
        return []
    wider = await asyncio.to_thread(
        lambda: [(i, wider_job(ctx, jobs[i], settings, system_prompt)) for i in unclear]
    )
    pairs = [(i, job) for i, job in wider if job is not None]
    if stats is not None:
        stats["ricerca"] = len(pairs)
    if not pairs:
        return []
    outcomes = await _run(session, [job.request for _, job in pairs], settings)
    errors: list[PipelineError] = []
    for (i, job), outcome in zip(pairs, outcomes, strict=True):
        result, error = decide_operation(job, outcome, settings)
        if error is not None:
            errors.append(error)
        first = decided[i][0]
        usage = first.usage + result.usage
        if result.reason in (Reason.VERIFICATO, Reason.CONTRADDIZIONE):
            decided[i] = (result.model_copy(update={"usage": usage}), None)
            jobs[i] = job
        else:
            decided[i] = (first.model_copy(update={"usage": usage}), decided[i][1])
    return errors


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
    language_jobs: list[LanguageJob] = []
    if settings.compare_languages:
        skip = {r.target.index for r in results if r.reason in _NO_LANGUAGE_CHECK}
        language_jobs = plan_language_checks(ctx, settings, {i for i in skip if i is not None})
    if stats is not None:
        stats["inline"] = sum(1 for job in jobs if not job.request.use_tools)
        stats["search"] = sum(1 for job in jobs if job.request.use_tools)
        if language_jobs:
            stats["lingue"] = len(language_jobs)
    # le sessioni delle lingue girano insieme a quelle del manuale: il ciclo non dura di più
    every = await _run(
        session, [job.request for job in jobs] + [job.request for job in language_jobs], settings
    )
    outcomes, language_outcomes = every[: len(jobs)], every[len(jobs) :]
    decided = [
        decide_operation(job, outcome, settings)
        for job, outcome in zip(jobs, outcomes, strict=True)
    ]
    errors = [error for _, error in decided if error is not None]

    if settings.search_when_unverifiable:
        errors += await _second_search(ctx, session, settings, system_prompt, jobs, decided, stats)

    repeats = settings.confirm_contradiction
    doubtful = [
        i for i, (result, _) in enumerate(decided) if result.reason is Reason.CONTRADDIZIONE
    ]
    different = [
        (job, judgement)
        for job, outcome in zip(language_jobs, language_outcomes, strict=True)
        if (judgement := decide_languages(job, outcome)) is not None
    ]
    language_usage: dict[int, Usage] = {}
    for job, outcome in zip(language_jobs, language_outcomes, strict=True):
        language_usage[job.index] = language_usage.get(job.index, Usage()) + outcome.usage
    if repeats and (doubtful or different):
        requests = [copy for i in doubtful for copy in _repeated(jobs[i].request, repeats)]
        language_requests = [
            copy for job, _ in different for copy in _repeated(job.request, repeats)
        ]
        if stats is not None:
            stats["conferma"] = len(requests) + len(language_requests)
        every = await _run(session, requests + language_requests, settings)
        confirmations, language_confirmations = every[: len(requests)], every[len(requests) :]
        confirmed = []
        for n, (job, judgement) in enumerate(different):
            again = language_confirmations[n * repeats : (n + 1) * repeats]
            for outcome in again:
                language_usage[job.index] = language_usage[job.index] + outcome.usage
            if all(decide_languages(job, outcome) is not None for outcome in again):
                confirmed.append((job, judgement))
        different = confirmed
        for n, i in enumerate(doubtful):
            checked = [
                decide_operation(jobs[i], outcome, settings)
                for outcome in confirmations[n * repeats : (n + 1) * repeats]
            ]
            errors += [error for _, error in checked if error is not None]
            decided[i] = (confirm_contradiction(decided[i][0], [r for r, _ in checked]), None)

    results += [result for result, _ in decided]
    if language_jobs:
        results = _with_languages(results, different, language_usage)
    results.sort(key=lambda item: item.target.index or 0)
    return results, errors


def _with_languages(
    results: list[CheckResult],
    different: list[tuple[LanguageJob, LanguagesJudgement]],
    usage: dict[int, Usage],
) -> list[CheckResult]:
    """Il costo delle sessioni delle lingue va sull'operazione; dove le lingue dicono cose
    diverse (confermato) l'esito diventa ERRATO INCOERENZA_LINGUE."""
    found = {job.index: judgement for job, judgement in different}
    merged: list[CheckResult] = []
    for result in results:
        index = result.target.index
        if index is None or index not in usage:
            merged.append(result)
            continue
        total = result.usage + usage[index]
        judgement = found.get(index)
        if judgement is None:
            merged.append(result.model_copy(update={"usage": total}))
            continue
        merged.append(
            make_result(
                CHECK,
                result.target,
                Reason.INCOERENZA_LINGUE,
                "La descrizione italiana e quella inglese non dicono la stessa cosa (confronto "
                f"tra le due lingue): italiano «{judgement.italian_quote}», inglese "
                f"«{judgement.english_quote}». {judgement.rationale}",
                # le citazioni vengono dal ciclo, ritrovate dal codice nelle due lingue
                evidence=[
                    Evidence(document_key="CICLO (italiano)", quote=judgement.italian_quote),
                    Evidence(document_key="CICLO (inglese)", quote=judgement.english_quote),
                ],
                decided_by="agent",
                usage=total,
            )
        )
    return merged
