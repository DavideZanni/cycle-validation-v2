"""La misura con molti documenti (N5), in piccolo: deve girare e dire numeri sensati."""

from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.evaluation.scale import ScaleShape, measure_scale


def test_a_small_fake_knowledge_is_measured() -> None:
    result = measure_scale(ScaleShape(documents=12, lines=200, tasks=5, standard_practices=3))
    assert result.objects == 14  # documenti, manifest e indice dei task
    assert result.startup_s > 0
    assert result.known_task_us > 0
    lines = result.lines()
    assert lines[0].startswith("Conoscenza finta: 12 documenti")


def test_the_scale_command_prints_the_measures() -> None:
    out = CliRunner().invoke(
        cli.app,
        ["eval", "scala", "--documenti", "8", "--righe", "100", "--task", "4", "--spm", "2"],
    )
    assert out.exit_code == 0, out.output
    assert "Avvio" in out.output and "Codice sbagliato" in out.output
