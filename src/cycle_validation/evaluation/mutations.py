"""Mutazioni: da ogni caso rivisto, copie con un difetto messo apposta e copie con modifiche
innocue.

I cicli veri con un errore sono pochi, ma sono quelli che misurano gli errori mancati. Qui il
programma li fabbrica da cicli giusti, con un difetto di cui il **codice** sa l'esito: una
targa che non esiste è sempre ERRATO, un task o una scheda che non esistono sono sempre
WARNING. Le righe dell'operazione toccata che potrebbero cambiare (per esempio il giudizio
sulla descrizione) si tolgono dagli attesi: si confronta solo ciò che è certo.

Le modifiche innocue (spazi doppi, targhe in minuscolo) non devono cambiare niente: se lo
fanno, il programma dipende da come è scritto il ciclo, non da cosa dice.

Le copie leggono il ciclo da `ciclo.json` (il PDF non è mutato) e la stessa conoscenza della
suite di partenza.
"""

import json
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cycle_validation.errors import ConfigError
from cycle_validation.golden import load_cases

MARKER = ".mutazioni"
SUFFIX = "-MUT"
_PATH_KEYS = ("conoscenza", "macchine")

Rows = list[dict[str, Any]]


@dataclass(frozen=True)
class Mutation:
    kind: str  # "difetto" | "innocua"
    description: str
    apply: Callable[[dict[str, Any], Rows], tuple[dict[str, Any], Rows, int | None] | None]


def _verified(rows: Rows, check: str, index: int) -> bool:
    return any(
        r["check"] == check
        and r.get("index") == index
        and r["verdict"] == "CORRETTO"
        and r.get("reason") in (None, "VERIFICATO")
        for r in rows
    )


def _defect(
    check: str, field: str, verdict: str, reason: str | None
) -> Callable[[dict[str, Any], Rows], tuple[dict[str, Any], Rows, int | None] | None]:
    """Il primo valore verificato di `field` diventa un codice che non esiste."""

    def apply(cycle: dict[str, Any], rows: Rows) -> tuple[dict[str, Any], Rows, int | None] | None:
        for index, operation in enumerate(cycle.get("operations", [])):
            if not _verified(rows, check, index):
                continue
            if field == "task_codes":
                if not operation.get("task_codes"):
                    continue
                operation["task_codes"] = [code + SUFFIX for code in operation["task_codes"]]
            elif field == "process_sheet":
                if not operation.get("process_sheet"):
                    continue
                operation["process_sheet"] = {
                    **operation["process_sheet"],
                    "code": operation["process_sheet"]["code"] + SUFFIX,
                }
            else:
                if not operation.get(field):
                    continue
                operation[field] = operation[field] + SUFFIX
            kept = [r for r in rows if r.get("kind") != "operation" or r.get("index") != index]
            row = {"check": check, "kind": "operation", "index": index, "verdict": verdict}
            if reason is not None:
                row["reason"] = reason
            return cycle, [*kept, row], index
        return None

    return apply


def _double_spaces(
    cycle: dict[str, Any], rows: Rows
) -> tuple[dict[str, Any], Rows, int | None] | None:
    touched = False
    for operation in cycle.get("operations", []):
        text = operation.get("operation_description") or ""
        if " " in text:
            operation["operation_description"] = re.sub(" ", "  ", text)
            touched = True
    return (cycle, rows, None) if touched else None


def _lowercase_tags(
    cycle: dict[str, Any], rows: Rows
) -> tuple[dict[str, Any], Rows, int | None] | None:
    touched = False
    for operation in cycle.get("operations", []):
        tag = operation.get("machine_tag")
        if tag and tag != tag.lower():
            operation["machine_tag"] = tag.lower()
            touched = True
    return (cycle, rows, None) if touched else None


MUTATIONS: dict[str, Mutation] = {
    "targa_non_attiva": Mutation(
        "difetto",
        "la targa di un'operazione diventa una macchina che non esiste: atteso ERRATO",
        _defect("machine_tag", "machine_tag", "ERRATO", "MACCHINA_NON_ATTIVA"),
    ),
    "task_inesistente": Mutation(
        "difetto",
        "i task di un'operazione diventano codici che il manuale non ha: atteso WARNING",
        _defect("task_code", "task_codes", "WARNING", None),
    ),
    "scheda_inesistente": Mutation(
        "difetto",
        "la scheda di un'operazione diventa una scheda che non esiste: atteso WARNING",
        _defect("process_sheet", "process_sheet", "WARNING", "FONTE_ASSENTE"),
    ),
    "spazi_doppi": Mutation(
        "innocua",
        "spazi doppi nelle descrizioni: niente deve cambiare",
        _double_spaces,
    ),
    "targhe_minuscole": Mutation(
        "innocua",
        "targhe scritte in minuscolo: niente deve cambiare",
        _lowercase_tags,
    ),
}


def _suite_yaml(source: Path) -> dict[str, Any]:
    data = yaml.safe_load((source / "suite.yaml").read_text(encoding="utf-8")) or {}
    for key in _PATH_KEYS:
        value = data.get(key)
        if value and not Path(value).is_absolute():
            data[key] = (source / value).resolve().as_posix()
    data["estrazione"] = "ciclo_json"
    return data


def _prepare(dest: Path) -> None:
    if dest.exists() and any(dest.iterdir()):
        if not (dest / MARKER).is_file():
            raise ConfigError(
                f"La cartella {dest} non è stata scritta dal generatore di mutazioni: "
                "non la tocco. Scegline un'altra."
            )
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (dest / MARKER).write_text("Scritta da `cycle-validation eval mutazioni`.\n", encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def _suites(cases: Path) -> list[Path]:
    if (cases / "suite.yaml").is_file():
        return [cases]
    if not cases.is_dir():
        raise ConfigError(f"Cartella dei casi non trovata: {cases}")
    return [p for p in sorted(cases.iterdir()) if (p / "suite.yaml").is_file()]


def mutate_cases(cases: Path, out: Path) -> list[str]:
    """Scrive in `out/<suite>/` le mutazioni dei casi rivisti. Restituisce `suite/caso__tipo`."""
    suites = _suites(cases)
    if not suites:
        raise ConfigError(f"Nessuna suite (cartella con suite.yaml) in {cases}.")
    made: list[str] = []
    for source in suites:
        dest = out / source.name
        _prepare(dest)
        (dest / "suite.yaml").write_text(
            "# Scritta da `cycle-validation eval mutazioni`: non modificare a mano.\n"
            + yaml.safe_dump(_suite_yaml(source), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
            newline="\n",
        )
        for case in load_cases(source):
            if not case.expected.rivisto or case.cycle_json is None:
                continue
            original = json.loads(case.cycle_path.read_text(encoding="utf-8"))
            expected = case.expected.model_dump(mode="json", exclude_none=True)
            for name, mutation in MUTATIONS.items():
                rows = json.loads(json.dumps(expected["rows"]))
                done = mutation.apply(json.loads(json.dumps(original)), rows)
                if done is None:
                    continue
                cycle, new_rows, operation = done
                target = dest / f"{case.name}__{name}"
                target.mkdir()
                _write_json(target / "ciclo.json", cycle)
                mutated = {**expected, "rows": new_rows, "rivisto": True}
                if mutation.kind == "difetto":
                    mutated.pop("status", None)  # lo stato del ciclo cambia: non si confronta
                _write_json(target / "expected.json", mutated)
                _write_json(
                    target / "mutazione.json",
                    {
                        "origine": f"{source.name}/{case.name}",
                        "mutazione": name,
                        "tipo": f"{mutation.kind}: {mutation.description}",
                        "operazione": operation,
                    },
                )
                made.append(f"{source.name}/{case.name}__{name}")
    return made
