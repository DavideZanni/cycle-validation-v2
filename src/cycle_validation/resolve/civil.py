"""Risoluzione dei riferimenti del ciclo nelle voci della knowledge base."""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from cycle_validation.checks.uncertainty import describe, is_doubtful
from cycle_validation.domain.check import Reason
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.port import DocumentInfo, KnowledgeBase, TaskLocation
from cycle_validation.kb.task_text import find_task_in_text
from cycle_validation.text import normalize_code

_NUMBERS = re.compile(r"\d+")
# Una fonte che cita solo la sezione ATA, con o senza `CIR` davanti (`CIR 72-00-01`).
_SECTION_ONLY = re.compile(r"^(?:CIR)?(\d{2}-\d{2}-\d{2})$")

# Il capitolo 70 dei manuali GE è quello delle pratiche standard: i suoi task stanno nel
# manuale SPM anche quando il ciclo cita solo il manuale del motore ("TASK 70-11-00-350-002
# ABC123456 TASK 72-11-31-..."). Il tipo è il `kind` dei documenti nel manifest.
STANDARD_PRACTICES_KIND = "SPM"
_STANDARD_PRACTICES_TASK = re.compile(r"70-")
# Una procedura DR citata come nella stampa ("D.R. CASE #00000000", "DR CASE 00000000"):
# nella conoscenza il suo codice è il solo numero.
_DR_CASE_NAME = re.compile(r"^\s*D\.?\s*R\.?\s*(?:CASE)?[\s/#]*(\d{6,})\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class DocumentResolution:
    """Esito della ricerca di un documento: quello scelto e l'eventuale problema."""

    document: DocumentInfo | None
    problem: Reason | None = None
    message: str = ""


@dataclass(frozen=True)
class OperationRefs:
    found: tuple[TaskLocation, ...]
    missing: tuple[str, ...]


def version_key(document: DocumentInfo) -> tuple[tuple[int, ...], str]:
    version = document.version or ""
    return tuple(int(number) for number in _NUMBERS.findall(version)), version


def resolve_document(name: str, kb: KnowledgeBase, issue: str | None = None) -> DocumentResolution:
    """Sceglie la pubblicazione disponibile più recente e segnala ciò che non torna."""
    candidates = kb.find_manuals(name)
    if not candidates and (case := _DR_CASE_NAME.match(name)) is not None:
        candidates = kb.find_manuals(case[1])
    if not candidates:
        return DocumentResolution(
            None, Reason.FONTE_ASSENTE, f"Il riferimento {name} non è nella knowledge base."
        )
    codes = {document.code or document.key for document in candidates}
    if len(codes) > 1:
        listed = ", ".join(sorted(codes))
        return DocumentResolution(
            None,
            Reason.RIFERIMENTO_AMBIGUO,
            f"Il riferimento {name} corrisponde a più pubblicazioni: {listed}.",
        )
    published = [document for document in candidates if document.published]
    if not published:
        return DocumentResolution(
            None, Reason.FONTE_ASSENTE, f"Il documento {name} risulta non pubblicato."
        )
    chosen = max(published, key=version_key)
    if chosen.partial:
        return DocumentResolution(
            chosen,
            Reason.PUBBLICAZIONE_PARZIALE,
            f"La pubblicazione {chosen.key} è disponibile solo in parte.",
        )
    if issue is not None:
        if chosen.version is None:
            return DocumentResolution(
                chosen,
                Reason.VERSIONE_DIVERSA,
                f"Il ciclo cita la issue {issue} di {name}, ma la issue disponibile non è nota.",
            )
        if normalize_code(issue) != normalize_code(chosen.version):
            return DocumentResolution(
                chosen,
                Reason.VERSIONE_DIVERSA,
                f"Il ciclo cita la issue {issue} di {name}; quella disponibile è {chosen.version}.",
            )
    if is_doubtful(chosen.uncertain):
        return DocumentResolution(
            chosen,
            Reason.DATO_INCERTO,
            f"Il documento {chosen.key} è disponibile.{describe(chosen.uncertain)}",
        )
    return DocumentResolution(chosen)


def _unique(names: Sequence[str]) -> list[str]:
    seen: dict[str, str] = {}
    for name in names:
        seen.setdefault(normalize_code(name), name)
    return list(seen.values())


def linked_sources(cycle: Cycle, operation: Operation) -> list[Source]:
    """Fonti con lo stesso repair code dell'operazione; se nessuna, tutte le fonti."""
    if operation.repair_code is not None:
        wanted = normalize_code(operation.repair_code)
        linked = [
            source
            for source in cycle.sources
            if source.repair_code is not None and normalize_code(source.repair_code) == wanted
        ]
        if linked:
            return linked
    return list(cycle.sources)


def manuals_for_operation(cycle: Cycle, operation: Operation) -> list[str]:
    return _unique([source.manual for source in linked_sources(cycle, operation)])


def locate_task(kb: KnowledgeBase, manuals: Sequence[str], task: str) -> TaskLocation | None:
    """Il task nei manuali indicati; un task delle pratiche standard (capitolo 70) che lì
    non c'è si cerca nei documenti SPM."""
    for manual in manuals:
        hit = kb.find_task(manual, task)
        if hit is not None:
            return hit
    if _STANDARD_PRACTICES_TASK.match(normalize_code(task)):
        return kb.find_task_in_kind(STANDARD_PRACTICES_KIND, task)
    return None


def cited_section(task: str | None) -> str | None:
    """La sezione ATA, se la fonte cita solo quella (`CIR 72-00-01` → `72-00-01`)."""
    match = _SECTION_ONLY.match(normalize_code(task or ""))
    return match.group(1) if match else None


def section_locations(kb: KnowledgeBase, manual: str, section: str) -> list[TaskLocation]:
    """I task di una sezione ATA nei documenti del manuale: in ogni documento, dal primo titolo
    della sezione (`CIR 72-00-01, REPAIR 002`, `72-00-01-110-001 ...`) al titolo di un'altra
    sezione. Nei manuali GE ogni CIR (ispezione, ogni REPAIR) è spesso un file a sé."""
    locations: list[TaskLocation] = []
    for document in kb.find_manuals(manual):
        if not document.published:
            continue
        found = find_task_in_text(read_lines(document.path), section, sections=True)
        if found is not None:
            locations.append(
                TaskLocation(
                    manual_key=document.key,
                    task=section,
                    document=document,
                    line_start=found[0],
                    line_end=found[1],
                )
            )
    return locations


def resolve_operation(cycle: Cycle, operation: Operation, kb: KnowledgeBase) -> OperationRefs:
    """Cerca ogni task code dell'operazione nei manuali delle fonti collegate (e, per il
    capitolo 70, nel manuale SPM)."""
    manuals = manuals_for_operation(cycle, operation)
    found: list[TaskLocation] = []
    missing: list[str] = []
    for code in operation.task_codes:
        location = locate_task(kb, manuals, code)
        if location is None:
            missing.append(code)
        else:
            found.append(location)
    return OperationRefs(tuple(found), tuple(missing))


def _dedupe(locations: Sequence[TaskLocation]) -> tuple[TaskLocation, ...]:
    seen: dict[tuple[str, int], TaskLocation] = {}
    for location in locations:
        seen.setdefault((location.document.key, location.line_start), location)
    return tuple(seen.values())


def whole_document(document: DocumentInfo) -> TaskLocation:
    return TaskLocation(
        manual_key=document.key,
        task="",
        document=document,
        line_start=1,
        line_end=max(len(read_lines(document.path)), 1),
    )


def cited_documents(cycle: Cycle, kb: KnowledgeBase, order: Sequence[str]) -> list[DocumentInfo]:
    """Documenti citati dalle fonti e disponibili, ordinati per tipo secondo `order`."""
    documents: dict[str, DocumentInfo] = {}
    for source in cycle.sources:
        document = resolve_document(source.manual, kb).document
        if document is not None:
            documents.setdefault(document.key, document)
    ranks = {normalize_code(kind): rank for rank, kind in enumerate(order)}

    def rank(document: DocumentInfo) -> int:
        return ranks.get(normalize_code(document.kind or ""), len(ranks))

    return sorted(documents.values(), key=rank)


def context_locations(
    cycle: Cycle,
    operation: Operation,
    kb: KnowledgeBase,
    *,
    extra_tasks: Sequence[tuple[str | None, str]] = (),
    extra_documents: Sequence[DocumentInfo] = (),
) -> tuple[TaskLocation, ...]:
    """Testo con cui confrontare l'operazione: i suoi task; se non ne ha di risolti,
    i task delle fonti collegate; infine quelli aggiunti dal profilo (per DR). Se nessuno
    di questi si trova, i documenti interi di `extra_documents` (la procedura DR).

    Una fonte senza task può essere un documento che è tutto un task (LEAP): l'indice gli
    dà come codice del task il codice del documento, quindi si prova quello (e la chiave).
    Un task DR senza manuale si cerca nei manuali citati dal ciclo per l'operazione. Una
    fonte che cita solo la sezione ATA porta tutti i task di quella sezione."""
    found = resolve_operation(cycle, operation, kb).found
    if found:
        return _dedupe(found)
    sources = linked_sources(cycle, operation)
    pairs: list[tuple[str, str]] = []
    sections: list[TaskLocation] = []
    for source in sources:
        if (section := cited_section(source.task)) is not None:
            # la fonte cita solo la sezione: tutti i suoi task nel manuale
            sections += section_locations(kb, source.manual, section)
            continue
        if source.task is not None:
            pairs.append((source.manual, source.task))
            continue
        document = resolve_document(source.manual, kb).document
        if document is not None:
            names = _unique([name for name in (document.code, document.key) if name])
            pairs += [(source.manual, name) for name in names]
    manuals = _unique([source.manual for source in sources])
    lookups = [([manual], task) for manual, task in pairs]
    for manual, task in extra_tasks:
        lookups.append(([manual] if manual is not None else manuals, task))
    locations = [hit for names, task in lookups if (hit := locate_task(kb, names, task))]
    locations += sections
    if not locations:
        locations = [whole_document(document) for document in extra_documents]
    return _dedupe(locations)
