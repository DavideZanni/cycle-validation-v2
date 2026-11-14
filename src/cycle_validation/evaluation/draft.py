"""Bozza degli esiti attesi per un ciclo vero: la scrive il programma, la corregge una persona.

Scrivere `expected.json` a mano, riga per riga, è lento. Qui il programma valida il ciclo una
volta e propone i suoi esiti come attesi, con `"rivisto": false`; `revisione.md` li mostra in
una tabella leggibile, con la spiegazione e la citazione. Chi conosce il ciclo corregge le
righe sbagliate e mette `"rivisto": true`. Fino ad allora gli esperimenti saltano il caso: una
bozza non controllata misurerebbe il programma contro se stesso.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from cycle_validation.domain.report import Report
from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.run import (
    SessionFactory,
    Suite,
    case_dependencies,
    load_prompts,
)
from cycle_validation.evaluation.variant import Variant
from cycle_validation.golden import Expected, GoldenCase, case_request
from cycle_validation.pipeline import arun_validation


def _cell(text: str, limit: int = 160) -> str:
    flat = " ".join(text.split()).replace("|", "/")
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def _review(report: Report, case_dir: Path) -> str:
    lines = [
        f"# Revisione degli esiti attesi: {case_dir.name}",
        "",
        "Bozza scritta da `cycle-validation eval prepara`. Per ogni riga decidi se l'esito è",
        "quello giusto. Se non lo è, correggi `verdict` e `reason` della stessa riga in",
        "`expected.json` (stesso ordine di questa tabella). Controlla anche `ciclo.json`: è il",
        "ciclo letto dal PDF e fa da riferimento per misurare l'estrazione.",
        "",
        'Quando hai finito, in `expected.json` metti `"rivisto": true`: da quel momento il caso',
        "entra negli esperimenti.",
        "",
        f"Stato del ciclo proposto: **{report.status.value}**.",
        "",
        "| # | Controllo | Su che cosa | Esito | Motivo | Spiegazione | Citazione |",
        "|---|---|---|---|---|---|---|",
    ]
    for number, result in enumerate(report.results, 1):
        quote = result.evidence[0].quote if result.evidence else ""
        lines.append(
            f"| {number} | {result.check.value} | {_cell(result.target.label or '-', 40)} "
            f"| {result.verdict.value} | {result.reason.value} | {_cell(result.rationale)} "
            f"| {_cell(quote, 80)} |"
        )
    lines.append("")
    return "\n".join(lines)


def draft_case(
    case_dir: Path,
    suite: Suite,
    variant: Variant,
    session_factory: SessionFactory,
    *,
    project_root: Path,
    workdir: Path,
    profile: str | None = None,
    selectors: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> Report:
    """Valida `case_dir/ciclo.pdf` e scrive `expected.json` (bozza), `revisione.md` e, se
    manca, `ciclo.json`. Se `ciclo.json` c'è già, il ciclo si legge da lì."""
    pdf = case_dir / "ciclo.pdf"
    if not pdf.is_file():
        raise ConfigError(f"Manca il PDF del ciclo: {pdf}")
    expected_path = case_dir / "expected.json"
    if expected_path.is_file() and not overwrite:
        current = json.loads(expected_path.read_text(encoding="utf-8"))
        if current.get("rivisto", True):
            raise ConfigError(
                f"{expected_path} è già stato rivisto: non lo sovrascrivo. "
                "Per rifare la bozza cancellalo, oppure usa --sovrascrivi."
            )
    expected = Expected(
        profile=profile or suite.config.profilo or "mos",
        selectors=selectors,
        rivisto=False,
        rows=[],
    )
    case = GoldenCase(case_dir.name, case_dir, expected)
    from_pdf = case.cycle_json is None
    session = session_factory(variant.settings.agent, workdir / "transcripts")
    deps = case_dependencies(
        variant,
        suite,
        case,
        suite.knowledge(workdir),
        session,
        load_prompts(variant, project_root),
        from_pdf=from_pdf,
    )
    report = asyncio.run(arun_validation(case_request(case), deps))
    if from_pdf:
        case.cycle_path.write_text(
            report.cycle.model_dump_json(indent=2, exclude_none=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    draft: dict[str, Any] = {
        "profile": expected.profile,
        **({"selectors": selectors} if selectors else {}),
        "rivisto": False,
        "status": report.status.value,
        "rows": [
            {
                "check": r.check.value,
                "kind": r.target.kind.value,
                "index": r.target.index,
                "verdict": r.verdict.value,
                "reason": r.reason.value,
            }
            for r in report.results
        ],
    }
    expected_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (case_dir / "revisione.md").write_text(
        _review(report, case_dir), encoding="utf-8", newline="\n"
    )
    return report
