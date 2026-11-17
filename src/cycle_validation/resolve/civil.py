"""Risoluzione dei riferimenti del ciclo nelle voci della knowledge base."""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from cycle_validation.checks.uncertainty import describe, is_doubtful
from cycle_validation.domain.check import Reason
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.port import DocumentInfo, KnowledgeBase, TaskLocation
from cycle_validation.text import normalize_code

_NUMBERS = re.compile(r"\d+")


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


def _version_key(document: DocumentInfo) -> tuple[tuple[int, ...], str]:
    version = document.version or ""
    return tuple(int(number) for number in _NUMBERS.findall(version)), version


def resolve_document(name: str, kb: KnowledgeBase, issue: str | None = None) -> DocumentResolution:
    """Sceglie la pubblicazione disponibile più recente e segnala ciò che non torna."""
    candidates = kb.find_manuals(name)
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
    chosen = max(published, key=_version_key)
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


def resolve_operation(cycle: Cycle, operation: Operation, kb: KnowledgeBase) -> OperationRefs:
    """Cerca ogni task code dell'operazione nei manuali delle fonti collegate."""
    manuals = manuals_for_operation(cycle, operation)
    found: list[TaskLocation] = []
    missing: list[str] = []
    for code in operation.task_codes:
        location = next(
            (hit for manual in manuals if (hit := kb.find_task(manual, code)) is not None), None
        )
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
) -> tuple[TaskLocation, ...]:
    """Testo con cui confrontare l'operazione: i suoi task; se non ne ha di risolti,
    i task delle fonti collegate; infine quelli aggiunti dal profilo (per DR).

    Una fonte senza task può essere un documento che è tutto un task (LEAP): l'indice gli
    dà come codice del task il codice del documento, quindi si prova quello (e la chiave).
    Un task DR senza manuale si cerca nei manuali citati dal ciclo per l'operazione."""
    found = resolve_operation(cycle, operation, kb).found
    if found:
        return _dedupe(found)
    sources = linked_sources(cycle, operation)
    pairs: list[tuple[str, str]] = []
    for source in sources:
        if source.task is not None:
            pairs.append((source.manual, source.task))
            continue
        document = resolve_document(source.manual, kb).document
        if document is not None:
            names = _unique([name for name in (document.code, document.key) if name])
            pairs += [(source.manual, name) for name in names]
    manuals = _unique([source.manual for source in sources])
    for manual, task in extra_tasks:
        pairs += [(manual, task)] if manual is not None else [(name, task) for name in manuals]
    locations = [hit for manual, task in pairs if (hit := kb.find_task(manual, task))]
    return _dedupe(locations)
