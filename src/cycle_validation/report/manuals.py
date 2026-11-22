"""Quali manuali servono nella conoscenza per i cicli di prova.

I cicli arrivano dalle stampe (lette con il parser, zero token) o dai `report.json` delle prove
già fatte. Per ogni manuale citato: in quali cicli, quali task e capitoli, se la conoscenza lo
ha (con una conoscenza locale, oppure dall'esito del controllo della fonte nei report) e per
quali operazioni con un errore noto serve. Sullo schermo i manuali escono come M1, M2, ...; i
codici veri vanno solo nel file sul PC.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from cycle_validation.domain.cycle import Cycle
from cycle_validation.errors import CycleValidationError
from cycle_validation.kb.port import KnowledgeBase

_SPACES = re.compile(r"\s+")


def _code(value: object) -> str:
    return _SPACES.sub(" ", str(value or "")).strip().upper()


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
class CycleSeen:
    """Un ciclo di prova: fonti, operazioni e (dai report) l'esito del controllo delle fonti."""

    name: str
    sources: list[dict[str, Any]]
    operations: list[dict[str, Any]]
    reasons: dict[int, str] = field(default_factory=dict)


def from_report(name: str, report: dict[str, Any]) -> CycleSeen:
    cycle = report.get("cycle") or {}
    reasons: dict[int, str] = {}
    for result in report.get("results") or []:
        target = result.get("target") or {}
        index = target.get("index")
        is_source = result.get("check") == "source" and target.get("kind") == "source"
        if is_source and isinstance(index, int):
            reasons[index] = str(result.get("reason") or "")
    return CycleSeen(
        name=name,
        sources=list(cycle.get("sources") or []),
        operations=list(cycle.get("operations") or []),
        reasons=reasons,
    )


def from_cycle(name: str, cycle: Cycle) -> CycleSeen:
    data = cycle.model_dump()
    return CycleSeen(name=name, sources=data["sources"], operations=data["operations"])


@dataclass
class ManualNeed:
    code: str
    issues: set[str] = field(default_factory=set)
    cycles: set[str] = field(default_factory=set)
    tasks: set[str] = field(default_factory=set)
    reasons: Counter[str] = field(default_factory=Counter)
    error_ops: dict[str, set[str]] = field(default_factory=dict)
    in_knowledge: bool | None = None  # None: nessuna conoscenza locale data
    missing_tasks: set[str] = field(default_factory=set)

    @property
    def chapters(self) -> list[str]:
        return sorted({_chapter(task) for task in self.tasks})

    @property
    def state(self) -> str:
        if self.in_knowledge is not None:
            if not self.in_knowledge:
                return "manca"
            if self.missing_tasks:
                return f"c'è, ma mancano {len(self.missing_tasks)} task"
            return "c'è"
        if not self.reasons:
            return "non controllato"
        if set(self.reasons) == {"VERIFICATO"}:
            return "c'è"
        if set(self.reasons) == {"FONTE_ASSENTE"}:
            return "manca"
        return "in parte: " + ", ".join(f"{r} {n}" for r, n in sorted(self.reasons.items()))

    @property
    def needed(self) -> bool:
        return self.state != "c'è"

    @property
    def error_count(self) -> int:
        return sum(len(ops) for ops in self.error_ops.values())


@dataclass
class ManualsFound:
    manuals: list[ManualNeed]
    cycles: list[str]
    # task citati dalle operazioni ma da nessuna fonte del ciclo (per esempio quelli `70-`)
    loose_tasks: dict[str, set[str]]
    # operazioni con un errore noto che non portano a nessun manuale delle fonti del ciclo
    unmatched: list[str]


def needed_manuals(
    cycles: list[CycleSeen],
    errors: dict[str, set[str]],
    kb: KnowledgeBase | None = None,
) -> ManualsFound:
    """Il nome di un ciclo si confronta con le impronte di `errors` (per esempio
    `errori-298bc28e` o `298bc28e` con `298bc28e`)."""
    found: dict[str, ManualNeed] = {}
    loose: dict[str, set[str]] = {}
    unmatched: list[str] = []
    for seen in cycles:
        by_task: dict[str, set[str]] = {}
        for index, source in enumerate(seen.sources):
            code = _code(source.get("manual"))
            if not code:
                continue
            need = found.setdefault(code, ManualNeed(code=str(source.get("manual")).strip()))
            need.cycles.add(seen.name)
            if source.get("issue"):
                need.issues.add(str(source["issue"]).strip())
            task = _code(source.get("task"))
            if task:
                need.tasks.add(task)
                by_task.setdefault(task, set()).add(code)
            if seen.reasons.get(index):
                need.reasons[seen.reasons[index]] += 1
        wanted = next((ops for key, ops in errors.items() if key in seen.name.lower()), set())
        for operation in seen.operations:
            tasks = [_code(task) for task in operation.get("task_codes") or [] if _code(task)]
            for task in tasks:
                if task not in by_task:
                    loose.setdefault(task, set()).add(seen.name)
            number = _op(operation.get("operation_number"))
            if number not in wanted:
                continue
            codes = {code for task in tasks for code in by_task.get(task, set())}
            if not codes:
                unmatched.append(
                    f"{seen.name} op {number}: {len(tasks)} task, nessuno nelle fonti del ciclo"
                )
            for code in codes:
                found[code].error_ops.setdefault(seen.name, set()).add(number)
    if kb is not None:
        for need in found.values():
            need.in_knowledge = bool(kb.find_manuals(need.code))
            if need.in_knowledge:
                need.missing_tasks = {
                    task for task in need.tasks if kb.find_task(need.code, task) is None
                }
    manuals = sorted(
        found.values(),
        key=lambda m: (-m.error_count, not m.needed, -len(m.cycles), m.code),
    )
    return ManualsFound(
        manuals=manuals,
        cycles=sorted(seen.name for seen in cycles),
        loose_tasks=loose,
        unmatched=unmatched,
    )


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
            f"{len(need.chapters)} capitoli"
        )
        if need.error_ops:
            line += f" · serve per {need.error_count} errori ({_ops(need)})"
        lines.append(line)
    if result.loose_tasks:
        chapters = {_chapter(task) for task in result.loose_tasks}
        lines.append(
            f"task senza manuale nelle fonti del ciclo: {len(result.loose_tasks)} in "
            f"{len(chapters)} capitoli"
        )
    return lines


def file_lines(result: ManualsFound, names: dict[str, list[str]] | None = None) -> list[str]:
    """Le stesse righe con i codici veri, i capitoli e i task: restano sul PC. `names`:
    impronta del ciclo → nomi dei file (per ritrovare le stampe)."""
    needed = sum(need.needed for need in result.manuals)
    lines = [
        f"Manuali citati dai cicli di prova: {len(result.manuals)}; da ingestionare: {needed}.",
        "Ordine: prima quelli che servono per gli errori noti, poi quelli che mancano, poi gli",
        "altri. Per ognuno bastano i capitoli scritti sotto.",
        "",
    ]
    for number, need in enumerate(result.manuals, start=1):
        lines.append(f"M{number}  {need.code}  ({need.state})")
        lines.append(f"    edizione: {', '.join(sorted(need.issues)) or '-'}")
        lines.append(f"    capitoli: {', '.join(need.chapters) or '-'}")
        lines.append(f"    task: {', '.join(sorted(need.tasks)) or '-'}")
        if need.missing_tasks:
            lines.append(
                f"    task che la conoscenza non ha: {', '.join(sorted(need.missing_tasks))}"
            )
        if need.error_ops:
            lines.append(f"    serve per gli errori: {_ops(need)}")
        lines.append(f"    cicli: {', '.join(sorted(need.cycles))}")
        lines.append("")
    if result.loose_tasks:
        lines.append(
            "Task citati dalle operazioni ma da nessuna fonte del ciclo (manuale da capire,"
        )
        lines.append("per esempio SPM per i task 70-):")
        for task in sorted(result.loose_tasks):
            lines.append(
                f"    {task}  (capitolo {_chapter(task)}; cicli: "
                f"{', '.join(sorted(result.loose_tasks[task]))})"
            )
        lines.append("")
    if result.unmatched:
        lines.append("Operazioni con errore senza un manuale tra le fonti del ciclo:")
        lines.extend(f"    {line}" for line in result.unmatched)
        lines.append("")
    if names:
        lines.append("Cicli (impronta: file):")
        for name in sorted(names):
            lines.append(f"    {name}: {' | '.join(names[name])}")
    return lines
