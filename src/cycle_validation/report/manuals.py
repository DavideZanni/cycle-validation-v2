"""Quali manuali servono nella conoscenza: letti dai `report.json` delle prove già fatte.

Per ogni manuale citato dai cicli: in quali cicli, quali task e capitoli, se la conoscenza lo
aveva (esito del controllo della fonte) e per quali operazioni con un errore noto serve. Zero
token: legge solo i file. Sullo schermo i manuali escono come M1, M2, ...; i codici veri vanno
solo nel file sul PC.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from cycle_validation.errors import CycleValidationError

_SPACES = re.compile(r"\s+")


def _code(value: object) -> str:
    return _SPACES.sub("", str(value or "")).upper()


def _op(value: object) -> str:
    return str(value or "").strip().lstrip("0") or "0"


def _chapter(task: str) -> str:
    """Il capitolo di un task: i primi due pezzi (`72-00-01-110-001` → `72-00`)."""
    parts = [part for part in task.split("-") if part]
    return "-".join(parts[:2]) if len(parts) >= 2 else task


def parse_errors(values: list[str]) -> dict[str, set[str]]:
    """`impronta=op,op` → {impronta: {op, ...}} (numeri di operazione senza zeri davanti)."""
    errors: dict[str, set[str]] = {}
    for value in values:
        name, sep, ops = value.partition("=")
        if not sep or not name.strip() or not ops.strip():
            raise CycleValidationError(f"--errori «{value}»: si scrive impronta=op,op.")
        errors.setdefault(name.strip().lower(), set()).update(
            _op(op) for op in ops.split(",") if op.strip()
        )
    return errors


@dataclass
class ManualNeed:
    code: str
    issues: set[str] = field(default_factory=set)
    cycles: set[str] = field(default_factory=set)
    tasks: set[str] = field(default_factory=set)
    reasons: Counter[str] = field(default_factory=Counter)
    error_ops: dict[str, set[str]] = field(default_factory=dict)

    @property
    def chapters(self) -> list[str]:
        return sorted({_chapter(task) for task in self.tasks})

    @property
    def state(self) -> str:
        if not self.reasons:
            return "non controllato"
        if set(self.reasons) == {"VERIFICATO"}:
            return "c'è"
        if set(self.reasons) == {"FONTE_ASSENTE"}:
            return "manca"
        return "in parte: " + ", ".join(f"{r} {n}" for r, n in sorted(self.reasons.items()))

    @property
    def error_count(self) -> int:
        return sum(len(ops) for ops in self.error_ops.values())


@dataclass
class ManualsFound:
    manuals: list[ManualNeed]
    cycles: list[str]
    # operazioni con un errore noto che non portano a nessun manuale delle fonti del ciclo
    unmatched: list[str]


def needed_manuals(reports: dict[str, dict[str, Any]], errors: dict[str, set[str]]) -> ManualsFound:
    """`reports`: nome della prova → contenuto di `report.json`. Il nome della prova si
    confronta con le impronte di `errors` (per esempio `errori-298bc28e` con `298bc28e`)."""
    found: dict[str, ManualNeed] = {}
    unmatched: list[str] = []
    for name, report in reports.items():
        cycle = report.get("cycle") or {}
        sources = cycle.get("sources") or []
        reasons = {
            (result.get("target") or {}).get("index"): str(result.get("reason") or "")
            for result in report.get("results") or []
            if result.get("check") == "source"
            and (result.get("target") or {}).get("kind") == "source"
        }
        by_task: dict[str, set[str]] = {}
        for index, source in enumerate(sources):
            code = _code(source.get("manual"))
            if not code:
                continue
            need = found.setdefault(code, ManualNeed(code=str(source.get("manual")).strip()))
            need.cycles.add(name)
            if source.get("issue"):
                need.issues.add(str(source["issue"]).strip())
            task = _code(source.get("task"))
            if task:
                need.tasks.add(task)
                by_task.setdefault(task, set()).add(code)
            if reasons.get(index):
                need.reasons[reasons[index]] += 1
        wanted = next((ops for key, ops in errors.items() if key in name.lower()), set())
        for operation in cycle.get("operations") or []:
            number = _op(operation.get("operation_number"))
            if number not in wanted:
                continue
            codes = {
                code
                for task in operation.get("task_codes") or []
                for code in by_task.get(_code(task), set())
            }
            if not codes:
                tasks = len(operation.get("task_codes") or [])
                unmatched.append(f"{name} op {number}: {tasks} task, nessuno nelle fonti del ciclo")
            for code in codes:
                found[code].error_ops.setdefault(name, set()).add(number)
    manuals = sorted(
        found.values(),
        key=lambda m: (-m.error_count, m.state == "c'è", -len(m.cycles), m.code),
    )
    return ManualsFound(manuals=manuals, cycles=sorted(reports), unmatched=unmatched)


def _ops(need: ManualNeed) -> str:
    return "; ".join(
        f"{name} op {', '.join(sorted(ops, key=lambda o: (len(o), o)))}"
        for name, ops in sorted(need.error_ops.items())
    )


def screen_lines(result: ManualsFound) -> list[str]:
    """Righe senza codici veri: i manuali sono M1, M2, ..."""
    lines = []
    for number, need in enumerate(result.manuals, start=1):
        line = (
            f"M{number}: {need.state} · {len(need.cycles)} cicli · {len(need.tasks)} task in "
            f"{len(need.chapters)} capitoli · edizione {'scritta' if need.issues else 'non scritta'}"
        )
        if need.error_ops:
            line += f" · serve per {need.error_count} errori ({_ops(need)})"
        lines.append(line)
    return lines


def file_lines(result: ManualsFound) -> list[str]:
    """Le stesse righe con i codici veri, i capitoli e i task: restano sul PC."""
    lines = [
        "Manuali citati dai cicli: " + ", ".join(result.cycles),
        "Ordine: prima quelli che servono per gli errori noti, poi quelli che mancano.",
        "",
    ]
    for number, need in enumerate(result.manuals, start=1):
        lines.append(f"M{number}  {need.code}  ({need.state})")
        lines.append(f"    edizione: {', '.join(sorted(need.issues)) or '-'}")
        lines.append(f"    cicli: {', '.join(sorted(need.cycles))}")
        if need.error_ops:
            lines.append(f"    serve per gli errori: {_ops(need)}")
        lines.append(f"    capitoli: {', '.join(need.chapters) or '-'}")
        lines.append(f"    task: {', '.join(sorted(need.tasks)) or '-'}")
        lines.append("")
    if result.unmatched:
        lines.append("Operazioni con errore senza un manuale tra le fonti del ciclo:")
        lines.extend(f"    {line}" for line in result.unmatched)
    return lines
