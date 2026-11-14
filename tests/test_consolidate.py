from cycle_validation.checks.base import make_result
from cycle_validation.domain.check import (
    CheckName,
    CheckResult,
    Reason,
    Target,
    TargetKind,
    Verdict,
)
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.domain.report import CycleStatus, PipelineError
from cycle_validation.verdict.consolidate import (
    apply_integrity,
    blocked_results,
    compute_counts,
    cycle_status,
    expected_rows,
    is_blocking_failure,
)

CYCLE = Cycle(
    sources=[Source(manual="M1", task="T1"), Source(manual="M2")],
    operations=[
        Operation(operation_number="0010", operation_description="a"),
        Operation(operation_number="0020", operation_description="b"),
    ],
)
ALL = [
    CheckName.DR_RECOMMENDATION,
    CheckName.SOURCE,
    CheckName.TASK_CODE,
    CheckName.MACHINE_TAG,
    CheckName.PROCESS_SHEET,
    CheckName.OPERATION_DESCRIPTION,
]


def result(
    check: CheckName, reason: Reason, index: int = 0, kind: str = "operation"
) -> CheckResult:
    if kind == "operation":
        target = Target.operation(index, CYCLE.operations[index])
    elif kind == "source":
        target = Target.source(index, CYCLE.sources[index])
    else:
        target = Target.cycle()
    return make_result(check, target, reason, "x")


def test_expected_rows_cover_every_active_check_and_target() -> None:
    rows = expected_rows(CYCLE, ALL)
    assert (CheckName.DR_RECOMMENDATION, Target.cycle()) in rows
    assert len([r for r in rows if r[0] is CheckName.SOURCE]) == 2
    assert len([r for r in rows if r[0] is CheckName.MACHINE_TAG]) == 2
    assert len(rows) == 1 + 2 + 4 * 2


def test_expected_rows_ignore_integrity() -> None:
    assert expected_rows(CYCLE, [CheckName.EXTRACTION_INTEGRITY]) == []


def test_unconfirmed_value_downgrades_correct_and_wrong_to_warning() -> None:
    unconfirmed = frozenset({(CheckName.MACHINE_TAG, TargetKind.OPERATION, 0)})
    ok = result(CheckName.MACHINE_TAG, Reason.VERIFICATO, 0)
    wrong = result(CheckName.MACHINE_TAG, Reason.MACCHINA_NON_ATTIVA, 0)
    other = result(CheckName.MACHINE_TAG, Reason.VERIFICATO, 1)
    na = result(CheckName.MACHINE_TAG, Reason.CAMPO_ASSENTE, 0)
    out = apply_integrity([ok, wrong, other, na], unconfirmed)
    assert [r.reason for r in out] == [
        Reason.ESTRAZIONE_NON_CONFERMATA,
        Reason.ESTRAZIONE_NON_CONFERMATA,
        Reason.VERIFICATO,
        Reason.CAMPO_ASSENTE,
    ]


def test_blocking_failure_rule() -> None:
    assert not is_blocking_failure(result(CheckName.DR_RECOMMENDATION, Reason.VERIFICATO, kind="c"))
    assert not is_blocking_failure(result(CheckName.MACHINE_TAG, Reason.CAMPO_ASSENTE))
    assert is_blocking_failure(
        result(CheckName.DR_RECOMMENDATION, Reason.DR_NON_APPLICABILE, kind="c")
    )
    assert is_blocking_failure(result(CheckName.SOURCE, Reason.FONTE_ASSENTE, kind="source"))


def test_blocked_rows_are_warnings() -> None:
    cause = result(CheckName.DR_RECOMMENDATION, Reason.DR_NESSUNA_CORRISPONDENZA, kind="c")
    blocked = blocked_results(CYCLE, [CheckName.SOURCE, CheckName.TASK_CODE], cause)
    assert len(blocked) == 2 + 2
    assert {r.reason for r in blocked} == {Reason.BLOCCATO_A_MONTE}
    assert all(r.verdict is Verdict.WARNING for r in blocked)
    assert (
        "recommendation" in blocked[0].rationale.casefold()
        or "dr_recommendation" in blocked[0].rationale
    )


def test_counts_exclude_integrity_and_na_from_ratio() -> None:
    results = [
        result(CheckName.MACHINE_TAG, Reason.VERIFICATO, 0),
        result(CheckName.MACHINE_TAG, Reason.MACCHINA_NON_ATTIVA, 1),
        result(CheckName.TASK_CODE, Reason.CAMPO_ASSENTE, 0),
        result(CheckName.TASK_CODE, Reason.FONTE_ASSENTE, 1),
        result(CheckName.EXTRACTION_INTEGRITY, Reason.ESTRAZIONE_NON_CONFERMATA, 1),
    ]
    counts = compute_counts(results)
    assert (counts.total, counts.corretto, counts.errato) == (4, 1, 1)
    assert (counts.warning, counts.non_applicabile) == (1, 1)
    assert counts.errors_ratio == 1 / 3


def test_ratio_is_zero_without_applicable_rows() -> None:
    assert compute_counts([]).errors_ratio == 0.0
    only_na = [result(CheckName.TASK_CODE, Reason.CAMPO_ASSENTE)]
    assert compute_counts(only_na).errors_ratio == 0.0


def test_status() -> None:
    clean = [result(CheckName.MACHINE_TAG, Reason.VERIFICATO)]
    assert cycle_status(clean, blocked=False, pipeline_errors=[]) is CycleStatus.COMPLETO
    assert cycle_status(clean, blocked=True, pipeline_errors=[]) is CycleStatus.BLOCCATO
    err = [PipelineError(stage="s", message="m")]
    assert cycle_status(clean, blocked=False, pipeline_errors=err) is CycleStatus.PARZIALE
    for reason in (Reason.ERRORE_TECNICO, Reason.BUDGET_ESAURITO):
        partial = [result(CheckName.MACHINE_TAG, reason)]
        assert cycle_status(partial, blocked=False, pipeline_errors=[]) is CycleStatus.PARZIALE
