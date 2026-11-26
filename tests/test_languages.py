"""Numeri diversi tra la descrizione italiana e quella inglese."""

import pytest

from cycle_validation.checks.languages import language_parts, number_mismatches


def test_a_number_changed_next_to_a_part_number_is_found() -> None:
    description = (
        "SPESSORE 13-38 MICRON SU PROVINI P/N 1234567/89 / "
        "ON TEST PIECES P/N 1234567/89, THICKNESS 13-58 MICRON"
    )
    assert number_mismatches(description) == [("38", "58")]


def test_two_numbers_changed_in_one_language_are_found() -> None:
    description = (
        "RACCORDARE AD ALMENO 30 VOLTE LA PROFONDITA', SEPARAZIONE 0,5 VOLTE / "
        "BLEND AT LEAST 10 TIMES THE DEPTH, SEPARATION 1.5 TIMES"
    )
    assert number_mismatches(description) == [("30", "10"), ("0,5", "1.5")]


def test_a_number_changed_in_one_language_is_found() -> None:
    description = (
        "APPLICARE IL LUBRIFICANTE, SPESSORE 13-38 MICRON / "
        "APPLY THE LUBRICANT, THICKNESS 13-58 MICRON"
    )
    assert number_mismatches(description) == [("38", "58")]


def test_a_number_changed_next_to_a_conversion_written_in_one_language_is_found() -> None:
    # 26-11: l'inglese scrive anche i pollici, l'italiano no; prima i pezzi non si allineavano
    description = (
        "PROFONDITA' MASSIMA 0,45 MM, RACCORDARE 10 VOLTE / "
        "MAXIMUM DEPTH 0.38 MM (0.015 IN), BLEND 10 TIMES"
    )
    assert number_mismatches(description) == [("0,45", "0.38")]


def test_a_conversion_written_in_one_language_alone_is_not_a_mismatch() -> None:
    description = (
        "PROFONDITA' MASSIMA 0,38 MM, RACCORDARE 10 VOLTE / "
        "MAXIMUM DEPTH 0.38 MM (0.015 IN), BLEND 10 TIMES"
    )
    assert number_mismatches(description) == []


@pytest.mark.parametrize(
    "description",
    [
        # stessi numeri, virgola e punto decimali
        "LIMITE 0,015 POLLICI, INGRANDIMENTO 4X / LIMIT .015 INCH, MAGNIFICATION 4X",
        # conversione mm ↔ pollici e °C ↔ °F
        "PROFONDITA' 0,38 MM A 20 °C / DEPTH 0.015 IN AT 68 °F",
        # un numero in più in una sola lingua: non è una sostituzione
        "RACCORDARE (VEDI OP. 25) 10 VOLTE / BLEND 10 TIMES",
        # un numero in più e uno diverso nello stesso punto: non si sa quale sia la traduzione
        "RACCORDARE (VEDI OP. 25) 12 VOLTE / BLEND 10 TIMES",
        # part number e range in ordine diverso nelle due lingue
        "SPESSORE 13-38 MICRON SU PROVINI P/N 1234567/89 / ON TEST PIECES P/N 1234567/89, "
        "THICKNESS 13-38 MICRON",
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
