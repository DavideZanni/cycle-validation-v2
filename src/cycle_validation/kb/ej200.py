"""Knowledge base EJ200: catalogo delle pubblicazioni e testo dei documenti, entrambi su S3.

I documenti EJ200 non si cercano per similarità: il codice citato (RN, EF, RDR) si risolve
nel catalogo e il testo è un markdown a righe, con marcatori di pagina, all'oggetto
`<text_prefix><document_id>/<content_hash>.md` dello store. Il catalogo ha un TTL e un errore di lettura non viene
memorizzato come catalogo valido. Le targhe sono i dati TM condivisi con i profili civili.

Con `pointer_key` il catalogo si legge dalla versione indicata da `current.json`
(`<versione>/catalog.json`) e ogni voce ricorda il prefisso dei testi della sua versione:
una validazione che ha già trovato una voce ne legge il testo anche dopo un cambio di versione.
Accanto c'è `uncertainty.json` (facoltativo): le voci scelte tra copie diverse con lo stesso
codice e issue, con il motivo. È un'aggiunta: se non si legge, o cita una voce assente dal
catalogo, quella parte si ignora con un avviso nel log e il catalogo resta usabile.
"""

import json
import logging
import re
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.documents import digest, file_name
from cycle_validation.kb.pointer import read_pointer
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.kb.stores import ObjectNotFoundError, ObjectStore
from cycle_validation.kb.structured import StructuredData, StructuredLayout, load_structured
from cycle_validation.text import normalize_code

log = logging.getLogger(__name__)

DEFAULT_CATALOG_KEY = "Manufacturing AI/exports/ej200_publication/catalog.json"
DEFAULT_TEXT_PREFIX = "Manufacturing AI/exports/ej200_publication/text/"
DEFAULT_TTL_S = 300.0
# Dentro la cartella di una versione pubblicata da knowledge-index.
POINTER_CATALOG = "catalog.json"
POINTER_TEXTS = "text/"
POINTER_UNCERTAINTY = "uncertainty.json"
# Campi che imposta questo codice, mai il file del catalogo.
_DERIVED = frozenset({"text_prefix", "uncertain"})


def base_code(code: str, issue: str | None) -> str:
    """Il codice della pubblicazione senza la issue: il catalogo pubblicato scrive
    `"code": "EJ00000X-02", "issue": "02"`, ma le issue della stessa pubblicazione devono
    avere lo stesso codice (`EJ00000X`), altrimenti diventano pubblicazioni diverse."""
    if issue:
        suffix = f"-{normalize_code(issue)}"
        if normalize_code(code).endswith(suffix) and len(code.strip()) > len(suffix):
            return code.strip()[: -len(suffix)].rstrip(" -")
    return code


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
    # Lo imposta il catalogo letto da un puntatore, mai il file: dove stanno i testi.
    text_prefix: str | None = None
    # Da `uncertainty.json` della stessa versione, mai dal file del catalogo.
    uncertain: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _code_without_issue(self) -> "CatalogEntry":
        self.code = base_code(self.code, self.issue)
        return self

    @property
    def key(self) -> str:
        return f"{self.code}-{self.issue}" if self.issue else self.code


def parse_catalog(raw: bytes) -> list[CatalogEntry]:
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            loaded = loaded.get("publications", loaded.get("documents", []))
        return [
            CatalogEntry.model_validate(
                {k: v for k, v in item.items() if k not in _DERIVED}
                if isinstance(item, dict)
                else item
            )
            for item in loaded
        ]
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise KnowledgeError(f"Catalogo EJ200 non valido: {type(exc).__name__}") from exc


class _UncertainEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    issue: str | None = None
    document_id: str
    reasons: list[str] = Field(min_length=1)


class _Uncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal[1]
    catalog: list[_UncertainEntry] = Field(default_factory=list)


def _entry_key(code: str, issue: str | None, document_id: str) -> tuple[str, str, str]:
    return normalize_code(base_code(code, issue)), issue or "", document_id


def with_uncertainty(entries: list[CatalogEntry], raw: bytes) -> list[CatalogEntry]:
    """Le voci con i motivi di `uncertainty.json`. File non valido: voci invariate; voce
    assente dal catalogo: saltata. In entrambi i casi un avviso nel log."""
    try:
        doubts = _Uncertainty.model_validate_json(raw)
    except ValidationError as exc:
        log.warning("%s EJ200 ignorato: %s", POINTER_UNCERTAINTY, type(exc).__name__)
        return entries
    known = {_entry_key(e.code, e.issue, e.document_id) for e in entries}
    reasons: dict[tuple[str, str, str], set[str]] = {}
    for item in doubts.catalog:
        key = _entry_key(item.code, item.issue, item.document_id)
        if key not in known:
            log.warning(
                "%s: la voce %s issue %s (%s) non è nel catalogo, ignorata.",
                POINTER_UNCERTAINTY,
                item.code,
                item.issue or "n/d",
                item.document_id,
            )
            continue
        reasons.setdefault(key, set()).update(item.reasons)
    return [
        entry.model_copy(update={"uncertain": tuple(sorted(found))})
        if (found := reasons.get(_entry_key(entry.code, entry.issue, entry.document_id)))
        else entry
        for entry in entries
    ]


class Ej200Catalog:
    """Catalogo in cache con TTL. Un errore di lettura non viene memorizzato."""

    def __init__(
        self,
        store: ObjectStore,
        key: str = DEFAULT_CATALOG_KEY,
        ttl_s: float = DEFAULT_TTL_S,
        clock: Callable[[], float] = time.monotonic,
        *,
        pointer_key: str | None = None,
    ) -> None:
        self._store, self._key, self._ttl, self._clock = store, key, ttl_s, clock
        self._pointer_key = pointer_key
        self._version: str | None = None
        self._entries: list[CatalogEntry] | None = None
        self._by_name: dict[str, list[CatalogEntry]] = {}
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def _current(self) -> list[CatalogEntry]:
        """Catalogo valido, ricaricato se scaduto. Da chiamare con il lock preso."""
        fresh = self._entries is not None and self._clock() - self._loaded_at < self._ttl
        if not fresh:
            key, version, text_prefix, doubts_key = self._key, None, None, None
            if self._pointer_key is not None:
                try:
                    pointer = read_pointer(self._store, self._pointer_key)
                except KnowledgeError as exc:
                    raise SourceUnavailableError(str(exc)) from exc
                key = pointer.prefix + POINTER_CATALOG
                version, text_prefix = pointer.version, pointer.prefix + POINTER_TEXTS
                doubts_key = pointer.prefix + POINTER_UNCERTAINTY
            try:
                raw = self._store.get_bytes(key)
            except ObjectNotFoundError as exc:
                raise SourceUnavailableError(f"Catalogo EJ200 non trovato: {key}") from exc
            try:
                entries = parse_catalog(raw)
                if doubts_key is not None:
                    entries = self._with_doubts(entries, doubts_key)
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc
            if text_prefix is not None:
                entries = [
                    entry.model_copy(update={"text_prefix": text_prefix}) for entry in entries
                ]
            # Indice per nome (codice e riferimenti), nell'ordine del catalogo: una ricerca
            # non riscorre tutte le voci. Si ricostruisce solo a ogni ricarica.
            by_name: dict[str, list[CatalogEntry]] = {}
            for entry in entries:
                names = {normalize_code(entry.code), *map(normalize_code, entry.references)}
                for name in names:
                    by_name.setdefault(name, []).append(entry)
            self._entries, self._by_name, self._version = entries, by_name, version
            self._loaded_at = self._clock()
        assert self._entries is not None
        return self._entries

    def _with_doubts(self, entries: list[CatalogEntry], key: str) -> list[CatalogEntry]:
        try:
            raw = self._store.get_bytes(key)
        except ObjectNotFoundError:
            return entries  # versione senza incertezze (o scritta prima che esistessero)
        return with_uncertainty(entries, raw)

    @property
    def version(self) -> str | None:
        """Versione del puntatore del catalogo in uso; None senza puntatore."""
        if self._pointer_key is None:
            return None
        with self._lock:
            self._current()
            return self._version

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
        workdir: Path,
        store: ObjectStore,
        layout: StructuredLayout | None = None,
        *,
        text_prefix: str = DEFAULT_TEXT_PREFIX,
        tags: Callable[[], Sequence[MachineTagEntry]] | None = None,
    ) -> None:
        self._version = version
        self._catalog = catalog
        self._workdir = workdir
        self._store = store
        self._layout = layout or StructuredLayout(sp=None, dr=None)
        self._text_prefix = text_prefix
        self._tag_source = tags  # targhe da un'altra conoscenza (quella civile pubblicata)
        self._lock = threading.Lock()
        self._documents: dict[str, DocumentInfo] = {}
        self._building: dict[str, threading.Lock] = {}
        self._data: StructuredData | None = None

    @property
    def version(self) -> str:
        return self._catalog.version or self._version

    def preload(self) -> None:
        """Verifica che catalogo e dati TM siano leggibili: altrimenti il run non parte."""
        try:
            self._catalog.entries()
        except SourceUnavailableError as exc:
            raise KnowledgeError(str(exc)) from exc
        if self._tag_source is not None:
            try:
                self._tag_source()
            except SourceUnavailableError as exc:
                raise KnowledgeError(str(exc)) from exc
            return
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
        # il risultato, senza una seconda lettura del testo e senza due scritture dello
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
            body = self._read_text(entry) or f"{entry.title or entry.code}: nessun testo su S3."
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
            uncertain=entry.uncertain,
        )

    def _read_text(self, entry: CatalogEntry) -> str:
        prefix = entry.text_prefix or self._text_prefix
        key = f"{prefix}{entry.document_id}/{entry.content_hash}.md"
        try:
            return self._store.get_bytes(key).decode("utf-8").rstrip("\n")
        except ObjectNotFoundError:
            return ""

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        entries = self._catalog.find(manual) or self._by_code_and_issue(manual)
        latest: dict[str, CatalogEntry] = {}
        for entry in entries:
            if entry.published and (
                entry.code not in latest
                or _issue_key(entry.issue) > _issue_key(latest[entry.code].issue)
            ):
                latest[entry.code] = entry
        return [self._materialize(entry, full=latest.get(entry.code) is entry) for entry in entries]

    def _by_code_and_issue(self, manual: str) -> list[CatalogEntry]:
        """Il ciclo può citare una pubblicazione con la issue attaccata al codice
        (`<codice>-01`) mentre il catalogo ha codice e issue separati: se il nome intero non
        c'è, si prova codice + issue. Solo le voci di quella issue, nessuna supposizione."""
        match = _CODE_AND_ISSUE.fullmatch(manual.strip())
        if match is None:
            return []
        issue = match.group("issue")
        return [
            entry
            for entry in self._catalog.find(match.group("code"))
            if entry.issue is not None and _same_issue(entry.issue, issue)
        ]

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        return None  # EJ200: i riferimenti sono pubblicazioni intere, non task

    def find_task_in_kind(self, kind: str, task: str) -> TaskLocation | None:
        return None

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        wanted = normalize_code(tag)
        return next((t for t in self._tags() if normalize_code(t.tag) == wanted), None)

    def _tags(self) -> Sequence[MachineTagEntry]:
        if self._tag_source is not None:
            try:
                return self._tag_source()
            except KnowledgeError as exc:
                raise SourceUnavailableError(str(exc)) from exc
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


# `<codice>-<issue>`: la issue è l'ultimo pezzo dopo un trattino, corto (01, 2, A).
_CODE_AND_ISSUE = re.compile(r"(?P<code>.+?)\s*[-\u2010-\u2015]\s*(?P<issue>[0-9A-Za-z]{1,3})")


def _same_issue(left: str, right: str) -> bool:
    """`01` e `1` sono la stessa issue; le lettere si confrontano come codici."""
    if left.strip().isdigit() and right.strip().isdigit():
        return int(left) == int(right)
    return normalize_code(left) == normalize_code(right)


def _issue_key(issue: str | None) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", issue or ""))
