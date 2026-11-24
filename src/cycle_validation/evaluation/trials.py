"""Prove sui cicli veri: punteggio contro gli errori noti, report di ogni prova, riepilogo.

Una *prova* è un giro della v2 sugli stessi cicli (quelli «con errori», con gli errori messi
apposta e conosciuti, e le stampe giuste da cui sono stati fatti). Per ogni prova si scrivono
`prova.json` (i numeri) e `prestazioni.md` (il report da leggere); il riepilogo
`riepilogo.md` mette insieme tutte le prove della cartella.

Gli errori noti stanno in un file YAML (`eval/errori-noti.yaml`): per ogni ciclo, indicato con
le prime 8 cifre dell'impronta SHA-256 del PDF, le operazioni sbagliate apposta con una breve
descrizione, oppure `giusto: true` per una stampa senza errori. Niente codici veri: solo
impronte, numeri di operazione e descrizioni generiche. Un ciclo che non è nel file è un
ciclo *vero* (una stampa in uso, scelta da `eval scegli`): non ha errori noti, i suoi ERRATO
sono da verificare e i suoi WARNING contano nel lavoro a mano.
"""

import hashlib
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from cycle_validation.domain.check import CheckName, TargetKind, Verdict
from cycle_validation.domain.report import Report
from cycle_validation.evaluation.blind import CODE_KINDS

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
    # False per gli errori che chi scrive le migliorie non conosce (mutazioni cieche,
    # gruppo nascosto): i report ne danno solo il tipo e i conteggi
    visto: bool = True
    # operazioni il cui esito giusto aspetta una risposta delle persone (operazione → domanda):
    # un ERRATO lì non è né trovato né falso, si conta a parte
    in_attesa: dict[str, str] = Field(default_factory=dict)


class KnownErrors(_Strict):
    cicli: dict[str, KnownCycle]

    def cycle(self, fingerprint: str) -> KnownCycle | None:
        return self.cicli.get(fingerprint)


def load_known_errors(path: Path | Sequence[Path]) -> KnownErrors:
    """Uno o più file; un ciclo in più file vale l'ultimo."""
    paths = [path] if isinstance(path, Path) else list(path)
    cycles: dict[str, KnownCycle] = {}
    for one in paths:
        cycles.update(_known_cycles(one))
    return KnownErrors(cicli=cycles)


def _known_cycles(path: Path) -> dict[str, KnownCycle]:
    raw = yaml.safe_load(path.read_text("utf-8")) or {}
    return {
        str(key).lower(): KnownCycle.model_validate(
            {
                **(value or {}),
                "errori": {
                    op_key(op): str(text)
                    for op, text in ((value or {}).get("errori") or {}).items()
                },
                "in_attesa": {
                    op_key(op): str(text)
                    for op, text in ((value or {}).get("in_attesa") or {}).items()
                },
            }
        )
        for key, value in (raw.get("cicli") or {}).items()
    }


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
    kind: str  # "errori" | "giusto" | "vero"
    status: str
    counts: dict[str, int] = Field(default_factory=dict)
    found: list[Finding] = Field(default_factory=list)
    missed: list[Missed] = Field(default_factory=list)
    extra: list[Finding] = Field(default_factory=list)
    # ERRATO su operazioni in attesa di una risposta (`KnownCycle.in_attesa`): non contano
    pending: list[Finding] = Field(default_factory=list)
    cost_usd: float = 0.0
    tokens: int = 0
    cache_read_tokens: int = 0  # token di input riletti dalla cache (prompt caching, H10)
    duration_ms: int = 0
    failure: str | None = None
    seen: bool = True  # errori noti a chi scrive le migliorie (vedi `KnownCycle.visto`)


class Proposal(_Strict):
    """La proposta della variante (`eval/varianti/<nome>.yaml`): cosa cambia, perché, cosa ci si
    aspetta. Vuota quando la prova gira senza variante (per esempio la base)."""

    change: str = ""
    hypothesis: str = ""
    expected: str = ""

    def __bool__(self) -> bool:
        return bool(self.change or self.hypothesis or self.expected)


class Trial(_Strict):
    name: str
    started_at: datetime
    proposal: Proposal = Field(default_factory=Proposal)
    model: str = ""
    knowledge_version: str = ""
    prompt_version: str = ""
    tool_version: str = ""
    cycles: list[CycleScore] = Field(default_factory=list)

    def _errors(self, seen: bool | None) -> list[CycleScore]:
        return [c for c in self.cycles if c.kind == "errori" and (seen is None or c.seen == seen)]

    @property
    def seen_total(self) -> int:
        return sum(len(c.found) + len(c.missed) for c in self._errors(True))

    @property
    def seen_found(self) -> int:
        return sum(len(c.found) for c in self._errors(True))

    @property
    def unseen_total(self) -> int:
        """Errori mai visti che deve trovare il modello (copie cieche dei tipi in
        `MODEL_KINDS`, gruppo nascosto): misurano la generalizzazione."""
        return sum(
            sum(map(generalizes, [f.known for f in c.found] + [m.known for m in c.missed]))
            for c in self._errors(False)
        )

    @property
    def unseen_found(self) -> int:
        return sum(sum(generalizes(f.known) for f in c.found) for c in self._errors(False))

    def unseen_ops(self) -> set[tuple[str, str]]:
        return {
            (c.fingerprint, f.op)
            for c in self._errors(False)
            for f in c.found
            if generalizes(f.known)
        }

    @property
    def code_unseen_total(self) -> int:
        """Errori mai visti dei tipi che trova il codice con la stessa regola che li ha messi:
        dicono solo che non si è rotto niente, non che la v2 generalizza."""
        return sum(
            sum(
                not generalizes(text)
                for text in [f.known for f in c.found] + [m.known for m in c.missed]
            )
            for c in self._errors(False)
        )

    @property
    def code_unseen_found(self) -> int:
        return sum(sum(not generalizes(f.known) for f in c.found) for c in self._errors(False))

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
    def pending_errors(self) -> int:
        """ERRATO su operazioni in attesa di una risposta delle persone: non contano."""
        return sum(len(c.pending) for c in self.cycles)

    @property
    def extra_errors(self) -> int:
        """ERRATO da verificare: nei cicli con errori fuori lista e nei cicli veri."""
        return sum(len(c.extra) for c in self.cycles if c.kind != "giusto")

    @property
    def real_errors(self) -> int:
        """La parte di `extra_errors` nei cicli veri (non rivisti)."""
        return sum(len(c.extra) for c in self.cycles if c.kind == "vero")

    @property
    def real_cycles(self) -> int:
        return sum(1 for c in self.cycles if c.kind == "vero")

    @property
    def cycle_set(self) -> str:
        """Impronta dell'insieme dei cicli: si confrontano solo prove sugli stessi cicli."""
        names = ",".join(sorted(c.fingerprint for c in self.cycles))
        return hashlib.sha256(names.encode()).hexdigest()[:6]

    @property
    def cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.cycles)

    @property
    def tokens(self) -> int:
        return sum(c.tokens for c in self.cycles)

    @property
    def cache_read_tokens(self) -> int:
        return sum(c.cache_read_tokens for c in self.cycles)

    @property
    def duration_ms(self) -> int:
        return sum(c.duration_ms for c in self.cycles)

    @property
    def failures(self) -> int:
        return sum(1 for c in self.cycles if c.failure)

    def found_ops(self) -> set[tuple[str, str]]:
        return {(c.fingerprint, f.op) for c in self.cycles for f in c.found}

    @property
    def precision(self) -> float:
        """Errori noti trovati / tutti gli ERRATO dati sulle operazioni (1 se nessun ERRATO)."""
        given = self.known_found + self.false_errors + self.extra_errors
        return self.known_found / given if given else 1.0

    @property
    def clean_warnings(self) -> float:
        """WARNING per ciclo senza errori noti (giusti e veri): il lavoro a mano che la v2
        lascia su un ciclo senza errori."""
        clean = [c for c in self.cycles if c.kind in ("giusto", "vero") and not c.failure]
        return sum(c.counts.get("warning", 0) for c in clean) / len(clean) if clean else 0.0

    @property
    def cost_per_cycle(self) -> float:
        run = [c for c in self.cycles if not c.failure]
        return self.cost_usd / len(run) if run else 0.0

    @property
    def mean_ms(self) -> int:
        run = [c for c in self.cycles if not c.failure]
        return round(self.duration_ms / len(run)) if run else 0

    @property
    def max_ms(self) -> int:
        return max((c.duration_ms for c in self.cycles), default=0)


def _short(text: str, limit: int = _RATIONALE_CHARS) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def score_cycle(report: Report, known: KnownErrors, fingerprint: str | None = None) -> CycleScore:
    """Punteggio di un ciclo: ERRATO sulle operazioni confrontati con gli errori noti.
    `fingerprint` sostituisce l'impronta del PDF (una copia con un errore cieco ha il PDF del
    ciclo vero, ma un'impronta sua)."""
    fingerprint = (fingerprint or report.meta.pdf_sha256[:8]).lower()
    entry = known.cycle(fingerprint)
    kind = "vero" if entry is None else ("giusto" if entry.giusto else "errori")
    expected = entry.errori if entry is not None else {}
    waiting = entry.in_attesa if entry is not None else {}
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
        extra=[errato[op] for op in sorted(errato) if op not in expected and op not in waiting],
        pending=[
            errato[op].model_copy(update={"known": waiting[op]})
            for op in sorted(errato)
            if op not in expected and op in waiting
        ],
        cost_usd=usage.cost_usd,
        tokens=usage.input_tokens + usage.output_tokens,
        cache_read_tokens=usage.cache_read_tokens,
        duration_ms=report.timings_ms.get("total", usage.wall_ms),
        seen=entry.visto if entry is not None else True,
    )


def failed_cycle(fingerprint: str, known: KnownErrors, failure: str) -> CycleScore:
    """Un ciclo che la v2 non ha validato: i suoi errori noti contano come mancati."""
    entry = known.cycle(fingerprint)
    kind = "vero" if entry is None else ("giusto" if entry.giusto else "errori")
    expected = entry.errori if entry is not None else {}
    return CycleScore(
        fingerprint=fingerprint,
        kind=kind,
        status="non eseguito",
        missed=[Missed(op=op, known=text) for op, text in sorted(expected.items())],
        failure=_short(failure),
        seen=entry.visto if entry is not None else True,
    )


def build_trial(
    name: str,
    started_at: datetime,
    reports: Sequence[Report],
    cycles: Sequence[CycleScore],
    proposal: Proposal | None = None,
) -> Trial:
    """La prova: i punteggi dei cicli, nell'ordine «con errori», giusti, sconosciuti."""
    order = {"errori": 0, "giusto": 1, "vero": 2}
    meta = reports[0].meta if reports else None
    return Trial(
        name=name,
        started_at=started_at,
        proposal=proposal or Proposal(),
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


def error_kind(text: str | None) -> str:
    """Il tipo di un errore mai visto: `[numero_manuale] ...` → `numero_manuale`; senza
    parentesi (gruppo nascosto) → `nascosto`."""
    text = text or ""
    if text.startswith("[") and "]" in text:
        return text[1 : text.index("]")]
    return "nascosto"


def generalizes(text: str | None) -> bool:
    """Se un errore mai visto misura la generalizzazione: sì, se lo deve trovare il modello
    (gruppo nascosto e copie cieche dei tipi in `MODEL_KINDS`); no per i tipi in `CODE_KINDS`,
    che il codice trova con la stessa regola che li ha messi."""
    return error_kind(text) not in CODE_KINDS


def unseen_by_kind(trial: Trial) -> dict[str, tuple[int, int]]:
    """Tipo → (trovati, totali) degli errori mai visti."""
    counts: dict[str, list[int]] = {}
    for cycle in trial.cycles:
        if cycle.kind != "errori" or cycle.seen:
            continue
        for finding in cycle.found:
            counts.setdefault(error_kind(finding.known or ""), [0, 0])[0] += 1
        texts = [f.known or "" for f in cycle.found] + [m.known for m in cycle.missed]
        for text in texts:
            counts.setdefault(error_kind(text), [0, 0])[1] += 1
    return {kind: (found, total) for kind, (found, total) in sorted(counts.items())}


def unseen_answers(trial: Trial) -> dict[str, str]:
    """Tipo → cosa ha risposto la v2 sugli errori mai visti mancati, solo esito e motivo
    contati (per esempio «CORRETTO 12, WARNING EVIDENZA_NON_TROVATA 4»): dice perché li manca
    senza dire quali sono."""
    answers: dict[str, dict[str, int]] = {}
    for cycle in trial.cycles:
        if cycle.kind != "errori" or cycle.seen:
            continue
        for missed in cycle.missed:
            said = missed.said.split(":", 1)[0].strip() or "nessun esito"
            if cycle.failure:
                said = "ciclo non eseguito"
            bucket = answers.setdefault(error_kind(missed.known), {})
            bucket[said] = bucket.get(said, 0) + 1
    return {
        kind: ", ".join(f"{said} {n}" for said, n in sorted(counts.items(), key=lambda i: -i[1]))
        for kind, counts in answers.items()
    }


def _render_proposal(proposal: Proposal) -> list[str]:
    """La proposta in cima al report: così risultati e motivo della prova stanno insieme."""
    if not proposal:
        return [
            "## La proposta",
            "",
            "Nessuna variante: le impostazioni di `--config`, così come sono.",
            "",
        ]
    rows = (
        ("Cosa cambia", proposal.change),
        ("Perché (ipotesi)", proposal.hypothesis),
        ("Cosa ci si aspetta", proposal.expected),
    )
    return [
        "## La proposta",
        "",
        "| | |",
        "|---|---|",
        *(f"| {label} | {_cell(text or '-')} |" for label, text in rows),
        "",
        "La decisione (si tiene o no) è nel riepilogo; le considerazioni nel registro di "
        "`docs/MIGLIORIE.md`.",
        "",
    ]


def render_trial(trial: Trial) -> str:
    """Il report di una prova, da leggere."""
    when = trial.started_at.strftime("%d-%m-%Y %H:%M")
    lines = [
        f"# Prova «{trial.name}» del {when}",
        "",
        f"Modello `{trial.model or '-'}` · prompt `{trial.prompt_version or '-'}` · "
        f"v2 `{trial.tool_version or '-'}` · conoscenza `{trial.knowledge_version or '-'}`",
        "",
        *_render_proposal(trial.proposal),
        "## Punteggio",
        "",
        "| Misura | Valore |",
        "|---|---|",
        f"| Errori noti trovati | **{trial.known_found} su {trial.known_total}** "
        f"({_percent(trial.known_found, trial.known_total)}) |",
        f"| … visti (la lista che si conosce) | {trial.seen_found} su {trial.seen_total} "
        f"({_percent(trial.seen_found, trial.seen_total)}) |",
        f"| … **mai visti per il modello** (generalizzazione) | **{trial.unseen_found} su "
        f"{trial.unseen_total}** ({_percent(trial.unseen_found, trial.unseen_total)}) |",
        f"| … mai visti per il codice (solo controllo che non si rompe niente) | "
        f"{trial.code_unseen_found} su {trial.code_unseen_total} "
        f"({_percent(trial.code_unseen_found, trial.code_unseen_total)}) |",
        f"| Falsi errori nei cicli giusti | **{trial.false_errors}** |",
        f"| ERRATO in attesa di una risposta delle persone (non contano) | "
        f"{trial.pending_errors} |",
        f"| ERRATO da verificare (fuori lista; nei {trial.real_cycles} cicli veri: "
        f"{trial.real_errors}) | {trial.extra_errors} |",
        f"| Precisione (trovati / tutti gli ERRATO) | {round(100 * trial.precision)}% |",
        f"| WARNING per ciclo senza errori noti (giusti e veri) | {trial.clean_warnings:.1f} |",
        f"| Cicli non eseguiti | {trial.failures} |",
        f"| Costo per ciclo | {trial.cost_per_cycle:.4f} $ |",
        f"| Tempo per ciclo (medio / il più lento) | {_seconds(trial.mean_ms)} / "
        f"{_seconds(trial.max_ms)} |",
        f"| Costo | {trial.cost_usd:.2f} $ |",
        f"| Token (input + output) | {trial.tokens:,}".replace(",", ".") + " |",
        f"| Token di input riletti dalla cache (a parte; costano circa un decimo) | "
        f"{trial.cache_read_tokens:,}".replace(",", ".")
        + " |",
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
    hidden = [c for c in trial.cycles if c.kind == "errori" and not c.seen]
    for c in trial.cycles:
        if c in hidden:
            continue
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
    if hidden:
        lines.append(
            f"| {len(hidden)} copie con errori mai visti | errori | - | - | - | - | - | "
            f"{sum(c.cost_usd for c in hidden):.2f} $ | "
            f"{_seconds(sum(c.duration_ms for c in hidden))} |"
        )
    by_kind = unseen_by_kind(trial)
    if by_kind:
        lines += [
            "",
            "## Errori mai visti, per tipo",
            "",
            "Solo i conteggi: quali sono non si mostra, così chi scrive le migliorie non li "
            "impara. Se gli errori visti sono trovati molto più spesso di questi, la v2 ha "
            "imparato la lista e non generalizza. Le migliorie si scelgono sui tipi «modello» "
            "trovati peggio; i tipi «codice» li trova il codice con la stessa regola che li ha "
            "messi: servono solo a vedere che non si rompe niente.",
            "",
            "| Tipo | Chi lo deve trovare | Trovati | Cosa ha risposto la v2 sui mancati |",
            "|---|---|---|---|",
        ]
        answers = unseen_answers(trial)
        lines += [
            f"| {kind} | {'modello' if kind not in CODE_KINDS else 'codice'} | "
            f"{found} su {total} ({_percent(found, total)}) | {answers.get(kind, '-')} |"
            for kind, (found, total) in by_kind.items()
        ]
    lines += [
        "",
        "## Errori noti",
        "",
        "| Ciclo | Op | Errore | Trovato | Come / cosa ha detto la v2 |",
    ]
    lines.append("|---|---|---|---|---|")
    for c in trial.cycles:
        if c in hidden:
            continue
        for f in c.found:
            lines.append(
                f"| {c.fingerprint} | {f.op} | {_cell(f.known or '')} | **sì** | "
                f"`{f.reason}` ({f.check}) |"
            )
        for m in c.missed:
            lines.append(
                f"| {c.fingerprint} | {m.op} | {_cell(m.known)} | no | {_cell(m.said) or '-'} |"
            )
    extra = [(c, f) for c in trial.cycles if c not in hidden for f in c.extra]
    if extra:
        lines += [
            "",
            "## ERRATO in più",
            "",
            "Nei cicli giusti sono **falsi errori**; nei cicli con errori sono da guardare (un "
            "errore vero non messo nella lista, o un falso errore); nei cicli veri (stampe in "
            "uso, non rivisti) sono quasi sempre falsi errori: si guardano e, se l'errore c'è "
            "davvero, il ciclo va in `eval/errori-noti.yaml`.",
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


# --- Metriche e scelta della variante migliore -------------------------------------------
#
# Una *variante* è l'insieme delle prove con lo stesso nome (le ripetizioni). Regole, in ordine:
# 1. scartata se dà anche un solo falso errore nei cicli giusti, se un ciclo non è eseguito, se
#    un ciclo supera `MAX_CYCLE_MS` (il frontend aspetta 11 minuti) o se costa per ciclo più di
#    `MAX_COST_RATIO` volte la base;
# 2. servono almeno `MIN_REPETITIONS` prove: il modello non risponde sempre uguale;
# 3. classifica: errori trovati in tutte le ripetizioni (stabili), poi il minimo e la media dei
#    trovati, poi meno ERRATO da verificare, meno WARNING per ciclo senza errori noti, meno costo, meno tempo;
# 4. si tiene se è valida, ripetuta abbastanza, non trova meno errori stabili della base e sta
#    sopra la base in classifica. La scelta migliore è la prima valida della classifica.

MIN_REPETITIONS = 2
MAX_CYCLE_MS = 10 * 60 * 1000
MAX_COST_RATIO = 2.0
BASE_NAME = "base"


class Variant(_Strict):
    name: str
    repetitions: int
    known_total: int
    stable: int
    unseen_total: int = 0
    unseen_stable: int = 0  # errori mai visti trovati in tutte le ripetizioni
    found_min: int
    found_mean: float
    false_errors: int
    extra_max: int
    precision_min: float
    clean_warnings: float
    cost_per_cycle: float
    mean_ms: int
    max_ms: int
    failures: int
    decision: str = ""
    proposal: Proposal = Field(default_factory=Proposal)

    def rank_key(self) -> tuple[float, ...]:
        """Più grande = migliore."""
        return (
            self.stable,
            self.found_min,
            self.found_mean,
            -self.extra_max,
            -round(self.clean_warnings, 1),
            -round(self.cost_per_cycle, 2),
            -self.mean_ms,
        )

    def exclusion(self, base: "Variant | None") -> str | None:
        if self.false_errors:
            return f"{self.false_errors} falsi errori nei cicli giusti"
        if self.failures:
            return f"{self.failures} cicli non eseguiti"
        if self.max_ms > MAX_CYCLE_MS:
            return f"un ciclo dura {_seconds(self.max_ms)} (massimo {_seconds(MAX_CYCLE_MS)})"
        if (
            base is not None
            and base.cost_per_cycle > 0
            and self.cost_per_cycle > MAX_COST_RATIO * base.cost_per_cycle
        ):
            return f"costa più di {MAX_COST_RATIO:g} volte la base per ciclo"
        return None


def build_variants(trials: Sequence[Trial]) -> list[Variant]:
    """Le varianti (prove con lo stesso nome), in classifica, con la decisione rispetto alla base."""
    groups: dict[str, list[Trial]] = {}
    for trial in trials:
        groups.setdefault(trial.name.strip().casefold(), []).append(trial)
    variants: list[Variant] = []
    for group in groups.values():
        found = [t.known_found for t in group]
        stable = set.intersection(*(t.found_ops() for t in group))
        unseen = set.intersection(*(t.unseen_ops() for t in group))
        variants.append(
            Variant(
                name=group[-1].name,
                repetitions=len(group),
                known_total=max(t.known_total for t in group),
                stable=len(stable),
                unseen_total=max(t.unseen_total for t in group),
                unseen_stable=len(unseen),
                found_min=min(found),
                found_mean=sum(found) / len(found),
                false_errors=sum(t.false_errors for t in group),
                extra_max=max(t.extra_errors for t in group),
                precision_min=min(t.precision for t in group),
                clean_warnings=sum(t.clean_warnings for t in group) / len(group),
                cost_per_cycle=sum(t.cost_per_cycle for t in group) / len(group),
                mean_ms=round(sum(t.mean_ms for t in group) / len(group)),
                max_ms=max(t.max_ms for t in group),
                failures=sum(t.failures for t in group),
                proposal=next((t.proposal for t in reversed(group) if t.proposal), Proposal()),
            )
        )
    base = next((v for v in variants if v.name.casefold() == BASE_NAME), None)
    variants.sort(key=lambda v: v.rank_key(), reverse=True)
    for variant in variants:
        variant.decision = _decide(variant, base)
    return variants


def _decide(variant: Variant, base: Variant | None) -> str:
    reason = variant.exclusion(base)
    if reason:
        return f"scartata: {reason}"
    if variant.repetitions < MIN_REPETITIONS:
        return f"da ripetere ({variant.repetitions} prova su {MIN_REPETITIONS})"
    if variant is base or base is None:
        return "riferimento" if variant is base else "valida (manca la base)"
    if variant.stable < base.stable:
        return f"non si tiene: errori stabili {variant.stable} contro {base.stable} della base"
    if variant.unseen_stable < base.unseen_stable:
        return (
            f"non si tiene: errori mai visti {variant.unseen_stable} contro "
            f"{base.unseen_stable} della base (non generalizza)"
        )
    if variant.rank_key() > base.rank_key():
        return "si tiene: meglio della base"
    return "non si tiene: non è meglio della base"


def best_variant(variants: Sequence[Variant]) -> Variant | None:
    """La prima della classifica che si tiene (o la base, se nessuna la batte)."""
    for variant in variants:
        if variant.decision.startswith(("si tiene", "riferimento", "valida")):
            return variant
    return None


METRICS_HELP = (
    "**Metriche.** *Trovati*: errori noti segnati ERRATO (su "
    "`eval/errori-noti.yaml`). *Stabili*: trovati in tutte le ripetizioni. *Falsi errori*: "
    "ERRATO nelle stampe giuste (deve essere 0). *Da verificare*: ERRATO fuori dalla lista "
    "(nei cicli con errori e nei cicli veri). *Precisione*: trovati / tutti gli ERRATO. *Warning per ciclo senza errori*: "
    "lavoro a mano lasciato su un ciclo giusto o vero. *Costo* e *tempo* per ciclo.\n\n"
    "**Regola di scelta.** Scartata con un falso errore, un ciclo non eseguito, un ciclo oltre "
    f"{MAX_CYCLE_MS // 60000} minuti o un costo per ciclo oltre {MAX_COST_RATIO:g} volte la "
    f"base; servono almeno {MIN_REPETITIONS} prove con lo stesso nome. Classifica: stabili, "
    "trovati (minimo, poi media), meno da verificare, meno warning per ciclo senza errori noti, meno "
    "costo, meno tempo. Si tiene se non perde errori stabili, né errori **mai visti per il "
    "modello** (copie cieche che deve trovare il modello e gruppo nascosto: dicono se la v2 "
    "generalizza o ha imparato la lista), e sta sopra la base."
)


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
    variants = build_variants(trials)
    best = best_variant(variants)
    lines = [
        "# Riepilogo delle prove",
        "",
        f"{len(trials)} prove in {len(variants)} varianti, dal {first:%d-%m-%Y %H:%M} al "
        f"{last:%d-%m-%Y %H:%M}.",
        "",
        *(
            [
                "**Attenzione:** le prove di questa cartella non sono tutte sugli stessi cicli "
                f"({len({t.cycle_set for t in trials})} insiemi, colonna «Cicli»): il confronto "
                "vale solo tra prove con lo stesso insieme. Usa una cartella per insieme "
                "(`--cartella`).",
                "",
            ]
            if len({t.cycle_set for t in trials}) > 1
            else []
        ),
        "## Scelta migliore",
        "",
        (
            f"**«{best.name}»**: {best.stable} errori noti trovati in tutte le "
            f"{best.repetitions} prove (su {best.known_total}), 0 falsi errori, "
            f"{best.cost_per_cycle:.4f} $ e {_seconds(best.mean_ms)} per ciclo."
            if best is not None
            else "Nessuna variante valida: mancano ripetizioni o ci sono falsi errori."
        ),
        "",
        "## Classifica delle varianti",
        "",
        "| Pos. | Variante | Prove | Stabili | Mai visti stabili | Trovati min / medio | "
        "Falsi errori | "
        "Da verificare | Precisione | Warning per ciclo senza errori | Costo per ciclo | "
        "Tempo per ciclo (max) | Decisione |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for position, v in enumerate(variants, start=1):
        lines.append(
            f"| {position} | {_cell(v.name)} | {v.repetitions} | **{v.stable}** su "
            f"{v.known_total} | {v.unseen_stable} su {v.unseen_total} | "
            f"{v.found_min} / {v.found_mean:.1f} | {v.false_errors} | "
            f"{v.extra_max} | {round(100 * v.precision_min)}% | {v.clean_warnings:.1f} | "
            f"{v.cost_per_cycle:.4f} $ | {_seconds(v.mean_ms)} ({_seconds(v.max_ms)}) | "
            f"{v.decision} |"
        )
    lines += [
        "",
        METRICS_HELP,
        "",
        "## Le proposte e la decisione",
        "",
        "Cosa voleva provare ogni variante (dal suo file in `eval/varianti/`) accanto a quello "
        "che è successo. Le considerazioni si scrivono nel registro di `docs/MIGLIORIE.md`.",
        "",
        "| Variante | Cosa cambia | Perché (ipotesi) | Cosa ci si aspetta | Decisione |",
        "|---|---|---|---|---|",
        *(
            f"| {_cell(v.name)} | {_cell(v.proposal.change or '-')} | "
            f"{_cell(v.proposal.hypothesis or '-')} | {_cell(v.proposal.expected or '-')} | "
            f"{v.decision} |"
            for v in variants
        ),
        "",
        "## Le prove",
        "",
        "| Data | Prova | Cicli | Trovati | Mai visti | Falsi errori | Da verificare | "
        "Rispetto alla base | Costo | Tempo | Modello | Prompt | v2 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
            f"{len(trial.cycles)} ({trial.cycle_set}) | {trial.known_found} su {trial.known_total} "
            f"({_percent(trial.known_found, trial.known_total)}) | "
            f"{trial.unseen_found} su {trial.unseen_total} | {trial.false_errors} | "
            f"{trial.extra_errors} | {delta} | {trial.cost_usd:.2f} $ | "
            f"{_seconds(trial.duration_ms)} | {trial.model or '-'} | "
            f"{trial.prompt_version or '-'} | {trial.tool_version or '-'} |"
        )
    lines += [
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
            if cycle.kind != "errori" or not cycle.seen:
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
    found_sets = [trial.found_ops() - trial.unseen_ops() for trial in trials]
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
    pending = sorted(
        {(c.fingerprint, f.op, f.known or "") for t in trials for c in t.cycles for f in c.pending}
    )
    lines += [
        "",
        "## In attesa di una risposta",
        "",
        "Operazioni il cui esito giusto aspetta una domanda alle persone (`in_attesa` negli "
        "errori noti): un ERRATO lì non conta né come trovato né come falso errore.",
        "",
    ]
    if pending:
        lines += ["| Ciclo | Op | Domanda | Prove con ERRATO |", "|---|---|---|---|"]
        for name, op, question in pending:
            hits = sum(
                any(f.op == op for c in t.cycles if c.fingerprint == name for f in c.pending)
                for t in trials
            )
            lines.append(f"| {name} | {op} | {_cell(question)} | {hits} su {len(trials)} |")
    else:
        lines.append("Nessuna.")
    return "\n".join(lines) + "\n"


def write_summary(root: Path) -> Path:
    path = root / SUMMARY_REPORT
    root.mkdir(parents=True, exist_ok=True)
    path.write_text(render_summary(load_trials(root)), "utf-8")
    return path
