"""Quanto regge la conoscenza con molti documenti (N5): una conoscenza finta di N documenti.

In produzione l'ingestion avrà circa 2900 documenti, le prove ne hanno 75. La ricerca dei testi
è per codice esatto (un dizionario), quindi non dovrebbe rallentare; quello che cresce sono
l'avvio del servizio (scarica e legge tutta la conoscenza), il disco, la memoria e le ricerche
che leggono il testo (un task che l'indice non ha, i fratelli di un codice sbagliato).

Qui si scrive una conoscenza pubblicata finta (puntatore, manifest, documenti, indice dei task)
in una cartella, la si «scarica» come fa il servizio (`PublishedKnowledgeBase`, da una cartella
invece che da S3) e si misurano i tempi. Tutto inventato, niente dati veri.
"""

import random
import shutil
import tempfile
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.published import PublishedKnowledgeBase
from cycle_validation.kb.stores import LocalDirObjectStore
from cycle_validation.resolve.civil import STANDARD_PRACTICES_KIND, wrong_code_siblings

POINTER = "knowledge/civil/current.json"
VERSION = "scala"
_PREFIX = "knowledge/civil/v/scala/"


@dataclass(frozen=True)
class ScaleShape:
    documents: int = 2900
    lines: int = 3000  # righe per documento (circa 50 pagine)
    tasks: int = 30  # task per documento
    standard_practices: int = 30  # documenti SPM (capitolo 70), letti per i codici sbagliati
    line_counts: bool = True  # il manifest scrive le righe di ogni documento


def _task(document: int, number: int, spm: bool) -> str:
    if spm:
        return f"70-{document % 100:02d}-{number:02d}-350-{number + 1:03d}"
    return (
        f"72-{document % 100:02d}-{document // 100:02d}-{200 + number % 5 * 100}-{801 + number:03d}"
    )


def _key(document: int) -> str:
    return f"DOC-{document:04d}"


def write_knowledge(root: Path, shape: ScaleShape) -> int:
    """Scrive la conoscenza finta sotto `root` (la radice dello store). Restituisce i byte."""
    import json

    base = root / _PREFIX
    (base / "documents").mkdir(parents=True, exist_ok=True)
    documents: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    per_task = max(2, shape.lines // shape.tasks)
    for number in range(shape.documents):
        spm = number < shape.standard_practices
        key = _key(number)
        body: list[str] = []
        for t in range(shape.tasks):
            start = len(body) + 1
            body.append(f"TASK {_task(number, t, spm)} RIPARAZIONE DIMOSTRATIVA {t}")
            body.extend(
                f"Passo {n}: controllare la superficie, limite 0,{n % 90 + 10} mm, lente 10x."
                if n % 50
                else f"<!-- page {len(body) // 50 + 1} -->"
                for n in range(1, per_task)
            )
            tasks.append(
                {
                    "manual": key,
                    "task": _task(number, t, spm),
                    "line_start": start,
                    "line_end": len(body),
                }
            )
        (base / "documents" / f"{key}.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        row: dict[str, Any] = {
            "key": key,
            "file": f"documents/{key}.md",
            "aliases": [f"M-{number}"],
            "kind": STANDARD_PRACTICES_KIND if spm else "EM",
        }
        if shape.line_counts:
            row["lines"] = len(body)
        documents.append(row)
    (base / "manifest.json").write_text(
        json.dumps({"format": 1, "version": VERSION, "documents": documents}), encoding="utf-8"
    )
    (base / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")
    (root / POINTER).write_text(
        json.dumps({"format": 1, "version": VERSION, "path": "v/scala/"}), encoding="utf-8"
    )
    return sum(path.stat().st_size for path in base.rglob("*") if path.is_file())


def _timed(action: Callable[[], Any]) -> tuple[float, Any]:
    began = time.perf_counter()
    result = action()
    return time.perf_counter() - began, result


@dataclass
class ScaleResult:
    shape: ScaleShape
    megabytes: float
    objects: int
    startup_s: float
    reload_s: float
    peak_memory_mb: float
    known_task_us: float
    missing_task_ms: float
    wrong_code_cold_ms: float
    wrong_code_warm_ms: float

    def lines(self) -> list[str]:
        s = self.shape
        return [
            f"Conoscenza finta: {s.documents} documenti, {s.lines} righe e {s.tasks} task "
            f"ciascuno, {s.standard_practices} SPM; righe nel manifest: "
            f"{'sì' if s.line_counts else 'no'}",
            f"Disco: {self.megabytes:.0f} MB in {self.objects} file",
            f"Avvio (copia e lettura, come il servizio all'avvio): {self.startup_s:.1f} s",
            f"Riavvio con la versione già su disco: {self.reload_s:.1f} s",
            f"Memoria per la conoscenza letta (picco): {self.peak_memory_mb:.0f} MB",
            f"Task trovato nell'indice: {self.known_task_us:.1f} µs in media",
            f"Task che l'indice non ha (ricerca nel testo del manuale): "
            f"{self.missing_task_ms:.1f} ms in media",
            f"Codice sbagliato del capitolo 70 (manuale e tutti gli SPM): "
            f"{self.wrong_code_cold_ms:.0f} ms la prima volta, "
            f"{self.wrong_code_warm_ms:.0f} ms le volte dopo",
        ]


def measure_scale(shape: ScaleShape, folder: Path | None = None, seed: int = 7) -> ScaleResult:
    """Scrive, avvia e interroga la conoscenza finta. `folder` vuota = cartella temporanea."""
    own = folder is None
    root = Path(tempfile.mkdtemp(prefix="cv-scala-")) if folder is None else folder
    try:
        size = write_knowledge(root / "store", shape)
        objects = sum(1 for p in (root / "store" / _PREFIX).rglob("*") if p.is_file())
        store = LocalDirObjectStore(root / "store")
        startup, kb = _timed(
            lambda: _preloaded(PublishedKnowledgeBase(store, POINTER, root / "work"))
        )
        reload, _ = _timed(
            lambda: _preloaded(PublishedKnowledgeBase(store, POINTER, root / "work"))
        )
        tracemalloc.start()
        load_local_knowledge(root / "work" / VERSION, version=VERSION)
        peak = tracemalloc.get_traced_memory()[1] / 1e6
        tracemalloc.stop()

        rng = random.Random(seed)
        picks = [
            (rng.randrange(shape.standard_practices, shape.documents), rng.randrange(shape.tasks))
            for _ in range(2000)
        ]
        known, _ = _timed(lambda: [kb.find_task(f"M-{d}", _task(d, t, False)) for d, t in picks])
        misses = [rng.randrange(shape.standard_practices, shape.documents) for _ in range(50)]
        missing, _ = _timed(
            lambda: [kb.find_task(f"M-{d}", f"72-99-{d % 100:02d}-200-999") for d in misses]
        )
        manual = f"M-{shape.documents - 1}"
        cold, _ = _timed(lambda: wrong_code_siblings(kb, [manual], "70-99-01-350-999"))
        warm, _ = _timed(lambda: wrong_code_siblings(kb, [manual], "70-99-02-350-999"))
        return ScaleResult(
            shape=shape,
            megabytes=size / 1e6,
            objects=objects,
            startup_s=startup,
            reload_s=reload,
            peak_memory_mb=peak,
            known_task_us=known / len(picks) * 1e6,
            missing_task_ms=missing / len(misses) * 1e3,
            wrong_code_cold_ms=cold * 1e3,
            wrong_code_warm_ms=warm * 1e3,
        )
    finally:
        if own:
            shutil.rmtree(root, ignore_errors=True)


def _preloaded(kb: PublishedKnowledgeBase) -> PublishedKnowledgeBase:
    kb.preload()
    return kb
