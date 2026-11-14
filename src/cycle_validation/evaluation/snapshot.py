"""Fotografia della conoscenza: copia locale di alcuni prefissi S3, con la stessa struttura.

Gli esperimenti si confrontano solo sulla stessa conoscenza. Se le varianti leggessero S3 dal
vivo, un manuale aggiornato a metà giro cambierebbe gli esiti e il confronto non varrebbe più.
Con una fotografia datata tutte le varianti e tutte le ripetizioni leggono gli stessi file, e
il programma li legge con lo stesso codice di produzione (`RemoteKnowledgeBase`).
"""

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from cycle_validation.errors import ConfigError
from cycle_validation.kb.stores import LocalDirObjectStore, ObjectStore

INFO_FILE = "fotografia.json"


def snapshot_version(folder: Path) -> str | None:
    """La versione scritta da `take_snapshot`, se la cartella è una fotografia."""
    path = folder / INFO_FILE
    if not path.is_file():
        return None
    try:
        version = json.loads(path.read_text(encoding="utf-8")).get("versione")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    return str(version) if version else None


def take_snapshot(store: ObjectStore, prefixes: Sequence[str], dest: Path, *, source: str) -> int:
    """Copia in `dest` ogni oggetto sotto i prefissi. Restituisce quanti oggetti ha copiato."""
    if not prefixes:
        raise ConfigError("Indicare almeno un prefisso da copiare.")
    if dest.exists() and any(dest.iterdir()):
        raise ConfigError(
            f"La cartella {dest} non è vuota: una fotografia non si aggiorna, se ne fa una nuova."
        )
    target = LocalDirObjectStore(dest)
    keys = sorted({key for prefix in prefixes for key in store.list_keys(prefix)})
    keys = [key for key in keys if not key.endswith("/")]
    if not keys:
        raise ConfigError(f"Nessun oggetto sotto i prefissi: {', '.join(prefixes)}.")
    for key in keys:
        target.put_bytes(key, store.get_bytes(key))
    now = datetime.now()
    info = {
        "versione": f"foto-{now:%Y%m%d-%H%M}",
        "data": now.isoformat(timespec="seconds"),
        "origine": source,
        "prefissi": list(prefixes),
        "oggetti": len(keys),
    }
    (dest / INFO_FILE).write_text(
        json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    return len(keys)
