"""Knowledge base EJ200: catalogo delle pubblicazioni (S3) e testo dei documenti (indice).

Come nel sistema attuale i documenti EJ200 non si cercano per similarità: il codice citato
(RN, EF, RDR) si risolve nel catalogo e il testo si legge per identità esatta
(`document_id` e `content_hash`). Il catalogo ha un TTL e un errore di lettura non viene
memorizzato come catalogo valido. Le targhe sono i dati TM condivisi con i profili civili.
"""

import json
import re
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.documents import chunk_lines, digest, file_name
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.kb.stores import ObjectNotFoundError, ObjectStore, SearchIndex
from cycle_validation.kb.structured import StructuredData, StructuredLayout, load_structured
from cycle_validation.text import normalize_code

DEFAULT_CATALOG_KEY = "Manufacturing AI/exports/ej200_publication/catalog.json"
DEFAULT_TTL_S = 300.0


class CatalogEntry(BaseModel):
    """Una issue di una pubblicazione. `code` raggruppa le issue; `references` sono i nomi
    con cui i cicli la citano (più codici per lo stesso nome = riferimento ambiguo)."""

    model_config = ConfigDict(extra="ignore")

    code: str
    kind: str
    issue: str | None = None
    document_id: str
    content_hash: str
    title: str = ""
    published: bool = True
    partial: bool = False
    references: list[str] = Field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.code}-{self.issue}" if self.issue else self.code


def parse_catalog(raw: bytes) -> list[CatalogEntry]:
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            loaded = loaded.get("publications", loaded.get("documents", []))
        return [CatalogEntry.model_validate(item) for item in loaded]
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise KnowledgeError(f"Catalogo EJ200 non valido: {type(exc).__name__}") from exc


class Ej200Catalog:
    """Catalogo in cache con TTL. Un errore di lettura non viene memorizzato."""

    def __init__(
        self,
        store: ObjectStore,
        key: str = DEFAULT_CATALOG_KEY,
        ttl_s: float = DEFAULT_TTL_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._store, self._key, self._ttl, self._clock = store, key, ttl_s, clock
        self._entries: list[CatalogEntry] | None = None
        self._by_name: dict[str, list[CatalogEntry]] = {}
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def _current(self) -> list[CatalogEntry]:
        """Catalogo valido, ricaricato se scaduto. Da chiamare con il lock preso."""
        fresh = self._entries is not None and self._clock() - self._loaded_at < self._ttl
        if not fresh:
            try:
                raw = self._store.get_bytes(self._key)
            except ObjectNotFoundError as exc:
                raise SourceUnavailableError(f"Catalogo EJ200 non trovato: {self._key}") from exc
            try:
                entries = parse_catalog(raw)
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc
            # Indice per nome (codice e riferimenti), nell'ordine del catalogo: una ricerca
            # non riscorre tutte le voci. Si ricostruisce solo a ogni ricarica.
            by_name: dict[str, list[CatalogEntry]] = {}
            for entry in entries:
                names = {normalize_code(entry.code), *map(normalize_code, entry.references)}
                for name in names:
                    by_name.setdefault(name, []).append(entry)
            self._entries, self._by_name = entries, by_name
            self._loaded_at = self._clock()
        assert self._entries is not None
        return self._entries

    def entries(self) -> list[CatalogEntry]:
        with self._lock:
            return list(self._current())

    def find(self, name: str) -> list[CatalogEntry]:
        with self._lock:
            self._current()
            return list(self._by_name.get(normalize_code(name), ()))


class Ej200KnowledgeBase:
    def __init__(
        self,
        version: str,
        catalog: Ej200Catalog,
        index: SearchIndex,
        workdir: Path,
        store: ObjectStore,
        layout: StructuredLayout | None = None,
        *,
        document_id_field: str = "document_id",
        hash_field: str = "content_hash",
        order_field: str = "chunk_index",
        page_field: str = "page",
        text_field: str = "text",
    ) -> None:
        self._version = version
        self._catalog = catalog
        self._index = index
        self._workdir = workdir
        self._store = store
        self._layout = layout or StructuredLayout(sp=None, dr=None)
        self._fields = (document_id_field, hash_field, order_field, page_field, text_field)
        self._lock = threading.Lock()
        self._documents: dict[str, DocumentInfo] = {}
        self._building: dict[str, threading.Lock] = {}
        self._data: StructuredData | None = None
        self.exact_queries = 0

    @property
    def version(self) -> str:
        return self._version

    def preload(self) -> None:
        """Verifica che catalogo e dati TM siano leggibili: altrimenti il run non parte."""
        try:
            self._catalog.entries()
        except SourceUnavailableError as exc:
            raise KnowledgeError(str(exc)) from exc
        with self._lock:
            self._structured()

    def _structured(self) -> StructuredData:
        if self._data is None:
            self._data = load_structured(self._store, self._layout)
        return self._data

    def _materialize(self, entry: CatalogEntry, *, full: bool) -> DocumentInfo:
        cache_key = f"{entry.key}|{entry.content_hash}|{full}"
        with self._lock:
            cached = self._documents.get(cache_key)
            if cached is not None:
                return cached
            building = self._building.setdefault(cache_key, threading.Lock())
        # Un lock per documento: chi arriva mentre un altro lo sta scrivendo aspetta e riusa
        # il risultato, senza una seconda lettura dell'indice e senza due scritture dello
        # stesso file. Documenti diversi non si aspettano tra loro.
        with building:
            with self._lock:
                cached = self._documents.get(cache_key)
            if cached is not None:
                return cached
            info = self._write(entry, cache_key, full=full)
            with self._lock:
                self._documents[cache_key] = info
            return info

    def _write(self, entry: CatalogEntry, cache_key: str, *, full: bool) -> DocumentInfo:
        # Una cartella per issue, contenuto e forma (testo o segnaposto): chi sta leggendo il
        # file non se lo vede cambiare quando il catalogo si aggiorna. Il nome resta la chiave.
        path = self._workdir / "ej200" / digest(cache_key) / file_name(entry.key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if full:
            doc_id, hash_name, order, page_field, text_field = self._fields
            with self._lock:
                self.exact_queries += 1
            hits = self._index.search({doc_id: entry.document_id, hash_name: entry.content_hash})
            lines, _ = chunk_lines(hits, order=order, page=page_field, text=text_field)
            body = "\n".join(lines) or f"{entry.title or entry.code}: nessun testo nell'indice."
        else:
            body = f"{entry.code} issue {entry.issue or 'n/d'}: testo non caricato."
        path.write_text(f"{body}\n", encoding="utf-8")
        return DocumentInfo(
            key=entry.key,
            path=path,
            version=entry.issue,
            title=entry.title,
            code=entry.code,
            kind=entry.kind,
            published=entry.published,
            partial=entry.partial,
        )

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        entries = self._catalog.find(manual)
        latest: dict[str, CatalogEntry] = {}
        for entry in entries:
            if entry.published and (
                entry.code not in latest
                or _issue_key(entry.issue) > _issue_key(latest[entry.code].issue)
            ):
                latest[entry.code] = entry
        return [self._materialize(entry, full=latest.get(entry.code) is entry) for entry in entries]

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        return None  # EJ200: i riferimenti sono pubblicazioni intere, non task

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        wanted = normalize_code(tag)
        return next((t for t in self._tags() if normalize_code(t.tag) == wanted), None)

    def _tags(self) -> Sequence[MachineTagEntry]:
        with self._lock:
            try:
                return self._structured().machine_tags
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        return None  # le schede EJ200 non si verificano

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        return []

    def stats(self) -> dict[str, int]:
        entries = self._catalog.entries()
        return {
            "pubblicazioni": len({e.code for e in entries}),
            "issue": len(entries),
            "targhe": len(self._tags()),
        }


def _issue_key(issue: str | None) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", issue or ""))
