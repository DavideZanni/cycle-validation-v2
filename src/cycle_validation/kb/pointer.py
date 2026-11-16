"""Puntatore alla versione pubblicata della conoscenza (`current.json`).

Lo scrive il repo knowledge-index (o l'ingestion che lo usa) dopo aver caricato tutti i file:

    knowledge/civil/current.json   {"format": 1, "version": "r7", "path": "v/r7/", ...}
    knowledge/civil/v/r7/          manifest.json, documents/, tasks.json, ...

`path` è relativo alla cartella del puntatore e non può uscirne. Gli altri campi del
puntatore (impronta, conteggi, storico) qui non servono e si ignorano.
"""

import json
import re
from dataclasses import dataclass

from cycle_validation.errors import KnowledgeError, SourceUnavailableError
from cycle_validation.kb.stores import ObjectNotFoundError, ObjectStore

POINTER_FORMAT = 1
DEFAULT_CIVIL_POINTER = "Manufacturing AI/cv3/knowledge/civil/current.json"
DEFAULT_EJ200_POINTER = "Manufacturing AI/cv3/knowledge/ej200/current.json"

_VERSION = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


@dataclass(frozen=True)
class Pointer:
    version: str
    prefix: str  # chiave della cartella della versione, con la barra finale


def read_pointer(store: ObjectStore, key: str) -> Pointer:
    """Puntatore mancante = sorgente non raggiungibile; puntatore malformato = KnowledgeError."""
    try:
        raw = store.get_bytes(key)
    except ObjectNotFoundError as exc:
        raise SourceUnavailableError(f"Puntatore della conoscenza non trovato: {key}") from exc
    try:
        loaded = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KnowledgeError(f"Puntatore {key} non è JSON valido.") from exc
    if not isinstance(loaded, dict) or loaded.get("format") != POINTER_FORMAT:
        raise KnowledgeError(f"Puntatore {key}: atteso un oggetto con format {POINTER_FORMAT}.")
    version, path = loaded.get("version"), loaded.get("path")
    if not isinstance(version, str) or not _VERSION.match(version) or version in {".", ".."}:
        raise KnowledgeError(f"Puntatore {key}: versione non valida.")
    if not isinstance(path, str) or not _relative(path):
        raise KnowledgeError(f"Puntatore {key}: percorso non valido ({path!r}).")
    folder = key.rsplit("/", 1)[0] + "/" if "/" in key else ""
    return Pointer(version=version, prefix=folder + path.strip("/") + "/")


def _relative(path: str) -> bool:
    if not path.strip("/") or path.startswith("/") or "\\" in path:
        return False
    return all(part not in {"", ".", ".."} for part in path.strip("/").split("/"))
