"""Esportazione di una knowledge base remota nel formato della cartella locale.

Serve per golden set e sviluppo senza rete: si legge una volta dalle sorgenti reali e
si lavora poi sulla cartella. Il contenuto esportato supera la stessa suite di contratto.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cycle_validation.kb.documents import PAGE_MARKER, file_name, page_at, read_lines
from cycle_validation.kb.remote import RemoteKnowledgeBase


@dataclass
class ExportReport:
    manuals: int = 0
    tasks: int = 0
    missing: list[str] = field(default_factory=list)


def _dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_local_knowledge(
    kb: RemoteKnowledgeBase,
    out_dir: Path,
    manuals: Sequence[tuple[str, Sequence[str]]],
    *,
    version: str | None = None,
) -> ExportReport:
    """Scrive `out_dir` con manifest, documenti a righe, task, targhe, schede, recommendation."""
    report = ExportReport()
    (out_dir / "documents").mkdir(parents=True, exist_ok=True)
    manifest_docs: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    for manual, tasks in manuals:
        found = kb.find_manuals(manual)
        lines: list[str] = []
        page: int | None = None
        doc_version: str | None = found[0].version if found else None
        key = found[0].key if found else manual
        for task in tasks:
            location = kb.find_task(manual, task)
            if location is None:
                report.missing.append(f"{manual} / {task}")
                continue
            doc_version = doc_version or location.document.version
            first_page = page_at(location.document.path, location.line_start)
            if first_page is not None and first_page != page:
                lines.append(f"<!-- page {first_page} -->")
                page = first_page
            source = read_lines(location.document.path)
            start = len(lines) + 1
            for line in source[location.line_start - 1 : location.line_end]:
                lines.append(line)
                marker = PAGE_MARKER.match(line)
                if marker:
                    page = int(marker.group(1))
            task_rows.append(
                {"manual": key, "task": task, "line_start": start, "line_end": len(lines)}
            )
            report.tasks += 1
        if not lines:
            continue
        name = file_name(key)
        (out_dir / "documents" / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest_docs.append(
            {"key": key, "version": doc_version, "title": key, "file": f"documents/{name}"}
        )
        report.manuals += 1
    data = kb.structured()
    _dump(
        out_dir / "manifest.json",
        {"format": 1, "version": version or kb.version, "documents": manifest_docs},
    )
    _dump(out_dir / "tasks.json", task_rows)
    _dump(
        out_dir / "machine_tags.json",
        [{"tag": item.tag, "function": item.function} for item in data.machine_tags],
    )
    _dump(
        out_dir / "process_sheets.json",
        [
            {
                "code": item.code,
                "edition": item.edition,
                "treatment": item.treatment,
                "engine_families": list(item.engine_families),
            }
            for item in data.process_sheets
        ],
    )
    _dump(
        out_dir / "dr_recommendations.json",
        [
            {
                "serial_number": item.serial_number,
                "conditions": list(item.conditions),
                "procedure": item.procedure,
                "reference": item.reference,
                "manual": item.manual,
                "tasks": list(item.tasks),
            }
            for item in data.dr_recommendations
        ],
    )
    return report
