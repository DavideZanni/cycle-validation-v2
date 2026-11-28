"""Prova dei cicli EJ200 sul PC, senza lasciare tracce (autorizzata dall'utente il 27-11).

La conoscenza EJ200 non si scarica: catalogo e testi si leggono da S3 (AWS EU) attraverso il
puntatore `current.json`. Il modello legge i testi da file, quindi le pubblicazioni usate si
scrivono in una cartella temporanea (`cv-ej200-...`) che si cancella alla fine, anche dopo un
errore o Ctrl+C; quelle rimaste da una prova interrotta con forza si cancellano all'avvio della
prova dopo. Niente `runs\\`, niente report, niente transcript.

A schermo vanno solo l'impronta del PDF (8 caratteri), lo stato, i conteggi, i motivi e il
costo: mai una descrizione, una fonte o un codice EJ200. Un errore si stampa con il tipo, non
con il messaggio (potrebbe contenere un codice).
"""

import hashlib
import shutil
import tempfile
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from cycle_validation.domain.check import Verdict, WarningKind, warning_kind
from cycle_validation.domain.report import Report
from cycle_validation.errors import WrongModuleError

WORKDIR_PREFIX = "cv-ej200-"


@dataclass
class Ej200Outcome:
    """Il risultato di un ciclo, senza testo."""

    fingerprint: str
    status: str = ""
    corretti: int = 0
    da_guardare: int = 0
    non_controllabili: int = 0
    errati: int = 0
    non_applicabili: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0
    reasons: Counter[str] = field(default_factory=Counter)
    problem: str = ""  # vuoto = validato; altrimenti il tipo dell'errore

    @property
    def validated(self) -> bool:
        return not self.problem


def fingerprint(pdf: Path) -> str:
    return hashlib.sha256(pdf.read_bytes()).hexdigest()[:8]


def remove_leftovers(root: Path | None = None) -> int:
    """Cancella le cartelle temporanee rimaste da una prova interrotta con forza."""
    base = root or Path(tempfile.gettempdir())
    removed = 0
    for folder in base.glob(f"{WORKDIR_PREFIX}*"):
        if folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)
            removed += not folder.exists()
    return removed


@contextmanager
def temporary_workdir(root: Path | None = None) -> Iterator[Path]:
    """La cartella dei testi EJ200 di questa prova: si cancella sempre all'uscita."""
    folder = Path(tempfile.mkdtemp(prefix=WORKDIR_PREFIX, dir=root))
    try:
        yield folder
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def outcome_of(name: str, report: Report) -> Ej200Outcome:
    counts = report.counts
    reasons: Counter[str] = Counter()
    for result in report.results:
        if result.verdict is Verdict.CORRETTO:
            continue
        label = result.verdict.value
        if result.verdict is Verdict.WARNING:
            kind = warning_kind(result.reason)
            label = (
                "WARNING da guardare"
                if kind is WarningKind.DA_GUARDARE
                else ("WARNING non controllabile")
            )
        reasons[f"{label} · {result.check.value} · {result.reason.value}"] += 1
    return Ej200Outcome(
        fingerprint=name,
        status=report.status.value,
        corretti=counts.corretto,
        da_guardare=counts.warning_da_guardare,
        non_controllabili=counts.warning_non_controllabili,
        errati=counts.errato,
        non_applicabili=counts.non_applicabile,
        cost_usd=report.usage.cost_usd,
        seconds=report.timings_ms.get("total", 0) / 1000,
        reasons=reasons,
    )


def run_cycles(pdfs: Sequence[Path], validate: Callable[[Path], Report]) -> list[Ej200Outcome]:
    """Valida ogni PDF. Un ciclo non EJ200 o che non si legge non ferma gli altri."""
    outcomes: list[Ej200Outcome] = []
    for pdf in pdfs:
        try:
            name = fingerprint(pdf)
        except OSError as error:  # file che non si legge: non ferma gli altri
            outcomes.append(Ej200Outcome(fingerprint="????????", problem=type(error).__name__))
            continue
        try:
            outcomes.append(outcome_of(name, validate(pdf)))
        except WrongModuleError:
            outcomes.append(Ej200Outcome(fingerprint=name, problem="non è un ciclo EJ200"))
        except Exception as error:  # il messaggio può contenere testo EJ200
            outcomes.append(Ej200Outcome(fingerprint=name, problem=type(error).__name__))
    return outcomes


def render(outcomes: Sequence[Ej200Outcome]) -> list[str]:
    """Le righe da stampare: per ciclo e in totale, solo numeri e motivi."""
    lines: list[str] = []
    for item in outcomes:
        if not item.validated:
            lines.append(f"{item.fingerprint}: non validato ({item.problem})")
            continue
        lines.append(
            f"{item.fingerprint}: {item.status} · {item.corretti} corretti, {item.errati} "
            f"errati, {item.da_guardare} da guardare, {item.non_controllabili} non "
            f"controllabili, {item.non_applicabili} N/A · {item.cost_usd:.4f} $ · "
            f"{item.seconds:.0f} s"
        )
        lines.extend(f"    {reason}: {n}" for reason, n in sorted(item.reasons.items()))
    done = [item for item in outcomes if item.validated]
    total: Counter[str] = Counter()
    for item in done:
        total.update(item.reasons)
    lines.append(
        f"Totale: {len(done)} cicli validati su {len(outcomes)} · "
        f"{sum(i.errati for i in done)} errati, {sum(i.da_guardare for i in done)} da "
        f"guardare, {sum(i.non_controllabili for i in done)} non controllabili, "
        f"{sum(i.corretti for i in done)} corretti · "
        f"{sum(i.cost_usd for i in done):.4f} $"
    )
    lines.extend(f"    {reason}: {n}" for reason, n in sorted(total.items()))
    return lines
