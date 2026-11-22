"""Pubblicazione in azienda: il Dockerfile della v2 costruito da quello della v1.

Il repository personale è pubblico: i valori aziendali (nome del secret di ambiente, database e
tabella delle macchine, impostazioni con l'id del modello) non ci stanno. Il comando
`cycle-validation qa` gira sul PC aziendale, li legge dalla v1 e scrive il Dockerfile della copia
aziendale della v2:

- base e certificati come la v1 (la riga `FROM` e le istruzioni che parlano di certificati);
- la libreria di accesso `chatbot_ai_sdk` come nei requirements della v1 (stesso `.whl` di
  `vendor/`, stesse aggiunte, per esempio `[auth]`);
- le variabili aziendali come righe `ENV`;
- gunicorn come il Dockerfile della v2.

Sposta anche `buildspec.yml` sulla cartella della v2 (`cd app_cycle_validation_v2`) e, con
`--torna-alla-v1`, la rimette com'era. Funzioni pure: i file li legge e scrive la CLI.
"""

import json
import re
from dataclasses import dataclass

from cycle_validation.errors import CycleValidationError

V1_FOLDER = "app_cycle_validation"
V2_FOLDER = "app_cycle_validation_v2"
SETTINGS_FILE = "config/settings.azienda.yaml"
_CERTS = re.compile(r"ca-certificates|CA_BUNDLE|SSL_CERT|update-ca-certificates", re.IGNORECASE)
_WHEEL = re.compile(r"(chatbot_ai_sdk-[^\s\[#;]+\.whl)(\[[^\]]+\])?")
_CD = re.compile(rf"(\bcd\s+(?:\./)?){V1_FOLDER}(?![\w-])")
_CD_V2 = re.compile(rf"(\bcd\s+(?:\./)?){V2_FOLDER}(?![\w-])")
_LONG_NUMBER = re.compile(r"\d{6,}")

CMD = (
    'CMD ["gunicorn", "cycle_validation.api.entry:app", "--worker-class", '
    '"uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000", '
    '"--timeout", "600", "--graceful-timeout", "120", "--keep-alive", "75"]'
)


@dataclass(frozen=True)
class V1Image:
    base: str  # la riga FROM della v1
    certificates: list[str]  # istruzioni della v1 sui certificati, come sono scritte


def instructions(dockerfile: str) -> list[str]:
    """Le istruzioni del Dockerfile, con le righe continuate da `\\` unite (testo originale)."""
    found: list[str] = []
    current: list[str] = []
    for line in dockerfile.splitlines():
        if not current and (not line.strip() or line.lstrip().startswith("#")):
            continue
        current.append(line)
        if not line.rstrip().endswith("\\"):
            found.append("\n".join(current))
            current = []
    if current:
        found.append("\n".join(current))
    return found


def read_v1_image(dockerfile: str) -> V1Image:
    steps = instructions(dockerfile)
    bases = [step for step in steps if step.split(None, 1)[0].upper() == "FROM"]
    if not bases:
        raise CycleValidationError("Nel Dockerfile della v1 non c'è la riga FROM.")
    if len(bases) > 1:
        raise CycleValidationError(
            "Il Dockerfile della v1 ha più righe FROM (più fasi): da guardare a mano."
        )
    certificates = [step for step in steps if step not in bases and _CERTS.search(step)]
    return V1Image(base=bases[0], certificates=certificates)


def read_v1_wheel(requirements: str) -> tuple[str, str]:
    """Il `.whl` di `chatbot_ai_sdk` scritto nei requirements della v1 e le sue aggiunte."""
    for line in requirements.splitlines():
        if line.lstrip().startswith("#"):
            continue
        match = _WHEEL.search(line)
        if match:
            return match[1], match[2] or ""
    raise CycleValidationError("Nei requirements della v1 non c'è il .whl di chatbot_ai_sdk.")


def render_dockerfile(image: V1Image, wheel: str, extras: str, env: dict[str, str]) -> str:
    certificates = "\n".join(image.certificates)
    variables = " \\\n    ".join(f"{name}={json.dumps(value)}" for name, value in env.items())
    parts = [
        "# Generato da `cycle-validation qa` (COPILOT.md): non cambiarlo a mano, rilancia il",
        "# comando. Base e certificati come la v1, libreria di accesso come i requirements della",
        "# v1, valori aziendali nelle righe ENV.",
        image.base,
        "",
        "ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1",
        "WORKDIR /app",
    ]
    if certificates:
        parts += ["", "# certificati, come la v1", certificates]
    parts += [
        "",
        "COPY vendor ./vendor",
        f'RUN pip install --upgrade pip && pip install "./vendor/{wheel}{extras}"',
        "",
        "COPY pyproject.toml README.md ./",
        "COPY src ./src",
        "COPY config ./config",
        "COPY prompts ./prompts",
        'RUN pip install gunicorn ".[aws,redshift]"',
        "",
        f"ENV {variables}",
        "",
        "EXPOSE 8000",
        "# Un worker per processo, come la v1: le cache sono per processo.",
        CMD,
        "",
    ]
    return "\n".join(parts)


def switch_buildspec(text: str, *, to_v2: bool = True) -> tuple[str, int]:
    """`cd app_cycle_validation` diventa `cd app_cycle_validation_v2` (o il contrario).
    Restituisce il testo nuovo e quante righe sono cambiate."""
    if to_v2:
        return _CD.subn(rf"\g<1>{V2_FOLDER}", text)
    return _CD_V2.subn(rf"\g<1>{V1_FOLDER}", text)


def mentions(text: str, word: str) -> list[str]:
    """Le righe che contengono `word`, con i numeri lunghi coperti (account, ARN)."""
    return [_LONG_NUMBER.sub("…", line.strip()) for line in text.splitlines() if word in line]
