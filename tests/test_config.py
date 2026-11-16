from pathlib import Path

import pytest

from cycle_validation.config import Settings, load_profile, load_settings
from cycle_validation.domain.check import CheckName
from cycle_validation.errors import ConfigError


def test_defaults_without_file() -> None:
    settings = load_settings(None)
    assert settings == Settings()
    assert settings.agent.read_limit == 40
    assert settings.agent.inline_max_lines == 150


def test_repo_settings_file_matches_defaults(repo_root: Path) -> None:
    assert load_settings(repo_root / "config" / "settings.yaml") == Settings()


def test_missing_settings_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="non trovato"):
        load_settings(tmp_path / "assente.yaml")


def test_unknown_field_is_named(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("agent:\n  modello: x\n", encoding="utf-8")
    with pytest.raises(ConfigError, match=r"agent\.modello"):
        load_settings(path)


def test_out_of_range_value_is_named(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("agent:\n  concurrency: 0\n", encoding="utf-8")
    with pytest.raises(ConfigError, match=r"agent\.concurrency"):
        load_settings(path)


def test_invalid_yaml_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("agent: [", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML non valido"):
        load_settings(path)


@pytest.mark.parametrize("name", ["mos", "dr", "ej200"])
def test_repo_profiles_load(repo_root: Path, name: str) -> None:
    profile = load_profile(name, repo_root / "config" / "profiles")
    assert profile.name == name
    assert CheckName.OPERATION_DESCRIPTION in profile.checks


def test_dr_profile_blocks_on_recommendation(repo_root: Path) -> None:
    profile = load_profile("dr", repo_root / "config" / "profiles")
    assert profile.blocking_checks == [CheckName.DR_RECOMMENDATION]
    assert profile.requires_selectors


def test_ej200_profile_limits(repo_root: Path) -> None:
    profile = load_profile("ej200", repo_root / "config" / "profiles")
    assert profile.file_limits.max_bytes == 20 * 1024 * 1024
    assert profile.file_limits.max_pages == 60
    assert not profile.verify_process_sheet
    assert profile.reference_mode == "document"


def test_unknown_profile_lists_available(repo_root: Path) -> None:
    with pytest.raises(ConfigError, match="Disponibili: dr, ej200, mos"):
        load_profile("militare", repo_root / "config" / "profiles")


def test_blocking_check_must_be_active(tmp_path: Path) -> None:
    (tmp_path / "x.yaml").write_text(
        "name: x\nchecks: [source]\nblocking_checks: [dr_recommendation]\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="blocking_checks"):
        load_profile("x", tmp_path)


def test_mos_dr_and_ej200_profiles_use_the_pvrm320_layout_parser() -> None:
    # la stampa DR reale (vista il 16/11/2026) è lo stesso modulo PVRM320 dei MOS
    from kb_fixtures import PROFILES_DIR

    for name in ("ej200", "mos", "dr"):
        assert load_profile(name, PROFILES_DIR).layout_extractor == "pvrm320"
