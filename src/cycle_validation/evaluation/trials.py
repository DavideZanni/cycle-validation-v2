"""Prove sui cicli veri: punteggio contro gli errori noti, report di ogni prova, riepilogo.

Una *prova* è un giro della v2 sugli stessi cicli (quelli «con errori», con gli errori messi
apposta e conosciuti, e le stampe giuste da cui sono stati fatti). Per ogni prova si scrivono
`prova.json` (i numeri) e `prestazioni.md` (il report da leggere); il riepilogo
`riepilogo.md` mette insieme tutte le prove della cartella.

Gli errori noti stanno in un file YAML (`eval/errori-noti.yaml`): per ogni ciclo, indicato con
le prime 8 cifre dell'impronta SHA-256 del PDF, le operazioni sbagliate apposta con una breve
descrizione, oppure `giusto: true` per una stampa senza errori. Niente codici veri: solo
impronte, numeri di operazione e descrizioni generiche.
"""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from cycle_validation.domain.check import CheckName, TargetKind, Verdict
from cycle_validation.domain.report import Report

TRIAL_FILE = "prova.json"
TRIAL_REPORT = "prestazioni.md"
SUMMARY_REPORT = "riepilogo.md"
_RATIONALE_CHARS = 200


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KnownCycle(_Strict):
    """Un ciclo della prova: gli errori messi apposta (operazione → descrizione) o giusto."""

    errori: dict[str, str] = Field(default_factory=dict)
    giusto: bool = False
    # per una stampa giusta: l'impronta della stampa «con errori» fatta da lei
    di: str | None = None


class KnownErrors(_Strict):
    cicli: dict[str, KnownCycle]

    def cycle(self, fingerprint: str) -> KnownCycle | None:
        return self.cicli.get(fingerprint)


def load_known_errors(path: Path) -> KnownErrors:
    raw = yaml.safe_load(path.read_text("utf-8")) or {}
    cycles = {
        str(key).lower(): KnownCycle.model_validate(
            {
                **(value or {}),
                "errori": {
                    op_key(op): str(text)
                    for op, text in ((value or {}).get("errori") or {}).items()
                },
            }
        )
        for key, value in (raw.get("cicli") or {}).items()
    }
    return KnownErrors(cicli=cycles)


def op_key(label: object) -> str:
    """Numero di operazione confrontabile: `5`, `05`, `0005` → `005`."""
    text = str(label).strip()
    return f"{int(text):03d}" if text.isdigit() else text


class Finding(_Strict):
    """Un ERRATO della v2 su un'operazione."""

    op: str
    check: str
    reason: str
    rationale: str = ""
    # descrizione dell'errore noto, se l'ERRATO ne trova uno
    known: str | None = None


class Missed(_Strict):
    """Un errore noto che la v2 non ha segnato, con quello che ha detto su quell'operazione."""

    op: str
    known: str
    said: str = ""


class CycleScore(_Strict):
    fingerprint: str
    kind: str  # "errori" | "giusto" | "sconosciuto"
    status: str
    counts: dict[str, int] = Field(default_factory=dict)
    found: list[Finding] = Field(default_factory=list)
    missed: list[Missed] = Field(default_factory=list)
    extra: list[Finding] = Field(default_factory=list)
    cost_usd: float = 0.0
    tokens: int = 0
    duration_ms: int = 0
    failure: str | None = None


class Trial(_Strict):
    name: str
    started_at: datetime
    model: str = ""
    knowledge_version: str = ""
    prompt_version: str = ""
    tool_version: str = ""
    cycles: list[CycleScore] = Field(default_factory=list)

    @property
    def known_total(self) -> int:
        return sum(len(c.found) + len(c.missed) for c in self.cycles if c.kind == "errori")

    @property
    def known_found(self) -> int:
        return sum(len(c.found) for c in self.cycles if c.kind == "errori")

    @property
    def false_errors(self) -> int:
        return sum(len(c.extra) for c in self.cycles if c.kind == "giusto")

    @property
    def extra_errors(self) -> int:
        return sum(len(c.extra) for c in self.cycles if c.kind != "giusto")

    @property
    def cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.cycles)

    @property
    def tokens(self) -> int:
        return sum(c.tokens for c in self.cycles)

    @property
    def duration_ms(self) -> int:
        return sum(c.duration_ms for c in self.cycles)

    @property
    def failures(self) -> int:
        return sum(1 for c in self.cycles if c.failure)

    def found_ops(self) -> set[tuple[str, str]]:
        return {(c.fingerprint, f.op) for c in self.cycles for f in c.found}


def _short(text: str, limit: int = _RATIONALE_CHARS) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def score_cycle(report: Report, known: KnownErrors) -> CycleScore:
    """Punteggio di un ciclo: ERRATO sulle operazioni confrontati con gli errori noti."""
    fingerprint = report.meta.pdf_sha256[:8].lower()
    entry = known.cycle(fingerprint)
    kind = "sconosciuto" if entry is None else ("giusto" if entry.giusto else "errori")
    expected = entry.errori if entry is not None else {}
    errato: dict[str, Finding] = {}
    said: dict[str, str] = {}
    for result in report.results:
        if result.target.kind is not TargetKind.OPERATION:
            continue
        op = op_key(result.target.label)
        if result.verdict is Verdict.ERRATO and op not in errato:
            errato[op] = Finding(
                op=op,
                check=result.check.value,
                reason=result.reason.value,
                rationale=_short(result.rationale),
                known=expected.get(op),
            )
        if result.check is CheckName.OPERATION_DESCRIPTION:
            said[op] = f"{result.verdict.value} {result.reason.value}: {_short(result.rationale)}"
    usage = report.usage
    return CycleScore(
        fingerprint=fingerprint,
        kind=kind,
        status=report.status.value,
        counts={
            "corretto": report.counts.corretto,
            "warning": report.counts.warning,
            "errato": report.counts.errato,
            "non_applicabile": report.counts.non_applicabile,
        },
        found=[errato[op] for op in sorted(errato) if op in expected],
        missed=[
            Missed(op=op, known=text, said=said.get(op, ""))
            for op, text in sorted(expected.items())
            if op not in errato
        ],
        extra=[errato[op] for op in sorted(errato) if op not in expected],
        cost_usd=usage.cost_usd,
        tokens=usage.input_tokens + usage.output_tokens,
        duration_ms=report.timings_ms.get("total", usage.wall_ms),
    )


def failed_cycle(fingerprint: str, known: KnownErrors, failure: str) -> CycleScore:
    """Un ciclo che la v2 non ha validato: i suoi errori noti contano come mancati."""
    entry = known.cycle(fingerprint)
    kind = "sconosciuto" if entry is None else ("giusto" if entry.giusto else "errori")
    expected = entry.errori if entry is not None else {}
    return CycleScore(
        fingerprint=fingerprint,
        kind=kind,
        status="non eseguito",
        missed=[Missed(op=op, known=text) for op, text in sorted(expected.items())],
        failure=_short(failure),
    )


def build_trial(
    name: str, started_at: datetime, reports: Sequence[Report], cycles: Sequence[CycleScore]
) -> Trial:
    """La prova: i punteggi dei cicli, nell'ordine «con errori», giusti, sconosciuti."""
    order = {"errori": 0, "giusto": 1, "sconosciuto": 2}
    meta = reports[0].meta if reports else None
    return Trial(
        name=name,
        started_at=started_at,
        model=meta.model if meta else "",
        knowledge_version=meta.knowledge_version if meta else "",
        prompt_version=meta.prompt_version if meta else "",
        tool_version=meta.tool_version if meta else "",
        cycles=sorted(cycles, key=lambda c: (order.get(c.kind, 3), c.fingerprint)),
    )


def _percent(part: int, whole: int) -> str:
    return f"{round(100 * part / whole)}%" if whole else "-"


def _seconds(ms: int) -> str:
    seconds = round(ms / 1000)
    return f"{seconds // 60} min {seconds % 60:02d} s" if seconds >= 60 else f"{seconds} s"


def _cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")


def render_trial(trial: Trial) -> str:
    """Il report di una prova, da leggere."""
    when = trial.started_at.strftime("%d-%m-%Y %H:%M")
    lines = [
        f"# Prova «{trial.name}» del {when}",
        "",
        f"Modello `{trial.model or '-'}` · prompt `{trial.prompt_version or '-'}` · "
        f"v2 `{trial.tool_version or '-'}` · conoscenza `{trial.knowledge_version or '-'}`",
        "",
        "## Punteggio",
        "",
        "| Misura | Valore |",
        "|---|---|",
        f"| Errori noti trovati | **{trial.known_found} su {trial.known_total}** "
        f"({_percent(trial.known_found, trial.known_total)}) |",
        f"| Falsi errori nei cicli giusti | **{trial.false_errors}** |",
        f"| ERRATO in più nei cicli con errori | {trial.extra_errors} |",
        f"| Cicli non eseguiti | {trial.failures} |",
        f"| Costo | {trial.cost_usd:.2f} $ |",
        f"| Token (input + output) | {trial.tokens:,}".replace(",", ".") + " |",
        f"| Tempo totale | {_seconds(trial.duration_ms)} |",
        "",
    ]
    reasons: dict[str, int] = {}
    for cycle in trial.cycles:
        for finding in cycle.found:
            reasons[finding.reason] = reasons.get(finding.reason, 0) + 1
    if reasons:
        lines += ["**Come li ha trovati:** "]
        lines[-1] += ", ".join(f"`{reason}` {count}" for reason, count in sorted(reasons.items()))
        lines.append("")
    lines += [
        "## Ciclo per ciclo",
        "",
        "| Ciclo | Tipo | Esito | Corretti / warning / errati / N.A. | Trovati | Mancati | "
        "ERRATO in più | Costo | Tempo |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in trial.cycles:
        counts = (
            f"{c.counts.get('corretto', 0)} / {c.counts.get('warning', 0)} / "
            f"{c.counts.get('errato', 0)} / {c.counts.get('non_applicabile', 0)}"
            if c.counts
            else "-"
        )
        lines.append(
            f"| {c.fingerprint} | {c.kind} | {c.status} | {counts} | "
            f"{', '.join(f.op for f in c.found) or '-'} | "
            f"{', '.join(m.op for m in c.missed) or '-'} | "
            f"{', '.join(f.op for f in c.extra) or '-'} | {c.cost_usd:.2f} $ | "
            f"{_seconds(c.duration_ms)} |"
        )
    lines += [
        "",
        "## Errori noti",
        "",
        "| Ciclo | Op | Errore | Trovato | Come / cosa ha detto la v2 |",
    ]
    lines.append("|---|---|---|---|---|")
    for c in trial.cycles:
        for f in c.found:
            lines.append(
                f"| {c.fingerprint} | {f.op} | {_cell(f.known or '')} | **sì** | "
                f"`{f.reason}` ({f.check}) |"
            )
        for m in c.missed:
            lines.append(
                f"| {c.fingerprint} | {m.op} | {_cell(m.known)} | no | {_cell(m.said) or '-'} |"
            )
    extra = [(c, f) for c in trial.cycles for f in c.extra]
    if extra:
        lines += [
            "",
            "## ERRATO in più",
            "",
            "Nei cicli giusti sono **falsi errori**; nei cicli con errori sono da guardare (un "
            "errore vero non messo nella lista, o un falso errore).",
            "",
            "| Ciclo | Tipo | Op | Controllo | Motivo | Spiegazione (inizio) |",
            "|---|---|---|---|---|---|",
        ]
        for c, f in extra:
            lines.append(
                f"| {c.fingerprint} | {c.kind} | {f.op} | {f.check} | `{f.reason}` | "
                f"{_cell(f.rationale)} |"
            )
    failed = [c for c in trial.cycles if c.failure]
    if failed:
        lines += ["", "## Cicli non eseguiti", ""]
        lines += [f"- {c.fingerprint}: {_cell(c.failure or '')}" for c in failed]
    return "\n".join(lines) + "\n"


def write_trial(trial: Trial, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / TRIAL_FILE).write_text(trial.model_dump_json(indent=2), "utf-8")
    (folder / TRIAL_REPORT).write_text(render_trial(trial), "utf-8")


def load_trials(root: Path) -> list[Trial]:
    """Tutte le prove della cartella, dalla più vecchia."""
    trials = [
        Trial.model_validate_json(path.read_text("utf-8")) for path in root.glob(f"*/{TRIAL_FILE}")
    ]
    return sorted(trials, key=lambda t: t.started_at)


def _baseline(trials: Sequence[Trial], index: int) -> Trial | None:
    """La prova di confronto: l'ultima «base» prima di questa, altrimenti la prima."""
    before = trials[:index]
    bases = [t for t in before if t.name.casefold().startswith("base")]
    if bases:
        return bases[-1]
    return trials[0] if index > 0 else None


def render_summary(trials: Sequence[Trial]) -> str:
    """Il riepilogo di tutte le prove: tabella delle prove ed errore per errore."""
    if not trials:
        return "# Riepilogo delle prove\n\nNessuna prova.\n"
    first, last = trials[0].started_at, trials[-1].started_at
    lines = [
        "# Riepilogo delle prove",
        "",
        f"{len(trials)} prove, dal {first:%d-%m-%Y %H:%M} al {last:%d-%m-%Y %H:%M}. Una "
        "miglioria si tiene se gli errori noti trovati non scendono e i falsi errori nei cicli "
        "giusti restano 0.",
        "",
        "## Le prove",
        "",
        "| Data | Prova | Errori noti trovati | Falsi errori | ERRATO in più | "
        "Rispetto alla base | Costo | Tempo | Modello | Prompt |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for index, trial in enumerate(trials):
        base = _baseline(trials, index)
        if base is None:
            delta = "-"
        else:
            diff = trial.known_found - base.known_found
            delta = f"{diff:+d} trovati, {trial.false_errors - base.false_errors:+d} falsi"
        lines.append(
            f"| {trial.started_at:%d-%m %H:%M} | {_cell(trial.name)} | "
            f"{trial.known_found} su {trial.known_total} "
            f"({_percent(trial.known_found, trial.known_total)}) | {trial.false_errors} | "
            f"{trial.extra_errors} | {delta} | {trial.cost_usd:.2f} $ | "
            f"{_seconds(trial.duration_ms)} | {trial.model or '-'} | "
            f"{trial.prompt_version or '-'} |"
        )
    best = max(trials, key=lambda t: (t.known_found - 2 * t.false_errors, t.started_at))
    lines += [
        "",
        f"**Prova migliore:** «{best.name}» del {best.started_at:%d-%m %H:%M} "
        f"({best.known_found} su {best.known_total}, {best.false_errors} falsi errori).",
        "",
        "## Errore per errore",
        "",
        "Per ogni errore noto: in quali prove è stato trovato (✓) e in quante. Un errore trovato "
        "solo in alcune prove con la stessa versione è un giudizio instabile del modello.",
        "",
    ]
    known: dict[tuple[str, str], str] = {}
    for trial in trials:
        for cycle in trial.cycles:
            if cycle.kind != "errori":
                continue
            pairs = [(f.op, f.known or "") for f in cycle.found]
            pairs += [(m.op, m.known) for m in cycle.missed]
            for op, text in pairs:
                known.setdefault((cycle.fingerprint, op), text)
    header = (
        "| Ciclo | Op | Errore | "
        + " | ".join(f"{i + 1}" for i in range(len(trials)))
        + " | Trovato in |"
    )
    lines += [
        "Colonne numerate come le prove della tabella sopra (1 = la più vecchia).",
        "",
        header,
        "|---|---|---|" + "---|" * len(trials) + "---|",
    ]
    found_sets = [trial.found_ops() for trial in trials]
    for (fingerprint, op), text in sorted(known.items()):
        marks = ["✓" if (fingerprint, op) in found else "·" for found in found_sets]
        count = marks.count("✓")
        lines.append(
            f"| {fingerprint} | {op} | {_cell(text)} | " + " | ".join(marks) + f" | "
            f"{count} su {len(trials)} |"
        )
    false_rows = [
        (trial, cycle, finding)
        for trial in trials
        for cycle in trial.cycles
        if cycle.kind == "giusto"
        for finding in cycle.extra
    ]
    lines += ["", "## Falsi errori nei cicli giusti", ""]
    if false_rows:
        lines += ["| Prova | Ciclo | Op | Motivo | Spiegazione (inizio) |", "|---|---|---|---|---|"]
        lines += [
            f"| {_cell(t.name)} | {c.fingerprint} | {f.op} | `{f.reason}` | {_cell(f.rationale)} |"
            for t, c, f in false_rows
        ]
    else:
        lines.append("Nessuno.")
    return "\n".join(lines) + "\n"


def write_summary(root: Path) -> Path:
    path = root / SUMMARY_REPORT
    root.mkdir(parents=True, exist_ok=True)
    path.write_text(render_summary(load_trials(root)), "utf-8")
    return path
