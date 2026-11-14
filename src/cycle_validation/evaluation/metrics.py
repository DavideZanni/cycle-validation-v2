"""Misure di una prova, calcolate dal file grezzo dei risultati.

I conteggi di errori (ERRATO falsi, errori mancati, esiti tecnici) sono medie per ripetizione,
così prove con un numero diverso di ripetizioni restano confrontabili.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean, median
from typing import Any

ERRATO = "ERRATO"
TECHNICAL_REASONS = frozenset({"ERRORE_TECNICO", "BUDGET_ESAURITO", "ESTRAZIONE_NON_CONFERMATA"})
UNVERIFIED_CITATION = "CITAZIONE_NON_VERIFICATA"
PHASES = ("ingest", "extract", "checks")
STATUS = "stato"


@dataclass
class Metrics:
    repetitions: int
    cases: frozenset[str]
    # Qualità
    concordance: float
    by_check: dict[str, float]
    false_errato: float
    missed_errors: float
    citations_verified: float | None
    # Stabilità (None con una sola ripetizione)
    unstable_rows: int | None
    unstable_cases: int | None
    # Tempo e costo
    time_median_ms: float
    time_max_ms: int
    worst_case: tuple[str, float]
    phase_median_ms: dict[str, float]
    agent_overhead_ms: float | None
    cost_per_cycle: float
    tokens_per_cycle: float
    # Robustezza
    technical: float
    failures: int
    mismatches: list[str] = field(default_factory=list)


def _key(row: dict[str, Any]) -> tuple[str, str, int | None]:
    return (row["check"], row["kind"], row["index"])


def _where(record: dict[str, Any], key: tuple[str, str, int | None]) -> str:
    check, kind, index = key
    return f"r{record['ripetizione']} {record['suite']}/{record['caso']} {check}[{kind} {index}]"


def _matches(expected: dict[str, Any], found: dict[str, Any] | None) -> bool:
    if found is None or found["verdict"] != expected["verdict"]:
        return False
    return expected.get("reason") is None or found["reason"] == expected["reason"]


def measure(data: dict[str, Any]) -> Metrics:
    records: list[dict[str, Any]] = data["esecuzioni"]
    repetitions = len({record["ripetizione"] for record in records}) or 1
    rows = matched = 0
    check_rows: dict[str, int] = defaultdict(int)
    check_matched: dict[str, int] = defaultdict(int)
    false_errato = missed = technical = failures = 0
    verified = unverified = 0
    mismatches: list[str] = []
    # (caso, riga) -> esiti osservati nelle ripetizioni
    seen: dict[tuple[str, Any], set[Any]] = defaultdict(set)
    totals: list[int] = []
    per_case: dict[str, list[int]] = defaultdict(list)
    phases: dict[str, list[int]] = defaultdict(list)
    overhead = sessions = 0
    costs: list[float] = []
    tokens: list[int] = []

    for record in records:
        case = f"{record['suite']}/{record['caso']}"
        actual = {_key(row): row for row in record["ottenuti"]}
        expected_keys = set()
        for expected in record["attesi"]:
            key = _key(expected)
            expected_keys.add(key)
            found = actual.get(key)
            rows += 1
            check_rows[key[0]] += 1
            seen[(case, key)].add(None if found is None else (found["verdict"], found["reason"]))
            if _matches(expected, found):
                matched += 1
                check_matched[key[0]] += 1
            else:
                mismatches.append(
                    f"{_where(record, key)}: atteso {expected['verdict']}, ottenuto "
                    + ("niente" if found is None else f"{found['verdict']} ({found['reason']})")
                )
            got_errato = found is not None and found["verdict"] == ERRATO
            if expected["verdict"] == ERRATO and not got_errato:
                missed += 1
            elif expected["verdict"] != ERRATO and got_errato:
                false_errato += 1
        false_errato += sum(
            1
            for key, row in actual.items()
            if key not in expected_keys and row["verdict"] == ERRATO
        )
        if record.get("stato_atteso"):
            rows += 1
            check_rows[STATUS] += 1
            seen[(case, STATUS)].add(record["stato"])
            if record["stato"] == record["stato_atteso"]:
                matched += 1
                check_matched[STATUS] += 1
            else:
                mismatches.append(
                    f"r{record['ripetizione']} {case} stato: atteso {record['stato_atteso']}, "
                    f"ottenuto {record['stato']}"
                )
        for row in record["ottenuti"]:
            if row["reason"] in TECHNICAL_REASONS:
                technical += 1
            if row["decided_by"] == "agent" and row["prova"]:
                verified += 1
            elif row["reason"] == UNVERIFIED_CITATION:
                unverified += 1
        technical += record.get("errori_pipeline", 0)
        if record["guasto"]:
            failures += 1
            technical += 1
            continue
        times = record["tempi_ms"]
        totals.append(times.get("total", 0))
        per_case[case].append(times.get("total", 0))
        for phase in PHASES:
            if phase in times:
                phases[phase].append(times[phase])
        usage = record["consumi"]
        costs.append(float(usage.get("cost_usd", 0.0)))
        tokens.append(
            sum(
                int(usage.get(name, 0))
                for name in (
                    "input_tokens",
                    "output_tokens",
                    "cache_read_tokens",
                    "cache_write_tokens",
                )
            )
        )
        if usage.get("wall_ms"):
            overhead += int(usage["wall_ms"]) - int(usage.get("api_duration_ms", 0))
            sessions += int(usage.get("sessions", 0))

    unstable = {item for item, outcomes in seen.items() if len(outcomes) > 1}
    medians = {case: median(values) for case, values in per_case.items()}
    worst = max(medians.items(), key=lambda item: item[1]) if medians else ("", 0.0)
    return Metrics(
        repetitions=repetitions,
        cases=frozenset(f"{r['suite']}/{r['caso']}" for r in records),
        concordance=matched / rows if rows else 1.0,
        by_check={name: check_matched[name] / count for name, count in check_rows.items()},
        false_errato=false_errato / repetitions,
        missed_errors=missed / repetitions,
        citations_verified=verified / (verified + unverified) if verified + unverified else None,
        unstable_rows=len(unstable) if repetitions > 1 else None,
        unstable_cases=len({case for case, _ in unstable}) if repetitions > 1 else None,
        time_median_ms=median(totals) if totals else 0.0,
        time_max_ms=max(totals) if totals else 0,
        worst_case=worst,
        phase_median_ms={phase: median(values) for phase, values in phases.items()},
        agent_overhead_ms=overhead / sessions if sessions else None,
        cost_per_cycle=mean(costs) if costs else 0.0,
        tokens_per_cycle=mean(tokens) if tokens else 0.0,
        technical=technical / repetitions,
        failures=failures,
        mismatches=mismatches,
    )
