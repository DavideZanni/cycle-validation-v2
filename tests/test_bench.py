"""Il banco di prova sulle 14 stampe vere (27-11 notte): errori messi dal programma su ogni
operazione possibile, trovati dai controlli del codice. Solo impronte e numeri di operazione."""

import pytest
from kb_fixtures import memory_knowledge, profile

from cycle_validation.config import load_settings
from cycle_validation.evaluation.bench import KINDS, BenchResult, render_bench, run_bench


@pytest.fixture(scope="module")
def bench() -> BenchResult:
    return run_bench(memory_knowledge(), load_settings(None).agent, profile("mos"))


def test_every_kind_of_error_is_tried(bench: BenchResult) -> None:
    assert all(bench.kinds[kind].copies > 0 for kind in KINDS)


def test_the_code_finds_almost_every_error_and_raises_no_false_alarm(
    bench: BenchResult,
) -> None:
    for kind in KINDS:
        result = bench.kinds[kind]
        assert result.other_errato == 0, kind
        assert result.found / result.copies >= 0.9, (kind, result.missed)


def test_the_numbers_misses_are_the_two_known_limits(bench: BenchResult) -> None:
    # un numero scritto due volte per sbaglio in inglese e un numero in più in una lingua: la
    # v2 non allinea più le due lingue (limiti noti, DOCUMENTAZIONE 6.5)
    assert set(bench.kinds["numero_una_lingua"].missed) <= {"8d3c673c 060", "e9b74c84 010"}


def test_the_reading_matches_the_v1_except_the_known_errors(bench: BenchResult) -> None:
    reading = bench.reading
    assert reading.operations_same == reading.operations_v1
    # una targa cambiata a mano (8d3c673c 070) e una scheda tolta (c5ff3cd6 030): gli errori
    # noti, che la v1 legge diversamente
    assert set(reading.differences) == {
        "8d3c673c 070: targa diversa",
        "c5ff3cd6 030: scheda diversa",
    }


def test_the_screen_has_only_fingerprints_and_counts(bench: BenchResult) -> None:
    text = "\n".join(render_bench(bench))
    assert "trovati" in text and "Lettura della stampa" in text
    assert " / " not in text  # niente testo delle descrizioni
