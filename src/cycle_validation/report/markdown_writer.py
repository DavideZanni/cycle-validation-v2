"""report.md: riepilogo, tabella delle fonti, tabella delle operazioni, dettaglio con fonte."""

from cycle_validation.domain.check import CheckName, CheckResult, Evidence, Verdict
from cycle_validation.domain.report import Report

_SYMBOL = {
    Verdict.CORRETTO: "OK",
    Verdict.WARNING: "WARNING",
    Verdict.ERRATO: "ERRATO",
    Verdict.NON_APPLICABILE: "N/A",
}
_COLUMNS = (
    ("Descrizione", CheckName.OPERATION_DESCRIPTION),
    ("Task code", CheckName.TASK_CODE),
    ("Targa", CheckName.MACHINE_TAG),
    ("Scheda", CheckName.PROCESS_SHEET),
)


def _cell(result: CheckResult | None) -> str:
    return "—" if result is None else _SYMBOL[result.verdict]


def _cite(evidence: Evidence) -> str:
    parts = [evidence.document_key]
    if evidence.version:
        parts.append(evidence.version)
    if evidence.page is not None:
        parts.append(f"p. {evidence.page}")
    if evidence.line is not None:
        parts.append(f"riga {evidence.line}")
    return ", ".join(parts)


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(report: Report) -> str:
    meta, counts = report.meta, report.counts
    by_key = {(r.check, r.target.kind.value, r.target.index): r for r in report.results}
    lines = [
        f"# Validazione del ciclo {report.cycle.cycle_code or meta.pdf_name}",
        "",
        f"- Profilo: {meta.profile}",
        f"- Stato del ciclo: **{report.status.value}**",
        f"- Esiti: {counts.corretto} corretti, {counts.warning} warning, "
        f"{counts.errato} errati, {counts.non_applicabile} non applicabili "
        f"(quota errori {counts.errors_ratio:.0%})",
        f"- PDF: {meta.pdf_name} (sha256 {meta.pdf_sha256[:12]})",
        f"- Knowledge base: {meta.knowledge_version}; modello: {meta.model}; "
        f"prompt: {meta.prompt_version}",
        f"- Costo stimato: {report.usage.cost_usd:.4f} USD in {report.usage.sessions} sessioni",
        "",
        "## Fonti",
        "",
        "| # | Manuale | Task | Esito |",
        "|---|---|---|---|",
    ]
    for index, source in enumerate(report.cycle.sources):
        result = by_key.get((CheckName.SOURCE, "source", index))
        lines.append(f"| {index + 1} | {source.manual} | {source.task or '—'} | {_cell(result)} |")
    lines += [
        "",
        "## Operazioni",
        "",
        "| Operazione | " + " | ".join(name for name, _ in _COLUMNS) + " |",
        "|---|" + "---|" * len(_COLUMNS),
    ]
    for index, operation in enumerate(report.cycle.operations):
        cells = [_cell(by_key.get((check, "operation", index))) for _, check in _COLUMNS]
        lines.append(f"| {operation.operation_number} | " + " | ".join(cells) + " |")
    lines += ["", "## Dettaglio", ""]
    for item in report.results:
        if item.verdict is Verdict.NON_APPLICABILE:
            continue
        lines.append(
            f"- **{item.check.value}** · {item.target.label} · {item.verdict.value} "
            f"({item.reason.value}): {_escape(item.rationale)}"
        )
        lines.extend(f"  - Fonte: {_cite(e)} — «{_escape(e.quote)}»" for e in item.evidence)
    if report.pipeline_errors:
        lines += ["", "## Errori tecnici", ""]
        lines += [f"- {e.stage} {e.target}: {e.message}" for e in report.pipeline_errors]
    return "\n".join(lines) + "\n"
