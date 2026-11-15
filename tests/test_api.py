import json
from pathlib import Path
from typing import Any

import pytest
from api_support import (
    Env,
    FailingStore,
    civil_pdf,
    ej200_pdf,
    recorded,
    same_shape,
)

BASE = "/cycle_validation"


def upload_civil(env: Env, who: str = "civile", **data: Any) -> Any:
    form = {"is_dr": "false", **data}
    files = {"file": ("ciclo.pdf", civil_pdf(), "application/pdf")}
    return env.client.post(
        f"{BASE}/upload?session_id=s1", data=form, files=files, headers=env.auth(who)
    )


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


# --- autenticazione e autorizzazione ------------------------------------------------------


def test_health_is_public_and_matches_the_recorded_response(env: Env) -> None:
    response = env.client.get(f"{BASE}/health")
    assert response.status_code == 200
    assert response.json() == recorded("health.json")


def test_without_the_user_set_by_the_frontend_it_is_401(env: Env) -> None:
    # L'accesso lo verifica il frontend: il backend non legge token, solo l'utente che riceve.
    assert env.client.get(f"{BASE}/flow/start").status_code == 401
    assert (
        env.client.get(f"{BASE}/flow/start", headers={"Authorization": "Bearer x"}).status_code
        == 401
    )
    assert env.client.get(f"{BASE}/flow/start", headers={"sso": "chiunque"}).status_code == 401


@pytest.mark.parametrize("user", ["", "  ", "../altro", "a/b", "..", "x" * 129, "anna\\bob"])
def test_a_user_that_could_reach_other_users_files_is_refused(env: Env, user: str) -> None:
    # L'utente finisce nel percorso S3 delle sessioni: niente barre, niente vuoto.
    headers = {"X-User": user, "X-Services": "all"}
    assert env.client.get(f"{BASE}/flow/start", headers=headers).status_code == 401


def test_the_header_names_follow_the_frontend(tmp_path: Path) -> None:
    env = Env(tmp_path, user_header="X-Utente", services_header="X-Gruppi")
    headers = {"X-Utente": "anna.rossi@example.com", "X-Gruppi": "cv, cv_ej200"}
    assert env.client.get(f"{BASE}/ej200/flow/start", headers=headers).status_code == 200
    assert env.client.get(f"{BASE}/flow/start", headers={"X-User": "anna"}).status_code == 401


def test_service_permissions(env: Env) -> None:
    assert env.client.get(f"{BASE}/flow/start", headers=env.auth("altro")).status_code == 403
    assert env.client.get(f"{BASE}/ej200/flow/start", headers=env.auth("civile")).status_code == 403
    assert env.client.get(f"{BASE}/ej200/flow/start", headers=env.auth("ej200")).status_code == 200
    assert env.client.get(f"{BASE}/flow/start", headers=env.auth("ej200")).status_code == 200
    assert env.client.get(f"{BASE}/ej200/flow/start", headers=env.auth("tutto")).status_code == 200


# --- flusso e conversazione ---------------------------------------------------------------


def test_flow_start_matches_the_recorded_message(env: Env) -> None:
    response = env.client.get(f"{BASE}/flow/start?session_id=abc", headers=env.auth())
    assert response.json() == recorded("flow_start_civil.json")
    bad = env.client.get(f"{BASE}/flow/start?session_id=a b!", headers=env.auth())
    assert bad.status_code == 422 and bad.json()["ok"] is False


@pytest.mark.parametrize(
    ("body", "is_dr", "needs"),
    [
        ({"answer": "sì"}, True, "serial"),
        ({"answer": "yes"}, True, "serial"),
        ({"answer": "no"}, False, "PDF"),
        ({"answer": "0"}, False, "PDF"),
        ({"dr_serial_number": "SN1", "dr_condition": [1, 2]}, True, "PDF"),
        ({"dr_serial_number": "SN1", "dr_condition": "1,2"}, True, "PDF"),
    ],
)
def test_conversation(env: Env, body: dict[str, Any], is_dr: bool, needs: str) -> None:
    response = env.client.post(f"{BASE}/conversation", json=body, headers=env.auth())
    assert response.status_code == 200
    data = response.json()
    assert not same_shape(data, recorded("conversation.json"))
    assert data["is_dr"] is is_dr and needs.lower() in data["next_message"].lower()


@pytest.mark.parametrize(
    "body",
    [
        {"answer": "forse"},
        {"answer": "no", "dr_serial_number": "SN1"},
        {},
        {"dr_serial_number": "SN1"},
    ],
)
def test_conversation_rejects_bad_requests(env: Env, body: dict[str, Any]) -> None:
    response = env.client.post(f"{BASE}/conversation", json=body, headers=env.auth())
    assert response.status_code == 422 and response.json()["ok"] is False


# --- upload civile ------------------------------------------------------------------------


def test_civil_upload_matches_the_recorded_shape_and_records_cost(env: Env) -> None:
    response = upload_civil(env)
    assert response.status_code == 200
    body = response.json()
    assert not same_shape(body, recorded("upload_success_civil.json"))
    assert body["state"] == "succeeded" and body["result"]["file_name"] == "ciclo.pdf"
    payload = body["result"]["payload"]
    assert payload["cycle_errors_count"] == 2 and 0 <= payload["cycle_errors_count_perc"] <= 1
    assert set(payload["operations"][0]) >= {
        "operationFeedback",
        "targaCRespFeedback",
        "schedaFeedback",
    }
    assert len(env.metrics.costs) == 1 and env.metrics.costs[0] > 0


def test_upload_rejections_use_the_historic_codes_and_error_shape(env: Env) -> None:
    wrong_ext = env.client.post(
        f"{BASE}/upload",
        data={"is_dr": "false"},
        files={"file": ("a.txt", b"x")},
        headers=env.auth("civile"),
    )
    assert wrong_ext.status_code == 415
    assert not same_shape(wrong_ext.json(), recorded("error_civil.json"))
    empty = env.client.post(
        f"{BASE}/upload",
        data={"is_dr": "false"},
        files={"file": ("a.pdf", b"")},
        headers=env.auth("civile"),
    )
    assert empty.status_code == 400
    junk = env.client.post(
        f"{BASE}/upload",
        data={"is_dr": "false"},
        files={"file": ("a.pdf", b"non pdf")},
        headers=env.auth("civile"),
    )
    assert junk.status_code == 415
    assert (
        env.client.post(
            f"{BASE}/upload", files={"file": ("a.pdf", b"x")}, headers=env.auth("civile")
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "data",
    [
        {"is_dr": "true"},
        {"is_dr": "true", "dr_serial_number": "SN-DEMO-001"},
        {"is_dr": "false", "dr_serial_number": "SN-DEMO-001", "dr_condition": "1"},
        {"is_dr": "forse"},
    ],
)
def test_dr_selector_policy_is_enforced_by_the_form(env: Env, data: dict[str, str]) -> None:
    assert upload_civil(env, **data).status_code == 422


@pytest.mark.parametrize("condition", ["1", "1,2", "[1,2]"])
def test_dr_upload_accepts_every_condition_format(env: Env, condition: str) -> None:
    response = upload_civil(
        env, is_dr="true", dr_serial_number="SN-DEMO-001", dr_condition=condition
    )
    assert response.status_code == 200
    assert response.json()["state"] == "succeeded"


def test_blocked_dr_is_reported_in_the_payload(env: Env) -> None:
    response = upload_civil(env, is_dr="true", dr_serial_number="SN-DEMO-002", dr_condition="1,2")
    payload = response.json()["result"]["payload"]
    assert payload["drRecommendationFeedback"].startswith("Error found:")
    assert payload["cycle_status"] == "bloccato"


def test_processing_exception_is_state_failed_with_traceback_toggle(tmp_path: Path) -> None:
    class Boom:
        async def run(self, profile: str, request: Any) -> Any:
            raise RuntimeError("esploso")

    with_tb = Env(tmp_path, runner=Boom())
    body = upload_civil(with_tb).json()
    # il testo dell'eccezione non esce più (vedi i test su "limiti e messaggi"): resta il tipo
    assert body["state"] == "failed" and "RuntimeError" in body["error"]
    assert "test_api.py" in body["error_info"]["traceback"]
    without = Env(tmp_path, runner=Boom(), include_traceback=False)
    assert "traceback" not in upload_civil(without).json()["error_info"]


def test_knowledge_unavailable_is_503(tmp_path: Path) -> None:
    from cycle_validation.errors import KnowledgeError

    class Down:
        async def run(self, profile: str, request: Any) -> Any:
            raise KnowledgeError("knowledge base non caricabile")

    assert upload_civil(Env(tmp_path, runner=Down())).status_code == 503


# --- upload EJ200 -------------------------------------------------------------------------


def upload_ej200(env: Env, data: bytes | None = None, who: str = "ej200") -> Any:
    files = {"file": ("ciclo.pdf", data if data is not None else ej200_pdf(), "application/pdf")}
    return env.client.post(f"{BASE}/ej200/upload?session_id=s1", files=files, headers=env.auth(who))


def test_ej200_upload_matches_the_recorded_shape(env: Env) -> None:
    response = upload_ej200(env)
    assert response.status_code == 200, response.text
    body = response.json()
    assert not same_shape(body, recorded("upload_success_ej200.json"))
    assert body["job_id"] and body["finished_at"].endswith("+00:00")
    assert (
        body["result"]["payload"]["operations"][0]["schedaFeedback"]
        == "N/A - Nessuna scheda indicata."
    )


def test_ej200_rejections(env: Env) -> None:
    from cycle_validation.testing.pdf import build_pdf

    assert upload_ej200(env, build_pdf(["Documento qualsiasi " * 10])).status_code == 422
    assert upload_ej200(env, b"x" * 300).status_code == 415
    assert upload_ej200(env, b"").status_code == 400


def test_ej200_kill_switch_is_501(tmp_path: Path) -> None:
    assert upload_ej200(Env(tmp_path, ej200_enabled=False)).status_code == 501


def test_ej200_unexpected_error_is_generic_without_traceback(tmp_path: Path) -> None:
    class Boom:
        async def run(self, profile: str, request: Any) -> Any:
            raise RuntimeError("segreto interno")

    response = upload_ej200(Env(tmp_path, runner=Boom()))
    assert response.status_code == 500
    assert "segreto" not in response.text and "traceback" not in response.text


# --- sessioni -----------------------------------------------------------------------------


def session_body(identifier: str = "s1", **extra: Any) -> dict[str, Any]:
    return {
        "id": identifier,
        "name": "Prova",
        "username": "qualcuno",
        "createdAt": "2026-11-13T10:00:00Z",
        "updatedAt": "2026-11-13T11:00:00Z",
        **extra,
    }


def test_civil_session_lifecycle_uses_the_verified_sso(env: Env) -> None:
    headers = env.auth("civile")
    assert (
        env.client.post(f"{BASE}/sessions", json=session_body(), headers=headers).status_code == 200
    )
    keys = env.store.list_keys("")
    assert any("ChatSessions/sso-civile/s1.json" in k for k in keys)
    assert any("ChatSessionsComplete/sso-civile/s1.json" in k for k in keys)
    listed = env.client.get(f"{BASE}/sessions/chiunque", headers=headers).json()
    assert [s["id"] for s in listed] == ["s1"]
    assert env.client.get(f"{BASE}/sessions/chiunque/s1", headers=headers).json()["useCase"] == "cv"
    assert env.client.get(f"{BASE}/sessions/x/nope", headers=headers).status_code == 404
    assert (
        env.client.delete(f"{BASE}/sessions/s1?username=altro", headers=headers).status_code == 200
    )
    assert env.client.get(f"{BASE}/sessions/x/s1", headers=headers).status_code == 404
    assert any("ChatSessionsComplete" in k for k in env.store.list_keys(""))


def test_session_validation(env: Env) -> None:
    headers = env.auth("civile")
    assert (
        env.client.post(f"{BASE}/sessions", json=session_body("a b"), headers=headers).status_code
        == 422
    )
    assert env.client.post(f"{BASE}/sessions", json={"id": "x"}, headers=headers).status_code == 422
    assert env.client.get(f"{BASE}/sessions/u/bad id!", headers=headers).status_code in (404, 422)


def test_ej200_sessions_ignore_extra_fields_and_set_owner_and_track(env: Env) -> None:
    headers = env.auth("ej200")
    body = {k: v for k, v in session_body().items() if k != "username"}
    body |= {"username": "altro", "track": "civile", "id": "e1"}
    assert env.client.post(f"{BASE}/ej200/sessions", json=body, headers=headers).status_code == 200
    saved = env.client.get(f"{BASE}/ej200/sessions/e1", headers=headers).json()
    assert saved["track"] == "ej200" and saved["owner"] == "sso-ej" and "username" not in saved
    env.client.post(
        f"{BASE}/ej200/sessions",
        json=body | {"id": "e2", "updatedAt": "2027-01-01"},
        headers=headers,
    )
    assert [s["id"] for s in env.client.get(f"{BASE}/ej200/sessions", headers=headers).json()] == [
        "e2",
        "e1",
    ]
    assert env.client.delete(f"{BASE}/ej200/sessions/e1", headers=headers).status_code == 200
    assert any("EJ200/ChatSessionsComplete/sso-ej/e1.json" in k for k in env.store.list_keys(""))


# --- feedback -----------------------------------------------------------------------------


def test_civil_feedback_is_one_object_per_feedback(env: Env) -> None:
    headers = env.auth("civile")
    for message, vote in (("m1", "up"), ("m2", "boh")):
        body = {
            "sessionId": "s1",
            "cycleId": "c",
            "vote": vote,
            "feedbackText": "t",
            "messageId": message,
        }
        assert env.client.post(f"{BASE}/feedback", json=body, headers=headers).json() == {
            "ok": True
        }
    keys = env.store.list_keys("Manufacturing AI/CycleValidationMemory/Feedback/sso-civile/")
    assert len(keys) == 2
    votes = sorted(json.loads(env.store.get_bytes(k))["vote"] for k in keys)
    assert votes == ["negative", "positive"]


def test_feedback_write_failure_is_an_error_not_a_success(tmp_path: Path) -> None:
    env = Env(tmp_path, store=FailingStore())
    response = env.client.post(
        f"{BASE}/feedback", json={"sessionId": "s1", "vote": "up"}, headers=env.auth("civile")
    )
    assert response.status_code == 503 and response.json()["ok"] is False


def test_ej200_feedback_validation(env: Env) -> None:
    headers = env.auth("ej200")
    assert (
        env.client.post(
            f"{BASE}/ej200/feedback",
            json={"sessionId": "s1", "vote": "up", "x": 1},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        env.client.post(
            f"{BASE}/ej200/feedback", json={"sessionId": "s1", "vote": "meh"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        env.client.post(f"{BASE}/ej200/feedback", json={"vote": "up"}, headers=headers).status_code
        == 422
    )
    assert (
        env.client.post(
            f"{BASE}/ej200/feedback", json={"sessionId": "a b", "vote": "up"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        len(env.store.list_keys("Manufacturing AI/CycleValidationMemory/EJ200/Feedback/sso-ej/"))
        == 1
    )


def test_image_upload_is_accepted_by_extension_and_refused_without_a_transcriber(env: Env) -> None:
    from test_document_ingest import png_bytes

    response = env.client.post(
        f"{BASE}/upload",
        data={"is_dr": "false"},
        files={"file": ("foto.PNG", png_bytes(), "image/png")},
        headers=env.auth("civile"),
    )
    assert response.status_code == 415
    assert "trascrittore" in response.json()["error"]["message"]


# --- limiti e messaggi ---------------------------------------------------------------------


class Recording:
    def __init__(self) -> None:
        self.calls = 0

    async def run(self, profile: str, request: Any) -> Any:
        self.calls += 1
        raise RuntimeError("non doveva partire")


@pytest.mark.parametrize("route", ["/upload", "/ej200/upload"])
def test_an_upload_over_the_service_limit_is_413_before_any_processing(
    tmp_path: Path, route: str
) -> None:
    runner = Recording()
    env = Env(tmp_path, runner=runner, max_upload_bytes=1000)
    response = env.client.post(
        f"{BASE}{route}",
        data={"is_dr": "false"},
        files={"file": ("ciclo.pdf", b"%PDF-1.4 " + b"x" * 2000)},
        headers=env.auth("tutto"),
    )
    assert response.status_code == 413
    assert runner.calls == 0


def test_an_unexpected_failure_never_returns_the_exception_text(tmp_path: Path) -> None:
    # il messaggio di un'eccezione imprevista può contenere testo del ciclo (per esempio un
    # errore di validazione riporta il valore rifiutato): al client arriva solo il tipo
    class Boom:
        async def run(self, profile: str, request: Any) -> Any:
            raise ValueError("Rettificare la sede fino al diametro 46,00 mm")

    body = upload_civil(Env(tmp_path, runner=Boom())).json()
    assert body["state"] == "failed"
    assert "46,00" not in json.dumps(body, ensure_ascii=False)
    assert "ValueError" in body["error"] and body["error_info"]["type"] == "ValueError"
    assert "traceback" in body["error_info"]  # i frame restano, senza il messaggio


def test_an_unexpected_failure_outside_the_upload_is_500_without_the_exception_text(
    tmp_path: Path,
) -> None:
    class BrokenStore(FailingStore):
        def list_keys(self, prefix: str) -> list[str]:
            raise ValueError("contenuto riservato della sessione")

    env = Env(tmp_path, store=BrokenStore())
    response = env.client.get(f"{BASE}/sessions/chiunque", headers=env.auth("civile"))
    assert response.status_code == 500
    assert "riservato" not in response.text
    assert "ValueError" in response.json()["error"]["message"]


def test_civil_sessions_cannot_be_listed_without_a_user_segment(env: Env) -> None:
    response = env.client.get(f"{BASE}/sessions", headers=env.auth("civile"))
    assert response.status_code == 404


def test_civil_feedback_must_be_an_object(env: Env) -> None:
    response = env.client.post(f"{BASE}/feedback", json=["up"], headers=env.auth("civile"))
    assert response.status_code == 422
    assert "oggetto JSON" in response.json()["error"]["message"]


def test_ej200_extraction_failure_is_422_with_its_message(tmp_path: Path) -> None:
    from cycle_validation.errors import ExtractionError

    class NoOperations:
        async def run(self, profile: str, request: Any) -> Any:
            raise ExtractionError("Il ciclo estratto non contiene operazioni.")

    response = upload_ej200(Env(tmp_path, runner=NoOperations()))
    assert response.status_code == 422
    assert "non contiene operazioni" in response.json()["error"]["message"]


def test_simultaneous_validations_are_capped_by_api_max_workers(tmp_path: Path) -> None:
    # Ogni validazione apre più sessioni del modello: senza tetto, dieci caricamenti insieme
    # sono decine di sessioni contemporanee e le quote di Bedrock finiscono.
    import asyncio

    import httpx

    class Counting:
        def __init__(self) -> None:
            self.active = 0
            self.peak = 0

        async def run(self, profile: str, request: Any) -> Any:
            self.active += 1
            self.peak = max(self.peak, self.active)
            await asyncio.sleep(0.05)
            self.active -= 1
            raise RuntimeError("basta contare")

    runner = Counting()
    env = Env(tmp_path, runner=runner, max_workers=2)
    app = env.client.app

    async def upload(client: httpx.AsyncClient) -> int:
        files = {"file": ("ciclo.pdf", civil_pdf(), "application/pdf")}
        response = await client.post(
            "/cycle_validation/validation/upload",
            data={"domain": "civil", "civil_type": "mos"},
            files=files,
            headers=env.auth(),
        )
        return response.status_code

    async def main() -> list[int]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return list(await asyncio.gather(*(upload(client) for _ in range(5))))

    codes = asyncio.run(main())
    assert runner.peak == 2, codes


# --- avvio --------------------------------------------------------------------------------


def test_the_knowledge_is_loaded_when_the_service_starts(tmp_path: Path) -> None:
    # MIGLIORIE B7: l'attesa del download sta all'avvio, non sulla prima validazione
    from fastapi.testclient import TestClient

    from cycle_validation.api.app import create_app

    calls: list[str] = []
    env = Env(tmp_path, warmup=lambda: calls.append("preload"))
    assert calls == []
    with TestClient(create_app(env.services)) as client:
        assert calls == ["preload"]
        assert client.get(f"{BASE}/health").status_code == 200


def test_a_knowledge_that_cannot_be_read_stops_the_service_at_start(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from cycle_validation.api.app import create_app
    from cycle_validation.errors import KnowledgeError

    def broken() -> None:
        raise KnowledgeError("targhe.json: campo `tag` mancante")

    env = Env(tmp_path, warmup=broken)
    with pytest.raises(KnowledgeError, match="targhe"), TestClient(create_app(env.services)):
        pass


def test_the_runner_preloads_the_knowledge_of_each_profile() -> None:
    import dataclasses

    from support import make_deps

    from cycle_validation.api.runner import PipelineRunner

    loaded: list[str] = []

    class Kb:
        def __init__(self, name: str) -> None:
            self.name = name

        def preload(self) -> None:
            loaded.append(self.name)

    deps, _ = make_deps()
    runner = PipelineRunner(lambda profile: dataclasses.replace(deps, kb=Kb(profile)))
    runner.preload(["mos", "dr", "ej200"])
    assert loaded == ["mos", "dr", "ej200"]
