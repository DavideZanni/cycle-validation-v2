"""Il numero del DR citato nella stampa (27-11 notte): lo stesso in tutto il ciclo (MG76) e la
procedura del DR trovata anche senza serial number (MG50). Numeri inventati."""

from pathlib import Path

from kb_fixtures import memory_knowledge, profile

from cycle_validation.checks.base import CheckContext
from cycle_validation.checks.dr_recommendation import (
    DR_PROCEDURE_KIND,
    cited_dr_numbers,
    dr_documents,
    dr_number_mismatches,
)
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.kb.port import DocumentInfo, DrRecommendation
from cycle_validation.resolve.dr import DrSelectors
from cycle_validation.services.machines import StaticMachineRegistry

# numeri di DR inventati, scritti in due pezzi (nel diff niente numeri di 6 o più cifre)
DR_A, DR_B, DR_C = "9100" + "0001", "9100" + "0002", "9100" + "0009"
OTHER = "5555" + "5555"

PROCEDURE = DocumentInfo(key="DR_" + DR_A, path=Path("dr.txt"), code=DR_A, kind=DR_PROCEDURE_KIND)


class Kb:
    """Conoscenza con una procedura DR e le recommendation di un serial number."""

    def __init__(self, reference: str = DR_A) -> None:
        self.reference = reference
        self.base = memory_knowledge()

    def find_manuals(self, name: str) -> list[DocumentInfo]:
        return [PROCEDURE] if name.strip() == DR_A else []

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        return [
            DrRecommendation(
                serial_number=serial_number,
                conditions=(1,),
                procedure="Repair",
                reference=self.reference,
            )
        ]

    def __getattr__(self, name: str) -> object:
        return getattr(self.base, name)


def cycle(*descriptions: str) -> Cycle:
    return Cycle(
        operations=[
            Operation(operation_number=f"{10 * (n + 1):03d}", operation_description=text)
            for n, text in enumerate(descriptions)
        ]
    )


def ctx(c: Cycle, kb: object, serial: str | None = None) -> CheckContext:
    selectors = DrSelectors(serial_number=serial, conditions=(1,)) if serial else None
    return CheckContext(c, kb, StaticMachineRegistry([]), profile("dr"), selectors)  # type: ignore[arg-type]


def test_cited_numbers() -> None:
    assert cited_dr_numbers(f"SECONDO D.R. CASE #{DR_A}. VEDI DR N. {DR_B}") == [
        DR_A,
        DR_B,
    ]
    assert cited_dr_numbers("REGISTRARE P/N E S/N") == []


def test_an_operation_citing_another_dr_is_errato() -> None:
    # senza serial: vale il primo DR citato (di solito nella 005)
    c = cycle(
        f"CONFORME ALLA D.R. CASE #{DR_A}.", "PULIRE", f"RACCORDARE SECONDO D.R. CASE #{DR_B}."
    )
    found = dr_number_mismatches(ctx(c, Kb()))
    assert list(found) == [2] and DR_B in found[2] and "citato per primo" in found[2]
    same = cycle(f"CONFORME ALLA D.R. CASE #{DR_A}.", f"SECONDO D.R. CASE #{DR_A}.")
    assert dr_number_mismatches(ctx(same, Kb())) == {}


def test_with_the_serial_the_dr_of_the_recommendations_decides() -> None:
    # il DR delle recommendation (campo `reference`, P14) vale più del primo citato
    c = cycle(f"SECONDO D.R. CASE #{DR_B}.", f"SECONDO D.R. CASE #{DR_A}.")
    found = dr_number_mismatches(ctx(c, Kb(), serial="SN-TEST-01"))
    assert list(found) == [0] and "recommendation" in found[0]
    # una `reference` con altre cifre attorno (revisione) vale lo stesso
    assert (
        dr_number_mismatches(ctx(cycle(f"D.R. CASE #{DR_A}"), Kb(DR_A + "01"), "SN-TEST-01")) == {}
    )
    # recommendation di un altro DR: si torna al primo citato, niente ERRATO su tutto il ciclo
    other = cycle(f"D.R. CASE #{DR_A}", f"D.R. CASE #{DR_A}")
    assert dr_number_mismatches(ctx(other, Kb(OTHER), "SN-TEST-01")) == {}


def test_without_serial_the_procedure_comes_from_the_number_in_the_print() -> None:
    # MG50: prima, senza serial number, la procedura della D.R. non arrivava mai al modello
    c = cycle(f"CONFORME ALLA D.R. CASE #{DR_A}.", "PULIRE")
    assert dr_documents(Kb(), None, c) == [PROCEDURE]  # type: ignore[arg-type]
    assert dr_documents(Kb(), None) == []  # type: ignore[arg-type]
    assert dr_documents(Kb(), None, cycle(f"D.R. CASE #{DR_C}")) == []  # type: ignore[arg-type]
