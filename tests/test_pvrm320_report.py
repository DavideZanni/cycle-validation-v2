"""Parser della stampa PVRM320 reale (cicli di lavorazione MOS ed EJ200)."""

import json
from pathlib import Path

import pytest
from pvrm320_report_fixtures import (
    CONT,
    FOOTER,
    NEXT,
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
from cycle_validation.extract.pvrm320_report import (
    is_pvrm320_report,
    note_task,
    parse_pvrm320_report,
)


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


def test_full_task_codes_are_read_whole() -> None:
    """Stampa vera: il codice completo del task non va tagliato alle prime tre coppie."""
    body = block(
        ["NOTE", "000000"],
        "005",
        [
            "SECONDO TASK 70-11-00-350-002 ABC123456 TASK 72-11-31-200-801",
            "FIGURE 801 (SHEET 3) E TASK 72-11-32 REPAIR 004",
        ],
    )
    assert ops(one_page(body))["005"].task_codes == [
        "70-11-00-350-002",
        "72-11-31-200-801",
        "72-11-32 REPAIR 004",
    ]


def test_civil_source_is_the_oem_manual_with_the_task_from_the_notes() -> None:
    cycle = civil()
    assert len(cycle.sources) == 1
    source = cycle.sources[0]
    assert (source.manual, source.task, source.repair_code) == (
        "ABC123456",
        "72-00-00 REPAIR 001",
        "B1",
    )


def test_each_repair_code_is_a_source_with_the_task_of_its_own_page() -> None:
    # stampa con due riparazioni: ogni pagina ha in testata la sua, con il task nella NOTE
    footer = ["RIP: A1 OEM: ABC123456".ljust(46) + "CHANGE: 7"]
    pages = [
        page(1, block(["QQ/901"], "010", ["ISPEZIONARE"]), repair="A1", note="CIR 72-00-01"),
        page(
            2,
            block(["QQ/902"], "020", ["RIPARARE"]),
            footer,
            repair="A3",
            note="CIR 72-00-01, REPAIR 004",
        ),
    ]
    cycle = parse_pvrm320_report(as_document(pages))
    assert [(s.manual, s.task, s.repair_code) for s in cycle.sources] == [
        ("ABC123456", "72-00-01", "A1"),
        ("ABC123456", "72-00-01 REPAIR 004", "A3"),
    ]
    assert ops(cycle)["020"].repair_code == "A3"


def test_a_subtask_cited_in_the_text_is_a_task_code() -> None:
    body = block(
        ["QQ/901"], "005", ["RACCORDARE SECONDO MANUALE ABC123456 SUBTASK 70-11-00-350-035"]
    )
    cycle = parse_pvrm320_report(as_document([page(1, body, FOOTER)]))
    assert ops(cycle)["005"].task_codes == ["70-11-00-350-035"]


@pytest.mark.parametrize(
    ("note", "task"),
    [
        ("72-00-00 REPAIR 001", "72-00-00 REPAIR 001"),
        ("CIR 72-00-00, REPAIR 001 VEDI NOTA", "72-00-00 REPAIR 001"),
        ("TASK 72-00-00-200-801", "72-00-00-200-801"),
        ("BLENDING 72-00-00-200-801", "72-00-00-200-801"),
        ("APPL. LUBRIFIC. SECCO", None),
        ("CIR 72-00-00", "72-00-00"),
        ("S26/00001", None),
        (None, None),
    ],
)
def test_the_task_in_the_header_note(note: str | None, task: str | None) -> None:
    assert note_task(note) == task


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
    with pytest.raises(ExtractionError, match=r"senza numero.*comincia con «OPERAZIONE DI CUI"):
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


def test_rn_and_ef_are_sources_with_or_without_the_word_before_the_code() -> None:
    body = block(
        ["QQ/901"],
        "010",
        [
            "IN ACCORDO ALLA RDR EJ000001R-01, ALLA RN",
            "RN-EJ-000-0000-01 E ALLA EF EF000A0000-02;",
            "VEDI ANCHE RN-EJ-000-0000-01 ED EF000B0000-01.",
            "RETURN THE PART; EF FINISHED; RIF. SD S00/00000",
        ],
    )
    cycle = one_page(body, ["RIP: A3 OEM: AA/BB/CCC"])
    assert [s.manual for s in cycle.sources] == [
        "EJ000001R-01",
        "RN-EJ-000-0000-01",
        "EF000A0000-02",
        "EF000B0000-01",
    ]


def test_the_cited_paragraph_is_read_after_the_code_or_before_its_type() -> None:
    body = block(
        ["QQ/901"],
        "010",
        [
            "IN ACCORDO ALLA RDR EJ000001R-01 PAR. 2.1 (RIF. SD S00/00000)",
            "E AL PAR. 3.4 DELLA RN RN-EJ-000-0000-01; EF EF000A0000-01.",
        ],
    )
    cycle = one_page(body, ["RIP: A3 OEM: AA/BB/CCC"])
    assert [(s.manual, s.section) for s in cycle.sources] == [
        ("EJ000001R-01", "PAR. 2.1"),
        ("RN-EJ-000-0000-01", "PAR. 3.4"),
        ("EF000A0000-01", None),
    ]


def test_sp_orig_is_not_a_task_code_in_a_civil_cycle() -> None:
    # nei cicli civili il task sta nel testo; SP.ORIG. resta solo sotto la scheda
    operation = ops(civil())["040"]
    assert "11-22-33-444-555" not in operation.task_codes


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


def _note_page_with_tail(tail: list[str], with_note: bool = True) -> object:
    """Stampa DR vera (21-11-2026), pagina 2, valori inventati: la riga NOTE si ferma a metà
    frase e il seguito sta dopo il banner di fine pagina, senza numero di operazione."""
    note = block(["NOTE", "999999"], "005", ["QUESTA PROCEDURA FORNISCE LE"]) if with_note else []
    body = [
        *note,
        *block(["QQ/901", "RSP001"], "010", ["PRELIEVO DEL PEZZO", NEXT]),
        "*** C O N T I N U A ***",
        *tail,
    ]
    second = [row(text=CONT), *block(["QQ/902"], "020", ["LAVORO DI PROVA"])]
    return parse_pvrm320_report(as_document([page(1, body), page(2, second, FOOTER)]))


def test_the_block_after_the_page_end_banner_continues_the_truncated_note() -> None:
    tail = [
        row(text="ISTRUZIONI DI PROVA PER LA RACCORDATURA."),
        row(text="* * * * * * * * * * * * * *"),
        row(text="THIS TEST PROCEDURE PROVIDES INSTRUCTIONS."),
    ]
    by_number = ops(_note_page_with_tail(tail))
    assert by_number["005"].operation_description == (
        "QUESTA PROCEDURA FORNISCE LE ISTRUZIONI DI PROVA PER LA RACCORDATURA."
        " / THIS TEST PROCEDURE PROVIDES INSTRUCTIONS."
    )
    assert by_number["010"].operation_description == "PRELIEVO DEL PEZZO"
    assert by_number["020"].operation_description == "LAVORO DI PROVA"


def test_without_a_truncated_operation_the_block_after_the_banner_is_an_error() -> None:
    with pytest.raises(ExtractionError, match="senza numero"):
        _note_page_with_tail([row(text="TESTO DI CUI NON SI SA IL PADRONE")], with_note=False)


def test_the_block_after_the_banner_completes_a_truncated_operation_with_its_sheet() -> None:
    """Stampa DR vera, pagina 5, valori inventati: l'op. 050 ha solo la prima riga, la 060
    comincia subito sotto e continua alla pagina dopo; dopo il banner c'è il seguito della 050,
    con la sua riga SCHEDA, poi il tratteggio."""
    first = block(["QQ/900"], "040", ["LAVAGGIO DEL PEZZO.", STARS, "WASHING"], closed=False)
    second = [
        row(text=CONT),
        row(text="OF THE PART."),
        SEP,
        row(text="D.T. 16-09-30"),
        row("QQ/901", "050", ""),
        row("RSP001", "", "ESEGUIRE ATTACCO CHIMICO DI PROVA DELLE"),
        row(text="D.T. 16-09-30"),
        row("QQ/902", "060", ""),
        row("RSP002", "", "ESEGUIRE CONTROLLO DI PROVA DELLE AREE."),
        row(text=NEXT),
        SEP,
        "*** C O N T I N U A ***",
        row(text="SUPERFICI DI PROVA."),
        row(text="MATERIALE BASE: PROVA"),
        row(text="* * * * * * * * * * * * * *"),
        row(text="SWAB ETCH ALL TEST AREAS."),
        f"{'SCHEDA : PG 901':<24}SP.ORIG. 11-22-33-444-556     SP.XXXX",
        SEP,
    ]
    third = [row(text=CONT), *block(["QQ/903"], "060", ["CHECK THE TEST AREAS."])]
    cycle = parse_pvrm320_report(
        as_document([page(1, first), page(2, second), page(3, third, FOOTER)])
    )
    by_number = ops(cycle)
    assert by_number["050"].operation_description == (
        "ESEGUIRE ATTACCO CHIMICO DI PROVA DELLE SUPERFICI DI PROVA. MATERIALE BASE: PROVA"
        " / SWAB ETCH ALL TEST AREAS."
    )
    assert by_number["050"].process_sheet is not None
    assert by_number["050"].process_sheet.code == "PG 901"
    assert by_number["060"].process_sheet is None
    assert "CHECK THE TEST AREAS." in by_number["060"].operation_description
    # la 040 ha già la parte in inglese: non è un'operazione rimasta a metà
    assert by_number["040"].operation_description == "LAVAGGIO DEL PEZZO. / WASHING OF THE PART."


def test_a_heading_block_between_two_operations_goes_to_the_next_one() -> None:
    """Stampe vere: «***** OPERAZIONE EVENTUALE *****» sta in un blocco a sé, chiuso dal
    tratteggio, e riguarda l'operazione dopo. Prima il parser si fermava («blocco senza numero
    di operazione»)."""
    body = block(["QQ/901"], "010", ["PRIMA OPERAZIONE", STARS, "FIRST OPERATION"])
    body += [row(text="***** OPERAZIONE EVENTUALE *****"), SEP]
    body += block(["QQ/902"], "020", ["SECONDA OPERAZIONE", STARS, "SECOND OPERATION"])
    cycle = parse_pvrm320_report(as_document([page(1, body, FOOTER)]))
    assert [op.operation_number for op in cycle.operations] == ["010", "020"]
    assert cycle.operations[0].operation_description == "PRIMA OPERAZIONE / FIRST OPERATION"
    assert cycle.operations[1].operation_description.startswith(
        "***** OPERAZIONE EVENTUALE ***** SECONDA OPERAZIONE"
    )


def test_a_heading_at_the_end_of_a_page_goes_to_the_first_operation_of_the_next() -> None:
    first = [
        *block(["QQ/901"], "010", ["PRIMA OPERAZIONE"]),
        row(text="***** OPERAZIONE EVENTUALE *****"),
        SEP,
    ]
    second = block(["QQ/902"], "020", ["SECONDA OPERAZIONE"])
    cycle = parse_pvrm320_report(as_document([page(1, first, FOOTER), page(2, second, FOOTER)]))
    assert cycle.operations[1].operation_description.startswith("***** OPERAZIONE EVENTUALE")


def test_ordinary_orphan_text_still_stops_the_parser() -> None:
    body = [*block(["QQ/901"], "010", ["PRIMA OPERAZIONE"]), row(text="TESTO ORFANO"), SEP]
    with pytest.raises(ExtractionError):
        parse_pvrm320_report(as_document([page(1, body, FOOTER)]))


def test_an_empty_repair_field_does_not_take_the_next_line() -> None:
    """27-11 (revisione del codice): `\\s*` dopo i due punti attraversava l'a capo e un campo
    RIPARAZIONE vuoto prendeva la prima parola della riga dopo."""
    from cycle_validation.extract.pvrm320_report import _PAGE_REPAIR

    assert _PAGE_REPAIR.search("RIPARAZIONE :   \nNOTE....... ABC") is None
    found = _PAGE_REPAIR.search("RIPARAZIONE : B1    72-00-00 REPAIR 001")
    assert found is not None and found["repair"] == "B1"


def test_the_task_column_at_the_end_of_a_text_line_is_read_and_left_out_of_the_text() -> None:
    """27-11 sera: la colonna SP.ORIG finita sulla stessa riga del testo era letta come testo;
    ora è il task dell'operazione (H17) e non sta nella descrizione."""
    body = [
        row("ZC/001", "030", "RACCORDARE I DIFETTI."),
        row(text="AREE RACCORDATE. * SP.ORIG. 70-11-00-350-003 SP.FIAT"),
        SEP,
    ]
    operation = ops(parse_pvrm320_report(as_document([page(1, body)])))["030"]
    assert operation.original_task == "70-11-00-350-003"
    assert operation.operation_description == "RACCORDARE I DIFETTI. AREE RACCORDATE."


def test_another_machine_for_the_same_operation_on_the_next_page_is_kept() -> None:
    """H19 (27-11 sera): una stampa con errori aveva la macchina cambiata in una pagina sola."""
    first = block(["QQ/901", "RSP001"], "010", ["PRIMA PARTE"], closed=False)
    second = [row("QQ/902", "010", "SECONDA PARTE"), SEP, row("QQ/903", "020", "ALTRA"), SEP]
    third = [row("QQ/903", "020", "ANCORA"), SEP]
    cycle = parse_pvrm320_report(
        as_document([page(1, first), page(2, second), page(3, third, FOOTER)])
    )
    by_number = ops(cycle)
    assert by_number["010"].machine_tag == "QQ/901"
    assert by_number["010"].other_machine_tags == ["QQ/902"]
    # la stessa targa ripetuta su un'altra pagina non conta
    assert by_number["020"].other_machine_tags == []
