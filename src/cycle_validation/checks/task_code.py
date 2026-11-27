"""Controllo `task_code`: i codici citati dall'operazione esistono nei documenti collegati.

Profili "task" (MOS, DR): il codice è un task del manuale citato.
Profili "document" (EJ200): il codice compare nel testo delle pubblicazioni citate.

Profili "task", prima di tutto (H17, 27-11 sera): il task scritto nella colonna SP.ORIG accanto
all'operazione, se è della stessa famiglia del task della testata (stesse prime quattro parti,
per esempio 70-11-00-350) ma diverso, è un ERRATO: la stampa si contraddice. Nelle stampe con
errori messi a mano il task cambiato di una cifra esiste spesso nel manuale, quindi il
controllo «task inesistente» non lo vede. Un task di un'altra famiglia (attacco chimico,
liquidi penetranti, pulizia) è un altro processo e non si confronta.
"""

import re

from cycle_validation.checks.base import CheckContext, evidence_at, make_result, per_operation
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.kb.documents import folded_text
from cycle_validation.kb.port import DocumentInfo
from cycle_validation.resolve.civil import (
    cited_documents,
    manuals_for_operation,
    resolve_operation,
    wrong_code_siblings,
)
from cycle_validation.text import normalize_code, squash

CHECK = CheckName.TASK_CODE


def _by_task(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult:
    refs = resolve_operation(ctx.cycle, operation, ctx.kb)
    manuals = manuals_for_operation(ctx.cycle, operation)
    wrong = {
        code: siblings
        for code in refs.missing
        if (siblings := wrong_code_siblings(ctx.kb, manuals, code))
    }
    if wrong:
        detail = "; ".join(
            f"{code} (nel manuale ci sono {', '.join(siblings[:5])})"
            for code, siblings in wrong.items()
        )
        return make_result(
            CHECK,
            target,
            Reason.TASK_INESISTENTE,
            f"Task code che non esistono nel manuale, codice probabilmente sbagliato: {detail}.",
        )
    if refs.missing:
        return make_result(
            CHECK,
            target,
            Reason.FONTE_ASSENTE,
            f"Task code non trovati nei manuali citati: {', '.join(refs.missing)}.",
        )
    return make_result(
        CHECK,
        target,
        Reason.VERIFICATO,
        "Tutti i task code citati sono presenti nei manuali citati.",
        evidence=[evidence_at(item.document, item.line_start) for item in refs.found],
    )


def _code_pattern(code: str) -> re.Pattern[str]:
    """Il codice per intero: spazi e a capo ammessi tra i caratteri, ma non una lettera o una
    cifra attaccata prima o dopo. `72-31-0` dentro `72-31-00` non è lo stesso codice."""
    body = r"\s*".join(re.escape(char) for char in squash(code))
    return re.compile(rf"(?<![^\W_]){body}(?![^\W_])")


def _find_in_text(code: str, documents: list[DocumentInfo]) -> Evidence | None:
    pattern = _code_pattern(code)
    for document in documents:
        text = folded_text(document.path)
        match = pattern.search(text)
        if match is not None:
            return evidence_at(document, text.count("\n", 0, match.start()) + 1)
    return None


def _by_document(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult:
    documents = cited_documents(ctx.cycle, ctx.kb, ctx.profile.document_order)
    if not documents:
        return make_result(
            CHECK,
            target,
            Reason.FONTE_ASSENTE,
            "Nessuno dei documenti citati dal ciclo è disponibile: codici non verificati.",
        )
    found = {code: _find_in_text(code, documents) for code in operation.task_codes}
    missing = [code for code, evidence in found.items() if evidence is None]
    if missing:
        return make_result(
            CHECK,
            target,
            Reason.EVIDENZA_NON_TROVATA,
            f"Codici non trovati nel testo dei documenti citati: {', '.join(missing)}.",
        )
    return make_result(
        CHECK,
        target,
        Reason.VERIFICATO,
        "Tutti i codici citati compaiono nei documenti citati.",
        evidence=[evidence for evidence in found.values() if evidence is not None],
    )


_FULL_TASK = re.compile(r"^(?P<family>\d{2}-\d{2}-\d{2}-\d{3})-\d{3}$")


def header_task_mismatch(cycle: Cycle, operation: Operation) -> tuple[str, str] | None:
    """(task dell'operazione, task della testata) quando sono della stessa famiglia ma diversi.
    Conta la testata della riparazione dell'operazione, se le fonti dicono la riparazione."""
    code = normalize_code(operation.original_task or "")
    match = _FULL_TASK.match(code)
    if match is None:
        return None
    header = [
        normalize_code(source.task)
        for source in cycle.sources
        if source.task
        and (
            operation.repair_code is None
            or source.repair_code is None
            or normalize_code(source.repair_code) == normalize_code(operation.repair_code)
        )
    ]
    if code in header:
        return None
    same = [
        task for task in header if (m := _FULL_TASK.match(task)) and m["family"] == match["family"]
    ]
    return (code, same[0]) if same else None


def _check_one(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult:
    if ctx.profile.reference_mode != "document" and (
        pair := header_task_mismatch(ctx.cycle, operation)
    ):
        return make_result(
            CHECK,
            target,
            Reason.TASK_DIVERSO_DALLA_TESTATA,
            f"Il task accanto all'operazione ({pair[0]}) è diverso da quello della testata "
            f"({pair[1]}), della stessa famiglia: uno dei due è sbagliato.",
        )
    if not operation.task_codes:
        return make_result(CHECK, target, Reason.CAMPO_ASSENTE, "Nessun task code citato.")
    if ctx.profile.reference_mode == "document":
        return _by_document(ctx, target, operation)
    return _by_task(ctx, target, operation)


def check_task_codes(ctx: CheckContext) -> list[CheckResult]:
    return per_operation(ctx, CHECK, _check_one)
