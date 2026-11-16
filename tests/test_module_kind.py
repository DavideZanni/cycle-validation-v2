"""Il file caricato deve essere del tipo scelto: MOS, DR oppure militare (EJ200).

Il tipo si legge dalla testata del modulo (campo PROGETTO e riferimenti DR). Se il tipo
letto è diverso da quello scelto il run si ferma subito con "Modulo sbagliato", prima di
qualunque estrazione. Se la testata non si riconosce non si blocca nulla: assente non
significa sbagliato. Tutti i valori qui sotto sono inventati.
"""

from pathlib import Path
from typing import Any

import pytest
from api_support import Env
from support import make_deps

from cycle_validation.config import ModuleCheckSettings, load_settings
from cycle_validation.errors import IngestError, WrongModuleError
from cycle_validation.module_kind import check_module_kind, detect_module_kind
from cycle_validation.pipeline import RunRequest, run_validation
from cycle_validation.resolve.dr import DrSelectors
from cycle_validation.testing.pdf import build_pdf

RULES = ModuleCheckSettings()
MOS_NOTE = "72-00-01 REPAIR 001"
DR_NOTE = "DR 000123 REV 2"


def page(project: str | None, note: str = MOS_NOTE, number: int = 1) -> str:
    """Pagina nel layout della stampa: testata, poi la tabella delle operazioni."""
    lines = [
        "PGM PVRM320",
        f"  ** C I C L O    D I   L A V O R A Z I O N E **      PAG.   {number}",
        "CICLO :   CICLO-DEMO-001            DESCR.CICLO : SUPPORTO DIMOSTRATIVO",
    ]
    if project is not None:
        lines.append(f"TIPO CICLO : NORMALE                PROGETTO...   {project}")
    lines += [
        f"RIPARAZIONE : R1                    {note}",
        "TARGA       * NUM.   *    DESCRIZIONE  OPERAZIONE     *",
        "TM-1001     * 010    *  Pulire il supporto con solvente tipo A.",
        "            *        *  Per i limiti vedere DR 999 e la scheda.",
    ]
    return "\n".join(lines)


# --- riconoscimento -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        (page("GENX-1B/GENX-2B"), "mos"),
        (page("LEAP-1A"), "mos"),
        (page("GENX-1B", DR_NOTE), "dr"),
        (page("LEAP-1B", "DEPARTURE  RECOMMENDATION 45"), "dr"),
        # come la stampa DR reale: in NOTE c'è solo il numero di segnalazione difetti
        (page("GENX-1B/GENX-2B", "S99/01234-BLENDING DIFETT"), "dr"),
        (page("EJ200 RICAMBI N", "S00/00001"), "ej200"),
        (page("ej200 ricambi"), "ej200"),
        (page("MOTORE SCONOSCIUTO"), None),
        (page(None), None),
        ("Documento qualsiasi senza testata " * 5, None),
    ],
)
def test_detect_module_kind(text: str, kind: str | None) -> None:
    assert detect_module_kind(text, RULES) == kind


def test_a_dr_mentioned_only_in_an_operation_does_not_make_a_dr_cycle() -> None:
    assert "DR 999" in page("GENX-1B")
    assert detect_module_kind(page("GENX-1B"), RULES) == "mos"


def test_the_dr_marker_must_be_a_whole_word() -> None:
    assert detect_module_kind(page("GENX-1B", "RDR-300 DRILL"), RULES) == "mos"


def test_the_header_of_any_page_counts() -> None:
    text = "\n".join([page(None, number=1), page("EJ200 RICAMBI", number=2)])
    assert detect_module_kind(text, RULES) == "ej200"


def test_conflicting_headers_are_not_recognised() -> None:
    text = "\n".join([page("GENX-1B"), page("EJ200 RICAMBI", number=2)])
    assert detect_module_kind(text, RULES) is None


def test_without_dr_markers_mos_and_dr_are_just_civil() -> None:
    rules = ModuleCheckSettings(dr_markers=[])
    assert detect_module_kind(page("GENX-1B"), rules) == "civil"
    assert detect_module_kind(page("GENX-1B", DR_NOTE), rules) == "civil"


# --- confronto con la scelta --------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "chosen"),
    [
        (page("GENX-1B"), "mos"),
        (page("GENX-1B", DR_NOTE), "dr"),
        (page("EJ200 RICAMBI"), "ej200"),
        (page("MOTORE SCONOSCIUTO"), "mos"),
        (page(None), "dr"),
        (page(None), "ej200"),
    ],
)
def test_matching_or_unrecognised_modules_pass(text: str, chosen: str) -> None:
    check_module_kind(text, chosen, RULES)


@pytest.mark.parametrize(
    ("text", "chosen", "said"),
    [
        (page("GENX-1B", DR_NOTE), "mos", "hai scelto un ciclo civile MOS.*è un ciclo civile DR"),
        (page("GENX-1B"), "dr", "hai scelto un ciclo civile DR.*è un ciclo civile MOS"),
        (page("EJ200 RICAMBI"), "mos", "ciclo civile MOS.*è un ciclo militare"),
        (page("EJ200 RICAMBI"), "dr", "ciclo civile DR.*è un ciclo militare"),
        (page("GENX-1B"), "ej200", "ciclo militare.*è un ciclo civile MOS"),
        (page("LEAP-1A", DR_NOTE), "ej200", "ciclo militare.*è un ciclo civile DR"),
    ],
)
def test_a_different_module_is_rejected(text: str, chosen: str, said: str) -> None:
    with pytest.raises(WrongModuleError, match=said) as caught:
        check_module_kind(text, chosen, RULES)
    assert str(caught.value).startswith("Modulo sbagliato")
    assert caught.value.http_status == 422
    assert isinstance(caught.value, IngestError)


def test_without_dr_markers_only_civil_against_military_is_checked() -> None:
    rules = ModuleCheckSettings(dr_markers=[])
    check_module_kind(page("GENX-1B", DR_NOTE), "mos", rules)
    check_module_kind(page("GENX-1B"), "dr", rules)
    with pytest.raises(WrongModuleError, match="è un ciclo civile\\."):
        check_module_kind(page("GENX-1B"), "ej200", rules)


def test_the_check_can_be_switched_off() -> None:
    check_module_kind(page("EJ200 RICAMBI"), "mos", ModuleCheckSettings(enabled=False))


def test_profiles_outside_the_three_kinds_are_not_checked() -> None:
    check_module_kind(page("EJ200 RICAMBI"), "altro", RULES)


def test_settings_reject_an_invalid_marker(tmp_path: Path) -> None:
    from cycle_validation.errors import ConfigError

    path = tmp_path / "settings.yaml"
    path.write_text("module_check:\n  dr_markers: ['[']\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="dr_markers"):
        load_settings(path)


def test_shipped_settings_load_with_the_module_check() -> None:
    settings = load_settings(Path("config/settings.yaml"))
    assert settings.module_check.enabled
    assert settings.module_check.dr_markers


# --- pipeline -----------------------------------------------------------------------------


class NeverExtract:
    def __init__(self) -> None:
        self.calls = 0

    async def extract(self, pdf: Any) -> Any:
        self.calls += 1
        raise AssertionError("l'estrazione non deve partire")


def run(profile: str, text: str, **request: Any) -> tuple[Any, NeverExtract]:
    deps, session = make_deps(profile)
    extractor = NeverExtract()
    deps = type(deps)(**{**deps.__dict__, "extractor": extractor})
    with pytest.raises(WrongModuleError) as caught:
        run_validation(RunRequest(pdf_bytes=build_pdf([text]), **request), deps)
    assert session.requests == []
    return caught.value, extractor


def test_the_pipeline_stops_before_extraction_on_a_wrong_module() -> None:
    error, extractor = run("mos", page("EJ200 RICAMBI"))
    assert "militare" in str(error) and extractor.calls == 0


def test_the_pipeline_rejects_a_mos_loaded_as_dr() -> None:
    selectors = DrSelectors(serial_number="SN-DEMO-001", conditions=(1,))
    error, extractor = run("dr", page("GENX-1B"), selectors=selectors)
    assert "ciclo civile MOS" in str(error) and extractor.calls == 0


def test_a_civil_file_loaded_as_military_gets_the_wrong_module_message() -> None:
    # il profilo EJ200 chiede anche il testo "EJ200": il messaggio utile è l'altro
    error, _ = run("ej200", page("GENX-1B"))
    assert str(error).startswith("Modulo sbagliato") and "civile MOS" in str(error)


def test_a_document_that_is_not_a_cycle_still_fails_the_ej200_text_check() -> None:
    deps, _ = make_deps("ej200")
    request = RunRequest(pdf_bytes=build_pdf(["Documento qualsiasi " * 10]))
    with pytest.raises(IngestError, match="non è del tipo atteso") as caught:
        run_validation(request, deps)
    assert not isinstance(caught.value, WrongModuleError)


def test_the_recognised_module_is_validated_as_before(tmp_path: Path) -> None:
    from support import example_cycle

    from cycle_validation.testing.pdf import cycle_pdf_text

    deps, _ = make_deps("mos")
    text = page("GENX-1B") + "\n" + cycle_pdf_text(example_cycle())
    report = run_validation(RunRequest(pdf_bytes=build_pdf([text])), deps, tmp_path / "run")
    assert report.results


# --- API ----------------------------------------------------------------------------------

BASE = "/cycle_validation"


def post(env: Env, route: str, text: str, who: str = "tutto", **data: str) -> Any:
    files = {"file": ("ciclo.pdf", build_pdf([text]), "application/pdf")}
    return env.client.post(f"{BASE}/{route}", data=data, files=files, headers=env.auth(who))


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


@pytest.mark.parametrize(
    ("route", "data", "text"),
    [
        ("validation/upload", {"domain": "civil", "civil_type": "mos"}, page("EJ200 RICAMBI")),
        ("validation/upload", {"domain": "military"}, page("GENX-1B")),
        ("validation/upload", {"domain": "civil", "civil_type": "mos"}, page("GENX-1B", DR_NOTE)),
        ("upload", {"is_dr": "false"}, page("EJ200 RICAMBI")),
        ("ej200/upload", {}, page("LEAP-1A")),
    ],
)
def test_every_upload_route_answers_422_wrong_module(
    env: Env, route: str, data: dict[str, str], text: str
) -> None:
    response = post(env, route, text, **data)
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["message"].startswith("Modulo sbagliato")
