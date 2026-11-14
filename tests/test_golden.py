import asyncio
import json
from pathlib import Path

import pytest
from support import make_deps

from cycle_validation.domain.check import Verdict
from cycle_validation.errors import ConfigError
from cycle_validation.extract.from_file import load_cycle
from cycle_validation.golden import GoldenCase, evaluate_case, load_cases, run_golden
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.testing.pdf import synthetic_cycle_pdf

GOLDEN = Path(__file__).parent / "golden"


def deps_for(case: GoldenCase) -> Dependencies:
    deps, _ = make_deps(case.expected.profile, cycle_path=case.cycle_path)
    return deps


def test_cases_are_loaded() -> None:
    cases = load_cases(GOLDEN / "mos")
    assert [c.name for c in cases] == [
        "contraddetto",
        "fonte_e_codice_assenti",
        "macchina_non_attiva",
        "pulito",
        "scheda_non_applicabile",
    ]
    with pytest.raises(ConfigError):
        load_cases(GOLDEN / "nope")


def test_mos_golden_set_is_fully_concordant() -> None:
    summary = asyncio.run(run_golden(load_cases(GOLDEN / "mos"), deps_for))
    assert summary.concordance == 1.0, summary.render()
    assert summary.inline_share == 1.0
    assert "concordanza 100.0%" in summary.render()


def test_mismatches_are_reported_per_row() -> None:
    case = next(c for c in load_cases(GOLDEN / "mos") if c.name == "pulito")
    report = run_validation(
        RunRequest(pdf_bytes=synthetic_cycle_pdf(load_cycle(case.cycle_path))),
        deps_for(case),
    )
    assert evaluate_case(case, report).mismatches == []
    wrong = GoldenCase(
        case.name,
        case.directory,
        case.expected.model_copy(
            update={"rows": [case.expected.rows[0].model_copy(update={"verdict": Verdict.ERRATO})]}
        ),
    )
    result = evaluate_case(wrong, report)
    assert len(result.mismatches) == 1 and result.concordance < 1.0
    assert "atteso ERRATO, ottenuto CORRETTO" in result.mismatches[0]


def test_invalid_expected_file_is_explicit(tmp_path: Path) -> None:
    folder = tmp_path / "x"
    folder.mkdir()
    (folder / "ciclo.json").write_text("{}", encoding="utf-8")
    (folder / "expected.json").write_text(json.dumps({"rows": [{"check": "boh"}]}), "utf-8")
    with pytest.raises(ConfigError, match=r"expected.json"):
        load_cases(tmp_path)
