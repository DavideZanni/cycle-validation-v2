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
from cycle_validation.errors import CycleValidationError, SourceUnavailableError
from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import DocumentInfo, KnowledgeBase
from cycle_validation.kb.task_text import is_task_code, lines_with, task_section
from cycle_validation.resolve.civil import cited_section, section_locations

_SPACES = re.compile(r"\s+")
_SPM_PREFIX = "70-"
SPM = "SPM (pratiche standard, task 70-)"
_MAX_OTHER_FILES = 30
_MAX_LINE = 110

# Perché un task citato non è nella conoscenza (vedi `explain_missing`).
NOT_A_TASK = "forma"
IN_TEXT = "testo"
ONLY_SECTION = "sezione"
ABSENT = "assente"
_WHY = {
    IN_TEXT: "scritto nel testo, ma non come titolo di un task",
    ONLY_SECTION: "nel testo c'è solo la sua sezione",
    ABSENT: "non è nel testo del manuale",
    NOT_A_TASK: "citato in una forma che non è un task (né 72-00-01-110-001 né 72-00-01 REPAIR 001)",
}
_WHY_SHORT = {
    IN_TEXT: "nel testo ma non come titolo",
    ONLY_SECTION: "solo la sezione nel testo",
    ABSENT: "non nel testo",
    NOT_A_TASK: "forma non da task",
}


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
    military: bool = False  # ciclo EJ200: la sua conoscenza resta su AWS, fuori dalla lista
    kind: str = ""  # dalla testata: mos, dr, ej200, civil o vuoto (vedi `module_kind.py`)


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


def from_cycle(name: str, cycle: Cycle, *, military: bool = False, kind: str = "") -> CycleSeen:
    data = cycle.model_dump()
    return CycleSeen(
        name=name,
        sources=data["sources"],
        operations=data["operations"],
        military=military,
        kind=kind,
    )


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
    standard_practices: bool = False  # i task 70- (manuale SPM)
    files: list[str] = field(default_factory=list)  # PDF sul PC con il codice nel percorso
    chapter_files: list[str] = field(default_factory=list)  # ... e un capitolo citato nel nome
    # task mancante → (perché, righe del testo dove compare: «documento riga N: testo»)
    missing_why: dict[str, tuple[str, list[str]]] = field(default_factory=dict)

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
    files_checked: bool = False  # match_files è stato chiamato
    military: list[str] = field(default_factory=list)  # cicli EJ200 lasciati fuori


def _found(kb: KnowledgeBase, manual: str, task: str) -> bool:
    """Come la v2: il task nel manuale, oppure, se la fonte cita solo la sezione, almeno un
    task di quella sezione."""
    if kb.find_task(manual, task) is not None:
        return True
    section = cited_section(task)
    return section is not None and bool(section_locations(kb, manual, section))


def cycle_coverage(seen: CycleSeen, kb: KnowledgeBase) -> tuple[int, int]:
    """Quante operazioni del ciclo la v2 può confrontare con la conoscenza: (coperte, totali).
    Un'operazione è coperta se tutti i suoi task sono nella conoscenza (quelli del capitolo 70
    nell'SPM, gli altri in un manuale delle fonti con lo stesso repair code, o di tutte le
    fonti); senza task, se almeno un manuale collegato c'è (la v2 la confronta con le fonti)."""
    linked_by = [
        (_code(source.get("manual")), _code(source.get("repair_code")))
        for source in seen.sources
        if _code(source.get("manual"))
    ]
    present = {code for code, _ in linked_by if kb.find_manuals(code)}
    all_manuals = list(dict.fromkeys(code for code, _ in linked_by))
    covered = 0
    for operation in seen.operations:
        repair = _code(operation.get("repair_code"))
        same = [code for code, rc in linked_by if repair and rc == repair]
        linked = [code for code in dict.fromkeys(same or all_manuals) if code in present]
        tasks = [_code(task) for task in operation.get("task_codes") or [] if _code(task)]
        if not tasks:
            covered += bool(linked)
            continue
        covered += all(
            kb.find_task_in_kind("SPM", task) is not None
            if task.startswith(_SPM_PREFIX)
            else any(_found(kb, code, task) for code in linked)
            for task in tasks
        )
    return covered, len(seen.operations)


def needed_manuals(
    cycles: list[CycleSeen],
    errors: dict[str, set[str]],
    kb: KnowledgeBase | None = None,
) -> ManualsFound:
    """Come la v2 (`resolve/civil.py`): i task di un'operazione stanno nei manuali delle fonti
    con lo stesso repair code (se nessuna, tutte le fonti del ciclo); quelli del capitolo 70 nel
    manuale SPM. Un'operazione senza task si confronta con le fonti collegate. Il nome di un
    ciclo si confronta con le impronte di `errors` (`errori-298bc28e` o `298bc28e`)."""
    found: dict[str, ManualNeed] = {}
    loose: dict[str, set[str]] = {}
    unmatched: list[str] = []
    military = sorted(seen.name for seen in cycles if seen.military)
    for seen in cycles:
        if seen.military:
            continue
        linked_by: list[tuple[str, str]] = []  # (manuale, repair code della fonte)
        for index, source in enumerate(seen.sources):
            code = _code(source.get("manual"))
            if not code:
                continue
            need = found.setdefault(code, ManualNeed(code=str(source.get("manual")).strip()))
            need.cycles.add(seen.name)
            linked_by.append((code, _code(source.get("repair_code"))))
            if source.get("issue"):
                need.issues.add(str(source["issue"]).strip())
            task = _code(source.get("task"))
            if task:
                need.tasks.add(task)
            if seen.reasons.get(index):
                need.reasons[seen.reasons[index]] += 1
        all_manuals = list(dict.fromkeys(code for code, _ in linked_by))
        wanted = next((ops for key, ops in errors.items() if key in seen.name.lower()), set())
        for operation in seen.operations:
            repair = _code(operation.get("repair_code"))
            same = [code for code, rc in linked_by if repair and rc == repair]
            linked = list(dict.fromkeys(same)) or all_manuals
            tasks = [_code(task) for task in operation.get("task_codes") or [] if _code(task)]
            own: set[str] = set()
            for task in tasks:
                if task.startswith(_SPM_PREFIX):
                    spm = found.setdefault(SPM, ManualNeed(code=SPM, standard_practices=True))
                    spm.tasks.add(task)
                    spm.cycles.add(seen.name)
                    own.add(SPM)
                elif linked:
                    for code in linked:
                        found[code].tasks.add(task)
                    own.update(linked)
                else:
                    loose.setdefault(task, set()).add(seen.name)
            number = _op(operation.get("operation_number"))
            if number not in wanted:
                continue
            targets = own or set(linked)
            if not targets:
                unmatched.append(f"{seen.name} op {number}: il ciclo non cita nessun manuale")
            for code in targets:
                found[code].error_ops.setdefault(seen.name, set()).add(number)
    if kb is not None:
        for need in found.values():
            if need.standard_practices:
                need.missing_tasks = {
                    task for task in need.tasks if kb.find_task_in_kind("SPM", task) is None
                }
                need.in_knowledge = len(need.missing_tasks) < len(need.tasks)
                continue
            need.in_knowledge = bool(kb.find_manuals(need.code))
            if need.in_knowledge:
                need.missing_tasks = {
                    task for task in need.tasks if not _found(kb, need.code, task)
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
        military=military,
    )


def _hits(documents: list[DocumentInfo], code: str) -> list[str]:
    hits: list[str] = []
    for document in documents:
        try:
            lines = read_lines(document.path)
        except SourceUnavailableError:
            continue
        for number in lines_with(lines, code, limit=3 - len(hits)):
            text = " ".join(lines[number - 1].split())
            if len(text) > _MAX_LINE:
                text = text[: _MAX_LINE - 1] + "…"
            hits.append(f"{document.key} riga {number}: {text}")
        if len(hits) >= 3:
            break
    return hits


def explain_missing(result: ManualsFound, kb: IndexedKnowledgeBase) -> None:
    """Per ogni task che la conoscenza non ha, guarda nel testo dei documenti del manuale (o
    in quelli SPM): il codice c'è ma non come titolo (l'indice non lo riconosce), c'è solo la
    sua sezione, non c'è proprio, oppure il ciclo lo cita in una forma che non è un task."""
    for need in result.manuals:
        if not need.missing_tasks:
            continue
        documents = (
            kb.documents_of_kind("SPM") if need.standard_practices else kb.find_manuals(need.code)
        )
        for task in sorted(need.missing_tasks):
            hits = _hits(documents, task)
            if not is_task_code(task, sections=need.standard_practices):
                need.missing_why[task] = (NOT_A_TASK, hits)
            elif hits:
                need.missing_why[task] = (IN_TEXT, hits)
            else:
                section = task_section(task)
                found = _hits(documents, section) if section else []
                need.missing_why[task] = (ONLY_SECTION, found) if found else (ABSENT, [])


def _why_counts(need: ManualNeed) -> str:
    counts = Counter(why for why, _ in need.missing_why.values())
    return ", ".join(f"{_WHY_SHORT[why]} {counts[why]}" for why in _WHY_SHORT if counts[why])


def _letters(text: str) -> str:
    return re.sub(r"[^0-9A-Z]", "", text.upper())


def _chapter_pattern(chapter: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in chapter.split("-") if part]
    return re.compile(r"(?<![0-9])" + r"[-_ .]?".join(parts) + r"(?![0-9])")


def match_files(result: ManualsFound, paths: list[str]) -> None:
    """I PDF sul PC che sembrano i file di ogni manuale: il codice del manuale (o «SPM») nel
    percorso; tra questi, quelli con un capitolo citato nel nome del file."""
    result.files_checked = True
    flat = [(path, _letters(path)) for path in paths]
    for need in result.manuals:
        key = "SPM" if need.standard_practices else _letters(need.code)
        if len(key) < 3:
            continue
        need.files = sorted(path for path, letters in flat if key in letters)
        patterns = [_chapter_pattern(chapter) for chapter in need.chapters]
        need.chapter_files = [
            path
            for path in need.files
            if any(
                pattern.search(path.replace("\\", "/").rsplit("/", 1)[-1]) for pattern in patterns
            )
        ]


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
        if need.standard_practices:
            line += " (SPM)"
        if need.missing_why:
            line += f" (task mancanti: {_why_counts(need)})"
        if need.error_ops:
            line += f" · serve per {need.error_count} errori ({_ops(need)})"
        if result.files_checked:
            line += (
                f" · PDF sul PC: {len(need.files)}, dei capitoli citati: {len(need.chapter_files)}"
            )
        lines.append(line)
    if result.military:
        lines.append(f"cicli EJ200 lasciati fuori (conoscenza solo su AWS): {len(result.military)}")
    if result.loose_tasks:
        chapters = {_chapter(task) for task in result.loose_tasks}
        lines.append(
            f"task di cicli senza fonti: {len(result.loose_tasks)} in {len(chapters)} capitoli"
        )
    return lines


def count_text(result: ManualsFound) -> str:
    """Quanti manuali citati, quanti mancano del tutto, quanti ci sono ma senza tutti i task.
    I secondi non si sistemano ingestionando di nuovo gli stessi file: servono altri file (o il
    task è solo citato in una frase)."""
    missing = sum(need.state == "manca" for need in result.manuals)
    partial = sum(need.needed and need.state != "manca" for need in result.manuals)
    return (
        f"Manuali citati: {len(result.manuals)}; da ingestionare (mancano): {missing}; "
        f"già dentro ma con task che mancano: {partial}"
    )


def file_lines(result: ManualsFound, names: dict[str, list[str]] | None = None) -> list[str]:
    """Le stesse righe con i codici veri, i capitoli e i task: restano sul PC. `names`:
    impronta del ciclo → nomi dei file (per ritrovare le stampe)."""
    lines = [
        count_text(result) + ".",
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
            for task in sorted(need.missing_why):
                why, hits = need.missing_why[task]
                lines.append(f"        {task}: {_WHY[why]}")
                lines.extend(f"            {hit}" for hit in hits)
        if need.error_ops:
            lines.append(f"    serve per gli errori: {_ops(need)}")
        lines.append(f"    cicli: {', '.join(sorted(need.cycles))}")
        if result.files_checked:
            lines.append(f"    PDF sul PC con un capitolo citato: {len(need.chapter_files)}")
            lines.extend(f"        {path}" for path in need.chapter_files)
            others = [path for path in need.files if path not in need.chapter_files]
            lines.append(f"    altri PDF sul PC con il codice del manuale: {len(others)}")
            lines.extend(f"        {path}" for path in others[:_MAX_OTHER_FILES])
            if len(others) > _MAX_OTHER_FILES:
                lines.append(f"        ... e altri {len(others) - _MAX_OTHER_FILES}")
        lines.append("")
    if result.loose_tasks:
        lines.append("Task di cicli che non citano nessun manuale (manuale da capire):")
        for task in sorted(result.loose_tasks):
            lines.append(
                f"    {task}  (capitolo {_chapter(task)}; cicli: "
                f"{', '.join(sorted(result.loose_tasks[task]))})"
            )
        lines.append("")
    if result.military:
        lines.append(
            "Cicli EJ200, lasciati fuori: la loro conoscenza resta su AWS (ingestion ej200):"
        )
        lines.append(f"    {', '.join(result.military)}")
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
