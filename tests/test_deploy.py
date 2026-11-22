"""Pubblicazione in QA: il Dockerfile della v2 costruito sul PC da quello della v1 (`qa`)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.deploy import (
    instructions,
    read_v1_image,
    read_v1_wheel,
    switch_buildspec,
)
from cycle_validation.errors import CycleValidationError

V1_DOCKERFILE = """FROM python:3.14.10-slim
# certificato della macchina di build
WORKDIR /app
COPY ca-certificates.crt /usr/local/share/ca-certificates/build.crt
RUN apt-get update && \\
    apt-get install -y --no-install-recommends ca-certificates && \\
    update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY . .
RUN pip install -r requirements.txt
CMD ["gunicorn", "app_backend:app"]
"""
WHEEL = "chatbot_ai_sdk-0.4.0rc2-py3-none-any.whl"
REQUIREMENTS = (
    f"fastapi\n# vecchia: ./vendor/chatbot_ai_sdk-0.3.0-py3-none-any.whl\n./vendor/{WHEEL}[auth]\n"
)
V1_CODE = {
    "app_backend.py": 'from secret_loader import load_secrets\nload_secrets("ambiente-finto")\n',
    "config.py": 'import os\nSECRET_NAME = os.getenv("SECRET_NAME")\n',
    "credentials.py": (
        "def get_db_credentials():\n"
        '    credentials = {"host": "h", "username": "u", "password": "p", "database": "db_finto"}\n'
        '    return credentials["host"], credentials["username"], credentials["password"], '
        'credentials["database"]\n'
    ),
    "tools.py": (
        "from credentials import get_db_credentials\n"
        "def verify_active_TM(tags):\n"
        "    host, user, pwd, dbname = get_db_credentials()\n"
        "    RedshiftConnector(host=host, database=dbname)\n"
        "    sql = \"SELECT work_center_cd FROM schema_x.tabella_y WHERE work_center_usage_cd = 'TO'\"\n"
    ),
}
BUILDSPEC = """version: 0.2
phases:
  build:
    commands:
      - cp /etc/ssl/certs/ca-certificates.crt app_cycle_validation/ca-certificates.crt
      - cd app_cycle_validation
      - docker build -t $ECR_REPO_NAME:latest .
"""


def test_continued_lines_are_one_instruction() -> None:
    steps = instructions(V1_DOCKERFILE)
    assert steps[0] == "FROM python:3.14.10-slim"
    assert steps[3].startswith("RUN apt-get update") and steps[3].endswith("update-ca-certificates")


def test_base_and_certificates_come_from_the_v1() -> None:
    image = read_v1_image(V1_DOCKERFILE)
    assert image.base == "FROM python:3.14.10-slim"
    assert [step.split()[0] for step in image.certificates] == ["COPY", "RUN", "ENV"]
    assert not any("torch" in step for step in image.certificates)
    with pytest.raises(CycleValidationError, match="più righe FROM"):
        read_v1_image("FROM a AS build\nFROM b\n")


def test_the_wheel_is_the_one_in_the_requirements() -> None:
    assert read_v1_wheel(REQUIREMENTS) == (WHEEL, "[auth]")
    with pytest.raises(CycleValidationError):
        read_v1_wheel("fastapi\n")


def test_buildspec_goes_to_the_v2_and_back() -> None:
    v2, count = switch_buildspec(BUILDSPEC)
    assert count == 2 and "cd app_cycle_validation_v2\n" in v2
    assert "app_cycle_validation_v2/ca-certificates.crt" in v2  # il certificato va nella v2
    assert switch_buildspec(v2) == (v2, 0)  # già sulla v2: niente
    assert switch_buildspec(v2, to_v2=False) == (BUILDSPEC, 2)
    # a metà (prima versione del comando: solo `cd`): si sposta il resto
    half = BUILDSPEC.replace("cd app_cycle_validation", "cd app_cycle_validation_v2")
    assert switch_buildspec(half) == (v2, 1)


def _company(tmp_path: Path) -> Path:
    """Repository aziendale finto: v1, v2 (cartella di lavoro) e buildspec nella radice."""
    v1 = tmp_path / "app_cycle_validation"
    (v1 / "vendor").mkdir(parents=True)
    (v1 / "Dockerfile").write_text(V1_DOCKERFILE, encoding="utf-8")
    (v1 / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    (v1 / "vendor" / WHEEL).write_bytes(b"PK finto")
    for name, text in V1_CODE.items():
        (v1 / name).write_text(text, encoding="utf-8")
    v2 = tmp_path / "app_cycle_validation_v2"
    (v2 / "data").mkdir(parents=True)
    (v2 / "config").mkdir()
    settings = Path("config/settings.yaml").read_text(encoding="utf-8")
    (v2 / "data" / "settings.yaml").write_text(
        settings.replace("save_transcripts: false", "save_transcripts: true"), encoding="utf-8"
    )
    (tmp_path / "buildspec.yml").write_text(BUILDSPEC, encoding="utf-8")
    return v2


def test_qa_writes_the_company_dockerfile_and_hides_the_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    v2 = _company(tmp_path)
    monkeypatch.chdir(v2)
    result = CliRunner().invoke(cli.app, ["qa", "--conoscenza-civile", "k/civil/current.json"])
    assert result.exit_code == 0, result.output

    dockerfile = (v2 / "Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.splitlines()[3] == "FROM python:3.14.10-slim"
    assert "update-ca-certificates" in dockerfile and "torch" not in dockerfile
    assert f'pip install "./vendor/{WHEEL}[auth]"' in dockerfile
    assert 'CV_ENV_SECRET="ambiente-finto"' in dockerfile
    assert 'REDSHIFT_DATABASE="db_finto"' in dockerfile
    assert "FROM schema_x.tabella_y WHERE work_center_usage_cd = 'TO'" in dockerfile
    assert 'MACHINES_SOURCE="diretta"' in dockerfile
    assert 'EJ200_VALIDATION_ENABLED="false"' in dockerfile
    assert 'CYCLE_VALIDATION_CONFIG="config/settings.azienda.yaml"' in dockerfile
    assert (v2 / "vendor" / WHEEL).read_bytes() == b"PK finto"
    settings = (v2 / "config" / "settings.azienda.yaml").read_text(encoding="utf-8")
    assert "save_transcripts: false" in settings
    assert "cd app_cycle_validation_v2" in (tmp_path / "buildspec.yml").read_text(encoding="utf-8")

    for value in ("ambiente-finto", "db_finto", "tabella_y"):
        assert value not in result.output
    assert "buildspec: percorsi spostati sulla v2: 2." in result.output
    assert "Dockerfile scritto" in result.output

    back = CliRunner().invoke(cli.app, ["qa", "--torna-alla-v1"])
    assert back.exit_code == 0, back.output
    assert (tmp_path / "buildspec.yml").read_text(encoding="utf-8") == BUILDSPEC


def test_qa_with_ej200_needs_its_knowledge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    v2 = _company(tmp_path)
    monkeypatch.chdir(v2)
    runner = CliRunner()
    missing = runner.invoke(cli.app, ["qa", "--conoscenza-civile", "c.json", "--ej200"])
    assert missing.exit_code == 1 and "--conoscenza-ej200" in missing.output
    ok = runner.invoke(
        cli.app,
        ["qa", "--conoscenza-civile", "c.json", "--ej200", "--conoscenza-ej200", "e.json"],
    )
    assert ok.exit_code == 0, ok.output
    dockerfile = (v2 / "Dockerfile").read_text(encoding="utf-8")
    assert 'EJ200_VALIDATION_ENABLED="true"' in dockerfile
    assert 'EJ200_KNOWLEDGE_POINTER="e.json"' in dockerfile


def test_qa_stops_when_the_v1_code_does_not_say_enough(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    v2 = _company(tmp_path)
    (tmp_path / "app_cycle_validation" / "app_backend.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(v2)
    result = CliRunner().invoke(cli.app, ["qa", "--conoscenza-civile", "c.json"])
    assert result.exit_code == 1
    assert "secret di ambiente" in result.output
    assert not (v2 / "Dockerfile").exists()
