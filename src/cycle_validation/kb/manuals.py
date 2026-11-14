"""Testo dei manuali da un indice di ricerca, con ricerca ESATTA per manuale e task.

Il codice trova il dove: una `term` query sui metadati (manuale, task) restituisce i chunk
del task; il testo viene riscritto a righe in una cartella di lavoro, con i marcatori di
pagina, così che l'agente lo legga a paragrafo (GRASP) e le citazioni siano verificabili.

I nomi dei campi dell'indice non sono noti a questa macchina: `ChunkSchema` li dichiara.
Se i metadati non bastano, `fallback` (la ricerca attuale ibrida top-k) risponde al posto
della ricerca esatta, restando dietro la stessa interfaccia.
"""

import threading
from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from cycle_validation.kb.documents import chunk_lines, file_name
from cycle_validation.kb.port import DocumentInfo, TaskLocation
from cycle_validation.kb.stores import SearchIndex
from cycle_validation.text import normalize_code


@dataclass(frozen=True)
class ChunkSchema:
    manual: str = "manual"
    task: str = "task"
    version: str = "version"
    page: str = "page"
    order: str = "chunk_index"
    text: str = "text"


class ChunkFallback(Protocol):
    def find_chunks(self, manual: str, task: str) -> list[dict[str, Any]]:
        """Ricerca non esatta (ibrida, top-k) dei chunk di un task."""
        ...


class ManualSource(Protocol):
    def find_manuals(self, manual: str) -> list[DocumentInfo]: ...

    def find_task(self, manual: str, task: str) -> TaskLocation | None: ...


def _variants(name: str) -> list[str]:
    stripped = name.strip()
    return list(dict.fromkeys([stripped, stripped.upper(), " ".join(stripped.split())]))


class IndexedManualSource:
    def __init__(
        self,
        index: SearchIndex,
        workdir: Path,
        schema: ChunkSchema | None = None,
        fallback: ChunkFallback | None = None,
        aliases: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self._index = index
        self._workdir = workdir
        self._schema = schema or ChunkSchema()
        self._fallback = fallback
        self._alias_of = {
            normalize_code(alias): canonical
            for canonical, names in (aliases or {}).items()
            for alias in names
        }
        self._lock = threading.Lock()
        self._building: dict[Hashable, threading.Lock] = {}
        self._manuals: dict[str, list[DocumentInfo]] = {}
        self._tasks: dict[tuple[str, str], TaskLocation | None] = {}

    def _once[K: Hashable, V](self, cache: dict[K, V], key: K, build: Callable[[], V]) -> V:
        """Valore in cache, costruito una volta sola. Il lock comune protegge solo le tabelle;
        la costruzione (rete, scrittura del file) sta sotto un lock della singola chiave: chi
        chiede la stessa cosa aspetta e riusa, chi chiede altro non aspetta."""
        with self._lock:
            if key in cache:
                return cache[key]
            building = self._building.setdefault((id(cache), key), threading.Lock())
        with building:
            with self._lock:
                if key in cache:
                    return cache[key]
            value = build()
            with self._lock:
                cache[key] = value
            return value

    def _search(self, manual: str, task: str | None = None) -> tuple[str, list[dict[str, Any]]]:
        schema = self._schema
        manual = self._alias_of.get(normalize_code(manual), manual)
        for variant in _variants(manual):
            filters = {schema.manual: variant}
            if task is not None:
                filters[schema.task] = task.strip()
            hits = self._index.search(filters, size=2000 if task else 1)
            if hits:
                return variant, hits
        return manual, []

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        key = normalize_code(manual)
        return list(self._once(self._manuals, key, lambda: self._build_manual(manual)))

    def _build_manual(self, manual: str) -> list[DocumentInfo]:
        found, hits = self._search(manual)
        if not hits:
            return []
        version = hits[0].get(self._schema.version)
        path = self._workdir / "manuals" / file_name(found)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"<!-- page 1 -->\nManuale {found}: il testo è disponibile per task.\n",
            encoding="utf-8",
        )
        return [
            DocumentInfo(
                key=found,
                path=path,
                version=None if version is None else str(version),
                title=found,
                code=found,
            )
        ]

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        cache_key = (normalize_code(manual), normalize_code(task))
        return self._once(self._tasks, cache_key, lambda: self._build_task(manual, task))

    def _chunks(self, manual: str, task: str) -> tuple[str, list[dict[str, Any]]]:
        found, hits = self._search(manual, task)
        if not hits and self._fallback is not None:
            hits = self._fallback.find_chunks(manual, task)
        return found, hits

    def _build_task(self, manual: str, task: str) -> TaskLocation | None:
        found, hits = self._chunks(manual, task)
        if not hits:
            return None
        schema = self._schema
        lines, first_text = chunk_lines(
            hits, order=schema.order, page=schema.page, text=schema.text
        )
        if not first_text:
            return None
        version = hits[0].get(schema.version)
        key = f"{found}/{task.strip()}"
        path = self._workdir / "tasks" / file_name(f"{found}__{task.strip()}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        document = DocumentInfo(
            key=key,
            path=path,
            version=None if version is None else str(version),
            title=f"{found} task {task.strip()}",
            code=found,
        )
        return TaskLocation(
            manual_key=found,
            task=task.strip(),
            document=document,
            line_start=first_text,
            line_end=len(lines),
        )


def chunks_from_documents(
    documents: Sequence[Mapping[str, Any]], schema: ChunkSchema | None = None
) -> list[dict[str, Any]]:
    """Utile ai test: completa i chunk con l'indice d'ordine se manca."""
    schema = schema or ChunkSchema()
    return [{schema.order: i, **dict(item)} for i, item in enumerate(documents)]
