import asyncio
from pathlib import Path
from typing import Any

from fakes import ONE_CALL, ScriptedSession
from kb_fixtures import BrokenKnowledge, memory_knowledge, profile

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
    results, errors = asyncio.run(check_operations(ctx(operations), session, SETTINGS, "s"))
    assert errors == []
    assert [r.target.index for r in results] == [0, 1, 2, 3]
    # L'operazione 3 non risolve il suo task code, ma ripiega sul task della fonte collegata.
    assert [r.reason for r in results] == [
        Reason.VERIFICATO,
        Reason.CONTRADDIZIONE,
        Reason.CAMPO_ASSENTE,
        Reason.CONTRADDIZIONE,
    ]
    assert len(session.requests) == 3


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
    settings = AgentSettings(retry_backoff_s=0, missing_task_note=True)
    request = job_for(missing, settings).request
    assert "72-00-01-999-009" in request.prompt
    assert "non sono nel manuale" in request.prompt
    assert "fonti del ciclo" in request.prompt


def test_the_missing_task_note_is_off_by_default_and_absent_when_the_task_exists() -> None:
    assert "non sono nel manuale" not in job_for(op(codes=["72-00-01-999-009"])).request.prompt
    settings = AgentSettings(retry_backoff_s=0, missing_task_note=True)
    assert "non sono nel manuale" not in job_for(op(), settings).request.prompt


def test_a_stuck_session_gives_a_technical_warning_not_a_wait() -> None:
    class Stuck:
        async def run(self, request: Any) -> Any:
            await asyncio.sleep(60)

    settings = SETTINGS.model_copy(update={"session_timeout_s": 0.05})
    results, errors = asyncio.run(check_operations(ctx([op()]), Stuck(), settings, "s"))
    assert [r.reason for r in results] == [Reason.ERRORE_TECNICO]
    assert errors and "tempo massimo" in errors[0].message
