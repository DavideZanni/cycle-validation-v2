"""Numeri diversi tra la descrizione italiana e quella inglese."""

import pytest

from cycle_validation.checks.languages import (
    language_blocks,
    language_parts,
    limit_direction,
    number_mismatches,
    strict_difference,
)


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


def test_a_number_changed_after_a_conversion_written_first_is_found() -> None:
    # 26-11 sera: l'inglese scrive prima i °F e poi i °C tra parentesi
    description = "TEMPERATURA 120 °C PER 2 ORE / TEMPERATURE 248 °F (240 °C) FOR 2 HOURS"
    assert number_mismatches(description) == [("120", "240")]
    description = "VEDI OP. 50, 120 °C / SEE OP. 25, 248 °F (120 °C)"
    assert number_mismatches(description) == [("50", "25")]


def test_a_number_changed_where_the_alignment_sees_a_deletion_is_found() -> None:
    # 26-11 sera: «50, 25» contro «25, 25» si allinea come un numero tolto e uno aggiunto
    description = "VEDI OP. 50 E OP. 25 / SEE OP. 25 AND OP. 25"
    assert number_mismatches(description) == [("50", "25")]


def test_a_code_changed_in_one_language_is_found() -> None:
    # 26-11 sera: i codici (part number, numeri di 5 cifre o più) prima non si confrontavano
    description = "SU PROVINI P/N 2469134, SPESSORE 13 MICRON / THICKNESS 13 MICRON ON P/N 1234567"
    assert number_mismatches(description) == [("2469134", "1234567")]


def test_codes_in_a_different_order_or_in_one_language_only_are_not_a_mismatch() -> None:
    assert number_mismatches("P/N 1234567 E 7654321 / P/N 7654321 AND 1234567") == []
    assert number_mismatches("PULIRE (RIF. 70012) / CLEAN") == []


@pytest.mark.parametrize("seed", range(40))
def test_every_blind_copy_with_a_number_changed_in_one_language_is_found(seed: int) -> None:
    """Le copie cieche `numero_una_lingua` le deve trovare questo controllo: il 26-11 ne trovava
    1 su 5 (codici e conversioni scritte prima del numero)."""
    import random

    from cycle_validation.domain.cycle import Operation
    from cycle_validation.evaluation.blind import _one_language_number

    descriptions = [
        "SPESSORE 13-38 MICRON SU PROVINI P/N 1234567 / ON TEST PIECES P/N 1234567, "
        "THICKNESS 13-38 MICRON",
        "RIF. SPEC. 70012 CLASSE 2, RACCORDARE 3 VOLTE / REF. SPEC. 70012 CLASS 2, BLEND 3 TIMES",
        "TEMPERATURA 120 °C PER 2 ORE / TEMPERATURE 248 °F (120 °C) FOR 2 HOURS",
        "PROFONDITA' MASSIMA 0,38 MM, RACCORDARE 7 VOLTE / "
        "MAXIMUM DEPTH 0.38 MM (0.015 IN), BLEND 7 TIMES",
        "VEDI OP. 25 E OP. 30, INGRANDIMENTO 4X / SEE OP. 25 AND OP. 30, MAGNIFICATION 4X",
    ]
    for description in descriptions:
        operation = Operation.model_construct(operation_description=description)
        copy = _one_language_number(operation, random.Random(seed))
        assert copy is not None
        assert number_mismatches(copy.operation_description), copy.operation_description


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
        # un rimando in una lingua sola: «operazione 70» contro una figura (MG78, 8d3c673c 060)
        "ISPEZIONARE NELLA OPERAZIONE 70 SUCCESSIVA, RAGGIO 0.005-0.060 INCH / "
        "CHECK IN NEXT STEP, REFER TO FIGURE 903, RADIUS 0.005-0.060 INCH",
        "VEDI FIG. 3, 2 VOLTE / SEE PAGE 12, 2 TIMES",
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


# --- versione stretta del confronto tra le lingue (I15, 27-11) ---


@pytest.mark.parametrize(
    ("kind", "italian", "english", "accepted"),
    [
        # errori veri: negazione tolta in una lingua, limite al contrario
        ("negazione", "NON RACCORDARE IL BORDO", "BLEND THE EDGE", True),
        ("negazione", "RACCORDARE IL BORDO", "DO NOT BLEND THE EDGE", True),
        ("limite", "PROFONDITÀ MASSIMA 0,5", "MINIMUM DEPTH 0.5", True),
        ("limite", "SUPERIORE A 4X", "NOT TO EXCEED 4X", True),
        ("limite", "ALMENO 3 VOLTE", "AT MOST 3 TIMES", True),
        # falsi errori della campagna del 26-27-11: traduzioni libere
        (
            "negazione",
            "PRESA IN CARICO DA PERIZIA",
            "HANDLING OF THE PART TO THE REPAIR AREA",
            False,
        ),
        ("limite", "LARGHEZZA", "LENGTH", False),
        ("negazione", "CARTA ABRASIVA", "CROCUS CLOTH", False),
        # stessa negazione o stesso limite nelle due lingue
        ("negazione", "NON PIEGARE", "DO NOT BEND", False),
        ("limite", "AL MASSIMO 2 MM", "MAXIMUM 2 MM", False),
        # «No.» abbreviazione di numero, non una negazione
        ("negazione", "FIGURA 3", "FIGURE No. 3", False),
        # un altro tipo non diventa mai ERRATO
        ("materiale", "OLIO", "GREASE", False),
    ],
)
def test_the_strict_check_accepts_only_what_the_code_finds_in_the_quotes(
    kind: str, italian: str, english: str, accepted: bool
) -> None:
    assert strict_difference(kind, italian, english) is accepted


def test_a_range_with_minimum_and_maximum_has_no_direction() -> None:
    assert limit_direction("MINIMO 1 MASSIMO 2", "it") is None
    assert limit_direction("NON OLTRE 2", "it") == "giù"
    assert limit_direction("OLTRE 2", "it") == "su"


# 27-11 sera: nelle stampe di raccordatura la 010 ha una riga di asterischi pieni dentro ogni
# lingua (prima della nota), quindi quattro parti; prima non si confrontava e i limiti cambiati
# in una lingua sola non si vedevano (tre stampe con errori)
SPLIT_010 = (
    "IDENTIFICARE I DIFETTI CON LA MATITA. SE NON E STATA APPROVATA UNA DR RISPETTARE I "
    "LIMITI: - MASSIMO 8 RACCORDATURE SU TUTTA LA PALA - MASSIMO 2 SUL BORDO D'ENTRATA"
    " / RIPORTARE DI SEGUITO IL NUMERO DEI DIFETTI E CREARE UNA CARTELLA CON LE FOTO"
    " / IDENTIFY THE DEFECTS WITH THE PENCIL. IF THERE IS NOT AN APPROVED DR USE THE "
    "FOLLOWING LIMITS: - MAXIMUM NUMBER OF BLENDS FOR ONE BLADE IS 4 - MAXIMUM NUMBER OF "
    "BLENDS ON LEADING EDGE IS 2"
    " / CREATE A FOLDER NAMED AS THIS OL WITH THE DEFECTS PICTURES"
)


def test_a_language_split_in_more_parts_is_put_back_together() -> None:
    blocks = language_blocks(SPLIT_010)
    assert blocks is not None
    assert blocks[0].startswith("IDENTIFICARE") and "CARTELLA" in blocks[0]
    assert blocks[1].startswith("IDENTIFY") and "FOLDER" in blocks[1]
    assert number_mismatches(SPLIT_010) == [("8", "4")]
    assert number_mismatches(SPLIT_010.replace("MASSIMO 8", "MASSIMO 4")) == []


def test_parts_that_do_not_end_as_italian_then_english_are_not_compared() -> None:
    english_first = " / ".join(reversed(SPLIT_010.split(" / ")))
    assert language_blocks(english_first) is None
    # due parti: come prima, senza riconoscere la lingua
    assert language_blocks("A 1 / B 2") == ("A 1", "B 2")


def test_references_are_compared_only_with_references_of_the_same_kind() -> None:
    # MG78 (27-11 notte): il rimando a un'operazione non sposta più i valori, e un valore
    # cambiato accanto a un rimando in una lingua sola ora si vede
    assert number_mismatches("RACCORDARE (VEDI OP. 25) 12 VOLTE / BLEND 10 TIMES") == [("12", "10")]
    assert number_mismatches("VEDI FIGURA 3 / SEE FIGURE 4") == [("3", "4")]
    assert number_mismatches("VEDI OPERAZIONE 70 / SEE FIGURE 70") == []


def test_a_limit_reversed_between_the_languages_is_found_by_the_code() -> None:
    # MG75 (27-11 notte): come la 060 dei cicli veri
    from cycle_validation.checks.languages import limit_mismatches

    found = limit_mismatches(
        "- LENTE CON INGRANDIMENTO SUPERIORE A 4X PUÒ ESSERE USATA / "
        "- MAGNIFICATION NOT TO EXCEED 4X CAN BE USED"
    )
    assert len(found) == 1 and "SUPERIORE A 4X" in found[0][0] and "EXCEED 4X" in found[0][1]


@pytest.mark.parametrize(
    "description",
    [
        # stesso verso, parole diverse
        "INDICAZIONI INFERIORI A 0.38 MM / INDICATIONS LESS THAN 0.38 MM",
        # «almeno» contro «non meno di»: tutti e due un minimo
        "DISTANZA ALMENO 5 VOLTE / DISTANCE NO LESS THAN 5 TIMES",
        # «almeno N» contro «più di N»: stesso verso (regola dell'utente, MG41)
        "LUNGHEZZA ALMENO 4 VOLTE / LENGTH MORE THAN 4 TIMES",
        # un numero d'elenco non è un valore
        "SINO 4X SOLO COME RIFERIMENTO 5) NEL CASO / (5) INDICATIONS OVER 5 MM",
        # il limite in una lingua sola
        "INGRANDIMENTO 4X / MAGNIFICATION NOT TO EXCEED 4X",
    ],
)
def test_no_limit_mismatch(description: str) -> None:
    from cycle_validation.checks.languages import limit_mismatches

    assert limit_mismatches(description) == []


def test_an_action_changed_in_one_language_is_found_by_the_code() -> None:
    # MG47 (27-11 notte): come e9b74c84 040
    from cycle_validation.checks.languages import action_mismatches

    assert action_mismatches(
        "VERIFICARE CHE SIA STATO RIMOSSO IL METALLO / VERIFY THAT THE METAL HAS BEEN BLENDED"
    ) == [("rimuovere", "raccordare")]


@pytest.mark.parametrize(
    "description",
    [
        "RACCORDARE PER RIMUOVERE IL DANNO / BLEND TO REMOVE THE DAMAGE",
        # un'azione in più in una lingua sola: una frase in più, non un errore
        "RACCORDARE I DIFETTI / BLEND THE DEFECTS AND POLISH",
        "COLLAUDO DELLA RIMOZIONE / INSPECTION OF THE METAL REMOVAL",
        "PULIRE IL PEZZO",
    ],
)
def test_no_action_mismatch(description: str) -> None:
    from cycle_validation.checks.languages import action_mismatches

    assert action_mismatches(description) == []
