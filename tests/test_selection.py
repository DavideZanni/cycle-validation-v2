"""Scelta iniziale del ciclo: civile o militare e, per il civile, MOS o DR.

La regola sta in `selection.py` (pura); le rotte `validation/options` e `validation/upload`
la espongono al frontend, che mostra i pulsanti.
"""

from pathlib import Path
from typing import Any

import pytest
from api_support import Env, civil_pdf, ej200_pdf

from cycle_validation.errors import CycleValidationError, SelectionError
from cycle_validation.selection import resolve_profile, selection_options

BASE = "/cycle_validation/validation"


# --- regola pura --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("domain", "civil_type", "profile"),
    [
        ("civil", "mos", "mos"),
        ("civil", "dr", "dr"),
        ("military", None, "ej200"),
        (" Civile ", " MOS ", "mos"),
        ("militare", "", "ej200"),
    ],
)
def test_resolve_profile(domain: str, civil_type: str | None, profile: str) -> None:
    assert resolve_profile(domain, civil_type) == profile


@pytest.mark.parametrize(
    ("domain", "civil_type", "fragment"),
    [
        (None, None, "civile o militare"),
        ("", "mos", "civile o militare"),
        ("navale", None, "civile o militare"),
        ("civil", None, "MOS o DR"),
        ("civil", "", "MOS o DR"),
        ("civil", "ej200", "MOS o DR"),
        ("military", "mos", "solo per i cicli civili"),
        ("military", "dr", "solo per i cicli civili"),
    ],
)
def test_invalid_choices_are_selection_errors(
    domain: str | None, civil_type: str | None, fragment: str
) -> None:
    with pytest.raises(SelectionError, match=fragment):
        resolve_profile(domain, civil_type)


def test_selection_error_is_an_expected_error() -> None:
    assert issubclass(SelectionError, CycleValidationError)


def test_options_describe_the_two_steps() -> None:
    tree = selection_options(military_enabled=True)
    first, second = tree["steps"]
    assert first["id"] == "domain"
    assert [item["value"] for item in first["options"]] == ["civil", "military"]
    assert second["id"] == "civil_type" and second["when"] == {"domain": "civil"}
    assert [item["value"] for item in second["options"]] == ["mos", "dr"]
    assert all(item["enabled"] for item in first["options"] + second["options"])


def test_options_mark_military_disabled() -> None:
    first = selection_options(military_enabled=False)["steps"][0]
    enabled = {item["value"]: item["enabled"] for item in first["options"]}
    assert enabled == {"civil": True, "military": False}


# --- rotte --------------------------------------------------------------------------------


class SpyRunner:
    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.profiles: list[str] = []

    async def run(self, profile: str, request: Any) -> Any:
        self.profiles.append(profile)
        return await self.inner.run(profile, request)


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


def spy(env: Env) -> SpyRunner:
    runner = SpyRunner(env.services.runner)
    env.services.runner = runner  # type: ignore[assignment]
    return runner


def upload(env: Env, who: str = "tutto", pdf: bytes | None = None, **data: str) -> Any:
    content = pdf if pdf is not None else civil_pdf()
    files = {"file": ("ciclo.pdf", content, "application/pdf")}
    return env.client.post(
        f"{BASE}/upload?session_id=s1", data=data, files=files, headers=env.auth(who)
    )


def test_options_route_needs_authentication(env: Env) -> None:
    assert env.client.get(f"{BASE}/options").status_code == 401
    assert env.client.get(f"{BASE}/options", headers=env.auth("altro")).status_code == 403


def test_options_route_returns_the_tree(env: Env) -> None:
    response = env.client.get(f"{BASE}/options", headers=env.auth("civile"))
    assert response.status_code == 200
    assert response.json() == selection_options(military_enabled=True)


def test_options_route_reports_military_disabled(tmp_path: Path) -> None:
    env = Env(tmp_path, ej200_enabled=False)
    body = env.client.get(f"{BASE}/options", headers=env.auth()).json()
    assert body == selection_options(military_enabled=False)


def test_civil_mos_runs_the_mos_profile(env: Env) -> None:
    runner = spy(env)
    response = upload(env, "civile", domain="civil", civil_type="mos")
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "succeeded"
    assert runner.profiles == ["mos"]


def test_civil_dr_runs_the_dr_profile_with_its_selectors(env: Env) -> None:
    runner = spy(env)
    response = upload(
        env,
        "civile",
        domain="civil",
        civil_type="dr",
        dr_serial_number="SN-DEMO-001",
        dr_condition="1",
    )
    assert response.status_code == 200, response.text
    assert runner.profiles == ["dr"]


def test_military_runs_the_ej200_profile(env: Env) -> None:
    runner = spy(env)
    response = upload(env, "ej200", pdf=ej200_pdf(), domain="military")
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "succeeded"
    assert runner.profiles == ["ej200"]


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"civil_type": "mos"},
        {"domain": "navale"},
        {"domain": "civil"},
        {"domain": "civil", "civil_type": "ej200"},
        {"domain": "military", "civil_type": "mos"},
        {"domain": "civil", "civil_type": "dr"},
        {"domain": "civil", "civil_type": "dr", "dr_serial_number": "SN-DEMO-001"},
        {"domain": "civil", "civil_type": "mos", "dr_serial_number": "SN-DEMO-001"},
        {"domain": "military", "dr_serial_number": "SN-DEMO-001", "dr_condition": "1"},
    ],
)
def test_invalid_choices_are_422_and_nothing_runs(env: Env, data: dict[str, str]) -> None:
    runner = spy(env)
    response = upload(env, "tutto", **data)
    assert response.status_code == 422, response.text
    assert response.json()["ok"] is False
    assert runner.profiles == []


def test_the_choice_is_checked_before_the_file(env: Env) -> None:
    runner = spy(env)
    response = env.client.post(
        f"{BASE}/upload",
        data={"domain": "military", "civil_type": "mos"},
        files={"file": ("a.txt", b"x")},
        headers=env.auth("tutto"),
    )
    assert response.status_code == 422
    assert runner.profiles == []


def test_military_needs_the_ej200_permission(env: Env) -> None:
    runner = spy(env)
    response = upload(env, "civile", pdf=ej200_pdf(), domain="military")
    assert response.status_code == 403
    assert runner.profiles == []


def test_civil_does_not_need_the_ej200_permission(env: Env) -> None:
    response = upload(env, "civile", domain="civil", civil_type="mos")
    assert response.status_code == 200


def test_military_kill_switch_is_501(tmp_path: Path) -> None:
    env = Env(tmp_path, ej200_enabled=False)
    runner = spy(env)
    response = upload(env, "tutto", pdf=ej200_pdf(), domain="military")
    assert response.status_code == 501
    assert runner.profiles == []


def test_rejected_files_keep_the_historic_codes(env: Env) -> None:
    wrong_ext = env.client.post(
        f"{BASE}/upload",
        data={"domain": "civil", "civil_type": "mos"},
        files={"file": ("a.txt", b"x")},
        headers=env.auth("civile"),
    )
    assert wrong_ext.status_code == 415
    empty = upload(env, "civile", pdf=b"", domain="civil", civil_type="mos")
    assert empty.status_code == 400
