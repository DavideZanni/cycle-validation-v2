"""Stadio 3: ogni valore estratto deve comparire nel testo del PDF.

Un valore che non compare può essere un errore di estrazione: l'esito del controllo
che lo riguarda non è affidabile e viene declassato a warning (vedi `apply_integrity`).
"""

import re
from dataclasses import dataclass

from cycle_validation.checks.base import make_result
from cycle_validation.domain.check import CheckName, CheckResult, Reason, Target, TargetKind
from cycle_validation.domain.cycle import Cycle
from cycle_validation.ingest.pdf import PdfDocument
from cycle_validation.text import squash

CHECK = CheckName.EXTRACTION_INTEGRITY
UnconfirmedKey = tuple[CheckName, TargetKind, int]
# Numeri (con i decimali) e parole di almeno due lettere: ciò che una descrizione afferma.
_TOKEN = re.compile(r"[0-9]+(?:[.,][0-9]+)*|[^\W\d_]{2,}")
# Quota di parole che può mancare dal PDF (sillabazione, refusi corretti dall'estrazione).
_MISSING_WORDS_TOLERATED = 0.2


@dataclass(frozen=True)
class IntegrityOutcome:
    results: tuple[CheckResult, ...]
    unconfirmed: frozenset[UnconfirmedKey]


def _description_gaps(description: str, haystack: str) -> list[str]:
    """Termini della descrizione che il PDF non riporta, se bastano a non fidarsi: anche un
    solo numero (è su valori e limiti che si decide una contraddizione), oppure troppe parole."""
    tokens = list(dict.fromkeys(_TOKEN.findall(description)))
    missing = [token for token in tokens if squash(token) not in haystack]
    numbers = [token for token in missing if token[0].isdigit()]
    if numbers:
        return numbers
    return missing if len(missing) > _MISSING_WORDS_TOLERATED * len(tokens) else []


def check_extraction_integrity(cycle: Cycle, pdf: PdfDocument) -> IntegrityOutcome:
    haystack = squash(pdf.text)

    def absent(value: str) -> bool:
        return squash(value) not in haystack

    results: list[CheckResult] = []
    unconfirmed: set[UnconfirmedKey] = set()

    for index, source in enumerate(cycle.sources):
        lost: list[str] = []
        if absent(source.manual):
            lost.append(f"manuale {source.manual}")
        if source.task is not None and absent(source.task):
            lost.append(f"task {source.task}")
        if lost:
            unconfirmed.add((CheckName.SOURCE, TargetKind.SOURCE, index))
            results.append(
                make_result(
                    CHECK,
                    Target.source(index, source),
                    Reason.ESTRAZIONE_NON_CONFERMATA,
                    f"Valori estratti che non compaiono nel testo del PDF: {'; '.join(lost)}.",
                )
            )

    for index, operation in enumerate(cycle.operations):
        missing: list[str] = []
        if absent(operation.operation_number):
            missing.append(f"numero operazione {operation.operation_number}")
        if operation.machine_tag is not None and absent(operation.machine_tag):
            missing.append(f"targa {operation.machine_tag}")
            unconfirmed.add((CheckName.MACHINE_TAG, TargetKind.OPERATION, index))
        lost_codes = [code for code in operation.task_codes if absent(code)]
        if lost_codes:
            missing.append(f"task code {', '.join(lost_codes)}")
            unconfirmed.add((CheckName.TASK_CODE, TargetKind.OPERATION, index))
        if operation.process_sheet is not None and absent(operation.process_sheet.code):
            missing.append(f"scheda {operation.process_sheet.code}")
            unconfirmed.add((CheckName.PROCESS_SHEET, TargetKind.OPERATION, index))
        gaps = _description_gaps(operation.operation_description, haystack)
        if gaps:
            missing.append(f"descrizione ({', '.join(gaps[:5])})")
            unconfirmed.add((CheckName.OPERATION_DESCRIPTION, TargetKind.OPERATION, index))
        if missing:
            results.append(
                make_result(
                    CHECK,
                    Target.operation(index, operation),
                    Reason.ESTRAZIONE_NON_CONFERMATA,
                    f"Valori estratti che non compaiono nel testo del PDF: {'; '.join(missing)}.",
                )
            )

    if not results:
        results.append(
            make_result(
                CHECK,
                Target.cycle(),
                Reason.VERIFICATO,
                "Tutti i valori estratti compaiono nel testo del PDF.",
            )
        )
    return IntegrityOutcome(tuple(results), frozenset(unconfirmed))
