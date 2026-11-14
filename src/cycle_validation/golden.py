"""Golden set: cicli con esiti attesi riga per riga, e misura della concordanza.

Una cartella per caso: `ciclo.json` (il ciclo), `expected.json` (esiti attesi) e, se
disponibile, `ciclo.pdf` reale. Senza PDF se ne genera uno sintetico dal ciclo.
"""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from cycle_validation.domain.check import CheckName, Reason, TargetKind, Verdict
from cycle_validation.domain.report import Report
from cycle_validation.errors import ConfigError
from cycle_validation.extract.from_file import load_cycle
from cycle_validation.pipeline import Dependencies, RunRequest, arun_validation
from cycle_validation.resolve.dr import DrSelectors
from cycle_validation.testing.pdf import synthetic_cycle_pdf


class ExpectedRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check: CheckName
    kind: TargetKind
    index: int | None = None
    verdict: Verdict
    reason: Reason | None = None


class Expected(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str = "mos"
    selectors: dict[str, object] | None = None
    status: str | None = None
    rows: list[ExpectedRow]


@dataclass(frozen=True)
class GoldenCase:
    name: str
    directory: Path
    expected: Expected

    @property
    def cycle_path(self) -> Path:
        return self.directory / "ciclo.json"

    @property
    def pdf_path(self) -> Path | None:
        path = self.directory / "ciclo.pdf"
        return path if path.is_file() else None

    def selectors(self) -> DrSelectors | None:
        raw = self.expected.selectors
        if not raw:
            return None
        conditions = raw["conditions"]
        assert isinstance(conditions, list)
        return DrSelectors(str(raw["serial_number"]), tuple(int(x) for x in conditions))


def load_cases(directory: Path) -> list[GoldenCase]:
    if not directory.is_dir():
        raise ConfigError(f"Cartella del golden set non trovata: {directory}")
    cases: list[GoldenCase] = []
    for folder in sorted(p for p in directory.iterdir() if p.is_dir()):
        path = folder / "expected.json"
        if not path.is_file() or not (folder / "ciclo.json").is_file():
            continue
        try:
            expected = Expected.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ConfigError(f"{path}: esiti attesi non validi ({exc})") from exc
        cases.append(GoldenCase(folder.name, folder, expected))
    return cases


@dataclass
class CaseResult:
    name: str
    rows: int
    matched: int
    mismatches: list[str] = field(default_factory=list)
    total_ms: int = 0
    cost_usd: float = 0.0
    inline_sessions: int = 0
    search_sessions: int = 0

    @property
    def concordance(self) -> float:
        return self.matched / self.rows if self.rows else 1.0


def evaluate_case(case: GoldenCase, report: Report) -> CaseResult:
    actual = {(r.check, r.target.kind, r.target.index): r for r in report.results}
    mismatches: list[str] = []
    for row in case.expected.rows:
        found = actual.get((row.check, row.kind, row.index))
        where = f"{row.check.value}[{row.kind.value} {row.index}]"
        if found is None:
            mismatches.append(f"{where}: atteso {row.verdict.value}, assente")
        elif found.verdict is not row.verdict:
            mismatches.append(
                f"{where}: atteso {row.verdict.value}, ottenuto {found.verdict.value} "
                f"({found.reason.value})"
            )
        elif row.reason is not None and found.reason is not row.reason:
            mismatches.append(
                f"{where}: atteso motivo {row.reason.value}, ottenuto {found.reason.value}"
            )
    if case.expected.status and report.status.value != case.expected.status:
        mismatches.append(f"stato: atteso {case.expected.status}, ottenuto {report.status.value}")
    rows = len(case.expected.rows) + (1 if case.expected.status else 0)
    return CaseResult(
        name=case.name,
        rows=rows,
        matched=rows - len(mismatches),
        mismatches=mismatches,
        total_ms=report.timings_ms.get("total", 0),
        cost_usd=report.usage.cost_usd,
        inline_sessions=report.session_modes.get("inline", 0),
        search_sessions=report.session_modes.get("search", 0),
    )


@dataclass
class GoldenSummary:
    cases: list[CaseResult]

    @property
    def rows(self) -> int:
        return sum(c.rows for c in self.cases)

    @property
    def matched(self) -> int:
        return sum(c.matched for c in self.cases)

    @property
    def concordance(self) -> float:
        return self.matched / self.rows if self.rows else 1.0

    @property
    def inline_share(self) -> float:
        total = sum(c.inline_sessions + c.search_sessions for c in self.cases)
        return sum(c.inline_sessions for c in self.cases) / total if total else 0.0

    def render(self) -> str:
        lines = [
            f"Golden set: {len(self.cases)} casi, concordanza {self.concordance:.1%} "
            f"({self.matched}/{self.rows}), costo {sum(c.cost_usd for c in self.cases):.4f} USD, "
            f"tempo {sum(c.total_ms for c in self.cases)} ms, "
            f"sessioni in linea {self.inline_share:.0%}"
        ]
        for case in self.cases:
            lines.append(f"- {case.name}: {case.matched}/{case.rows}")
            lines.extend(f"    {item}" for item in case.mismatches)
        return "\n".join(lines)


async def run_golden(
    cases: Sequence[GoldenCase], deps_for: Callable[[GoldenCase], Dependencies]
) -> GoldenSummary:
    results: list[CaseResult] = []
    for case in cases:
        deps = deps_for(case)
        request = (
            RunRequest(pdf_path=case.pdf_path, selectors=case.selectors())
            if case.pdf_path
            else RunRequest(
                pdf_bytes=synthetic_cycle_pdf(load_cycle(case.cycle_path)),
                pdf_name=f"{case.name}.pdf",
                selectors=case.selectors(),
            )
        )
        results.append(evaluate_case(case, await arun_validation(request, deps)))
    return GoldenSummary(results)
