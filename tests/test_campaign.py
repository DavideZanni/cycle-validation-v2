"""Campagna di prove: tutti gli esperimenti in fila, per modello e per insieme (dati inventati)."""

import hashlib
import shutil
from pathlib import Path

import pytest
from fakes import ScriptedSession
from kb_fixtures import EXAMPLE_KB, REPO_ROOT
from pvrm320_report_fixtures import civil_pages
from support import scripted_judge
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.evaluation.campaign import (
    CampaignFile,
    Outcome,
    done,
    folder_for,
    kept_on,
    plan,
    render_campaign,
)
from cycle_validation.testing.pdf import build_pdf

runner = CliRunner()

CAMPAIGN = """
varianti: [conferme_1]
ripetizioni: 2
modelli:
  haiku:
  sonnet: sonnet-finto
insiemi: [piccolo, grande]
grande: sempre
massimo_dollari: 10
"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Una cartella come quella della v2 sul PC: impostazioni, prompt, varianti, la lista dei
    cicli scelti (A0) con un ciclo noto e uno vero."""
    monkeypatch.chdir(tmp_path)
    models: list[str] = []

    def session(settings, transcripts):  # type: ignore[no-untyped-def]
        models.append(settings.model)
        return ScriptedSession(scripted_judge)

    monkeypatch.setattr(cli, "make_session", session)
    monkeypatch.setattr(cli, "_test_models", models, raising=False)
    # copie, non collegamenti: su Windows un collegamento simbolico chiede permessi da
    # amministratore (WinError 1314, 24-11)
    for name in ("config", "prompts", "eval/varianti"):
        shutil.copytree(REPO_ROOT / name, tmp_path / name)
    (tmp_path / "eval" / "campagna.yaml").write_text(CAMPAIGN, encoding="utf-8")
    # stampe PVRM320 finte (le legge il parser, senza modello): una nota e una vera
    noted = tmp_path / "con-errori.pdf"
    noted.write_bytes(build_pdf(civil_pages()))
    real = tmp_path / "vero.pdf"
    real.write_bytes(build_pdf([p.replace("MOTORE-1/MOTORE-2", "MOTORE-3") for p in civil_pages()]))
    fingerprint = hashlib.sha256(noted.read_bytes()).hexdigest()[:8]
    (tmp_path / "eval" / "errori-noti.yaml").write_text(
        f"cicli:\n  '{fingerprint}':\n    errori:\n      '005': un numero cambiato\n",
        encoding="utf-8",
    )
    lists = tmp_path / "runs" / "prove-grande"
    lists.mkdir(parents=True)
    (lists / "cicli.txt").write_text(f"{noted}\n{real}\n", encoding="utf-8")
    return tmp_path


def _campaign(*extra: str):  # type: ignore[no-untyped-def]
    return runner.invoke(cli.app, ["eval", "campagna", "--knowledge", str(EXAMPLE_KB), *extra])


def test_the_plan_is_free_and_shows_what_is_missing(project: Path) -> None:
    result = _campaign("--piano")
    assert result.exit_code == 0, result.output
    assert "haiku · piccolo:" in result.output and "sonnet · piccolo:" in result.output
    assert "base: 2 da fare → runs/prove-piccolo" in result.output
    assert "conferme_1: 2 da fare → runs/prove-piccolo-sonnet" in result.output
    assert not (project / "runs" / "prove-piccolo").exists()  # niente lanciato


def test_a_campaign_runs_everything_and_starts_again_where_it_stopped(project: Path) -> None:
    result = _campaign()
    assert result.exit_code == 0, result.output
    runs = project / "runs"
    assert (done(runs / "prove-piccolo", "base"), done(runs / "prove-piccolo", "conferme_1")) == (
        2,
        2,
    )
    assert done(runs / "prove-piccolo-sonnet", "base") == 2
    # «sempre»: tutte anche sul grande («se_si_tiene» è nel test di `plan`; qui la decisione
    # dipenderebbe dal tempo, ultimo criterio della classifica)
    assert done(runs / "prove-grande", "base") == 2
    assert done(runs / "prove-grande-sonnet", "conferme_1") == 2
    assert cli._test_models.count("sonnet-finto") > 0  # type: ignore[attr-defined]
    report = (runs / "campagna.md").read_text(encoding="utf-8")
    assert "## haiku · piccolo" in report and "## sonnet · grande" in report
    assert "## I modelli a confronto" in report
    assert "Prove fatte ora: 16" in result.output
    again = _campaign()
    assert "Prove fatte ora: 0" in again.output  # riparte da dove era: niente da rifare


def test_only_some_experiments_can_be_run(project: Path) -> None:
    result = _campaign("--modelli", "sonnet", "--insiemi", "piccolo", "--ripetizioni", "1")
    assert result.exit_code == 0, result.output
    runs = project / "runs"
    assert not (runs / "prove-piccolo").exists()  # haiku non lanciato
    assert done(runs / "prove-piccolo-sonnet", "base") == 1
    assert done(runs / "prove-piccolo-sonnet", "conferme_1") == 1
    assert "Modelli non nel file" in _campaign("--modelli", "opus").output


def test_two_models_can_run_together_in_two_terminals(project: Path) -> None:
    """Una campagna per modello (due terminali): ognuna scrive il suo report, che mostra tutti
    i modelli; alla fine `--solo-report` rifà quello unico senza lanciare niente."""
    runs = project / "runs"
    assert _campaign("--modelli", "haiku", "--insiemi", "piccolo").exit_code == 0
    assert _campaign("--modelli", "sonnet", "--insiemi", "piccolo").exit_code == 0
    assert not (runs / "campagna.md").exists()  # nessuno dei due sovrascrive l'altro
    haiku = (runs / "campagna-haiku.md").read_text("utf-8")
    sonnet = (runs / "campagna-sonnet.md").read_text("utf-8")
    assert "Lanciati ora: haiku" in haiku and "## sonnet · piccolo" in haiku
    assert "Lanciati ora: sonnet" in sonnet and "## haiku · piccolo" in sonnet
    assert "## I modelli a confronto" in sonnet
    result = _campaign("--solo-report")
    assert result.exit_code == 0, result.output
    assert "niente lanciato" in result.output
    report = (runs / "campagna.md").read_text("utf-8")
    assert "Solo il report" in report and "## sonnet · piccolo" in report
    assert done(runs / "prove-piccolo", "base") == 2  # niente rifatto


def test_the_campaign_stops_at_the_spending_cap(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_trial = cli._run_trial

    def costly(*args, **kwargs):  # type: ignore[no-untyped-def]
        trial, folder = real_trial(*args, **kwargs)
        trial.cycles[0].cost_usd = 1.0  # le sessioni finte non costano: un dollaro a prova
        return trial, folder

    monkeypatch.setattr(cli, "_run_trial", costly)
    result = _campaign("--massimo-dollari", "1.5")
    assert result.exit_code == 0, result.output
    assert "fermata: raggiunto il tetto" in result.output
    assert done(project / "runs" / "prove-piccolo", "base") == 2  # 1 $ + 1 $, poi stop
    assert done(project / "runs" / "prove-piccolo", "conferme_1") == 0
    assert "Campagna fermata" in (project / "runs" / "campagna.md").read_text("utf-8")


def test_an_unknown_variant_stops_before_spending(project: Path) -> None:
    result = _campaign("--varianti", "non_esiste")
    assert result.exit_code == 1
    assert "Variante non trovata" in result.output


def test_folders_and_the_large_set_follow_the_small_one(tmp_path: Path) -> None:
    config = CampaignFile.model_validate(
        {"varianti": ["a"], "modelli": {"haiku": None, "sonnet": "x"}, "grande": "se_si_tiene"}
    )
    assert folder_for(["haiku", "sonnet"], "haiku", "grande", tmp_path) == tmp_path / "prove-grande"
    assert (
        folder_for(["haiku", "sonnet"], "sonnet", "piccolo", tmp_path)
        == tmp_path / "prove-piccolo-sonnet"
    )
    assert kept_on(tmp_path / "manca") == {"base"}
    steps = plan(config, tmp_path, set_name="grande", model="haiku")
    assert [s.name for s in steps] == ["base"]  # nulla si tiene ancora sul piccolo
    every = config.model_copy(update={"grande": "sempre"})
    assert [s.name for s in plan(every, tmp_path, set_name="grande", model="haiku")] == [
        "base",
        "a",
    ]
    never = config.model_copy(update={"grande": "mai"})
    assert plan(never, tmp_path, set_name="grande", model="haiku") == []
    text = render_campaign(config, tmp_path, Outcome(), when="oggi", models=["haiku"])
    assert "Nessuna prova." in text
