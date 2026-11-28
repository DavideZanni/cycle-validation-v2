"""Campagna di prove: tutti gli esperimenti in fila, con Haiku e con Sonnet, sul piccolo e sul
grande, e un report finale unico (`runs/campagna.md`).

L'elenco sta in `eval/campagna.yaml`:

```yaml
varianti: [effort_medio, conferme_1]   # la base si fa sempre per prima
ripetizioni: 2
modelli:                               # nome → id del modello; vuoto = quello delle impostazioni
  haiku:
  sonnet: eu.anthropic.claude-sonnet-5-5
insiemi: [piccolo, grande]
grande: se_si_tiene                    # se_si_tiene | sempre | mai
massimo_dollari: 40
```

Ogni modello ha le sue cartelle (`runs/prove-<insieme>` per il primo, `runs/prove-<insieme>-
<modello>` per gli altri) e la sua base: una variante si confronta solo con la base dello stesso
modello. Le prove già fatte si contano e non si rifanno: una campagna interrotta riparte da dove
era. La spesa si somma prova per prova; al tetto la campagna si ferma e scrive il report.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.trials import (
    BASE_NAME,
    REFERENCE_FILE,
    WARNING_MEANING,
    Trial,
    Variant,
    best_variant,
    build_variants,
    load_reference,
    load_trials,
    unseen_answers,
    unseen_by_kind,
)

REPORT = "campagna.md"


def _default_models() -> dict[str, str | None]:
    return {"haiku": None}


def _default_sets() -> list[Literal["piccolo", "grande"]]:
    return ["piccolo", "grande"]


class CampaignFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    varianti: list[str] = Field(default_factory=list)
    ripetizioni: int = Field(default=2, ge=1)
    modelli: dict[str, str | None] = Field(default_factory=_default_models)
    insiemi: list[Literal["piccolo", "grande"]] = Field(default_factory=_default_sets)
    grande: Literal["se_si_tiene", "sempre", "mai"] = "se_si_tiene"
    massimo_dollari: float = Field(default=40.0, gt=0)
    # La variante con cui si confrontano le altre (28-11). Vuoto = la base. Si scrive in
    # `riferimento.txt` nelle cartelle delle prove, così anche `riepilogo.md` la usa.
    riferimento: str | None = None


def load_campaign(path: Path) -> CampaignFile:
    try:
        raw = yaml.safe_load(path.read_text("utf-8")) or {}
        return CampaignFile.model_validate(raw)
    except OSError as exc:
        raise ConfigError(f"Campagna non trovata: {path}") from exc
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"Campagna non valida in {path}: {exc}") from exc


def folder_for(models: Sequence[str], model: str, set_name: str, runs: Path) -> Path:
    """Il primo modello usa le cartelle di sempre (le prove lanciate a mano contano); gli
    altri hanno il nome del modello in fondo."""
    suffix = "" if model == models[0] else f"-{model}"
    return runs / f"prove-{set_name}{suffix}"


def done(folder: Path, name: str) -> int:
    """Quante prove con questo nome ci sono già nella cartella."""
    if not folder.is_dir():
        return 0
    return sum(t.name.casefold() == name.casefold() for t in load_trials(folder))


def kept_on(folder: Path) -> set[str]:
    """Le varianti che sul piccolo si tengono (più la base): quelle da provare sul grande."""
    if not folder.is_dir():
        return {BASE_NAME}
    variants = build_variants(load_trials(folder), load_reference(folder))
    kept = {v.name.casefold() for v in variants if v.decision.startswith("si tiene")}
    return kept | {BASE_NAME}


@dataclass
class Step:
    model: str
    set_name: str
    name: str
    folder: Path
    missing: int  # prove ancora da fare


@dataclass
class Outcome:
    spent: float = 0.0
    run: int = 0
    stopped: str = ""  # motivo dell'arresto, vuoto se finita
    errors: list[str] = field(default_factory=list)


def plan(
    config: CampaignFile,
    runs: Path,
    *,
    set_name: str,
    model: str,
    order: Sequence[str] | None = None,
) -> list[Step]:
    """Le prove di un modello su un insieme. Per il grande con `se_si_tiene` vale lo stato del
    piccolo nel momento in cui si chiama: va chiamato dopo aver finito il piccolo. `order` è
    l'ordine dei modelli nel file (decide le cartelle), anche quando se ne lancia uno solo."""
    order = list(order or config.modelli)
    names = [BASE_NAME, *(n for n in config.varianti if n.casefold() != BASE_NAME)]
    folder = folder_for(order, model, set_name, runs)
    if set_name == "grande":
        if config.grande == "mai":
            return []
        if config.grande == "se_si_tiene":
            small = folder_for(order, model, "piccolo", runs)
            kept = kept_on(small)
            names = [n for n in names if n.casefold() in kept]
    return [
        Step(model, set_name, name, folder, max(0, config.ripetizioni - done(folder, name)))
        for name in names
    ]


def _row(v: Variant) -> str:
    unseen = f"{v.unseen_stable} su {v.unseen_total}" if v.unseen_total else "-"
    return (
        f"| {v.name} | {v.repetitions} | **{v.stable}** su {v.known_total} | {unseen} | "
        f"{v.false_errors} | {v.extra_max} | {v.cost_per_cycle:.4f} $ | "
        f"{v.mean_ms / 1000:.0f} s | {v.decision} |"
    )


def render_campaign(
    config: CampaignFile,
    runs: Path,
    outcome: Outcome,
    *,
    when: str,
    models: Sequence[str],
    launched: Sequence[str] | None = None,
) -> str:
    """Il report finale: per ogni modello e insieme la scelta e la classifica, poi i modelli a
    confronto, gli errori mai visti e i WARNING per tipo (scelta migliore, ultima prova). `models` sono tutti i modelli del
    file, nel loro ordine (decide le cartelle): il report li mostra tutti, con le prove che ci
    sono. `launched` sono quelli lanciati ora (vuoto = solo il report, niente lanciato)."""
    launched = list(models if launched is None else launched)
    run_line = (
        f"Lanciati ora: {', '.join(launched)} · spesa {outcome.spent:.2f} $ su "
        f"{config.massimo_dollari:.0f} $ al massimo · prove fatte ora: {outcome.run}."
        if launched
        else "Solo il report: niente lanciato ora."
    )
    lines = [
        f"# Campagna di prove del {when}",
        "",
        f"Varianti: base, {', '.join(config.varianti) or '-'} · {config.ripetizioni} prove "
        f"ciascuna · modelli: {', '.join(models)} · grande: {config.grande}.",
        "",
        run_line,
        "",
    ]
    if 0 < len(launched) < len(models):
        lines += [
            f"Le prove degli altri modelli ({', '.join(m for m in models if m not in launched)}) "
            "sono quelle che c'erano quando questo report è stato scritto: se girano in un altro "
            "terminale, alla fine di tutti e due lancia `eval campagna --solo-report`.",
            "",
        ]
    if outcome.stopped:
        lines += [f"**Campagna fermata:** {outcome.stopped}. Rilanciala per continuare.", ""]
    if outcome.errors:
        lines += ["**Problemi:**", "", *(f"- {e}" for e in outcome.errors), ""]
    tables: dict[tuple[str, str], list[Variant]] = {}
    for model in models:
        for set_name in config.insiemi:
            folder = folder_for(models, model, set_name, runs)
            trials = load_trials(folder) if folder.is_dir() else []
            variants = build_variants(trials, load_reference(folder))
            tables[(model, set_name)] = variants
            lines += [f"## {model} · {set_name} (`{folder.as_posix()}`)", ""]
            if not variants:
                lines += ["Nessuna prova.", ""]
                continue
            best = best_variant(variants)
            lines += [
                f"**Scelta migliore:** {best.name if best else 'nessuna variante valida'}.",
                "",
                "| Variante | Prove | Stabili | Mai visti (modello) stabili | Falsi errori | "
                "Da verificare | Costo per ciclo | Tempo per ciclo | Decisione |",
                "|---|---|---|---|---|---|---|---|---|",
                *(_row(v) for v in variants),
                "",
            ]
    if len(models) > 1:
        lines += _compare(tables, models, config.insiemi)
    chosen = [
        (f"{m} · {s} · {t.name}", t)
        for m in models
        for s in config.insiemi
        if (t := _last_of_best(folder_for(models, m, s, runs))) is not None
    ]
    lines += _unseen_section(chosen)
    lines += _warning_section(chosen)
    lines += _warning_ops_section(chosen)
    lines += [
        "Dettagli di ogni insieme: `riepilogo.md` nella sua cartella. Le considerazioni le scrive "
        "Claude nel registro di `docs/MEMORIA.md`.",
        "",
    ]
    return "\n".join(lines)


def _compare(
    tables: dict[tuple[str, str], list[Variant]], models: Sequence[str], sets: Sequence[str]
) -> list[str]:
    lines = ["## I modelli a confronto", ""]
    for set_name in sets:
        by_model = {m: {v.name.casefold(): v for v in tables[(m, set_name)]} for m in models}
        names = sorted({n for table in by_model.values() for n in table}, key=_base_first)
        if not names:
            continue
        head = " | ".join(f"Stabili {m} | Mai visti {m} | Costo {m}" for m in models)
        lines += [
            f"**{set_name}**",
            "",
            f"| Variante | {head} |",
            "|---|" + "---|" * (3 * len(models)),
        ]
        for name in names:
            cells = []
            for m in models:
                v = by_model[m].get(name)
                cells += (
                    [
                        f"{v.stable}",
                        f"{v.unseen_stable} su {v.unseen_total}",
                        f"{v.cost_per_cycle:.4f} $",
                    ]
                    if v
                    else ["-", "-", "-"]
                )
            lines.append(f"| {name} | {' | '.join(cells)} |")
        lines.append("")
    return lines


def _base_first(name: str) -> tuple[int, str]:
    return (0 if name == BASE_NAME else 1, name)


def _last_of_best(folder: Path) -> Trial | None:
    """L'ultima prova della scelta migliore della cartella (la base se nessuna variante vale):
    le tabelle per tipo e per motivo guardano la versione che si tiene, non la base vecchia
    (fino al 28-11 guardavano l'ultima base sul piccolo, anche quando la base aveva prove fatte
    con il codice di prima)."""
    if not folder.is_dir():
        return None
    trials = load_trials(folder)
    reference = load_reference(folder)
    best = best_variant(build_variants(trials, reference))
    name = best.name.casefold() if best else reference
    picked = [t for t in trials if t.name.casefold() == name]
    return picked[-1] if picked else None


def _unseen_section(chosen: Sequence[tuple[str, Trial]]) -> list[str]:
    """Gli errori mai visti per tipo nell'ultima prova della scelta migliore (`chosen`:
    «modello · insieme · variante» e prova): da qui si scelgono le migliorie (solo conteggi,
    mai quali sono)."""
    lines = ["## Errori mai visti per tipo (scelta migliore, ultima prova)", ""]
    rows: list[str] = []
    for label, trial in chosen:
        answers = unseen_answers(trial)
        rows += [
            f"| {label} | {kind} | {found} su {total} | {answers.get(kind, '-')} |"
            for kind, (found, total) in unseen_by_kind(trial).items()
        ]
    if rows:
        header = "| Prova | Tipo | Trovati | Cosa ha risposto la v2 sui mancati |"
        lines += [header, "|---|---|---|---|", *rows, ""]
    else:
        lines.append("Nessuna prova con errori mai visti.")
    return [*lines, ""]


def _warning_section(chosen: Sequence[tuple[str, Trial]]) -> list[str]:
    """Da dove vengono i WARNING dei cicli senza errori noti, nell'ultima prova della scelta
    migliore di ogni insieme."""
    lines = [
        "## WARNING per motivo (scelta migliore, ultima prova, per ciclo senza errori noti)",
        "",
    ]
    rows: list[str] = []
    for label, trial in chosen:
        rows += [
            f"| {label} | `{reason}` | {per_cycle:.1f} | {WARNING_MEANING.get(reason, '-')} |"
            for reason, per_cycle in trial.clean_warning_reasons().items()
        ]
    if rows:
        lines += ["| Prova | Motivo | Per ciclo | Cosa vuol dire |", "|---|---|---|---|", *rows]
    else:
        lines.append("Nessuna prova.")
    return [*lines, ""]


def _warning_ops_section(chosen: Sequence[tuple[str, Trial]]) -> list[str]:
    """MG83: i WARNING dei cicli senza errori noti, operazione per operazione (impronta, numero,
    controllo e motivo): da qui si sceglie che cosa tagliare."""
    lines = [
        "## WARNING per operazione (scelta migliore, ultima prova, cicli senza errori noti)",
        "",
    ]
    rows: list[str] = []
    for label, trial in chosen:
        rows += [
            f"| {label} | {fingerprint} | {op} | `{reason}` |"
            for fingerprint, op, reason, _ in trial.clean_warning_ops()
        ]
    if rows:
        lines += ["| Prova | Ciclo | Op | Controllo e motivo |", "|---|---|---|---|", *rows]
    else:
        lines.append("Nessun dato (prove scritte prima del 28-11: rifai il riepilogo).")
    return [*lines, ""]


def write_reference(config: CampaignFile, folders: Sequence[Path]) -> None:
    """Scrive (o toglie) `riferimento.txt` nelle cartelle delle prove, dal campo
    `riferimento` della campagna."""
    for folder in folders:
        path = folder / REFERENCE_FILE
        if config.riferimento:
            folder.mkdir(parents=True, exist_ok=True)
            path.write_text(config.riferimento.strip() + "\n", "utf-8")
        elif path.exists():
            path.unlink()
