"""Parser della stampa PVRM320 reale (cicli di lavorazione MOS ed EJ200)."""

import json
from pathlib import Path

import pytest
from pvrm320_report_fixtures import (
    CONT,
    FOOTER,
    SEP,
    STARS,
    as_document,
    block,
    civil_pages,
    ej200_pages,
    page,
    row,
)

from cycle_validation.errors import ExtractionError
from cycle_validation.extract.pvrm320 import parse_pvrm320
from cycle_validation.extract.pvrm320_report import is_pvrm320_report, parse_pvrm320_report


def civil():
    return parse_pvrm320_report(as_document(civil_pages()))


def ops(cycle):
    return {op.operation_number: op for op in cycle.operations}


def test_the_report_is_recognised_and_the_reference_layout_is_not_mistaken_for_it() -> None:
    assert is_pvrm320_report(as_document(civil_pages()))
    assert not is_pvrm320_report(as_document(["PVRM320 EJ200\nCYCLE: X\nOP 0010 y"]))


def test_header_fields() -> None:
    cycle = civil()
    assert cycle.cycle_code == "ABCD-12345678A100-1"
    assert cycle.cycle_description == "TEST BLADE STAGE 1"
    assert cycle.engine_model == "MOTORE-1/MOTORE-2"
    assert cycle.repair_code == "B1"


def test_operations_in_order_and_continuations_are_merged() -> None:
    cycle = civil()
    assert [op.operation_number for op in cycle.operations] == ["005", "010", "040", "050", "100"]
    assert ops(cycle)["040"].page == 2
    assert ops(cycle)["100"].page == 4
    # il testo della 040 sta a cavallo di due pagine
    assert "DRY CLEAN" in ops(cycle)["040"].operation_description


def test_the_target_column_is_the_machine_tag_and_note_rows_have_none() -> None:
    by_number = ops(civil())
    assert by_number["005"].machine_tag is None
    assert by_number["010"].machine_tag == "QQ/901"
    assert by_number["040"].machine_tag == "700001"
    assert by_number["050"].machine_tag == "QQ/902"


def test_process_sheet_comes_from_the_scheda_row_even_on_the_continuation_page() -> None:
    by_number = ops(civil())
    sheet = by_number["040"].process_sheet
    assert sheet is not None
    assert sheet.code == "SSS-900"
    assert sheet.model_dump()["sp_orig"] == "11-22-33-444-555"
    assert by_number["010"].process_sheet is None


def test_description_keeps_both_languages_and_drops_the_noise() -> None:
    text = ops(civil())["040"].operation_description
    assert "PULIRE A SECCO LE ZONE INDICATE" in text
    assert "DRY CLEAN THE MARKED ZONES" in text
    for noise in (
        "CONTINUAZIONE",
        "CONTINUA ALLA",
        "D.T.",
        "ATTREZZATURA",
        "Z0000001",
        "SP.ORIG",
        "....",
        "* * *",
    ):
        assert noise not in text
    assert "NOTA DI PROVA" in ops(civil())["050"].operation_description


def test_task_codes_come_from_the_text_once_per_code() -> None:
    assert ops(civil())["005"].task_codes == ["72-00-00 REPAIR 001"]
    assert ops(civil())["010"].task_codes == []


def test_civil_source_is_the_oem_manual_with_the_task_from_the_notes() -> None:
    cycle = civil()
    assert len(cycle.sources) == 1
    source = cycle.sources[0]
    assert (source.manual, source.task, source.repair_code) == (
        "ABC123456",
        "72-00-00 REPAIR 001",
        "B1",
    )


def test_ej200_source_is_the_rdr_and_the_oem_placeholder_is_ignored() -> None:
    cycle = parse_pvrm320_report(as_document(ej200_pages()))
    assert [s.manual for s in cycle.sources] == ["EJ000001R-01"]
    assert cycle.repair_code == "A3"
    by_number = ops(cycle)
    # la continuazione senza numero d'operazione resta sulla 020; SP.ORIG senza scheda non fa una scheda
    assert by_number["020"].process_sheet is None
    assert by_number["030"].process_sheet is not None
    assert by_number["030"].process_sheet.code == "PG 900"
    assert "SECONDO SCHEDA" in by_number["030"].operation_description


def test_the_dispatcher_uses_the_report_parser_and_still_reads_the_reference_layout() -> None:
    assert parse_pvrm320(as_document(civil_pages())).cycle_code == "ABCD-12345678A100-1"


def test_a_report_without_operations_is_an_extraction_error() -> None:
    document = as_document(civil_pages()[:1] + civil_pages()[-1:])
    with pytest.raises(ExtractionError):
        parse_pvrm320_report(document)


def test_other_star_glyphs_from_ocr_or_pdf_text_are_accepted() -> None:
    pages = [text.replace("*", "★") if "TARGA" in text else text for text in civil_pages()]
    # le righe di asterischi della descrizione restano riconosciute come separatore
    cycle = parse_pvrm320_report(as_document(pages))
    assert ops(cycle)["010"].machine_tag == "QQ/901"


# --- sugli esempi reali, se presenti su questa macchina (materiale aziendale, fuori da git) ----
# Né il testo né i valori attesi stanno in git: accanto a ogni trascrizione ignorata c'è un
# `atteso.json` locale. Senza quei file i casi non esistono e il test risulta saltato.

ROOT = Path(__file__).resolve().parents[1]
REAL_FOLDERS = (
    ROOT / "docs/Esempio ciclo mos/trascrizione",
    ROOT / "docs/Esempio EJ200/trascrizione",
    ROOT / "docs/Esempio ciclo DR/trascrizione",
)


def _real_cases() -> list[tuple[Path, Path]]:
    return [
        (text, folder / "atteso.json")
        for folder in REAL_FOLDERS
        if (folder / "atteso.json").is_file()
        for text in sorted(folder.glob("*_trascritto.txt"))
    ]


@pytest.mark.parametrize(("text_path", "expected_path"), _real_cases())
def test_real_examples_match_their_local_expectations(text_path: Path, expected_path: Path) -> None:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    cycle = parse_pvrm320_report(as_document(text_path.read_text(encoding="utf-8").split("")))
    by_number = ops(cycle)
    sheets = {n: op.process_sheet.code for n, op in by_number.items() if op.process_sheet}
    # i confronti non mostrano i valori: in caso di errore il log non deve contenere dati aziendali
    assert (cycle.cycle_code == expected["cycle_code"]) is True
    assert ([s.manual for s in cycle.sources] == expected["sources"]) is True
    if "operation_numbers" in expected:
        assert (list(by_number) == expected["operation_numbers"]) is True
    if "n_operations" in expected:
        assert len(by_number) == expected["n_operations"]
    if "all_sheets" in expected:
        assert (sheets == expected["all_sheets"]) is True
    for number, code in expected.get("sheets", {}).items():
        assert (sheets.get(number) == code) is True
    for number, codes in expected.get("task_codes", {}).items():
        assert (by_number[number].task_codes == codes) is True


def squeeze(pages: list[str]) -> list[str]:
    """Come l'estrazione di PDFium: le sequenze di spazi diventano uno spazio solo."""
    import re

    return [re.sub(r"[ \t]+", " ", text) for text in pages]


def test_collapsed_whitespace_from_pdf_extraction_gives_the_same_cycle() -> None:
    for pages in (civil_pages(), ej200_pages()):
        assert parse_pvrm320_report(as_document(squeeze(pages))) == parse_pvrm320_report(
            as_document(pages)
        )


# --- ingressi degeneri -------------------------------------------------------------------------


def one_page(body: list[str], footer: list[str] | None = FOOTER) -> object:
    return parse_pvrm320_report(as_document([page(1, body, footer)]))


def test_the_responsibility_centre_is_never_taken_for_the_machine_tag() -> None:
    # operazione senza targa: la seconda riga della colonna è il centro responsabile
    cycle = one_page(block(["", "RSP001"], "010", ["LAVORO A BANCO", "SECONDA RIGA"]))
    assert ops(cycle)["010"].machine_tag is None


def test_an_empty_sheet_label_is_neither_a_sheet_nor_a_machine_tag() -> None:
    body = [row("", "010", "LAVORO A BANCO"), row("SCHEDA :", "", "ALTRO TESTO"), SEP]
    operation = ops(one_page(body))["010"]
    assert operation.machine_tag is None
    assert operation.process_sheet is None


def test_a_continuation_without_its_marker_stays_on_the_open_operation() -> None:
    first = block(["QQ/901", "RSP001"], "010", ["PRIMA PARTE"], closed=False)
    second = [row(text="SECONDA PARTE"), SEP, *block(["QQ/902"], "020", ["ALTRA OPERAZIONE"])]
    cycle = parse_pvrm320_report(as_document([page(1, first), page(2, second, FOOTER)]))
    by_number = ops(cycle)
    assert by_number["010"].operation_description == "PRIMA PARTE SECONDA PARTE"
    assert by_number["020"].operation_description == "ALTRA OPERAZIONE"


def test_the_continuation_marker_does_not_reopen_an_operation_that_was_closed() -> None:
    first = block(["QQ/901"], "010", ["PRIMA OPERAZIONE"])
    second = [row(text=CONT), row(text="***** PREMESSA *****"), row("QQ/902", "020", "SECONDA")]
    cycle = parse_pvrm320_report(as_document([page(1, first), page(2, second, FOOTER)]))
    by_number = ops(cycle)
    assert by_number["010"].operation_description == "PRIMA OPERAZIONE"
    assert "PREMESSA" in by_number["020"].operation_description


def test_a_block_of_text_without_operation_number_is_not_silently_dropped() -> None:
    body = [
        *block(["QQ/901"], "010", ["PRIMA OPERAZIONE"]),
        row("QQ/902", "", "OPERAZIONE DI CUI SI E PERSO IL NUMERO"),
        SEP,
    ]
    with pytest.raises(ExtractionError, match="senza numero"):
        one_page(body)


def test_fill_in_dots_are_removed_but_the_rest_of_the_line_is_kept() -> None:
    body = block(["QQ/901"], "010", ["MISURARE LO SPESSORE", "VALORE: ........ MM (MINIMO 1,5 MM)"])
    text = ops(one_page(body))["010"].operation_description
    assert "MINIMO 1,5 MM" in text
    assert "...." not in text


@pytest.mark.parametrize("glyph", ["∗", "＊", "⁎", "✱"])
def test_asterisk_look_alikes_are_read_as_column_separators(glyph: str) -> None:
    pages = [text.replace("*", glyph) for text in civil_pages()]
    assert parse_pvrm320_report(as_document(pages)) == civil()


def test_the_footer_is_read_with_spaces_around_the_colons() -> None:
    footer = ["RIP : B1   OEM : ABC123456      CHANGE : 7"]
    cycle = one_page(block(["QQ/901"], "010", ["LAVORO"]), footer)
    assert [s.manual for s in cycle.sources] == ["ABC123456"]


def test_the_word_after_rdr_is_a_source_only_if_it_looks_like_a_code() -> None:
    body = block(
        ["QQ/901"], "010", ["SECONDO LA RDR ALLEGATA E LA RDR", "EJ000001R-01", STARS, "SEE RDR"]
    )
    cycle = one_page(body, ["RIP: A3 OEM: AA/BB/CCC"])
    assert [s.manual for s in cycle.sources] == ["EJ000001R-01"]


def test_the_repair_code_of_an_operation_is_the_one_in_the_header_of_its_page() -> None:
    first = [row("ZC/001", "010", "PRELIEVO DEL PEZZO DI PROVA."), SEP]
    second = [row("ZC/002", "020", "LAVORO DI PROVA."), SEP]
    cycle = parse_pvrm320_report(
        as_document([page(1, first, repair="A3"), page(2, second, repair="B7")])
    )
    assert {n: op.repair_code for n, op in ops(cycle).items()} == {"010": "A3", "020": "B7"}


def test_a_sheet_line_without_column_stars_still_gives_the_sheet_and_its_sp_orig() -> None:
    """Stampa vera: «SCHEDA : PG 300» è più larga della colonna TARGA e la riga non ha `*`."""
    body = [
        row("TG0001", "030", ""),
        row("RSP004", "", "LAVAGGIO DI PROVA SECONDO SCHEDA."),
        f"{'SCHEDA : PG 900':<24}SP.ORIG. X1Y22300001Z999ZZ     SP.XXXX",
        SEP,
        row("TG0002", "040", "CONTROLLO DI PROVA."),
        f"{'':<24}SP.ORIG. X1Y22300002Z999ZZ     SP.XXXX",
        SEP,
    ]
    for pages in ([page(1, body)], squeeze([page(1, body)])):
        by_number = ops(parse_pvrm320_report(as_document(pages)))
        sheet = by_number["030"].process_sheet
        assert sheet is not None
        assert sheet.model_dump() == {"code": "PG 900", "sp_orig": "X1Y22300001Z999ZZ"}
        assert by_number["030"].operation_description == "LAVAGGIO DI PROVA SECONDO SCHEDA."
        # SP.ORIG. senza SCHEDA non fa una scheda
        assert by_number["040"].process_sheet is None


def test_a_bare_date_above_the_block_is_not_part_of_the_description() -> None:
    body = [row(text="13-10-26".rjust(58)), row("TG0001", "060", "CONTROLLO DI PROVA."), SEP]
    by_number = ops(parse_pvrm320_report(as_document([page(1, body)])))
    assert by_number["060"].operation_description == "CONTROLLO DI PROVA."


def test_a_word_broken_across_lines_is_rejoined_when_the_cycle_has_it_whole() -> None:
    body = [
        row("TG0001", "020", "RIMUOVERE LA QUANTITÀ MI"),
        row("", "", "NIMA DI MATERIALE E LE SUPERFICI"),
        row("", "", "E I BORDI. ELIMINA"),
        row("", "", "RE IL DIFETTO DA"),
        row("", "", "TE PROVE."),
        SEP,
        row("TG0002", "030", "DISTANZA MINIMA DI 1 MM; SUPERFICIE PULITA."),
        row("", "", "IN DATE DIVERSE."),
        SEP,
    ]
    for pages in ([page(1, body)], squeeze([page(1, body)])):
        by_number = ops(parse_pvrm320_report(as_document(pages)))
        # MINIMA compare intera nella 030; ELIMINARE no, e resta com'è; SUPERFICI / E e DA / TE
        # sono parole distinte anche se SUPERFICIE e DATE compaiono nel ciclo
        assert by_number["020"].operation_description == (
            "RIMUOVERE LA QUANTITÀ MINIMA DI MATERIALE E LE SUPERFICI E I BORDI. ELIMINA "
            "RE IL DIFETTO DA TE PROVE."
        )
