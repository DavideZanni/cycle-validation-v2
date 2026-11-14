from pathlib import Path

import pytest

from cycle_validation.errors import ConfigError
from cycle_validation.legacy_prompts import (
    describe_use_cases,
    load_use_case,
    load_use_cases,
)

DIR = Path(__file__).parent / "fixtures" / "prompts" / "use_cases"


def test_load_standard_fields() -> None:
    case = load_use_case(DIR / "operations_validation.yaml")
    assert case.name == "operations_validation"
    assert case.variables == ("operation_description", "context")
    assert case.max_tokens == 4000 and case.temperature == 0
    assert case.system.startswith("Sei un verificatore")


def test_alternative_field_names_and_defaults() -> None:
    case = load_use_case(DIR / "TM_validation.yaml")
    assert case.system == "Verifica le targhe macchina."
    assert case.max_tokens == 7000  # predefinito del wrapper attuale
    assert case.variables == ("machine_tag", "tm_data")


def test_render_fills_placeholders_and_names_missing_variables() -> None:
    case = load_use_case(DIR / "operations_validation.yaml")
    text = case.render({"operation_description": "Pulire", "context": "Manuale"})
    assert "Operazione: Pulire" in text and "Contesto: Manuale" in text
    with pytest.raises(ConfigError, match="context"):
        case.render({"operation_description": "x"})


def test_variables_are_inferred_when_not_declared(tmp_path: Path) -> None:
    path = tmp_path / "x.yaml"
    path.write_text("prompt: 'Ciao {nome}, {nome} e {altro}'\n", encoding="utf-8")
    assert load_use_case(path).variables == ("nome", "altro")


@pytest.mark.parametrize("content", ["- a\n- b\n", "system: solo\n", ": : :\n  - ["])
def test_invalid_files_are_explicit(tmp_path: Path, content: str) -> None:
    path = tmp_path / "x.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError):
        load_use_case(path)


def test_directory_and_description() -> None:
    cases = load_use_cases(DIR)
    assert sorted(cases) == ["TM_validation", "operations_validation"]
    table = describe_use_cases(cases)
    assert "| TM_validation | machine_tag, tm_data |" in table
    with pytest.raises(ConfigError):
        load_use_cases(DIR / "nope")
