from cycle_validation.text import normalize_code, normalize_quote, squash


def test_codes_match_regardless_of_case_and_spaces() -> None:
    assert normalize_code(" spm 72-00-00 ") == normalize_code("SPM72-00-00")


def test_typographic_dashes_are_plain_dashes() -> None:
    assert normalize_code("72–00–00") == "72-00-00"


def test_squash_ignores_layout() -> None:
    assert squash("TM - 04\n57") == squash("tm-0457")


def test_quotes_match_across_line_breaks_and_double_spaces() -> None:
    assert normalize_quote("Clean  the\npart") == normalize_quote("clean the part")


def test_quote_normalization_keeps_word_boundaries() -> None:
    assert normalize_quote("clean the part") != normalize_quote("cleanthepart")
