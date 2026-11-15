"""Varianti degli esperimenti: file YAML che ereditano dalla baseline e cambiano poche chiavi."""

from pathlib import Path

import pytest

from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.variant import load_variant

ROOT = Path(__file__).parents[1]


def write(folder: Path, name: str, body: str) -> Path:
    path = folder / f"{name}.yaml"
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    config = tmp_path / "settings.yaml"
    config.write_text("agent:\n  model: haiku\n  concurrency: 4\n", encoding="utf-8")
    write(tmp_path, "baseline", f"nome: baseline\ndescrizione: oggi\nconfig: {config.as_posix()}\n")
    return tmp_path


def test_a_variant_changes_only_what_it_declares(folder: Path) -> None:
    path = write(
        folder,
        "effort_low",
        "nome: effort_low\ndescrizione: meno\nbase: baseline\nagent:\n  effort: low\n",
    )
    variant = load_variant(path)
    assert variant.name == "effort_low"
    assert variant.description == "meno"
    assert variant.settings.agent.effort == "low"
    assert variant.settings.agent.concurrency == 4  # dalla config della baseline
    assert variant.settings.agent.model == "haiku"
    assert variant.chain == ["baseline", "effort_low"]
    assert variant.session == "sdk"


def test_inheritance_goes_through_more_than_one_level(folder: Path) -> None:
    write(folder, "veloce", "nome: veloce\nbase: baseline\nagent:\n  effort: low\n")
    path = write(folder, "veloce12", "nome: veloce12\nbase: veloce\nagent:\n  concurrency: 12\n")
    variant = load_variant(path)
    assert (variant.settings.agent.effort, variant.settings.agent.concurrency) == ("low", 12)
    assert variant.chain == ["baseline", "veloce", "veloce12"]


def test_the_config_option_replaces_the_starting_settings(folder: Path, tmp_path: Path) -> None:
    other = tmp_path / "locale.yaml"
    other.write_text("agent:\n  use_bedrock: false\n", encoding="utf-8")
    variant = load_variant(folder / "baseline.yaml", config_override=other)
    assert variant.settings.agent.use_bedrock is False
    assert variant.settings.agent.concurrency == 6  # predefinito: la config originale non c'è più


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("nome: x\nagent:\n  effortt: low\n", "effortt"),
        ("nome: x\nsconosciuto: 1\n", "sconosciuto"),
        ("nome: altro\n", "nome"),
        ("nome: x\nbase: manca\n", "manca"),
        ("nome: x\nsessione: diretta\n", "diretta"),
        ("nome: x\nbase: baseline\nconfig: a.yaml\n", "config"),
    ],
)
def test_invalid_variants_are_rejected_with_a_clear_message(
    folder: Path, body: str, message: str
) -> None:
    path = write(folder, "x", body)
    with pytest.raises(ConfigError, match=message):
        load_variant(path)


def test_an_inheritance_cycle_is_rejected(folder: Path) -> None:
    write(folder, "a", "nome: a\nbase: b\n")
    write(folder, "b", "nome: b\nbase: a\n")
    with pytest.raises(ConfigError, match="ciclo"):
        load_variant(folder / "a.yaml")


def test_the_variants_in_the_project_are_valid() -> None:
    folder = ROOT / "eval" / "varianti"
    names = sorted(path.stem for path in folder.glob("*.yaml"))
    assert {"baseline", "effort_low", "concorrenza_12", "sonnet"} <= set(names)
    for name in names:
        variant = load_variant(folder / f"{name}.yaml", project_root=ROOT)
        assert variant.chain[0] == "baseline"


def test_the_service_keeps_no_transcripts_but_the_experiments_do() -> None:
    # Nel servizio il testo di cicli e manuali non va su disco; negli esperimenti serve.
    from cycle_validation.config import AgentSettings, load_settings

    assert AgentSettings().save_transcripts is False
    assert load_settings(ROOT / "config" / "settings.yaml").agent.save_transcripts is False
    for path in (ROOT / "eval" / "varianti").glob("*.yaml"):
        variant = load_variant(path, project_root=ROOT)
        assert variant.settings.agent.save_transcripts is True, path.name
