"""Controllo `process_sheet`: la scheda esiste ed è applicabile alla famiglia del motore."""

import re
from functools import partial

from cycle_validation.checks.base import CheckContext, guarded, make_result
from cycle_validation.checks.uncertainty import describe, is_doubtful
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.domain.cycle import Operation
from cycle_validation.text import normalize_code

CHECK = CheckName.PROCESS_SHEET


def engine_family(engine_model: str | None, families: list[str]) -> str | None:
    """Famiglia del motore riconosciuta nel modello (per esempio GENX in "GENX-1B")."""
    if engine_model is None:
        return None
    model = normalize_code(engine_model)
    return next((family for family in families if normalize_code(family) in model), None)


# Una parte del trattamento scritto da knowledge-index quando le righe con lo stesso codice
# hanno motori diversi: `testo [GENX, LEAP]`, con l'eventuale ` (ed. X)` dopo.
_ENGINE_PART = re.compile(r"^(?P<text>.*?)\s*\[(?P<families>[^\[\]]*)\](?P<rest>.*)$")
_SEPARATOR = "; "


def treatment_for_family(treatment: str | None, family: str | None) -> str | None:
    """Le sole parti del trattamento legate alla famiglia del motore (`A [GENX]; B [LEAP]`
    con GENX dà `A`). Senza famiglia, o se nessuna parte la nomina, il trattamento intero:
    meglio tutti i valori che nessuno."""
    if family is None or not treatment:
        return treatment
    wanted = normalize_code(family)
    kept: list[str] = []
    for part in treatment.split(_SEPARATOR):
        match = _ENGINE_PART.match(part)
        if match is None:
            continue
        families = {normalize_code(item) for item in match["families"].split(",")}
        if wanted in families:
            kept.append(f"{match['text']}{match['rest']}".strip())
    return _SEPARATOR.join(kept) if kept else treatment


def _check_one(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult:
    sheet = operation.process_sheet
    if sheet is None:
        return make_result(CHECK, target, Reason.CAMPO_ASSENTE, "Nessuna scheda indicata.")
    if not ctx.profile.verify_process_sheet:
        return make_result(
            CHECK,
            target,
            Reason.NON_VERIFICATO_PER_PROFILO,
            f"Le schede non sono verificate per il profilo {ctx.profile.name}.",
        )
    code = normalize_code(sheet.code)
    excluded = next(
        (p for p in ctx.profile.excluded_sheet_prefixes if code.startswith(normalize_code(p))),
        None,
    )
    if excluded is not None:
        return make_result(
            CHECK,
            target,
            Reason.ESCLUSO_DA_REGOLA,
            f"Le schede con prefisso {excluded} sono escluse dal controllo.",
        )
    entry = ctx.kb.find_process_sheet(sheet.code)
    if entry is None:
        return make_result(
            CHECK,
            target,
            Reason.FONTE_ASSENTE,
            f"La scheda {sheet.code} non è presente nei dati delle schede di processo.",
        )
    family = engine_family(ctx.cycle.engine_model, ctx.profile.engine_families)
    allowed = {normalize_code(item) for item in entry.engine_families}
    if family is not None and allowed and normalize_code(family) not in allowed:
        return make_result(
            CHECK,
            target,
            Reason.EVIDENZA_NON_TROVATA,
            f"La scheda {entry.code} non risulta applicabile alla famiglia {family} "
            f"(famiglie previste: {', '.join(entry.engine_families)}).",
        )
    edition = f" edizione {entry.edition}" if entry.edition else ""
    # L'applicabilità si afferma solo se è stata confrontata: serve la famiglia del motore e
    # l'elenco delle famiglie della scheda. Altrimenti è provata soltanto la presenza.
    if family is not None and allowed:
        applicability = f"è presente e applicabile alla famiglia {family}"
    else:
        applicability = "è presente (applicabilità non verificata: " + (
            "la scheda non elenca famiglie di motore)"
            if family is not None
            else "famiglia del motore non riconosciuta)"
        )
    return make_result(
        CHECK,
        target,
        Reason.DATO_INCERTO if is_doubtful(entry.uncertain) else Reason.VERIFICATO,
        f"La scheda {entry.code}{edition} {applicability}." + describe(entry.uncertain),
        evidence=[Evidence(document_key="SP", quote=f"{entry.code}: {entry.treatment or ''}")],
    )


def check_process_sheets(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, operation in enumerate(ctx.cycle.operations):
        target = Target.operation(index, operation)
        results.append(guarded(CHECK, target, partial(_check_one, ctx, target, operation)))
    return results
