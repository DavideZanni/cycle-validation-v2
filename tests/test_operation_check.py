import asyncio
from pathlib import Path
from typing import Any

from fakes import ONE_CALL, ScriptedSession
from kb_fixtures import DOC_72, BrokenKnowledge, memory_knowledge, profile

from cycle_validation.agent.prompt import (
    build_operation_prompt,
    judgement_schema,
    load_prompt,
    prompt_version,
)
from cycle_validation.agent.session import SessionOutcome, SessionRequest, SessionStatus
from cycle_validation.checks.base import CheckContext
from cycle_validation.checks.operation import (
    OperationJob,
    check_operations,
    decide_operation,
    plan_operation_checks,
)
from cycle_validation.config import AgentSettings
from cycle_validation.domain.check import Reason, Verdict
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.services.machines import StaticMachineRegistry

SETTINGS = AgentSettings(retry_backoff_s=0)
QUOTE_OK = {"file": "MAN-DEMO-72.md", "line": 7, "quote": "Pulire il supporto con solvente tipo A."}


def ctx(operations: list[Operation], kb: Any = None) -> CheckContext:
    cycle = Cycle(
        engine_model="GENX-1B",
        sources=[Source(manual="MAN-DEMO-72", task="72-00-01-110-001", repair_code="R-01")],
        operations=operations,
    )
    return CheckContext(cycle, kb or memory_knowledge(), StaticMachineRegistry([]), profile("mos"))


def op(description: str = "Pulire il supporto", codes: list[str] | None = None) -> Operation:
    return Operation(
        operation_number="0010",
        operation_description=description,
        repair_code="R-01",
        task_codes=codes if codes is not None else ["72-00-01-110-001"],
        machine_tag="TM-1001",
    )


def answer(judgement: str, citations: list[dict[str, Any]], why: str = "perché") -> dict[str, Any]:
    return {"judgement": judgement, "rationale": why, "citations": citations}


def job_for(operation: Operation | None = None, settings: AgentSettings = SETTINGS) -> Any:
    jobs, _ = plan_operation_checks(ctx([operation or op()]), settings, "sistema")
    return jobs[0]


def decide(
    output: dict[str, Any] | None, status: SessionStatus = SessionStatus.OK, error: str = ""
):  # type: ignore[no-untyped-def]
    outcome = SessionOutcome(status=status, output=output, error=error, usage=ONE_CALL, attempts=3)
    return decide_operation(job_for(), outcome, SETTINGS)


def test_empty_description_is_not_applicable() -> None:
    jobs, immediate = plan_operation_checks(ctx([op("")]), SETTINGS, "s")
    assert jobs == []
    assert immediate[0].reason is Reason.CAMPO_ASSENTE


def test_no_resolved_reference_means_no_session() -> None:
    context = ctx([op(codes=["99-99"])])
    bare = CheckContext(
        context.cycle.model_copy(update={"sources": []}),
        context.kb,
        context.machines,
        context.profile,
    )
    jobs, immediate = plan_operation_checks(bare, SETTINGS, "s")
    assert jobs == []
    assert immediate[0].reason is Reason.FONTE_ASSENTE
    assert immediate[0].verdict is Verdict.WARNING


def test_unreachable_knowledge_is_technical_warning() -> None:
    jobs, immediate = plan_operation_checks(ctx([op()], BrokenKnowledge()), SETTINGS, "s")
    assert jobs == []
    assert immediate[0].reason is Reason.ERRORE_TECNICO


def test_short_text_goes_inline_without_tools() -> None:
    job = job_for()
    request = job.request
    assert not request.use_tools
    assert request.max_turns == SETTINGS.inline_max_turns
    assert "7: 2. Pulire il supporto con solvente tipo A." in request.prompt
    assert "Macchina TM-1001: Banco di lavaggio" in request.prompt
    assert "GENX-1B" in request.prompt


def test_long_text_goes_to_search_with_tools_on_cited_files_only() -> None:
    request = job_for(settings=AgentSettings(inline_max_lines=2)).request
    assert request.use_tools
    assert request.max_turns == SETTINGS.max_turns
    assert [p.name for p in request.allowed_files] == ["MAN-DEMO-72.md"]
    assert "Grep" in request.prompt
    assert "7: 2. Pulire" not in request.prompt


def test_coherent_with_verified_citation_is_correct() -> None:
    result, error = decide(answer("coerente", [QUOTE_OK]))
    assert (result.verdict, result.reason, result.decided_by) == (
        Verdict.CORRETTO,
        Reason.VERIFICATO,
        "agent",
    )
    assert result.evidence[0].line == 7
    assert error is None


def test_contradicted_with_verified_citation_is_wrong() -> None:
    result, _ = decide(answer("contraddetto", [QUOTE_OK]))
    assert (result.verdict, result.reason) == (Verdict.ERRATO, Reason.CONTRADDIZIONE)


def test_not_verifiable_is_a_warning() -> None:
    result, _ = decide(answer("non_verificabile", []))
    assert result.reason is Reason.EVIDENZA_NON_TROVATA


def test_judgement_without_verified_citation_is_a_warning() -> None:
    fake = {"file": "MAN-DEMO-72.md", "line": 7, "quote": "Immergere in acido a 80 gradi"}
    for judgement in ("coerente", "contraddetto"):
        for citations in ([], [fake]):
            result, _ = decide(answer(judgement, citations))
            assert result.reason is Reason.CITAZIONE_NON_VERIFICATA
            assert result.verdict is Verdict.WARNING


def test_max_turns_is_budget_warning() -> None:
    result, error = decide(None, SessionStatus.MAX_TURNS)
    assert result.reason is Reason.BUDGET_ESAURITO
    assert error is None


def test_technical_failure_gives_warning_and_pipeline_error() -> None:
    result, error = decide(None, SessionStatus.ERROR, "throttling")
    assert result.reason is Reason.ERRORE_TECNICO
    assert error is not None
    assert "throttling" in error.message
    assert "3 tentativi" in error.message


def test_malformed_output_is_technical_failure() -> None:
    result, error = decide({"judgement": "boh"})
    assert result.reason is Reason.ERRORE_TECNICO
    assert error is not None


def test_check_operations_end_to_end_with_scripted_session() -> None:
    operations = [op(), op("Descrizione sbagliata"), op(""), op(codes=["99-99"])]
    session = ScriptedSession(
        lambda r, a: answer("coerente" if "-000-" in r.session_id else "contraddetto", [QUOTE_OK])
    )
    # Con il salto del task mancante spento, l'operazione 3 non risolve il suo task code e
    # ripiega sul task della fonte collegata.
    settings = SETTINGS.model_copy(update={"skip_missing_task": False})
    results, errors = asyncio.run(check_operations(ctx(operations), session, settings, "s"))
    assert errors == []
    assert [r.target.index for r in results] == [0, 1, 2, 3]
    assert [r.reason for r in results] == [
        Reason.VERIFICATO,
        Reason.CONTRADDIZIONE,
        Reason.CAMPO_ASSENTE,
        Reason.CONTRADDIZIONE,
    ]
    assert len(session.planned) == 3
    assert len(session.requests) == 3 + 2 * SETTINGS.confirm_contradiction


def test_schema_is_closed_and_prompt_loads(repo_root: Path) -> None:
    schema = judgement_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"judgement", "rationale", "citations"}
    text = load_prompt(repo_root / "prompts", "operation_check.md")
    assert "coerente" in text
    assert prompt_version(text) == prompt_version(text) != prompt_version(text + "x")


def test_build_prompt_lists_task_codes() -> None:
    operation = op()
    cycle = ctx([operation]).cycle
    locations = job_for().locations
    prompt = build_operation_prompt(cycle, operation, [], locations, inline=True, settings=SETTINGS)
    assert "Task code citati: 72-00-01-110-001" in prompt


def test_request_is_frozen_model() -> None:
    assert isinstance(job_for().request, SessionRequest)


# --- sorgenti che smettono di rispondere a metà controllo ----------------------------------


def test_a_cited_document_that_cannot_be_read_anymore_gives_a_warning_not_a_verdict(
    tmp_path: Path,
) -> None:
    # la citazione non si può più verificare: il giudizio dell'agente da solo non basta,
    # né per CORRETTO né per ERRATO
    from kb_fixtures import DOC_72

    from cycle_validation.kb.port import TaskLocation

    copy = tmp_path / "MAN-DEMO-72.md"
    copy.write_bytes(DOC_72.path.read_bytes())
    document = DOC_72.model_copy(update={"path": copy})
    location = TaskLocation(
        manual_key=document.key,
        task="72-00-01-110-001",
        document=document,
        line_start=5,
        line_end=9,
    )
    job = OperationJob(0, op(), (location,), job_for().request)
    copy.unlink()
    for judgement in ("coerente", "contraddetto"):
        outcome = SessionOutcome(
            status=SessionStatus.OK, output=answer(judgement, [QUOTE_OK]), usage=ONE_CALL
        )
        result, _ = decide_operation(job, outcome, SETTINGS)
        assert (result.verdict, result.reason) == (
            Verdict.WARNING,
            Reason.CITAZIONE_NON_VERIFICATA,
        )
        assert not result.evidence


class WithoutStructuredData:
    """Knowledge base in cui i manuali rispondono e i dati di targhe e schede no."""

    def __init__(self) -> None:
        self._inner = memory_knowledge()

    def find_machine_tag(self, tag: str) -> Any:
        from cycle_validation.errors import SourceUnavailableError

        raise SourceUnavailableError("dati TM non raggiungibili")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def test_the_session_is_still_planned_when_the_extra_facts_are_unavailable() -> None:
    with_facts, _ = plan_operation_checks(ctx([op()]), SETTINGS, "sistema")
    assert "Macchina TM-1001" in with_facts[0].request.prompt

    jobs, immediate = plan_operation_checks(
        ctx([op()], kb=WithoutStructuredData()), SETTINGS, "sistema"
    )
    assert immediate == [] and len(jobs) == 1
    assert "Macchina TM-1001" not in jobs[0].request.prompt
    assert "Pulire il supporto" in jobs[0].request.prompt


def test_the_model_is_told_when_the_cited_task_does_not_exist() -> None:
    # MIGLIORIE A2: il task citato non c'è, il testo è quello delle fonti del ciclo. Detto
    # esplicitamente, il modello non scambia la differenza di codice per un dubbio sul testo.
    missing = op(codes=["72-00-01-999-009"])
    settings = AgentSettings(retry_backoff_s=0, missing_task_note=True, skip_missing_task=False)
    request = job_for(missing, settings).request
    assert "72-00-01-999-009" in request.prompt
    assert "non sono nel manuale" in request.prompt
    assert "fonti del ciclo" in request.prompt


def test_the_missing_task_note_is_off_by_default_and_absent_when_the_task_exists() -> None:
    judged = AgentSettings(retry_backoff_s=0, skip_missing_task=False)
    assert (
        "non sono nel manuale" not in job_for(op(codes=["72-00-01-999-009"]), judged).request.prompt
    )
    settings = AgentSettings(retry_backoff_s=0, missing_task_note=True, skip_missing_task=False)
    assert "non sono nel manuale" not in job_for(op(), settings).request.prompt


def test_a_stuck_session_gives_a_technical_warning_not_a_wait() -> None:
    class Stuck:
        async def run(self, request: Any) -> Any:
            await asyncio.sleep(60)

    settings = SETTINGS.model_copy(update={"session_timeout_s": 0.05})
    results, errors = asyncio.run(check_operations(ctx([op()]), Stuck(), settings, "s"))
    assert [r.reason for r in results] == [Reason.ERRORE_TECNICO]
    assert errors and "tempo massimo" in errors[0].message


def test_a_missing_task_can_skip_the_model_with_a_direct_warning() -> None:
    # MIGLIORIE B6 (A2 strada 2): niente sessione, WARNING che dice quale task manca
    settings = AgentSettings(retry_backoff_s=0, skip_missing_task=True)
    jobs, immediate = plan_operation_checks(
        ctx([op(codes=["72-00-01-999-009"]), op()]), settings, "s"
    )
    assert [job.index for job in jobs] == [1]
    assert [r.reason for r in immediate] == [Reason.FONTE_ASSENTE]
    assert immediate[0].verdict is Verdict.WARNING
    assert "72-00-01-999-009" in immediate[0].rationale


def test_a_missing_task_skips_the_model_by_default() -> None:
    assert AgentSettings().skip_missing_task is True


def test_the_model_can_still_judge_a_missing_task_when_asked() -> None:
    settings = AgentSettings(retry_backoff_s=0, skip_missing_task=False)
    jobs, immediate = plan_operation_checks(ctx([op(codes=["72-00-01-999-009"])]), settings, "s")
    assert len(jobs) == 1 and immediate == []


def _kb_with_sheet(treatment: str) -> Any:
    from cycle_validation.kb.memory import IndexedKnowledgeBase
    from cycle_validation.kb.port import ProcessSheetEntry

    base = memory_knowledge()
    sheet = ProcessSheetEntry(code="SP-0101", treatment=treatment, engine_families=("GENX", "LEAP"))
    return IndexedKnowledgeBase(
        base.version,
        documents=[DOC_72],
        tasks=[base.find_task("MAN-DEMO-72", "72-00-01-110-001")],  # type: ignore[list-item]
        machine_tags=base.machine_tags(),
        process_sheets=[sheet],
    )


def _prompt_with_sheet(treatment: str, engine_model: str = "GENX-1B") -> str:
    operation = Operation.model_validate({**op().model_dump(), "process_sheet": "SP-0101"})
    context = ctx([operation], _kb_with_sheet(treatment))
    context = CheckContext(
        context.cycle.model_copy(update={"engine_model": engine_model}),
        context.kb,
        context.machines,
        context.profile,
    )
    jobs, _ = plan_operation_checks(context, SETTINGS, "sistema")
    return jobs[0].request.prompt


def test_the_agent_sees_only_the_treatment_of_the_cycle_engine() -> None:
    prompt = _prompt_with_sheet("Lavaggio con solvente [GENX]; Lavaggio ad acqua [LEAP]")
    assert "Scheda SP-0101: Lavaggio con solvente" in prompt
    assert "Lavaggio ad acqua" not in prompt


def test_the_treatment_keeps_every_value_when_the_engine_is_unknown() -> None:
    prompt = _prompt_with_sheet("Lavaggio con solvente [GENX]; Lavaggio ad acqua [LEAP]", "XYZ")
    assert "Lavaggio con solvente [GENX]; Lavaggio ad acqua [LEAP]" in prompt


# --- conferma delle contraddizioni ----------------------------------------------------------


def _flipping(confirm: str) -> ScriptedSession:
    """Prima sessione: contraddizione; sessioni di conferma: `confirm`."""

    def reply(request: SessionRequest, attempt: int) -> dict[str, Any]:
        if "-conferma-" not in request.session_id:
            return answer("contraddetto", [QUOTE_OK])
        return answer(confirm, [] if confirm == "non_verificabile" else [QUOTE_OK])

    return ScriptedSession(reply)


def test_a_contradiction_found_again_by_every_confirmation_stays_wrong() -> None:
    session = _flipping("contraddetto")
    results, _ = asyncio.run(check_operations(ctx([op()]), session, SETTINGS, "s"))
    assert (results[0].verdict, results[0].reason) == (Verdict.ERRATO, Reason.CONTRADDIZIONE)
    assert [r.session_id for r in session.requests] == [
        "op-000-0010",
        "op-000-0010-conferma-1",
        "op-000-0010-conferma-2",
    ]
    assert results[0].usage.sessions == 3 * ONE_CALL.sessions


def test_a_contradiction_that_a_confirmation_does_not_find_is_an_unstable_warning() -> None:
    for confirm in ("coerente", "non_verificabile"):
        stats: dict[str, int] = {}
        results, errors = asyncio.run(
            check_operations(ctx([op()]), _flipping(confirm), SETTINGS, "s", stats)
        )
        result = results[0]
        assert (result.verdict, result.reason) == (Verdict.WARNING, Reason.GIUDIZIO_INSTABILE)
        assert "1 verifiche su 3" in result.rationale
        assert result.evidence  # la riga della contraddizione resta, per chi controlla a mano
        assert errors == []
        assert stats["conferma"] == 2


def test_a_confirmation_that_fails_technically_does_not_keep_the_error() -> None:
    session = ScriptedSession(
        lambda r, a: (
            RuntimeError("throttling")
            if "-conferma-2" in r.session_id
            else answer("contraddetto", [QUOTE_OK])
        )
    )
    results, errors = asyncio.run(check_operations(ctx([op()]), session, SETTINGS, "s"))
    assert (results[0].verdict, results[0].reason) == (Verdict.WARNING, Reason.ERRORE_TECNICO)
    assert errors and errors[0].target == "0010"


def test_no_confirmation_for_correct_judgements_or_when_turned_off() -> None:
    session = ScriptedSession(lambda r, a: answer("coerente", [QUOTE_OK]))
    asyncio.run(check_operations(ctx([op()]), session, SETTINGS, "s"))
    assert len(session.requests) == 1

    off = SETTINGS.model_copy(update={"confirm_contradiction": 0})
    session = _flipping("coerente")
    results, _ = asyncio.run(check_operations(ctx([op()]), session, off, "s"))
    assert results[0].reason is Reason.CONTRADDIZIONE
    assert len(session.requests) == 1


def test_numbers_that_differ_between_the_two_languages_are_errato_without_a_session() -> None:
    description = "SPESSORE 13-38 MICRON / THICKNESS 13-58 MICRON"
    jobs, immediate = plan_operation_checks(ctx([op(description)]), SETTINGS, "s")
    assert jobs == []
    assert immediate[0].reason is Reason.INCOERENZA_LINGUE
    assert immediate[0].verdict is Verdict.ERRATO
    assert "38 → 58" in immediate[0].rationale


def test_the_two_languages_are_judged_separately_and_it_can_be_switched_off() -> None:
    """`lingue_separate` (24-11), nella base dal 26-11: una lingua giusta non deve coprire
    l'altra."""
    bilingual = op("NON USARE SPAZZOLE / DO NOT USE BRUSHES")
    off = AgentSettings(retry_backoff_s=0, separate_languages=False)
    assert "Parte in italiano" not in job_for(bilingual, off).request.prompt
    separate = job_for(bilingual, AgentSettings(retry_backoff_s=0))  # acceso di default
    prompt = separate.request.prompt
    assert "Parte in italiano: NON USARE SPAZZOLE" in prompt
    assert "Parte in inglese: DO NOT USE BRUSHES" in prompt
    assert "ognuna delle due parti, separatamente" in prompt
    # una descrizione in una lingua sola resta com'è
    single = job_for(op(), AgentSettings(retry_backoff_s=0, separate_languages=True))
    assert "Parte in italiano" not in single.request.prompt


def test_the_elements_are_checked_one_by_one_and_it_can_be_switched_off() -> None:
    """`elementi_uno_per_uno` (24-11), nella base dal 26-11."""
    off = AgentSettings(retry_backoff_s=0, itemized_check=False)
    assert "scomponi la descrizione" not in job_for(op(), off).request.prompt
    itemized = job_for(op(), AgentSettings(retry_backoff_s=0)).request.prompt  # di default
    assert "scomponi la descrizione nei suoi elementi tecnici" in itemized


def test_the_general_definitions_note_is_only_in_its_variant() -> None:
    """`definizioni_generali` (26-11): «4 volte» del ciclo contro «3 volte» dell'SPM."""
    base = job_for(op(), AgentSettings(retry_backoff_s=0)).request.prompt
    assert "definizioni generali" not in base
    on = AgentSettings(retry_backoff_s=0, general_definitions_note=True)
    prompt = job_for(op(), on).request.prompt
    assert "**definizioni generali**" in prompt
    assert "rispondi `non_verificabile`" in prompt


def _second_search(second: str) -> ScriptedSession:
    """Prima verifica: non verificabile; seconda ricerca (sessione `-ricerca`): `second`."""
    return ScriptedSession(
        lambda r, a: (
            answer(second, [QUOTE_OK])
            if "-ricerca" in r.session_id
            else answer("non_verificabile", [])
        )
    )


SEARCH = SETTINGS.model_copy(update={"search_when_unverifiable": True})


def test_without_the_second_search_a_not_verifiable_stays_a_warning() -> None:
    session = _second_search("coerente")
    results, _ = asyncio.run(check_operations(ctx([op()]), session, SETTINGS, "s"))
    assert results[0].reason is Reason.EVIDENZA_NON_TROVATA
    assert len(session.requests) == 1


def test_the_second_search_looks_in_the_whole_cited_documents_with_tools() -> None:
    session = _second_search("coerente")
    results, errors = asyncio.run(check_operations(ctx([op()]), session, SEARCH, "s"))
    assert errors == []
    assert results[0].reason is Reason.VERIFICATO
    first, second = session.requests
    assert not first.use_tools and second.use_tools
    assert second.session_id == "op-000-0010-ricerca"
    assert "tutti i documenti citati dal ciclo" in second.prompt
    assert "documento intero" in second.prompt
    assert {p.name for p in second.allowed_files} == {"MAN-DEMO-72.md"}
    assert results[0].usage.sessions == 2 * ONE_CALL.sessions  # si pagano tutte e due


def test_a_second_search_that_finds_nothing_keeps_the_first_warning() -> None:
    session = _second_search("non_verificabile")
    results, _ = asyncio.run(check_operations(ctx([op()]), session, SEARCH, "s"))
    assert results[0].reason is Reason.EVIDENZA_NON_TROVATA
    assert results[0].usage.sessions == 2 * ONE_CALL.sessions


def test_a_contradiction_from_the_second_search_is_confirmed_on_the_same_documents() -> None:
    session = _second_search("contraddetto")
    results, _ = asyncio.run(check_operations(ctx([op()]), session, SEARCH, "s"))
    assert results[0].reason is Reason.CONTRADDIZIONE
    assert [r.session_id for r in session.requests] == [
        "op-000-0010",
        "op-000-0010-ricerca",
        "op-000-0010-ricerca-conferma-1",
        "op-000-0010-ricerca-conferma-2",
    ]


# --- confronto tra le due lingue (`agent.compare_languages`, variante `lingue_tra_loro`) ---

LANG_ON = SETTINGS.model_copy(update={"compare_languages": True})
BILINGUAL = "NON RACCORDARE IL BORDO / BLEND THE EDGE"


def _languages(verdict: str, italian: str = "NON RACCORDARE", english: str = "BLEND") -> dict:
    return {
        "languages": verdict,
        "rationale": "la negazione c'è solo in italiano",
        "italian_quote": italian,
        "english_quote": english,
    }


def _script(languages: Any, manual: str = "coerente") -> ScriptedSession:
    def reply(request: SessionRequest, attempt: int) -> dict[str, Any]:
        if "-lingue" in request.session_id:
            return languages(request) if callable(languages) else languages
        return answer(manual, [QUOTE_OK])

    return ScriptedSession(reply)


def test_the_languages_are_not_compared_by_default() -> None:
    session = _script(_languages("diverse"))
    results, _ = asyncio.run(check_operations(ctx([op(BILINGUAL)]), session, SETTINGS, "s"))
    assert results[0].reason is Reason.VERIFICATO
    assert not any("-lingue" in r.session_id for r in session.requests)


def test_two_languages_that_say_different_things_are_errato_after_confirmation() -> None:
    session = _script(_languages("diverse"))
    stats: dict[str, int] = {}
    results, errors = asyncio.run(
        check_operations(ctx([op(BILINGUAL)]), session, LANG_ON, "s", stats)
    )
    result = results[0]
    assert (result.verdict, result.reason) == (Verdict.ERRATO, Reason.INCOERENZA_LINGUE)
    assert "NON RACCORDARE" in result.rationale and result.decided_by == "agent"
    assert errors == []
    assert sorted(r.session_id for r in session.requests) == [
        "op-000-0010",
        "op-000-0010-lingue",
        "op-000-0010-lingue-conferma-1",
        "op-000-0010-lingue-conferma-2",
    ]
    assert result.usage.sessions == 4 * ONE_CALL.sessions
    assert stats["lingue"] == 1 and stats["conferma"] == 2


def test_the_languages_check_needs_quotes_found_in_their_own_language() -> None:
    for wrong in (_languages("diverse", "BLEND", "NON RACCORDARE"), _languages("diverse", "", "")):
        session = _script(wrong)
        results, _ = asyncio.run(check_operations(ctx([op(BILINGUAL)]), session, LANG_ON, "s"))
        assert results[0].reason is Reason.VERIFICATO
        # la sessione delle lingue si paga anche quando non cambia l'esito
        assert results[0].usage.sessions == 2 * ONE_CALL.sessions


def test_a_languages_difference_not_confirmed_leaves_the_manual_verdict() -> None:
    def flip(request: SessionRequest) -> dict[str, Any]:
        same = "-conferma-2" in request.session_id
        return _languages("uguali", "", "") if same else _languages("diverse")

    results, _ = asyncio.run(check_operations(ctx([op(BILINGUAL)]), _script(flip), LANG_ON, "s"))
    assert results[0].reason is Reason.VERIFICATO
    assert results[0].usage.sessions == 4 * ONE_CALL.sessions


def test_the_languages_are_compared_also_where_the_manual_is_missing() -> None:
    # il task citato non è nel manuale: senza il confronto tra le lingue resta FONTE_ASSENTE
    operation = op(BILINGUAL, codes=["72-00-01-110-999"])
    session = _script(_languages("diverse"))
    results, _ = asyncio.run(check_operations(ctx([operation]), session, LANG_ON, "s"))
    assert results[0].reason is Reason.INCOERENZA_LINGUE
    off, _ = asyncio.run(check_operations(ctx([operation]), _script({}), SETTINGS, "s"))
    assert off[0].reason is Reason.FONTE_ASSENTE


def test_no_languages_session_for_one_language_or_numbers_already_different() -> None:
    operations = [op("PULIRE IL PEZZO"), op("SPESSORE 13 MICRON / THICKNESS 18 MICRON")]
    session = _script(_languages("diverse"))
    results, _ = asyncio.run(check_operations(ctx(operations), session, LANG_ON, "s"))
    assert not any("-lingue" in r.session_id for r in session.requests)
    assert results[1].reason is Reason.INCOERENZA_LINGUE


def test_the_languages_prompt_has_both_texts_and_a_closed_schema() -> None:
    from cycle_validation.agent.prompt import build_languages_prompt, languages_schema

    prompt = build_languages_prompt(" NON RACCORDARE ", "BLEND")
    assert "## Descrizione in italiano\n\nNON RACCORDARE" in prompt
    assert "## Descrizione in inglese\n\nBLEND" in prompt
    assert "Nel dubbio rispondi `uguali`" in prompt
    schema = languages_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
