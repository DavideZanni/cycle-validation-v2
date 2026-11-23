"""Numeri diversi tra la descrizione italiana e quella inglese."""

import pytest

from cycle_validation.checks.languages import language_parts, number_mismatches


def test_a_number_changed_in_one_language_is_found() -> None:
    description = (
        "APPLICARE IL LUBRIFICANTE, SPESSORE 13-38 MICRON / "
        "APPLY THE LUBRICANT, THICKNESS 13-58 MICRON"
    )
    assert number_mismatches(description) == [("38", "58")]


@pytest.mark.parametrize(
    "description",
    [
        # stessi numeri, virgola e punto decimali
        "LIMITE 0,015 POLLICI, INGRANDIMENTO 4X / LIMIT .015 INCH, MAGNIFICATION 4X",
        # conversione mm ↔ pollici e °C ↔ °F
        "PROFONDITA' 0,38 MM A 20 °C / DEPTH 0.015 IN AT 68 °F",
        # un numero in più in una sola lingua: non è una sostituzione
        "RACCORDARE (VEDI OP. 25) 10 VOLTE / BLEND 10 TIMES",
        # una sola lingua
        "PULIRE IL PEZZO 2 VOLTE",
        # più di due parti: non si sa quale sia la traduzione di quale
        "A 1 / B 2 / C 3",
    ],
)
def test_no_mismatch(description: str) -> None:
    assert number_mismatches(description) == []


def test_language_parts() -> None:
    assert language_parts("UNO / ONE") == ("UNO", "ONE")
    assert language_parts("SOLO ITALIANO") is None
