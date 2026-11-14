"""Porte verso le sorgenti remote (oggetti e ricerca) con le loro implementazioni.

Le implementazioni reali (`S3ObjectStore`, `OpenSearchIndex`) ricevono un client già
costruito: questo modulo non importa boto3 né opensearch-py e non tocca credenziali.
Le implementazioni in memoria e su cartella servono a test, golden set e sviluppo offline.
"""

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Protocol

from cycle_validation.errors import SourceUnavailableError


class ObjectNotFoundError(KeyError):
    """L'oggetto richiesto non esiste nello store."""


class ObjectStore(Protocol):
    def get_bytes(self, key: str) -> bytes:
        """Solleva ObjectNotFoundError se manca, SourceUnavailableError se lo store non risponde."""
        ...

    def list_keys(self, prefix: str) -> list[str]: ...


class WritableObjectStore(ObjectStore, Protocol):
    """Store con scrittura: usato da sessioni e feedback del livello API."""

    def put_bytes(self, key: str, data: bytes) -> None:
        """Solleva SourceUnavailableError se la scrittura non riesce."""
        ...

    def delete(self, key: str) -> None: ...


class SearchIndex(Protocol):
    def search(self, filters: Mapping[str, str], *, size: int = 1000) -> list[dict[str, Any]]:
        """Documenti i cui campi coincidono esattamente con `filters`, in ordine d'indice."""
        ...


class InMemoryObjectStore:
    def __init__(self, objects: Mapping[str, bytes | str | Any] | None = None) -> None:
        self._objects: dict[str, bytes] = {}
        for key, value in (objects or {}).items():
            self.put(key, value)

    def put(self, key: str, value: bytes | str | Any) -> None:
        if isinstance(value, bytes):
            self._objects[key] = value
        elif isinstance(value, str):
            self._objects[key] = value.encode("utf-8")
        else:
            self._objects[key] = json.dumps(value, ensure_ascii=False).encode("utf-8")

    def get_bytes(self, key: str) -> bytes:
        try:
            return self._objects[key]
        except KeyError:
            raise ObjectNotFoundError(key) from None

    def put_bytes(self, key: str, data: bytes) -> None:
        self._objects[key] = data

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(key for key in self._objects if key.startswith(prefix))


class LocalDirObjectStore:
    """Una cartella che replica la struttura delle chiavi S3: per usare dati esportati."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root):
            raise ObjectNotFoundError(key)
        return path

    def get_bytes(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise ObjectNotFoundError(key)
        try:
            return path.read_bytes()
        except OSError as exc:
            raise SourceUnavailableError(f"Lettura di {key} non riuscita: {exc}") from exc

    def put_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        except OSError as exc:
            raise SourceUnavailableError(f"Scrittura di {key} non riuscita: {exc}") from exc

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def list_keys(self, prefix: str) -> list[str]:
        if not self._root.is_dir():
            return []
        keys = (
            path.relative_to(self._root).as_posix()
            for path in self._root.rglob("*")
            if path.is_file()
        )
        return sorted(key for key in keys if key.startswith(prefix))


class S3ObjectStore:
    """Adattatore su un client boto3 `s3` (iniettato). Nessun accesso diretto alle credenziali."""

    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def get_bytes(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            body: bytes = response["Body"].read()
            return body
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code in ("NoSuchKey", "404"):
                raise ObjectNotFoundError(key) from exc
            raise SourceUnavailableError(f"S3 non raggiungibile ({type(exc).__name__}).") from exc

    def put_bytes(self, key: str, data: bytes) -> None:
        try:
            self._client.put_object(Bucket=self._bucket, Key=key, Body=data)
        except Exception as exc:
            raise SourceUnavailableError(f"S3 non raggiungibile ({type(exc).__name__}).") from exc

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:
            raise SourceUnavailableError(f"S3 non raggiungibile ({type(exc).__name__}).") from exc

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        try:
            while True:
                args: dict[str, Any] = {"Bucket": self._bucket, "Prefix": prefix}
                if token:
                    args["ContinuationToken"] = token
                page = self._client.list_objects_v2(**args)
                keys.extend(item["Key"] for item in page.get("Contents", []))
                if not page.get("IsTruncated"):
                    return sorted(keys)
                token = page.get("NextContinuationToken")
        except Exception as exc:
            raise SourceUnavailableError(f"S3 non raggiungibile ({type(exc).__name__}).") from exc


class InMemorySearchIndex:
    """Indice finto con corrispondenza esatta sui campi, come una `term` query."""

    def __init__(self, documents: Iterable[Mapping[str, Any]]) -> None:
        self._documents = [dict(item) for item in documents]
        self.queries: list[dict[str, str]] = []

    def search(self, filters: Mapping[str, str], *, size: int = 1000) -> list[dict[str, Any]]:
        self.queries.append(dict(filters))
        hits = [
            item
            for item in self._documents
            if all(str(item.get(field)) == value for field, value in filters.items())
        ]
        return hits[:size]


class OpenSearchIndex:
    """Adattatore su un client opensearch-py (iniettato): query `term` in `bool.filter`."""

    def __init__(self, client: Any, index: str, sort_field: str | None = None) -> None:
        self._client = client
        self._index = index
        self._sort_field = sort_field

    def search(self, filters: Mapping[str, str], *, size: int = 1000) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "size": size,
            "query": {"bool": {"filter": [{"term": {f: v}} for f, v in filters.items()]}},
        }
        if self._sort_field:
            body["sort"] = [{self._sort_field: "asc"}]
        try:
            response = self._client.search(index=self._index, body=body)
            return [dict(hit["_source"]) for hit in response["hits"]["hits"]]
        except Exception as exc:
            raise SourceUnavailableError(
                f"OpenSearch non raggiungibile ({type(exc).__name__})."
            ) from exc


def load_jsonl_index(path: Path) -> InMemorySearchIndex:
    """Indice da un file JSONL (un chunk per riga): un'esportazione dell'indice reale."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        documents = [json.loads(line) for line in lines if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceUnavailableError(f"Chunk non leggibili in {path}: {exc}") from exc
    return InMemorySearchIndex(documents)
