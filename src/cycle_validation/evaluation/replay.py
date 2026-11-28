"""Prove rigiocate (`eval rigioca`, 28-11): una regola finale sulle prove già fatte, a 0 $.

Le regole finali (`verdict/final_rules.py`) lavorano solo sugli esiti già fatti: applicate ai
`report.json` delle prove di riferimento danno esattamente quello che darebbe una prova vera
con quelle stesse risposte del modello. Così non serve una campagna: si rifà il conto delle
prove di riferimento (con gli errori noti di adesso, anche copie cieche e gruppo nascosto) e
delle stesse prove con la regola in più, e si decide con le regole di sempre (`riepilogo.md`).

Vale solo per una variante che cambia **soltanto** le regole finali: se cambia anche il codice
dei controlli si prova con `eval senza-modello --variante`, se cambia il modello o il prompt
serve la campagna."""

import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cycle_validation.config import Settings
from cycle_validation.domain.report import Report
from cycle_validation.evaluation.trials import (
    REFERENCE_FILE,
    TRIAL_FILE,
    CycleScore,
    KnownErrors,
    Proposal,
    Trial,
    _read_trials,
    score_cycle,
    write_summary,
    write_trial,
)
from cycle_validation.verdict.final_rules import quote_diagnosis, quote_shapes, replay_report

REPLAYABLE = "agent.final_rules"


def _flat(data: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for key, value in data.items():
            out.update(_flat(value, f"{prefix}{key}."))
        return out
    return {prefix.rstrip("."): data}


def other_changes(reference: Settings, variant: Settings) -> list[str]:
    """Le impostazioni che la variante cambia oltre alle regole finali (vuoto = si rigioca)."""
    old, new = _flat(reference.model_dump(mode="json")), _flat(variant.model_dump(mode="json"))
    keys = sorted(set(old) | set(new))
    return [k for k in keys if k != REPLAYABLE and old.get(k) != new.get(k)]


def extra_rules(reference: Settings, variant: Settings) -> list[str]:
    """Le regole da aggiungere ai report di riferimento: quelle della variante dopo quelle che il
    riferimento aveva già. Errore se la variante non comincia con le regole del riferimento."""
    before, after = reference.agent.final_rules, variant.agent.final_rules
    if after[: len(before)] != before:
        raise ValueError(
            "la variante deve avere prima le regole finali del riferimento "
            f"({', '.join(before)}), poi le sue"
        )
    return after[len(before) :]


def _report(path: Path) -> Report | None:
    try:
        return Report.model_validate_json(path.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def replay_trials(
    root: Path,
    reference: str,
    variant: str,
    rules: Sequence[str],
    known: KnownErrors,
    proposal: Proposal | None = None,
) -> list[tuple[Trial, Trial]]:
    """Per ogni prova di `reference` nella cartella: (la prova ricalcolata con gli errori noti
    di adesso, la stessa con le regole `rules`). I cicli senza `report.json` (non eseguiti)
    restano come sono. Le prove in cui il modello non ha risposto si saltano."""
    pairs: list[tuple[Trial, Trial]] = []
    for path, trial in _read_trials(sorted(root.glob(f"*/{TRIAL_FILE}"))):
        if trial.name.strip().casefold() != reference.casefold() or trial.unusable:
            continue
        before: list[CycleScore] = []
        after: list[CycleScore] = []
        for cycle in trial.cycles:
            report = _report(path.parent / cycle.fingerprint / "report.json")
            if report is None:
                before.append(cycle)
                after.append(cycle)
                continue
            before.append(score_cycle(report, known, cycle.fingerprint))
            after.append(score_cycle(replay_report(report, rules), known, cycle.fingerprint))
        pairs.append(
            (
                trial.model_copy(update={"cycles": before}),
                trial.model_copy(
                    update={"name": variant, "cycles": after, "proposal": proposal or Proposal()}
                ),
            )
        )
    return pairs


def false_ok_quotes(root: Path, reference: str, known: KnownErrors) -> list[str]:
    """MG87: per ogni falso OK delle prove di `reference` (errore noto mancato con CORRETTO),
    che cosa c'è nella riga citata dal modello. Solo impronta, operazione, sì/no e conteggi."""
    lines: list[str] = []
    for path, trial in _read_trials(sorted(root.glob(f"*/{TRIAL_FILE}"))):
        if trial.name.strip().casefold() != reference.casefold() or trial.unusable:
            continue
        for cycle in trial.cycles:
            report = _report(path.parent / cycle.fingerprint / "report.json")
            if report is None:
                continue
            for missed in score_cycle(report, known, cycle.fingerprint).missed:
                if missed.said.startswith("CORRETTO"):
                    diagnosis = quote_diagnosis(report.cycle, report.results, missed.op)
                    shapes = quote_shapes(report.cycle, report.results, missed.op)
                    lines.append(f"{cycle.fingerprint} {missed.op}: {diagnosis}")
                    lines.append(f"{cycle.fingerprint} {missed.op} forma: {shapes}")
    return lines


def write_replay(folder: Path, reference: str, pairs: Sequence[tuple[Trial, Trial]]) -> Path:
    """Le prove rigiocate in una cartella loro (si rifà da capo ogni volta), con il riepilogo
    e la decisione contro `reference`."""
    if folder.exists():
        shutil.rmtree(folder)
    for number, (before, after) in enumerate(pairs, start=1):
        write_trial(before, folder / f"{number:02d}-riferimento")
        write_trial(after, folder / f"{number:02d}-rigiocata")
    (folder / REFERENCE_FILE).write_text(reference, "utf-8")
    return write_summary(folder)
