"""Controllo `process_sheet`: la scheda esiste ed è applicabile alla famiglia del motore.

Con `agent.sheet_consistency` (H18, 27-11 sera) la scheda deve anche essere coerente con
l'operazione, deciso dal codice: ERRATO se è di un'altra famiglia di motore, se il materiale
del suo trattamento non è quello scritto nella descrizione («materiale base: ...»), se il task
scritto accanto alla scheda non c'è nel manuale (che ha però task della stessa famiglia), o se
l'indice non ha la scheda ma ne ha altre con lo stesso prefisso. Nelle stampe con errori
messi a mano la v1 trova così le schede cambiate: un'altra lega, un altro motore, una cifra del
task cambiata.
"""

import re

from cycle_validation.checks.base import CheckContext, make_result, per_operation
from cycle_validation.checks.uncertainty import describe, is_doubtful
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.domain.cycle import Operation
from cycle_validation.kb.port import ProcessSheetEntry, process_sheets
from cycle_validation.resolve.civil import locate_task, manuals_for_operation, wrong_code_siblings
from cycle_validation.text import normalize_code, sheet_key

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


# Processi speciali (P6, decisa il 26-11): lì la scheda di processo è obbligatoria. Si
# riconoscono dalla descrizione, in italiano o in inglese.
_SPECIAL_PROCESS = re.compile(
    r"lubrificant\w*\s+secc\w*|rivestiment\w*|attacco\s+chimic\w*|liquidi\s+penetranti"
    r"|penetrant\w*|dry[\s-]+film|dry\s+lubricant\w*|coating\w*|chemical\s+etch\w*"
    r"|etching|\bFPI\b",
    re.IGNORECASE,
)


def special_process(description: str | None) -> str | None:
    """La parola del processo speciale nella descrizione, se c'è."""
    found = _SPECIAL_PROCESS.search(description or "")
    return found.group(0) if found else None


# Materiali (H18): gruppo → parole in italiano e in inglese. Il gamma TiAl è una lega di
# titanio: una scheda per il titanio non è un materiale diverso.
_MATERIALS: dict[str, re.Pattern[str]] = {
    "gamma TiAl": re.compile(
        r"gamma\s*-?\s*ti\s*-?\s*al\b|\btial\b|titanium\s+aluminide|alluminur\w*\s+di\s+titanio",
        re.IGNORECASE,
    ),
    "titanio": re.compile(r"\btitan(?:ium|io)\b|\bti[\s-]+(?:alloy|base)", re.IGNORECASE),
    "nichel": re.compile(
        r"\bnickel\b|\bnichel\b|\bni[\s-]+(?:based|base|alloy)|\binconel", re.IGNORECASE
    ),
    "cobalto": re.compile(r"\bcobalt\w*", re.IGNORECASE),
    "alluminio": re.compile(r"\balumin(?:um|ium|io)\b", re.IGNORECASE),
    "acciaio": re.compile(r"\bsteel\b|\bacciai[oi]\b", re.IGNORECASE),
}
_SAME_FAMILY = {"gamma TiAl": {"titanio"}, "titanio": {"gamma TiAl"}}
# «materiale base: gamma tial», «base material: ...»: fino al punto o alla parola dopo
_STATED_MATERIAL = re.compile(
    r"\b(?:base\s+)?materia(?:l|le)(?:\s+base)?\s*:\s*(?P<what>[^.;:/]{2,60})", re.IGNORECASE
)


def materials(text: str | None) -> set[str]:
    """I gruppi di materiale nominati nel testo."""
    return {name for name, pattern in _MATERIALS.items() if pattern.search(text or "")}


def stated_materials(description: str | None) -> set[str]:
    """I materiali scritti dopo «materiale base:» o «base material:» nella descrizione. Solo
    lì: altrove una descrizione può nominare un materiale per altri motivi (attrezzi, divieti)."""
    found: set[str] = set()
    for match in _STATED_MATERIAL.finditer(description or ""):
        found |= materials(match["what"])
    return found


def material_mismatch(description: str | None, treatment: str | None) -> tuple[set[str], set[str]]:
    """(materiali della descrizione, materiali della scheda) se non hanno niente in comune;
    insiemi vuoti se uno dei due non dice il materiale o se sono compatibili."""
    stated, sheet = stated_materials(description), materials(treatment)
    if not stated or not sheet:
        return set(), set()
    compatible = stated | {other for name in stated for other in _SAME_FAMILY.get(name, ())}
    return (stated, sheet) if not compatible & sheet else (set(), set())


_LETTERS = re.compile(r"^[A-Z]+")


def same_prefix_sheets(code: str, sheets: list[ProcessSheetEntry]) -> list[str]:
    """Le schede dell'indice con le stesse lettere iniziali (`ZZ` per `ZZ101-AA`), se
    l'indice non ha quella cercata."""
    prefix = _LETTERS.match(sheet_key(code))
    if prefix is None:
        return []
    wanted = sheet_key(code)
    if any(sheet_key(entry.code) == wanted for entry in sheets):
        return []
    found = {
        entry.code
        for entry in sheets
        if (other := _LETTERS.match(sheet_key(entry.code))) and other[0] == prefix[0]
    }
    return sorted(found)


_FULL_TASK = re.compile(r"^\d{2}-\d{2}-\d{2}-\d{3}-\d{3}$")


def _sheet_task(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult | None:
    """ERRATO se il task scritto accanto alla scheda (colonna SP.ORIG) non c'è nei manuali
    collegati, che hanno però task della stessa famiglia."""
    task = normalize_code(operation.original_task or "")
    if not _FULL_TASK.match(task) or ctx.profile.reference_mode == "document":
        return None
    manuals = manuals_for_operation(ctx.cycle, operation)
    if locate_task(ctx.kb, manuals, task) is not None:
        return None
    siblings = wrong_code_siblings(ctx.kb, manuals, task)
    if not siblings:
        return None
    return make_result(
        CHECK,
        target,
        Reason.TASK_INESISTENTE,
        f"Il task della scheda ({task}) non esiste nel manuale, che ha {', '.join(siblings[:5])}: "
        "codice probabilmente sbagliato.",
    )


def _check_one(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult:
    sheet = operation.process_sheet
    if sheet is None:
        process = special_process(operation.operation_description)
        if ctx.agent.special_process_sheet and process is not None:
            # un avviso, mai ERRATO (regola P6, confermata dall'utente il 27-11 sera)
            return make_result(
                CHECK,
                target,
                Reason.SCHEDA_FORSE_MANCANTE,
                f"Scheda mancante: operazione di processo speciale («{process}») senza scheda "
                "di processo.",
            )
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
    strict = ctx.agent.sheet_consistency
    if strict and (wrong_task := _sheet_task(ctx, target, operation)) is not None:
        return wrong_task
    entry = ctx.kb.find_process_sheet(sheet.code)
    if entry is None:
        others = same_prefix_sheets(sheet.code, process_sheets(ctx.kb)) if strict else []
        if others:
            return make_result(
                CHECK,
                target,
                Reason.SCHEDA_INESISTENTE,
                f"La scheda {sheet.code} non esiste nell'indice delle schede, che ha "
                f"{', '.join(others[:5])}: codice probabilmente sbagliato.",
            )
        return make_result(
            CHECK,
            target,
            Reason.FONTE_ASSENTE,
            f"La scheda {sheet.code} non è presente nei dati delle schede di processo.",
        )
    family = engine_family(ctx.cycle.engine_model, ctx.profile.engine_families)
    allowed = {normalize_code(item) for item in entry.engine_families}
    doubtful = is_doubtful(entry.uncertain)
    if family is not None and allowed and normalize_code(family) not in allowed:
        return make_result(
            CHECK,
            target,
            Reason.SCHEDA_ALTRO_MOTORE if strict and not doubtful else Reason.EVIDENZA_NON_TROVATA,
            f"La scheda {entry.code} non risulta applicabile alla famiglia {family} "
            f"(famiglie previste: {', '.join(entry.engine_families)}).",
        )
    if strict and not doubtful:
        stated, written = material_mismatch(
            operation.operation_description, treatment_for_family(entry.treatment, family)
        )
        if stated:
            return make_result(
                CHECK,
                target,
                Reason.SCHEDA_MATERIALE_DIVERSO,
                f"La scheda {entry.code} è per {', '.join(sorted(written))}, la descrizione dice "
                f"materiale {', '.join(sorted(stated))}: scheda probabilmente sbagliata.",
                evidence=[Evidence(document_key="SP", quote=f"{entry.code}: {entry.treatment}")],
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
        Reason.DATO_INCERTO if doubtful else Reason.VERIFICATO,
        f"La scheda {entry.code}{edition} {applicability}." + describe(entry.uncertain),
        evidence=[Evidence(document_key="SP", quote=f"{entry.code}: {entry.treatment or ''}")],
    )


def check_process_sheets(ctx: CheckContext) -> list[CheckResult]:
    return per_operation(ctx, CHECK, _check_one)
