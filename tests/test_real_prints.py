"""Le regole del codice sul testo vero delle 14 stampe della v1 (27-11 notte).

`docs/CONFRONTO_V1_14_CICLI.md` ha il testo originale delle stampe (permesso dal responsabile
dell'utente, 27-11). Qui si legge con il parser della v2 e si fanno i controlli della
descrizione decisi dal codice, senza modello e senza manuali: numeri, limiti e azioni tra le
lingue, lo stesso DR in tutto il ciclo. Ogni ERRATO deve essere un errore noto
(`eval/errori-noti.yaml`): sulle stampe giuste nessuno. Così una regola nuova si prova sulle
stampe vere prima di una campagna. Nel file di test solo impronte e numeri di operazione."""

import re
from pathlib import Path

import pytest
from kb_fixtures import memory_knowledge, profile

from cycle_validation.checks.base import CheckContext
from cycle_validation.checks.operation import plan_operation_checks
from cycle_validation.config import load_settings
from cycle_validation.domain.check import Verdict
from cycle_validation.domain.cycle import Cycle
from cycle_validation.evaluation.trials import load_known_errors
from cycle_validation.extract.pvrm320_report import parse_pvrm320_report
from cycle_validation.ingest.pdf import PdfDocument, PdfPage
from cycle_validation.services.machines import StaticMachineRegistry

ROOT = Path(__file__).resolve().parents[1]
PRINTS = ROOT / "docs" / "CONFRONTO_V1_14_CICLI.md"

# Gli ERRATO che il codice trova da solo sulla descrizione (27-11 notte). Se una regola ne
# trova di più, va bene solo se sono errori noti: il test lo dice e questa lista si aggiorna.
EXPECTED = {
    "22f586bb": {"010", "060"},  # «massima» contro «min» (MG81); limite al contrario (MG75)
    "298bc28e": {"035"},  # azione diversa (MG47), con la riga accanto a «continua» (MG77)
    "38960731": {"010", "050"},  # numeri
    "5ff17062": {"010"},
    "737dec71": {"060"},  # limite al contrario (MG75)
    "895167b9": {"010", "030", "060"},  # MG81; un altro DR (MG76); limite al contrario (MG75)
    "8d3c673c": {"140"},  # numeri (la 060 non più: rimando a un'operazione, MG78)
    "e9b74c84": {"025", "040"},  # numeri; azione diversa (MG47)
    "f355dc3c": {"010", "030"},  # numeri
}


def _cycles() -> dict[str, Cycle]:
    text = PRINTS.read_text("utf-8")
    parts = re.split(r"^### Testo originale (\w+)\n", text, flags=re.MULTILINE)
    cycles: dict[str, Cycle] = {}
    for fingerprint, body in zip(parts[1::2], parts[2::2], strict=True):
        pages = re.findall(r"```text\n(.*?)```", body, flags=re.DOTALL)
        pdf = PdfDocument(
            name=f"{fingerprint}.pdf",
            sha256="0" * 64,
            size_bytes=1,
            pages=tuple(PdfPage(number=n, text=page) for n, page in enumerate(pages, start=1)),
        )
        cycles[fingerprint] = parse_pvrm320_report(pdf)
    return cycles


@pytest.fixture(scope="module")
def errors_found_by_the_code() -> dict[str, set[str]]:
    settings = load_settings(None).agent
    kb = memory_knowledge()
    found: dict[str, set[str]] = {}
    for fingerprint, cycle in _cycles().items():
        ctx = CheckContext(cycle, kb, StaticMachineRegistry([]), profile("mos"), agent=settings)
        _, immediate = plan_operation_checks(ctx, settings, "s")
        found[fingerprint] = {
            cycle.operations[r.target.index].operation_number
            for r in immediate
            if r.verdict is Verdict.ERRATO and r.target.index is not None
        }
    return found


def test_the_fourteen_prints_are_read() -> None:
    cycles = _cycles()
    assert len(cycles) == 14
    assert all(cycle.operations for cycle in cycles.values())


def test_every_errato_of_the_code_is_a_known_error(
    errors_found_by_the_code: dict[str, set[str]],
) -> None:
    known = load_known_errors(ROOT / "eval" / "errori-noti.yaml")
    for fingerprint, ops in errors_found_by_the_code.items():
        entry = known.cycle(fingerprint)
        assert entry is not None, fingerprint
        allowed = set(entry.errori) | set(entry.in_attesa)
        assert ops <= allowed, (fingerprint, sorted(ops - allowed))


def test_the_code_finds_the_expected_errors(errors_found_by_the_code: dict[str, set[str]]) -> None:
    found = {key: ops for key, ops in errors_found_by_the_code.items() if ops}
    assert found == EXPECTED
