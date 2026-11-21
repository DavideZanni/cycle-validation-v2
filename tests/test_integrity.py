from cycle_validation.domain.check import CheckName, Reason, TargetKind
from cycle_validation.domain.cycle import Cycle
from cycle_validation.extract.integrity import check_extraction_integrity
from cycle_validation.ingest.pdf import PdfDocument, PdfPage


def _pdf(text: str) -> PdfDocument:
    return PdfDocument(
        name="c.pdf", sha256="0" * 64, size_bytes=1, pages=(PdfPage(number=1, text=text),)
    )


CYCLE = Cycle.model_validate(
    {
        "sources": [{"manual": "M1", "task": "72-00-01"}],
        "operations": [
            {
                "operation_number": "0010",
                "machine_tag": "TM-1001",
                "task_codes": ["72-00-01", "72-00-02"],
                "process_sheet": "SP-0101",
            }
        ],
    }
)


def test_all_values_confirmed() -> None:
    text = "Manuale M1\nOp 0010  Targa TM - 1001\nTask 72-00-01 e 72-00-02\nScheda SP-0101"
    outcome = check_extraction_integrity(CYCLE, _pdf(text))
    assert [result.reason for result in outcome.results] == [Reason.VERIFICATO]
    assert outcome.results[0].target.kind is TargetKind.CYCLE
    assert outcome.unconfirmed == frozenset()


def test_missing_values_are_reported_per_element() -> None:
    outcome = check_extraction_integrity(CYCLE, _pdf("Op 0010  Task 72-00-02"))
    reasons = {result.target.kind: result for result in outcome.results}
    assert set(reasons) == {TargetKind.SOURCE, TargetKind.OPERATION}
    operation = reasons[TargetKind.OPERATION]
    assert operation.reason is Reason.ESTRAZIONE_NON_CONFERMATA
    assert "targa TM-1001" in operation.rationale
    assert "task code 72-00-01" in operation.rationale
    assert "scheda SP-0101" in operation.rationale
    assert outcome.unconfirmed == {
        (CheckName.SOURCE, TargetKind.SOURCE, 0),
        (CheckName.MACHINE_TAG, TargetKind.OPERATION, 0),
        (CheckName.TASK_CODE, TargetKind.OPERATION, 0),
        (CheckName.PROCESS_SHEET, TargetKind.OPERATION, 0),
    }


def test_missing_operation_number_is_reported_without_downgrading_checks() -> None:
    text = "Manuale M1 Targa TM-1001 Task 72-00-01 72-00-02 Scheda SP-0101"
    outcome = check_extraction_integrity(CYCLE, _pdf(text))
    assert "numero operazione 0010" in outcome.results[0].rationale
    assert outcome.unconfirmed == frozenset()


def test_a_manual_that_is_not_in_the_pdf_leaves_the_source_unconfirmed() -> None:
    # un manuale inventato dall'estrazione ma presente nella knowledge base darebbe CORRETTO
    text = "Op 0010 Targa TM-1001 Task 72-00-01 72-00-02 Scheda SP-0101"
    outcome = check_extraction_integrity(CYCLE, _pdf(text))
    assert outcome.unconfirmed == {(CheckName.SOURCE, TargetKind.SOURCE, 0)}
    assert "manuale M1" in outcome.results[0].rationale


def _described(description: str) -> Cycle:
    return Cycle.model_validate(
        {"operations": [{"operation_number": "0010", "operation_description": description}]}
    )


DESCRIPTION_KEY = (CheckName.OPERATION_DESCRIPTION, TargetKind.OPERATION, 0)


def test_a_description_reflowed_by_the_page_layout_is_confirmed() -> None:
    cycle = _described("Rettificare la sede fino al diametro 45,00 mm.")
    text = "Op 0010   RETTIFICARE LA SEDE\n      fino  al diametro 45,00   mm."
    assert check_extraction_integrity(cycle, _pdf(text)).unconfirmed == frozenset()


def test_a_number_that_is_not_in_the_pdf_leaves_the_description_unconfirmed() -> None:
    # il giudizio del modello su un valore che il PDF non riporta non proverebbe nulla sul ciclo
    cycle = _described("Rettificare la sede fino al diametro 46,00 mm.")
    outcome = check_extraction_integrity(
        cycle, _pdf("Op 0010 Rettificare la sede fino al diametro 45,00 mm.")
    )
    assert outcome.unconfirmed == {DESCRIPTION_KEY}
    assert "46,00" in outcome.results[0].rationale


def test_a_description_mostly_absent_from_the_pdf_is_unconfirmed() -> None:
    cycle = _described("Lavare il pezzo e asciugare con cura")
    outcome = check_extraction_integrity(cycle, _pdf("Op 0010 Ispezionare il pezzo"))
    assert outcome.unconfirmed == {DESCRIPTION_KEY}


def test_one_reworded_word_in_a_long_description_is_tolerated() -> None:
    cycle = _described("Pulire accuratamente il supporto con solvente tipo A e asciugare")
    text = "Op 0010 Pulire accurata- mente il supporto con solvente tipo A e asciugare"
    assert check_extraction_integrity(cycle, _pdf(text)).unconfirmed == frozenset()


ROWS = (
    "OPERAZIONE 0010 Pulire il supporto.\nTarga TM-1001 Task 72-00-01-110-001\nScheda SP-0101\n"
    "OPERAZIONE 0020 Rettificare la sede.\nTarga TM-2002 Task 72-00-01-350-003\n"
    "OPERAZIONE 0030 Ispezionare la superficie.\nTarga TM-3003 Task 72-00-01-220-002\n"
    "OPERAZIONE 0040 Applicare protettivo.\nTarga - Task 72-00-01-999-009\nScheda SP-0202\n"
)


def _rows(**changes: dict[str, object]) -> Cycle:
    operations = [
        {
            "operation_number": "0010",
            "operation_description": "Pulire il supporto.",
            "machine_tag": "TM-1001",
            "task_codes": ["72-00-01-110-001"],
            "process_sheet": "SP-0101",
        },
        {
            "operation_number": "0020",
            "operation_description": "Rettificare la sede.",
            "machine_tag": "TM-2002",
            "task_codes": ["72-00-01-350-003"],
        },
        {
            "operation_number": "0030",
            "operation_description": "Ispezionare la superficie.",
            "machine_tag": "TM-3003",
            "task_codes": ["72-00-01-220-002"],
        },
        {
            "operation_number": "0040",
            "operation_description": "Applicare protettivo.",
            "task_codes": ["72-00-01-999-009"],
            "process_sheet": "SP-0202",
        },
    ]
    for number, change in changes.items():
        operations[int(number[1:])].update(change)
    return Cycle.model_validate({"operations": operations})


def test_rows_read_correctly_are_confirmed() -> None:
    outcome = check_extraction_integrity(_rows(), _pdf(ROWS))
    assert outcome.unconfirmed == frozenset()


def test_a_value_taken_from_another_row_is_not_confirmed() -> None:
    # La targa c'è nel PDF, ma su un'altra operazione: l'estrazione ha sbagliato riga.
    cycle = _rows(o3={"machine_tag": "TM-3003", "process_sheet": "SP-0101"})
    outcome = check_extraction_integrity(cycle, _pdf(ROWS))
    assert outcome.unconfirmed == {
        (CheckName.MACHINE_TAG, TargetKind.OPERATION, 3),
        (CheckName.PROCESS_SHEET, TargetKind.OPERATION, 3),
    }
    (result,) = outcome.results
    assert result.target.index == 3
    assert "TM-3003" in result.rationale and "su un'altra operazione" in result.rationale


def test_a_layout_by_columns_is_not_judged_by_rows() -> None:
    # Numeri, poi targhe, poi task in colonne: le righe non si ricostruiscono, non si giudica.
    columns = (
        "0010 0020 0030 0040\nPulire il supporto. Rettificare la sede. Ispezionare la superficie."
        " Applicare protettivo.\nTM-1001 TM-2002 TM-3003 -\n72-00-01-110-001 72-00-01-350-003 "
        "72-00-01-220-002 72-00-01-999-009\nSP-0101 SP-0202\n"
    )
    outcome = check_extraction_integrity(_rows(), _pdf(columns))
    assert outcome.unconfirmed == frozenset()


BANNER_TAIL = ROWS + "*** C O N T I N U A ***\nSEGUITO DELLA 0030.\nScheda SP-0303\n"


def test_a_sheet_after_the_page_end_banner_belongs_to_an_operation_of_that_page() -> None:
    # Stampe DR vere: il seguito di un'operazione rimasta a metà, scheda compresa, sta dopo il
    # banner di fine pagina, quindi dopo la riga dell'operazione successiva.
    on_page = _rows(o2={"process_sheet": "SP-0303", "page": 1})
    assert check_extraction_integrity(on_page, _pdf(BANNER_TAIL)).unconfirmed == frozenset()


def test_without_the_page_a_sheet_after_the_banner_is_still_out_of_row() -> None:
    outcome = check_extraction_integrity(_rows(o2={"process_sheet": "SP-0303"}), _pdf(BANNER_TAIL))
    assert outcome.unconfirmed == {(CheckName.PROCESS_SHEET, TargetKind.OPERATION, 2)}
