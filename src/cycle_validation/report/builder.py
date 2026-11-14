"""Costruzione del Report e scrittura dei file del run."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from cycle_validation.domain.check import CheckResult, Usage
from cycle_validation.domain.cycle import Cycle
from cycle_validation.domain.report import PipelineError, Report, RunMeta
from cycle_validation.report.legacy_payload import build_legacy_payload
from cycle_validation.report.markdown_writer import render_markdown
from cycle_validation.verdict.consolidate import compute_counts, cycle_status


def build_report(
    meta: RunMeta,
    cycle: Cycle,
    results: Sequence[CheckResult],
    *,
    timings_ms: Mapping[str, int],
    pipeline_errors: Sequence[PipelineError],
    blocked: bool,
    extra_usage: Usage | None = None,
    session_modes: Mapping[str, int] | None = None,
) -> Report:
    usage = extra_usage or Usage()
    for item in results:
        usage = usage + item.usage
    return Report(
        meta=meta,
        status=cycle_status(results, blocked=blocked, pipeline_errors=pipeline_errors),
        cycle=cycle,
        results=list(results),
        counts=compute_counts(results),
        timings_ms=dict(timings_ms),
        usage=usage,
        pipeline_errors=list(pipeline_errors),
        session_modes=dict(session_modes or {}),
    )


def write_outputs(report: Report, run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "cycle.json").write_text(
        report.cycle.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )
    (run_dir / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
    payload = build_legacy_payload(report)
    (run_dir / "payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
