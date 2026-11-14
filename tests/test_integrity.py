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
