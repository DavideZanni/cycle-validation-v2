"""Classifica delle varianti, per ambiente, contro la prova più recente della baseline.

Prima i paletti: una variante che ne supera uno è scartata, anche se è più veloce. Le ammesse
si ordinano per tempo mediano per ciclo, poi per costo.

Le prove con guasti simulati non entrano in classifica: verificano una regola sola, un guasto
dà WARNING e mai ERRATO. Regge se non ha più ERRATO falsi della baseline.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.metrics import Metrics, measure

BASELINE = "baseline"
_EPSILON = 1e-9


@dataclass
class Entry:
    name: str
    file: str
    date: str
    commit: str
    metrics: Metrics
    knowledge: dict[str, str] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    faults: dict[str, Any] | None = None


@dataclass
class Board:
    environment: str
    reference: Entry | None
    admitted: list[Entry]
    rejected: list[Entry]
    robustness: list[Entry] = field(default_factory=list)


def _load(folder: Path) -> list[tuple[Path, dict[str, Any]]]:
    if not folder.is_dir():
        raise ConfigError(f"Cartella dei risultati non trovata: {folder}")
    loaded = []
    for path in sorted(folder.glob("*.json")):
        try:
            loaded.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"{path}: risultati non leggibili ({exc})") from exc
    return loaded


def _num(value: float) -> str:
    return f"{value:g}".replace(".", ",")


def _guardrails(entry: Entry, reference: Entry) -> list[str]:
    m, ref = entry.metrics, reference.metrics
    if m.cases != ref.cases:
        return ["casi diversi dalla baseline: non confrontabile"]
    if entry.knowledge != reference.knowledge:
        return ["conoscenza diversa dalla baseline: non confrontabile, rilanciare la baseline"]
    reasons = []
    if m.false_errato > ref.false_errato + _EPSILON:
        reasons.append(f"più ERRATO falsi ({_num(m.false_errato)} contro {_num(ref.false_errato)})")
    if m.missed_errors > ref.missed_errors + _EPSILON:
        reasons.append(
            f"più errori mancati ({_num(m.missed_errors)} contro {_num(ref.missed_errors)})"
        )
    if m.concordance < ref.concordance - _EPSILON:
        reasons.append(
            f"concordanza più bassa ({_pct(m.concordance)} contro {_pct(ref.concordance)})"
        )
    if (
        m.unstable_rows is not None
        and ref.unstable_rows is not None
        and m.unstable_rows > ref.unstable_rows
    ):
        reasons.append(f"più righe instabili ({m.unstable_rows} contro {ref.unstable_rows})")
    if m.technical > ref.technical + _EPSILON:
        reasons.append(f"più esiti tecnici ({_num(m.technical)} contro {_num(ref.technical)})")
    if (
        m.extraction_accuracy is not None
        and ref.extraction_accuracy is not None
        and m.extraction_accuracy < ref.extraction_accuracy - _EPSILON
    ):
        reasons.append(
            f"estrazione dal PDF peggiore ({_pct(m.extraction_accuracy)} contro "
            f"{_pct(ref.extraction_accuracy)})"
        )
    return reasons


def _robustness(entry: Entry, reference: Entry) -> list[str]:
    m, ref = entry.metrics, reference.metrics
    if m.cases != ref.cases:
        return ["casi diversi dalla baseline: non confrontabile"]
    reasons = []
    if m.false_errato > ref.false_errato + _EPSILON:
        reasons.append(
            f"un guasto è diventato ERRATO ({_num(m.false_errato)} ERRATO falsi contro "
            f"{_num(ref.false_errato)})"
        )
    if m.failures:
        reasons.append(f"{m.failures} casi non arrivati in fondo")
    return reasons


def build_leaderboard(folder: Path) -> list[Board]:
    latest: dict[tuple[str, str], Entry] = {}
    for path, data in _load(folder):
        entry = Entry(
            name=data["variante"],
            file=path.name,
            date=data.get("data", ""),
            commit=data.get("commit", ""),
            metrics=measure(data),
            knowledge=data.get("conoscenza") or {},
            faults=data.get("guasti_simulati"),
        )
        key = (data["ambiente"], entry.name)
        if key not in latest or entry.date >= latest[key].date:
            latest[key] = entry
    boards = []
    for environment in sorted({env for env, _ in latest}):
        entries = [entry for (env, _), entry in latest.items() if env == environment]
        reference = next((e for e in entries if e.name == BASELINE), None)
        admitted: list[Entry] = []
        rejected: list[Entry] = []
        robustness: list[Entry] = []
        for entry in entries:
            if entry.faults:
                if reference is not None:
                    entry.reasons = _robustness(entry, reference)
                robustness.append(entry)
                continue
            if reference is not None and entry is not reference:
                entry.reasons = _guardrails(entry, reference)
            (rejected if entry.reasons else admitted).append(entry)
        admitted.sort(key=lambda e: (e.metrics.time_median_ms, e.metrics.cost_per_cycle, e.name))
        rejected.sort(key=lambda e: e.name)
        robustness.sort(key=lambda e: e.name)
        boards.append(Board(environment, reference, admitted, rejected, robustness))
    return boards


# --- testo ---------------------------------------------------------------------------------


def _pct(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.1%}".replace(".", ",")


def _seconds(ms: float | None) -> str:
    return "n/d" if ms is None else f"{ms / 1000:.1f} s".replace(".", ",")


def _delta(value: float, reference: float | None) -> str:
    if reference is None or reference == 0:
        return ""
    return f" ({value / reference - 1:+.0%})"


def _row(position: str, entry: Entry, reference: Entry | None) -> str:
    m = entry.metrics
    ref = reference.metrics if reference is not None and entry is not reference else None
    unstable = "n/d" if m.unstable_rows is None else f"{m.unstable_rows} ({m.unstable_cases} casi)"
    worst_name, worst_ms = m.worst_case
    cells = [
        position,
        f"`{entry.name}`",
        _pct(m.concordance),
        _num(m.false_errato),
        _num(m.missed_errors),
        unstable,
        _num(m.technical),
        _seconds(m.time_median_ms) + _delta(m.time_median_ms, ref.time_median_ms if ref else None),
        f"{worst_name} {_seconds(worst_ms)}",
        f"{m.cost_per_cycle:.4f}".replace(".", ",")
        + _delta(m.cost_per_cycle, ref.cost_per_cycle if ref else None),
        f"{m.tokens_per_cycle:.0f}",
        _seconds(m.agent_overhead_ms),
        _pct(m.citations_verified),
        _pct(m.extraction_accuracy),
        str(m.repetitions),
        f"{entry.commit} · {entry.date}",
    ]
    return "| " + " | ".join(cells) + " |"


_HEADER = (
    "| # | Variante | Concordanza | ERRATO falsi | Errori mancati | Righe instabili "
    "| Esiti tecnici | Tempo mediano per ciclo | Caso peggiore | Costo per ciclo (USD) "
    "| Token per ciclo | Avvio agente per sessione | Citazioni verificate | Estrazione "
    "| Ripetizioni | Prova |\n" + "|---" * 16 + "|"
)


def _board(board: Board) -> list[str]:
    lines = [f"## Ambiente: {board.environment}", ""]
    if board.reference is None:
        lines += [
            "Riferimento: nessuna prova della variante baseline in questo ambiente. "
            "Le varianti sono elencate senza paletti.",
            "",
        ]
    else:
        ref = board.reference
        lines += [
            f"Riferimento: `baseline`, prova `{ref.file}` ({ref.metrics.repetitions} ripetizioni, "
            f"{len(ref.metrics.cases)} casi). Le percentuali tra parentesi sono la differenza "
            "dalla baseline.",
            "",
        ]
    lines += ["### Ammesse, dalla più veloce", "", _HEADER]
    lines += [_row(str(n), e, board.reference) for n, e in enumerate(board.admitted, 1)]
    lines.append("")
    if board.rejected:
        lines += ["### Scartate", ""]
        lines += [f"- `{e.name}`: {'; '.join(e.reasons)}." for e in board.rejected]
        lines.append("")
    if board.robustness:
        lines += [
            "### Prove con guasti simulati",
            "",
            "Regola: un guasto dà WARNING, mai ERRATO. Gli esiti tecnici dicono quanti guasti sono "
            "arrivati ai controlli.",
            "",
        ]
        for e in board.robustness:
            shares = ", ".join(f"{k} {_num(v)}" for k, v in (e.faults or {}).items() if v)
            outcome = f"NON regge: {'; '.join(e.reasons)}" if e.reasons else "regge"
            if board.reference is None:
                outcome = "non giudicabile senza baseline"
            lines.append(
                f"- `{e.name}`: {outcome} (guasti: {shares}; esiti tecnici "
                f"{_num(e.metrics.technical)}, ERRATO falsi {_num(e.metrics.false_errato)})."
            )
        lines.append("")
    everyone = board.admitted + board.rejected
    checks = sorted({name for e in everyone for name in e.metrics.by_check})
    lines += ["### Concordanza per controllo", ""]
    lines.append("| Variante | " + " | ".join(checks) + " |")
    lines.append("|---" * (len(checks) + 1) + "|")
    for e in everyone:
        cells = [_pct(e.metrics.by_check.get(name)) for name in checks]
        lines.append(f"| `{e.name}` | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def render_leaderboard(boards: list[Board], now: datetime | None = None) -> str:
    stamp = (now or datetime.now()).isoformat(timespec="minutes")
    lines = [
        "# Classifica degli esperimenti",
        "",
        f"Scritta da `cycle-validation eval classifica` il {stamp}: non modificare a mano.",
        "Si confrontano solo prove dello stesso ambiente. Come leggerla: `eval/README.md`.",
        "",
    ]
    if not boards:
        lines += ["Nessuna prova in `eval/risultati/`.", ""]
    for board in boards:
        lines += _board(board)
    return "\n".join(lines)
