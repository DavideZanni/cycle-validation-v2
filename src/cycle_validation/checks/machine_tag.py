"""Controllo `machine_tag`: la targa esiste nei dati TM e la macchina è attiva.

Il registro delle macchine attive è la sorgente autorevole: una macchina dei dati TM che non è
attiva è un errore. Una targa che non c'è da nessuna parte (né nei dati TM né tra le attive) è
un warning "targa sconosciuta": di solito è scritta in un altro modo o l'elenco è incompleto.
Una targa attiva ma assente dai dati TM è anch'essa un warning.

Prima di tutto (anche con il registro spento, come sul PC): la stessa operazione con targhe
diverse su pagine diverse è un ERRATO, la stampa si contraddice (H19, 27-11 sera: una stampa
con errori messi a mano aveva una macchina cambiata in una pagina sola).
"""

from cycle_validation.checks.base import CheckContext, make_result, per_operation
from cycle_validation.checks.uncertainty import describe, is_doubtful
from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Reason, Target
from cycle_validation.domain.cycle import Operation

CHECK = CheckName.MACHINE_TAG


def _check_one(ctx: CheckContext, target: Target, operation: Operation) -> CheckResult:
    tag = operation.machine_tag
    if tag is not None and operation.other_machine_tags:
        others = ", ".join(operation.other_machine_tags)
        return make_result(
            CHECK,
            target,
            Reason.MACCHINE_DIVERSE,
            f"La stessa operazione ha targhe diverse nella stampa: {tag} e {others}. Una delle "
            "due è sbagliata.",
        )
    if tag is None:
        return make_result(CHECK, target, Reason.CAMPO_ASSENTE, "Nessuna targa macchina indicata.")
    entry = ctx.kb.find_machine_tag(tag)
    active = ctx.machines.is_active(tag)
    if not active and entry is None:
        return make_result(
            CHECK,
            target,
            Reason.TARGA_SCONOSCIUTA,
            f"Targa sconosciuta: {tag} non è nei dati delle targhe né tra le macchine attive. "
            "Va controllato come è scritta.",
        )
    if not active:
        return make_result(
            CHECK,
            target,
            Reason.MACCHINA_NON_ATTIVA,
            f"La macchina {tag} non risulta attiva nel registro delle macchine.",
        )
    if entry is None:
        return make_result(
            CHECK,
            target,
            Reason.FONTE_ASSENTE,
            f"La macchina {tag} è attiva ma non è presente nei dati delle targhe.",
        )
    function = f" ({entry.function})" if entry.function else ""
    return make_result(
        CHECK,
        target,
        Reason.DATO_INCERTO if is_doubtful(entry.uncertain) else Reason.VERIFICATO,
        f"La macchina {tag}{function} è attiva e presente nei dati delle targhe."
        + describe(entry.uncertain),
        evidence=[Evidence(document_key="TM", quote=f"{entry.tag}: {entry.function or ''}")],
    )


def check_machine_tags(ctx: CheckContext) -> list[CheckResult]:
    return per_operation(ctx, CHECK, _check_one)
