"""Stadio 3: ogni valore estratto deve comparire nel testo del PDF, e sulla riga giusta.

Un valore che non compare può essere un errore di estrazione: l'esito del controllo
che lo riguarda non è affidabile e viene declassato a warning (vedi `apply_integrity`).
Lo stesso se il valore compare, ma sotto un'altra operazione: l'estrazione ha sbagliato riga.
"""

import re
from dataclasses import dataclass

from cycle_validation.checks.base import make_result
from cycle_validation.domain.check import CheckName, CheckResult, Reason, Target, TargetKind
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.ingest.pdf import PdfDocument
from cycle_validation.text import squash

CHECK = CheckName.EXTRACTION_INTEGRITY
UnconfirmedKey = tuple[CheckName, TargetKind, int]
# Numeri (con i decimali) e parole di almeno due lettere: ciò che una descrizione afferma.
_TOKEN = re.compile(r"[0-9]+(?:[.,][0-9]+)*|[^\W\d_]{2,}")
# Quota di parole che può mancare dal PDF (sillabazione, refusi corretti dall'estrazione).
_MISSING_WORDS_TOLERATED = 0.2
# Oltre questa quota di codici fuori riga il PDF non è impaginato per righe: non si giudica.
_MISPLACED_TOLERATED = 0.25


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


def _row_values(operation: Operation) -> list[tuple[CheckName, str, str]]:
    """I codici di un'operazione che devono stare sulla sua riga: (controllo, etichetta, valore)."""
    values = []
    if operation.machine_tag is not None:
        values.append((CheckName.MACHINE_TAG, "targa", operation.machine_tag))
    values += [(CheckName.TASK_CODE, "task code", code) for code in operation.task_codes]
    if operation.process_sheet is not None:
        values.append((CheckName.PROCESS_SHEET, "scheda", operation.process_sheet.code))
    return values


def _row_blocks(cycle: Cycle, pdf: PdfDocument) -> dict[int, str]:
    """Il testo di ogni operazione: dalla riga con il suo numero alla riga dell'operazione dopo.

    I numeri si cercano in ordine, ognuno dopo il precedente. Un'operazione il cui numero non
    si trova resta senza blocco, e allora la sua riga non si giudica."""
    lines = pdf.text.splitlines()
    starts: dict[int, int] = {}
    cursor = 0
    for index, operation in enumerate(cycle.operations):
        number = re.compile(rf"(?<![\w-]){re.escape(operation.operation_number)}(?![\w-])")
        found = next((i for i in range(cursor, len(lines)) if number.search(lines[i])), None)
        if found is not None:
            starts[index] = found
            cursor = found + 1
    ordered = sorted(starts.items(), key=lambda item: item[1])
    blocks = {}
    for position, (index, start) in enumerate(ordered):
        end = ordered[position + 1][1] if position + 1 < len(ordered) else len(lines)
        blocks[index] = squash("\n".join(lines[start:end]))
    return blocks


def _misplaced(
    cycle: Cycle, pdf: PdfDocument, haystack: str
) -> dict[int, list[tuple[CheckName, str]]]:
    """Codici che il PDF riporta, ma non sulla riga della loro operazione.

    Se sono tanti, non è l'estrazione che sbaglia riga: è il PDF che non è impaginato per righe
    (per esempio a colonne), e allora non si giudica niente."""
    blocks = _row_blocks(cycle, pdf)
    found: dict[int, list[tuple[CheckName, str]]] = {}
    checked = 0
    for index, block in blocks.items():
        for check, label, value in _row_values(cycle.operations[index]):
            code = squash(value)
            if code not in haystack:
                continue  # già segnalato come valore assente
            checked += 1
            if code not in block:
                found.setdefault(index, []).append((check, f"{label} {value}"))
    wrong = sum(len(items) for items in found.values())
    if not checked or wrong > _MISPLACED_TOLERATED * checked:
        return {}
    return found


def check_extraction_integrity(cycle: Cycle, pdf: PdfDocument) -> IntegrityOutcome:
    haystack = squash(pdf.text)
    misplaced = _misplaced(cycle, pdf, haystack)

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
        elsewhere = misplaced.get(index, [])
        for check, _ in elsewhere:
            unconfirmed.add((check, TargetKind.OPERATION, index))
        problems = []
        if missing:
            problems.append(
                f"Valori estratti che non compaiono nel testo del PDF: {'; '.join(missing)}."
            )
        if elsewhere:
            problems.append(
                "Valori che il PDF riporta su un'altra operazione, non sulla "
                f"{operation.operation_number}: {'; '.join(label for _, label in elsewhere)}."
            )
        if problems:
            results.append(
                make_result(
                    CHECK,
                    Target.operation(index, operation),
                    Reason.ESTRAZIONE_NON_CONFERMATA,
                    " ".join(problems),
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
