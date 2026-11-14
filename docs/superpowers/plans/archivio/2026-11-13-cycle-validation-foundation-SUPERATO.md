# Cycle Validation — Fondamenta: piano di implementazione

> **SUPERATO — non eseguire.** Scritto prima di avere la documentazione del sistema attuale. Sostituito da `docs/superpowers/plans/2026-11-13-cycle-validation-v2-roadmap.md`. Restano validi, come codice da riprendere nel piano di dettaglio della Fase 1: Task 5 (path e citazioni), Task 8 (hook GRASP), Task 9 (runner), Task 10 (adattatore SDK), Task 11 (ingest PDF).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** costruire la pipeline di validazione di un ciclo motore dallo stadio di ingest al report, completa di tutto ciò che non dipende dai PDF reali e dalla documentazione dei manuali.

**Architecture:** sei stadi in sequenza (ingest PDFium → extract → precheck → validate → verdict → report) che comunicano tramite modelli pydantic. L'agente (Claude Agent SDK su Bedrock, una sessione per campo, in parallelo) trova l'evidenza nei manuali; il codice decide l'esito. L'SDK sta dietro l'interfaccia `FieldSession`, quindi tutto è testabile offline.

**Tech Stack:** Python ≥ 3.12, uv, pydantic 2, typer, pypdfium2, claude-agent-sdk 0.2.x, pyyaml, python-dotenv, pytest, ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-11-12-cycle-validation-design.md`

**Fuori da questo piano** (richiedono i PDF di esempio e la documentazione dell'ingestion dei manuali): implementazione reale di `FieldExtractor`, contenuto definitivo di `config/fields.yaml`, taratura di `prompts/validator.md`, golden set.

## Global Constraints

- Tutti i comandi si lanciano dalla radice del repository: `C:\Users\david\Downloads\Progetto Avio`.
- Python ≥ 3.12; `.python-version` contiene `3.13`.
- Dipendenze runtime ammesse: `claude-agent-sdk`, `pydantic`, `pypdfium2`, `python-dotenv`, `pyyaml`, `typer`. Nessun'altra.
- `claude_agent_sdk` si importa solo in `src/cycle_validation/agent/sdk_session.py` (e in `cli.py` tramite quel modulo).
- L'agente dispone solo dei tool `Read`, `Grep`, `Glob`, in sola lettura, confinati in `manuals_dir`.
- Esiti: esattamente `CORRETTO`, `WARNING`, `ERRATO`. Sottocodici di warning: `EVIDENZA_NON_TROVATA`, `CAMPO_MANCANTE`, `CONFLITTO`, `AL_LIMITE`, `BUDGET_ESAURITO`, `CITAZIONE_NON_VERIFICATA`, `ERRORE_TECNICO`.
- `CORRETTO` ed `ERRATO` richiedono almeno una citazione verificata.
- Identificatori in inglese; testi mostrati all'utente (messaggi, motivazioni, report) in italiano.
- `data/`, `runs/` e `.env` non entrano mai in git.
- La suite di default è offline. I test che chiamano Bedrock hanno il marker `bedrock` e sono esclusi di default.
- Niente `asyncio` plugin per pytest: i test asincroni usano `asyncio.run(...)`.
- Prima di ogni commit: `uv run ruff format .` e `uv run ruff check .` (zero errori).

## Mappa dei file

| File | Responsabilità | Task |
|---|---|---|
| `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example` | progetto e strumenti | 1 |
| `src/cycle_validation/errors.py` | errori fatali | 1 |
| `src/cycle_validation/models.py` | contratti dati | 1 |
| `src/cycle_validation/config.py`, `config/*.yaml` | configurazione | 2 |
| `src/cycle_validation/text.py` | normalizzazione, parsing numeri, formattazione | 3 |
| `src/cycle_validation/results.py` | costruzione di `FieldResult` | 3 |
| `src/cycle_validation/precheck/checks.py` | stadio 3 | 3 |
| `src/cycle_validation/verdict/rules.py` | confronto numerico | 4 |
| `src/cycle_validation/paths.py` | confinamento dei path | 5 |
| `src/cycle_validation/verdict/citations.py` | verifica citazioni | 5 |
| `src/cycle_validation/agent/session.py` | interfaccia `FieldSession` | 6 |
| `src/cycle_validation/verdict/decide.py` | esito finale | 6 |
| `src/cycle_validation/report/*.py` | stadio 6 | 7 |
| `src/cycle_validation/agent/hooks.py` | GRASP e confinamento | 8 |
| `src/cycle_validation/agent/runner.py` | parallelismo e retry | 9 |
| `src/cycle_validation/agent/prompt.py`, `agent/sdk_session.py`, `prompts/validator.md` | adattatore SDK | 10 |
| `src/cycle_validation/ingest/pdf_to_markdown.py` | stadio 1 | 11 |
| `src/cycle_validation/extract/*.py`, `pipeline.py`, `cli.py`, `README.md`, `docs/architecture.md` | orchestrazione e CLI | 12 |

I test stanno in `tests/test_<modulo>.py` (cartella piatta).

---

### Task 1: Scheletro del progetto e contratti dati

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example`, `README.md`
- Create: `src/cycle_validation/__init__.py`, `src/cycle_validation/errors.py`, `src/cycle_validation/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: niente.
- Produces: `cycle_validation.errors` → `CycleValidationError`, `ConfigError`, `IngestError`, `PipelineError`. `cycle_validation.models` → `Value`, `FieldType`, `RuleKind`, `ToleranceMode`, `Rule`, `FieldSpec`, `ExtractionStatus`, `SourceRef`, `ExtractedField`, `Judgement`, `Citation`, `AgentFinding`, `Verdict`, `WarningCode`, `DecidedBy`, `Usage`, `FieldResult`, `RunMeta`, `Totals`, `Report`.

- [ ] **Step 1: Creare i file di progetto**

`pyproject.toml`:

```toml
[project]
name = "cycle-validation"
version = "0.1.0"
description = "Validazione dei campi di un ciclo motore contro i manuali tecnici"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "claude-agent-sdk>=0.2.180",
    "pydantic>=2.9",
    "pypdfium2>=5.0",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
    "typer>=0.15",
]

[project.scripts]
cycle-validation = "cycle_validation.cli:app"

[dependency-groups]
dev = [
    "mypy>=1.13",
    "pytest>=8.3",
    "ruff>=0.8",
    "types-pyyaml>=6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cycle_validation"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-m 'not bedrock'"
markers = ["bedrock: test che chiamano AWS Bedrock (manuali, a pagamento)"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["pathlib.Path", "typer.Option", "typer.Argument"]

[tool.mypy]
python_version = "3.12"
strict = true
files = ["src"]

[[tool.mypy.overrides]]
module = ["pypdfium2.*"]
ignore_missing_imports = true
```

`.python-version`:

```
3.13
```

`.gitignore`:

```
.venv/
__pycache__/
*.pyc
.env
data/
runs/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

`.env.example`:

```
# Fa usare Bedrock al Claude Agent SDK
CLAUDE_CODE_USE_BEDROCK=1
AWS_REGION=eu-west-1
AWS_PROFILE=default
```

`README.md` (versione minima, completata nel Task 12):

```markdown
# Cycle Validation

Valida i campi di un ciclo motore (PDF) contro i manuali tecnici.

Design: `docs/superpowers/specs/2026-11-12-cycle-validation-design.md`
```

`src/cycle_validation/__init__.py`:

```python
"""Validazione dei campi di un ciclo motore contro i manuali tecnici."""
```

- [ ] **Step 2: Installare l'ambiente**

Run: `uv sync`
Expected: crea `.venv/` e `uv.lock`, termina senza errori.

- [ ] **Step 3: Scrivere il test che fallisce**

`tests/test_models.py`:

```python
import pytest
from pydantic import ValidationError

from cycle_validation.models import (
    DecidedBy,
    ExtractedField,
    FieldResult,
    FieldSpec,
    Usage,
    Verdict,
    WarningCode,
)


def test_field_spec_accepts_tolerance_on_number() -> None:
    spec = FieldSpec.model_validate(
        {
            "id": "max_egt",
            "label": "EGT massima",
            "type": "number",
            "rule": {"kind": "tolerance", "value": 5},
        }
    )
    assert spec.rule is not None
    assert spec.rule.value == 5.0


def test_field_spec_rejects_tolerance_on_string() -> None:
    with pytest.raises(ValidationError, match="tolerance"):
        FieldSpec.model_validate(
            {
                "id": "engine_model",
                "label": "Modello",
                "type": "string",
                "rule": {"kind": "tolerance", "value": 1},
            }
        )


def test_field_spec_rejects_invalid_id() -> None:
    with pytest.raises(ValidationError):
        FieldSpec.model_validate({"id": "Max EGT", "label": "EGT", "type": "number"})


def test_field_spec_rejects_unknown_key() -> None:
    with pytest.raises(ValidationError):
        FieldSpec.model_validate(
            {"id": "max_egt", "label": "EGT", "type": "number", "required": True}
        )


def test_extracted_field_coerces_integers_to_float() -> None:
    field = ExtractedField.model_validate({"id": "max_egt", "status": "ok", "value": 650})
    assert isinstance(field.value, float)


def test_extracted_field_keeps_strings() -> None:
    field = ExtractedField.model_validate({"id": "engine_model", "status": "ok", "value": "CF34"})
    assert field.value == "CF34"


def test_warning_requires_code() -> None:
    with pytest.raises(ValidationError, match="warning_code"):
        FieldResult(
            field_id="a",
            label="A",
            verdict=Verdict.WARNING,
            rationale="x",
            decided_by=DecidedBy.AGENT,
        )


def test_non_warning_rejects_code() -> None:
    with pytest.raises(ValidationError, match="warning_code"):
        FieldResult(
            field_id="a",
            label="A",
            verdict=Verdict.CORRETTO,
            warning_code=WarningCode.AL_LIMITE,
            rationale="x",
            decided_by=DecidedBy.RULE,
        )


def test_usage_addition_sums_every_counter() -> None:
    total = Usage(input_tokens=10, output_tokens=2, cost_usd=0.5, turns=1) + Usage(
        input_tokens=5, cache_read_tokens=7, duration_s=1.5, turns=2
    )
    assert total == Usage(
        input_tokens=15,
        output_tokens=2,
        cache_read_tokens=7,
        cost_usd=0.5,
        duration_s=1.5,
        turns=3,
    )
```

- [ ] **Step 4: Verificare che fallisca**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.models'`.

- [ ] **Step 5: Implementare errori e modelli**

`src/cycle_validation/errors.py`:

```python
"""Errori fatali: il run non può produrre un report."""


class CycleValidationError(Exception):
    """Base di tutti gli errori fatali del progetto."""


class ConfigError(CycleValidationError):
    """Configurazione assente o non valida."""


class IngestError(CycleValidationError):
    """PDF illeggibile o privo di testo."""


class PipelineError(CycleValidationError):
    """Precondizione della pipeline non soddisfatta."""
```

`src/cycle_validation/models.py`:

```python
"""Contratti dati condivisi da tutti gli stadi della pipeline."""

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Value = float | str


class FieldType(StrEnum):
    NUMBER = "number"
    STRING = "string"


class RuleKind(StrEnum):
    TOLERANCE = "tolerance"
    EXACT = "exact"


class ToleranceMode(StrEnum):
    ABSOLUTE = "absolute"
    PERCENT = "percent"


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: RuleKind
    value: float = Field(default=0.0, ge=0)
    mode: ToleranceMode = ToleranceMode.ABSOLUTE


class FieldSpec(BaseModel):
    """Un campo da validare, come dichiarato in config/fields.yaml."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1)
    type: FieldType
    unit: str | None = None
    group: str | None = None
    rule: Rule | None = None
    search_hints: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _tolerance_requires_number(self) -> Self:
        if (
            self.rule is not None
            and self.rule.kind is RuleKind.TOLERANCE
            and self.type is not FieldType.NUMBER
        ):
            raise ValueError("una regola 'tolerance' richiede type: number")
        return self


class ExtractionStatus(StrEnum):
    OK = "ok"
    MISSING = "missing"
    UNPARSEABLE = "unparseable"


class SourceRef(BaseModel):
    page: int | None = None
    line: int | None = None


class ExtractedField(BaseModel):
    """Valore di un campo estratto dal PDF del ciclo."""

    id: str
    status: ExtractionStatus
    raw_text: str | None = None
    value: Value | None = None
    unit: str | None = None
    source: SourceRef | None = None


class Judgement(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNCLEAR = "unclear"


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str
    line: int
    quote: str


class AgentFinding(BaseModel):
    """Output strutturato di una sessione agente. Tutti i campi sono obbligatori."""

    model_config = ConfigDict(extra="forbid")

    field_id: str
    found: bool
    reference_value: str | None
    reference_unit: str | None
    judgement: Judgement
    rationale: str
    citations: list[Citation]


class Verdict(StrEnum):
    CORRETTO = "CORRETTO"
    WARNING = "WARNING"
    ERRATO = "ERRATO"


class WarningCode(StrEnum):
    EVIDENZA_NON_TROVATA = "EVIDENZA_NON_TROVATA"
    CAMPO_MANCANTE = "CAMPO_MANCANTE"
    CONFLITTO = "CONFLITTO"
    AL_LIMITE = "AL_LIMITE"
    BUDGET_ESAURITO = "BUDGET_ESAURITO"
    CITAZIONE_NON_VERIFICATA = "CITAZIONE_NON_VERIFICATA"
    ERRORE_TECNICO = "ERRORE_TECNICO"


class DecidedBy(StrEnum):
    PRECHECK = "precheck"
    RULE = "rule"
    AGENT = "agent"


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    duration_s: float = 0.0
    turns: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
            duration_s=self.duration_s + other.duration_s,
            turns=self.turns + other.turns,
        )


class FieldResult(BaseModel):
    """Una riga della tabella di output."""

    field_id: str
    label: str
    cycle_value: Value | None = None
    cycle_unit: str | None = None
    reference_value: Value | None = None
    reference_unit: str | None = None
    verdict: Verdict
    warning_code: WarningCode | None = None
    rationale: str
    citations: list[Citation] = Field(default_factory=list)
    decided_by: DecidedBy
    usage: Usage = Field(default_factory=Usage)

    @model_validator(mode="after")
    def _warning_code_matches_verdict(self) -> Self:
        if (self.verdict is Verdict.WARNING) != (self.warning_code is not None):
            raise ValueError(
                "warning_code è obbligatorio con WARNING e vietato con gli altri esiti"
            )
        return self


class RunMeta(BaseModel):
    pdf_name: str
    pdf_sha256: str
    started_at: datetime
    model: str
    fields_sha256: str


class Totals(BaseModel):
    corretto: int = 0
    warning: int = 0
    errato: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_s: float = 0.0


class Report(BaseModel):
    meta: RunMeta
    results: list[FieldResult]
    totals: Totals
```

- [ ] **Step 6: Verificare che passi**

Run: `uv run pytest tests/test_models.py -v`
Expected: 9 passed.

- [ ] **Step 7: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add pyproject.toml uv.lock .python-version .gitignore .env.example README.md src tests
git commit -m "feat: add project skeleton and data contracts"
```

---

### Task 2: Configurazione

**Files:**
- Create: `src/cycle_validation/config.py`, `config/settings.yaml`, `config/fields.yaml`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `ConfigError` da `cycle_validation.errors`; `FieldSpec` da `cycle_validation.models`.
- Produces: `GraspSettings(before: int = 15, window: int = 30, max_limit: int = 60)`; `Settings(model: str, effort: Literal["low","medium","high","xhigh","max"] | None, manuals_dir: Path, concurrency: int, max_turns: int, retries: int, grasp: GraspSettings, near_limit_ratio: float)`; `load_settings(path: Path) -> Settings`; `load_fields(path: Path) -> list[FieldSpec]`.

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_config.py`:

```python
from pathlib import Path

import pytest

from cycle_validation.config import load_fields, load_settings
from cycle_validation.errors import ConfigError

REPO_ROOT = Path(__file__).resolve().parents[1]


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_load_settings_applies_defaults(tmp_path: Path) -> None:
    settings = load_settings(write(tmp_path, "settings.yaml", "model: some-model\n"))
    assert settings.model == "some-model"
    assert settings.effort is None
    assert settings.concurrency == 8
    assert settings.max_turns == 10
    assert settings.retries == 2
    assert settings.grasp.window == 30
    assert settings.near_limit_ratio == 0.10


def test_load_settings_rejects_unknown_key(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="non valida"):
        load_settings(write(tmp_path, "settings.yaml", "model: m\nconcurency: 4\n"))


def test_load_settings_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Impossibile leggere"):
        load_settings(tmp_path / "assente.yaml")


def test_load_settings_reports_invalid_yaml(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="YAML non valido"):
        load_settings(write(tmp_path, "settings.yaml", "model: [aperta\n"))


def test_load_fields_returns_specs(tmp_path: Path) -> None:
    text = (
        "fields:\n"
        "  - id: max_egt\n"
        "    label: EGT massima\n"
        "    type: number\n"
        "    unit: '°C'\n"
        "    rule: {kind: tolerance, value: 5}\n"
        "  - id: engine_model\n"
        "    label: Modello motore\n"
        "    type: string\n"
    )
    fields = load_fields(write(tmp_path, "fields.yaml", text))
    assert [f.id for f in fields] == ["max_egt", "engine_model"]


def test_load_fields_rejects_duplicate_ids(tmp_path: Path) -> None:
    text = (
        "fields:\n"
        "  - {id: max_egt, label: A, type: number}\n"
        "  - {id: max_egt, label: B, type: number}\n"
    )
    with pytest.raises(ConfigError, match="duplicati"):
        load_fields(write(tmp_path, "fields.yaml", text))


def test_load_fields_rejects_empty_list(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_fields(write(tmp_path, "fields.yaml", "fields: []\n"))


def test_shipped_config_files_are_valid() -> None:
    assert load_settings(REPO_ROOT / "config" / "settings.yaml").model
    assert load_fields(REPO_ROOT / "config" / "fields.yaml")
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.config'`.

- [ ] **Step 3: Implementare la configurazione**

`src/cycle_validation/config.py`:

```python
"""Caricamento e validazione di settings.yaml e fields.yaml."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cycle_validation.errors import ConfigError
from cycle_validation.models import FieldSpec

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class GraspSettings(BaseModel):
    """Finestra di lettura a paragrafo imposta all'agente."""

    model_config = ConfigDict(extra="forbid")

    before: int = Field(default=15, ge=0)
    window: int = Field(default=30, ge=1)
    max_limit: int = Field(default=60, ge=1)


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1)
    effort: Effort | None = None
    manuals_dir: Path = Path("data/manuals")
    concurrency: int = Field(default=8, ge=1)
    max_turns: int = Field(default=10, ge=1)
    retries: int = Field(default=2, ge=0)
    grasp: GraspSettings = Field(default_factory=GraspSettings)
    near_limit_ratio: float = Field(default=0.10, ge=0, lt=1)


class _FieldsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[FieldSpec] = Field(min_length=1)


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Impossibile leggere {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML non valido in {path}: {exc}") from exc


def load_settings(path: Path) -> Settings:
    data = _read_yaml(path)
    try:
        return Settings.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"Configurazione non valida in {path}:\n{exc}") from exc


def load_fields(path: Path) -> list[FieldSpec]:
    data = _read_yaml(path)
    try:
        fields = _FieldsFile.model_validate(data).fields
    except ValidationError as exc:
        raise ConfigError(f"Configurazione non valida in {path}:\n{exc}") from exc
    ids = [field.id for field in fields]
    duplicates = sorted({field_id for field_id in ids if ids.count(field_id) > 1})
    if duplicates:
        raise ConfigError(f"Id duplicati in {path}: {', '.join(duplicates)}")
    return fields
```

`config/settings.yaml`:

```yaml
# Modello Bedrock usato dalle sessioni agente. Verificare l'id abilitato nell'account:
# può servire un prefisso di inference profile (es. "eu.").
model: anthropic.claude-haiku-5-5

# Livello di ragionamento: low | medium | high | xhigh | max.
# Usare null con i modelli che non lo supportano (es. Haiku 4.5).
effort: low

# Unica cartella leggibile dall'agente, relativa alla cartella da cui si lancia la CLI.
manuals_dir: data/manuals

concurrency: 8        # sessioni agente in parallelo
max_turns: 10         # turni massimi per sessione
retries: 2            # nuovi tentativi su errore Bedrock
near_limit_ratio: 0.10   # ultimo 10% della tolleranza -> WARNING / AL_LIMITE

grasp:
  before: 15          # righe prima del match
  window: 30          # limit suggerito per Read
  max_limit: 60       # limit massimo accettato dall'hook
```

`config/fields.yaml`:

```yaml
# Campi del ciclo da validare.
# Il campo qui sotto è un ESEMPIO: va sostituito con i campi reali dei PDF del ciclo.
fields:
  - id: max_egt
    label: "Temperatura EGT massima"
    type: number            # number | string
    unit: "°C"              # opzionale
    group: null             # opzionale, riservato a un futuro raggruppamento
    rule:                   # opzionale: se presente, il confronto lo fa il codice
      kind: tolerance       # tolerance (solo number) | exact
      value: 5
      mode: absolute        # absolute | percent
    search_hints: ["EGT", "exhaust gas temperature"]
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_config.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/config.py config tests/test_config.py
git commit -m "feat: add settings and fields configuration loading"
```

---

### Task 3: Utilità di testo e precheck

**Files:**
- Create: `src/cycle_validation/text.py`, `src/cycle_validation/results.py`
- Create: `src/cycle_validation/precheck/__init__.py`, `src/cycle_validation/precheck/checks.py`
- Test: `tests/test_text.py`, `tests/test_precheck.py`

**Interfaces:**
- Consumes: modelli del Task 1.
- Produces:
  - `text.normalize_text(text: str) -> str`, `text.normalize_unit(unit: str) -> str`, `text.parse_number(text: str) -> float | None`, `text.format_value(value: Value | None, unit: str | None = None) -> str`
  - `results.make_result(spec: FieldSpec, extracted: ExtractedField | None, *, verdict: Verdict, decided_by: DecidedBy, rationale: str, warning_code: WarningCode | None = None, reference_value: Value | None = None, reference_unit: str | None = None, citations: list[Citation] | None = None) -> FieldResult`
  - `precheck.checks.precheck(spec: FieldSpec, extracted: ExtractedField | None) -> FieldResult | None` — `None` significa "serve l'agente".

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_text.py`:

```python
import pytest

from cycle_validation.text import format_value, normalize_text, normalize_unit, parse_number


@pytest.mark.parametrize(
    ("text", "expected"),
    [("650", 650.0), (" 12.5 ", 12.5), ("-3", -3.0), ("+0.25", 0.25)],
)
def test_parse_number_accepts_plain_numbers(text: str, expected: float) -> None:
    assert parse_number(text) == expected


@pytest.mark.parametrize("text", ["650,5", "1,250", "1.250,5", "650 °C", "circa 650", "", "1e3"])
def test_parse_number_rejects_ambiguous_forms(text: str) -> None:
    assert parse_number(text) is None


def test_normalize_text_collapses_whitespace_and_case() -> None:
    assert normalize_text("  Max   EGT\n650 ") == "max egt 650"


def test_normalize_unit_ignores_spaces_and_case() -> None:
    assert normalize_unit(" ° C ") == normalize_unit("°c")


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (650.0, "°C", "650 °C"),
        (654.8, None, "654.8"),
        (1234567.0, None, "1234567"),
        ("CF34", None, "CF34"),
        (None, "°C", "—"),
    ],
)
def test_format_value(value: float | str | None, unit: str | None, expected: str) -> None:
    assert format_value(value, unit) == expected
```

`tests/test_precheck.py`:

```python
from cycle_validation.models import (
    DecidedBy,
    ExtractedField,
    ExtractionStatus,
    FieldResult,
    FieldSpec,
    FieldType,
    Verdict,
    WarningCode,
)
from cycle_validation.precheck.checks import precheck

NUMBER_SPEC = FieldSpec(id="max_egt", label="EGT massima", type=FieldType.NUMBER, unit="°C")
STRING_SPEC = FieldSpec(id="engine_model", label="Modello motore", type=FieldType.STRING)


def extracted(**overrides: object) -> ExtractedField:
    data: dict[str, object] = {
        "id": "max_egt",
        "status": ExtractionStatus.OK,
        "raw_text": "650 °C",
        "value": 650.0,
        "unit": "°C",
    }
    data.update(overrides)
    return ExtractedField.model_validate(data)


def assert_missing(result: FieldResult | None) -> FieldResult:
    assert result is not None
    assert result.verdict is Verdict.WARNING
    assert result.warning_code is WarningCode.CAMPO_MANCANTE
    assert result.decided_by is DecidedBy.PRECHECK
    return result


def test_valid_field_goes_to_the_agent() -> None:
    assert precheck(NUMBER_SPEC, extracted()) is None


def test_absent_field_is_decided_here() -> None:
    result = assert_missing(precheck(NUMBER_SPEC, None))
    assert result.field_id == "max_egt"
    assert result.cycle_value is None


def test_missing_status() -> None:
    assert_missing(precheck(NUMBER_SPEC, extracted(status="missing", value=None)))


def test_unparseable_value_reports_raw_text() -> None:
    result = assert_missing(
        precheck(NUMBER_SPEC, extracted(status="unparseable", value=None, raw_text="n/d"))
    )
    assert "n/d" in result.rationale


def test_number_field_with_text_value() -> None:
    assert_missing(precheck(NUMBER_SPEC, extracted(value="alta")))


def test_string_field_with_numeric_value() -> None:
    assert_missing(precheck(STRING_SPEC, extracted(id="engine_model", value=5.0, unit=None)))


def test_unit_mismatch() -> None:
    result = assert_missing(precheck(NUMBER_SPEC, extracted(unit="°F")))
    assert "°F" in result.rationale


def test_unit_comparison_ignores_spacing_and_case() -> None:
    assert precheck(NUMBER_SPEC, extracted(unit="° c")) is None


def test_missing_unit_in_pdf_is_accepted() -> None:
    assert precheck(NUMBER_SPEC, extracted(unit=None)) is None
```

- [ ] **Step 2: Verificare che falliscano**

Run: `uv run pytest tests/test_text.py tests/test_precheck.py -v`
Expected: FAIL con `ModuleNotFoundError` per `cycle_validation.text` e `cycle_validation.precheck`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/text.py`:

```python
"""Normalizzazione di testo e unità, parsing e formattazione dei valori."""

import re

from cycle_validation.models import Value

_STRICT_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")


def normalize_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def normalize_unit(unit: str) -> str:
    return "".join(unit.split()).casefold()


def parse_number(text: str) -> float | None:
    """Interpreta solo '123' o '123.45'. Ogni altra forma è ambigua e restituisce None."""
    candidate = text.strip()
    if _STRICT_NUMBER.fullmatch(candidate) is None:
        return None
    return float(candidate)


def format_value(value: Value | None, unit: str | None = None) -> str:
    if value is None:
        return "—"
    text = f"{value:.12g}" if isinstance(value, float) else str(value)
    return f"{text} {unit}" if unit else text
```

`src/cycle_validation/results.py`:

```python
"""Costruzione uniforme delle righe del report."""

from cycle_validation.models import (
    Citation,
    DecidedBy,
    ExtractedField,
    FieldResult,
    FieldSpec,
    Value,
    Verdict,
    WarningCode,
)


def make_result(
    spec: FieldSpec,
    extracted: ExtractedField | None,
    *,
    verdict: Verdict,
    decided_by: DecidedBy,
    rationale: str,
    warning_code: WarningCode | None = None,
    reference_value: Value | None = None,
    reference_unit: str | None = None,
    citations: list[Citation] | None = None,
) -> FieldResult:
    return FieldResult(
        field_id=spec.id,
        label=spec.label,
        cycle_value=extracted.value if extracted else None,
        cycle_unit=(extracted.unit if extracted else None) or spec.unit,
        reference_value=reference_value,
        reference_unit=reference_unit,
        verdict=verdict,
        warning_code=warning_code,
        rationale=rationale,
        citations=citations or [],
        decided_by=decided_by,
    )
```

`src/cycle_validation/precheck/__init__.py`: file vuoto.

`src/cycle_validation/precheck/checks.py`:

```python
"""Stadio 3: decide senza LLM i casi che non richiedono giudizio."""

from cycle_validation.models import (
    DecidedBy,
    ExtractedField,
    ExtractionStatus,
    FieldResult,
    FieldSpec,
    FieldType,
    Verdict,
    WarningCode,
)
from cycle_validation.results import make_result
from cycle_validation.text import normalize_unit


def precheck(spec: FieldSpec, extracted: ExtractedField | None) -> FieldResult | None:
    """Restituisce l'esito se il campo è decidibile qui, None se serve l'agente."""

    def missing(rationale: str) -> FieldResult:
        return make_result(
            spec,
            extracted,
            verdict=Verdict.WARNING,
            warning_code=WarningCode.CAMPO_MANCANTE,
            decided_by=DecidedBy.PRECHECK,
            rationale=rationale,
        )

    if extracted is None or extracted.status is ExtractionStatus.MISSING:
        return missing("Campo assente nel PDF del ciclo.")
    if extracted.status is ExtractionStatus.UNPARSEABLE or extracted.value is None:
        return missing(f"Valore non interpretabile: {extracted.raw_text!r}.")
    if spec.type is FieldType.NUMBER and not isinstance(extracted.value, float):
        return missing(f"Atteso un numero, trovato {extracted.value!r}.")
    if spec.type is FieldType.STRING and not isinstance(extracted.value, str):
        return missing(f"Atteso un testo, trovato {extracted.value!r}.")
    if spec.unit and extracted.unit and normalize_unit(spec.unit) != normalize_unit(extracted.unit):
        return missing(f"Unità '{extracted.unit}' diversa da quella attesa '{spec.unit}'.")
    return None
```

- [ ] **Step 4: Verificare che passino**

Run: `uv run pytest tests/test_text.py tests/test_precheck.py -v`
Expected: tutti passed (18 in `test_text.py`, 9 in `test_precheck.py`).

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/text.py src/cycle_validation/results.py src/cycle_validation/precheck tests/test_text.py tests/test_precheck.py
git commit -m "feat: add text utilities and deterministic precheck"
```

---

### Task 4: Regole di confronto

**Files:**
- Create: `src/cycle_validation/verdict/__init__.py`, `src/cycle_validation/verdict/rules.py`
- Test: `tests/test_rules.py`

**Interfaces:**
- Consumes: `Rule`, `RuleKind`, `ToleranceMode`, `Value` dal Task 1; `normalize_text` dal Task 3.
- Produces: `RuleOutcome` (`PASS`, `NEAR_LIMIT`, `FAIL`); `check_tolerance(cycle: float, reference: float, rule: Rule, near_limit_ratio: float) -> RuleOutcome`; `check_exact(cycle: Value, reference: Value) -> RuleOutcome`; `apply_rule(rule: Rule, cycle: Value, reference: Value, near_limit_ratio: float) -> RuleOutcome`.

Semantica della tolleranza: `margine = value` (absolute) oppure `|reference| × value / 100` (percent). `|cycle − reference| > margine` → `FAIL`. Dentro il margine ma oltre `margine × (1 − near_limit_ratio)` → `NEAR_LIMIT`. Altrimenti `PASS`.

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_rules.py`:

```python
import pytest

from cycle_validation.models import Rule, RuleKind, ToleranceMode
from cycle_validation.verdict.rules import RuleOutcome, apply_rule, check_exact, check_tolerance

ABSOLUTE_5 = Rule(kind=RuleKind.TOLERANCE, value=5)
PERCENT_5 = Rule(kind=RuleKind.TOLERANCE, value=5, mode=ToleranceMode.PERCENT)
EXACT = Rule(kind=RuleKind.EXACT)


@pytest.mark.parametrize(
    ("cycle", "expected"),
    [
        (650.0, RuleOutcome.PASS),
        (652.0, RuleOutcome.PASS),
        (654.5, RuleOutcome.PASS),
        (654.8, RuleOutcome.NEAR_LIMIT),
        (655.0, RuleOutcome.NEAR_LIMIT),
        (645.1, RuleOutcome.NEAR_LIMIT),
        (655.1, RuleOutcome.FAIL),
        (640.0, RuleOutcome.FAIL),
    ],
)
def test_absolute_tolerance(cycle: float, expected: RuleOutcome) -> None:
    assert check_tolerance(cycle, 650.0, ABSOLUTE_5, 0.10) is expected


@pytest.mark.parametrize(
    ("cycle", "expected"),
    [(205.0, RuleOutcome.PASS), (209.5, RuleOutcome.NEAR_LIMIT), (211.0, RuleOutcome.FAIL)],
)
def test_percent_tolerance_uses_reference_as_base(cycle: float, expected: RuleOutcome) -> None:
    assert check_tolerance(cycle, 200.0, PERCENT_5, 0.10) is expected


def test_zero_tolerance_has_no_near_limit_band() -> None:
    rule = Rule(kind=RuleKind.TOLERANCE, value=0)
    assert check_tolerance(650.0, 650.0, rule, 0.10) is RuleOutcome.PASS
    assert check_tolerance(650.1, 650.0, rule, 0.10) is RuleOutcome.FAIL


def test_exact_numbers() -> None:
    assert check_exact(650.0, 650.0) is RuleOutcome.PASS
    assert check_exact(650.0, 650.5) is RuleOutcome.FAIL


def test_exact_text_ignores_case_and_spacing() -> None:
    assert check_exact("CF34-10E", "  cf34-10e ") is RuleOutcome.PASS
    assert check_exact("CF34-10E", "CF34-8E") is RuleOutcome.FAIL


def test_apply_rule_dispatches_by_kind() -> None:
    assert apply_rule(EXACT, "A", "a", 0.10) is RuleOutcome.PASS
    assert apply_rule(ABSOLUTE_5, 652.0, 650.0, 0.10) is RuleOutcome.PASS


def test_apply_rule_rejects_text_with_tolerance() -> None:
    with pytest.raises(TypeError):
        apply_rule(ABSOLUTE_5, "alta", 650.0, 0.10)
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_rules.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.verdict'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/verdict/__init__.py`: file vuoto.

`src/cycle_validation/verdict/rules.py`:

```python
"""Confronto deterministico tra valore del ciclo e valore di riferimento."""

import math
from enum import StrEnum

from cycle_validation.models import Rule, RuleKind, ToleranceMode, Value
from cycle_validation.text import normalize_text

_EPSILON = 1e-9


class RuleOutcome(StrEnum):
    PASS = "pass"
    NEAR_LIMIT = "near_limit"
    FAIL = "fail"


def check_tolerance(
    cycle: float, reference: float, rule: Rule, near_limit_ratio: float
) -> RuleOutcome:
    if rule.mode is ToleranceMode.ABSOLUTE:
        margin = rule.value
    else:
        margin = abs(reference) * rule.value / 100
    difference = abs(cycle - reference)
    if difference > margin + _EPSILON:
        return RuleOutcome.FAIL
    if margin > 0 and difference > margin * (1 - near_limit_ratio) + _EPSILON:
        return RuleOutcome.NEAR_LIMIT
    return RuleOutcome.PASS


def check_exact(cycle: Value, reference: Value) -> RuleOutcome:
    if isinstance(cycle, float) and isinstance(reference, float):
        equal = math.isclose(cycle, reference, rel_tol=0.0, abs_tol=_EPSILON)
    else:
        equal = normalize_text(str(cycle)) == normalize_text(str(reference))
    return RuleOutcome.PASS if equal else RuleOutcome.FAIL


def apply_rule(rule: Rule, cycle: Value, reference: Value, near_limit_ratio: float) -> RuleOutcome:
    if rule.kind is RuleKind.EXACT:
        return check_exact(cycle, reference)
    if not isinstance(cycle, float) or not isinstance(reference, float):
        raise TypeError("la regola 'tolerance' richiede valori numerici")
    return check_tolerance(cycle, reference, rule, near_limit_ratio)
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_rules.py -v`
Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/verdict tests/test_rules.py
git commit -m "feat: add deterministic comparison rules"
```

---

### Task 5: Confinamento dei path e verifica delle citazioni

**Files:**
- Create: `src/cycle_validation/paths.py`, `src/cycle_validation/verdict/citations.py`
- Test: `tests/test_citations.py`

**Interfaces:**
- Consumes: `Citation` dal Task 1; `normalize_text` dal Task 3.
- Produces: `paths.resolve_in_manuals(raw_path: str, manuals_dir: Path) -> Path | None` (path assoluto se sta dentro `manuals_dir`, altrimenti `None`); `citations.verify_citation(citation: Citation, manuals_dir: Path, slack: int = 3) -> bool`; `citations.verified_citations(citations: list[Citation], manuals_dir: Path) -> list[Citation]`.

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_citations.py`:

```python
from pathlib import Path

import pytest

from cycle_validation.models import Citation
from cycle_validation.paths import resolve_in_manuals
from cycle_validation.verdict.citations import verified_citations, verify_citation

TARGET = "La temperatura EGT massima ammessa è 650 °C."


@pytest.fixture
def manuals(tmp_path: Path) -> Path:
    directory = tmp_path / "manuals"
    (directory / "sub").mkdir(parents=True)
    lines = [f"Riga {number}." for number in range(1, 21)]
    lines[9] = TARGET  # riga 10
    (directory / "sub" / "engine.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "secret.md").write_text(TARGET + "\n", encoding="utf-8")
    return directory


def cite(line: int, quote: str = TARGET, file: str = "sub/engine.md") -> Citation:
    return Citation(file=file, line=line, quote=quote)


def test_quote_on_the_cited_line(manuals: Path) -> None:
    assert verify_citation(cite(10), manuals)


def test_quote_within_slack(manuals: Path) -> None:
    assert verify_citation(cite(8), manuals)
    assert verify_citation(cite(13), manuals)


def test_quote_outside_slack(manuals: Path) -> None:
    assert not verify_citation(cite(2), manuals)


def test_comparison_ignores_case_and_spacing(manuals: Path) -> None:
    assert verify_citation(cite(10, quote="egt   MASSIMA ammessa è 650"), manuals)


def test_absolute_path_inside_manuals(manuals: Path) -> None:
    absolute = str((manuals / "sub" / "engine.md").resolve())
    assert verify_citation(cite(10, file=absolute), manuals)


def test_file_outside_manuals_is_rejected(manuals: Path) -> None:
    assert not verify_citation(cite(1, file="../secret.md"), manuals)


def test_missing_file(manuals: Path) -> None:
    assert not verify_citation(cite(10, file="assente.md"), manuals)


def test_too_short_quote(manuals: Path) -> None:
    assert not verify_citation(cite(10, quote="è"), manuals)


def test_non_positive_line(manuals: Path) -> None:
    assert not verify_citation(cite(0), manuals)


def test_verified_citations_keeps_only_valid_ones(manuals: Path) -> None:
    good, bad = cite(10), cite(10, quote="testo inventato dall'agente")
    assert verified_citations([good, bad], manuals) == [good]


def test_resolve_in_manuals(manuals: Path) -> None:
    assert resolve_in_manuals("sub/engine.md", manuals) == (manuals / "sub" / "engine.md").resolve()
    assert resolve_in_manuals("../secret.md", manuals) is None
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_citations.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.paths'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/paths.py`:

```python
"""Confinamento dei path nella cartella dei manuali."""

from pathlib import Path


def resolve_in_manuals(raw_path: str, manuals_dir: Path) -> Path | None:
    """Restituisce il path assoluto se sta dentro manuals_dir, altrimenti None."""
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = manuals_dir / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(manuals_dir.resolve()):
        return None
    return resolved
```

`src/cycle_validation/verdict/citations.py`:

```python
"""Verifica che una citazione dell'agente esista davvero nel manuale."""

from pathlib import Path

from cycle_validation.models import Citation
from cycle_validation.paths import resolve_in_manuals
from cycle_validation.text import normalize_text

_MIN_QUOTE_LENGTH = 3


def verify_citation(citation: Citation, manuals_dir: Path, slack: int = 3) -> bool:
    """True se la citazione compare nel file entro `slack` righe dalla riga indicata."""
    quote = normalize_text(citation.quote)
    if len(quote) < _MIN_QUOTE_LENGTH or citation.line < 1:
        return False
    path = resolve_in_manuals(citation.file, manuals_dir)
    if path is None or not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(0, citation.line - 1 - slack)
    end = min(len(lines), citation.line + slack)
    return quote in normalize_text(" ".join(lines[start:end]))


def verified_citations(citations: list[Citation], manuals_dir: Path) -> list[Citation]:
    return [citation for citation in citations if verify_citation(citation, manuals_dir)]
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_citations.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/paths.py src/cycle_validation/verdict/citations.py tests/test_citations.py
git commit -m "feat: add path confinement and citation verification"
```

---

### Task 6: Interfaccia di sessione ed esito finale

**Files:**
- Create: `src/cycle_validation/agent/__init__.py`, `src/cycle_validation/agent/session.py`
- Create: `src/cycle_validation/verdict/decide.py`
- Test: `tests/test_decide.py`

**Interfaces:**
- Consumes: modelli (Task 1), `make_result`, `format_value`, `normalize_unit`, `parse_number` (Task 3), `RuleOutcome`, `apply_rule` (Task 4), `verified_citations` (Task 5).
- Produces:
  - `agent.session.SessionStatus` (`OK`, `MAX_TURNS`, `INVALID_OUTPUT`, `API_ERROR`)
  - `agent.session.SessionOutcome(status: SessionStatus, finding: AgentFinding | None = None, usage: Usage = Usage(), error: str | None = None)` — dataclass frozen
  - `agent.session.FieldSession` — Protocol con `async def run(self, spec: FieldSpec, extracted: ExtractedField, transcript_path: Path) -> SessionOutcome`
  - `verdict.decide.decide(spec: FieldSpec, extracted: ExtractedField, finding: AgentFinding, *, manuals_dir: Path, near_limit_ratio: float) -> FieldResult`
  - `verdict.decide.result_from_outcome(spec: FieldSpec, extracted: ExtractedField, outcome: SessionOutcome, *, manuals_dir: Path, near_limit_ratio: float) -> FieldResult` — include `usage`.

Ordine delle decisioni in `decide`: (1) `found = false` → `EVIDENZA_NON_TROVATA`; (2) nessuna citazione verificata → `CITAZIONE_NON_VERIFICATA`; (3) `judgement = unclear` → `CONFLITTO`; (4) campo con `rule` → confronto del codice; (5) campo senza `rule` → `match` = `CORRETTO`, `mismatch` = `ERRATO`.

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_decide.py`:

```python
from pathlib import Path

import pytest

from cycle_validation.agent.session import SessionOutcome, SessionStatus
from cycle_validation.models import (
    AgentFinding,
    Citation,
    DecidedBy,
    ExtractedField,
    ExtractionStatus,
    FieldResult,
    FieldSpec,
    FieldType,
    Judgement,
    Rule,
    RuleKind,
    Usage,
    Verdict,
    WarningCode,
)
from cycle_validation.verdict.decide import decide, result_from_outcome

MANUAL_LINE = "La temperatura EGT massima ammessa è 650 °C."
RULE_SPEC = FieldSpec(
    id="max_egt",
    label="EGT massima",
    type=FieldType.NUMBER,
    unit="°C",
    rule=Rule(kind=RuleKind.TOLERANCE, value=5),
)
TEXT_SPEC = FieldSpec(id="engine_model", label="Modello motore", type=FieldType.STRING)


@pytest.fixture
def manuals(tmp_path: Path) -> Path:
    directory = tmp_path / "manuals"
    directory.mkdir()
    (directory / "engine.md").write_text(f"# Limiti\n\n{MANUAL_LINE}\n", encoding="utf-8")
    return directory


def cycle(value: float | str, field_id: str = "max_egt") -> ExtractedField:
    return ExtractedField(id=field_id, status=ExtractionStatus.OK, value=value)


def finding(**overrides: object) -> AgentFinding:
    data: dict[str, object] = {
        "field_id": "max_egt",
        "found": True,
        "reference_value": "650",
        "reference_unit": "°C",
        "judgement": Judgement.MATCH,
        "rationale": "Il manuale indica 650 °C.",
        "citations": [Citation(file="engine.md", line=3, quote=MANUAL_LINE)],
    }
    data.update(overrides)
    return AgentFinding.model_validate(data)


def run(
    spec: FieldSpec, extracted: ExtractedField, found: AgentFinding, manuals: Path
) -> FieldResult:
    return decide(spec, extracted, found, manuals_dir=manuals, near_limit_ratio=0.10)


def test_evidence_not_found(manuals: Path) -> None:
    result = run(
        RULE_SPEC,
        cycle(650.0),
        finding(found=False, reference_value=None, reference_unit=None, citations=[]),
        manuals,
    )
    assert result.verdict is Verdict.WARNING
    assert result.warning_code is WarningCode.EVIDENZA_NON_TROVATA


def test_unverified_citation(manuals: Path) -> None:
    fake = [Citation(file="engine.md", line=3, quote="testo che nel manuale non esiste")]
    result = run(RULE_SPEC, cycle(650.0), finding(citations=fake), manuals)
    assert result.warning_code is WarningCode.CITAZIONE_NON_VERIFICATA
    assert result.citations == []


def test_conflicting_evidence_wins_over_the_rule(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(650.0), finding(judgement=Judgement.UNCLEAR), manuals)
    assert result.warning_code is WarningCode.CONFLITTO


def test_rule_pass(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(652.0), finding(), manuals)
    assert result.verdict is Verdict.CORRETTO
    assert result.warning_code is None
    assert result.decided_by is DecidedBy.RULE
    assert result.reference_value == 650.0
    assert len(result.citations) == 1


def test_rule_near_limit(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(654.8), finding(), manuals)
    assert result.verdict is Verdict.WARNING
    assert result.warning_code is WarningCode.AL_LIMITE


def test_rule_fail_ignores_agent_judgement(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(700.0), finding(judgement=Judgement.MATCH), manuals)
    assert result.verdict is Verdict.ERRATO
    assert "700" in result.rationale
    assert "650" in result.rationale


def test_unit_mismatch_is_a_conflict(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(650.0), finding(reference_unit="°F"), manuals)
    assert result.warning_code is WarningCode.CONFLITTO


def test_non_numeric_reference(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(650.0), finding(reference_value="650,5"), manuals)
    assert result.warning_code is WarningCode.EVIDENZA_NON_TROVATA


def test_missing_reference_value(manuals: Path) -> None:
    result = run(RULE_SPEC, cycle(650.0), finding(reference_value=None), manuals)
    assert result.warning_code is WarningCode.EVIDENZA_NON_TROVATA


@pytest.mark.parametrize(
    ("judgement", "verdict"),
    [(Judgement.MATCH, Verdict.CORRETTO), (Judgement.MISMATCH, Verdict.ERRATO)],
)
def test_field_without_rule_uses_agent_judgement(
    manuals: Path, judgement: Judgement, verdict: Verdict
) -> None:
    result = run(
        TEXT_SPEC,
        cycle("CF34", "engine_model"),
        finding(field_id="engine_model", reference_value="CF34", judgement=judgement),
        manuals,
    )
    assert result.verdict is verdict
    assert result.decided_by is DecidedBy.AGENT
    assert result.rationale == "Il manuale indica 650 °C."


def test_outcome_ok_delegates_to_decide_and_attaches_usage(manuals: Path) -> None:
    usage = Usage(input_tokens=100, output_tokens=20, turns=3)
    outcome = SessionOutcome(status=SessionStatus.OK, finding=finding(), usage=usage)
    result = result_from_outcome(
        RULE_SPEC, cycle(652.0), outcome, manuals_dir=manuals, near_limit_ratio=0.10
    )
    assert result.verdict is Verdict.CORRETTO
    assert result.usage == usage


def test_outcome_max_turns(manuals: Path) -> None:
    outcome = SessionOutcome(status=SessionStatus.MAX_TURNS, usage=Usage(turns=10))
    result = result_from_outcome(
        RULE_SPEC, cycle(652.0), outcome, manuals_dir=manuals, near_limit_ratio=0.10
    )
    assert result.warning_code is WarningCode.BUDGET_ESAURITO
    assert result.usage.turns == 10


@pytest.mark.parametrize("status", [SessionStatus.API_ERROR, SessionStatus.INVALID_OUTPUT])
def test_outcome_technical_error(manuals: Path, status: SessionStatus) -> None:
    outcome = SessionOutcome(status=status, error="HTTP 429: throttling")
    result = result_from_outcome(
        RULE_SPEC, cycle(652.0), outcome, manuals_dir=manuals, near_limit_ratio=0.10
    )
    assert result.warning_code is WarningCode.ERRORE_TECNICO
    assert "429" in result.rationale
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_decide.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.agent'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/agent/__init__.py`: file vuoto.

`src/cycle_validation/agent/session.py`:

```python
"""Interfaccia di una sessione agente: una sessione valida un campo."""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from cycle_validation.models import AgentFinding, ExtractedField, FieldSpec, Usage


class SessionStatus(StrEnum):
    OK = "ok"
    MAX_TURNS = "max_turns"
    INVALID_OUTPUT = "invalid_output"
    API_ERROR = "api_error"


@dataclass(frozen=True)
class SessionOutcome:
    status: SessionStatus
    finding: AgentFinding | None = None
    usage: Usage = field(default_factory=Usage)
    error: str | None = None


class FieldSession(Protocol):
    async def run(
        self, spec: FieldSpec, extracted: ExtractedField, transcript_path: Path
    ) -> SessionOutcome:
        """Cerca nei manuali l'evidenza per un campo e scrive la trascrizione su file."""
        ...
```

`src/cycle_validation/verdict/decide.py`:

```python
"""Assegna l'esito finale: l'agente fornisce l'evidenza, il codice giudica."""

from pathlib import Path

from cycle_validation.agent.session import SessionOutcome, SessionStatus
from cycle_validation.models import (
    AgentFinding,
    Citation,
    DecidedBy,
    ExtractedField,
    FieldResult,
    FieldSpec,
    FieldType,
    Judgement,
    Rule,
    RuleKind,
    ToleranceMode,
    Value,
    Verdict,
    WarningCode,
)
from cycle_validation.results import make_result
from cycle_validation.text import format_value, normalize_unit, parse_number
from cycle_validation.verdict.citations import verified_citations
from cycle_validation.verdict.rules import RuleOutcome, apply_rule

_RULE_VERDICTS: dict[RuleOutcome, tuple[Verdict, WarningCode | None]] = {
    RuleOutcome.PASS: (Verdict.CORRETTO, None),
    RuleOutcome.NEAR_LIMIT: (Verdict.WARNING, WarningCode.AL_LIMITE),
    RuleOutcome.FAIL: (Verdict.ERRATO, None),
}


def _describe_rule(rule: Rule) -> str:
    if rule.kind is RuleKind.EXACT:
        return "corrispondenza esatta"
    suffix = "%" if rule.mode is ToleranceMode.PERCENT else ""
    return f"tolleranza ±{rule.value:g}{suffix}"


def decide(
    spec: FieldSpec,
    extracted: ExtractedField,
    finding: AgentFinding,
    *,
    manuals_dir: Path,
    near_limit_ratio: float,
) -> FieldResult:
    decided_by = DecidedBy.RULE if spec.rule is not None else DecidedBy.AGENT

    def warn(
        code: WarningCode, rationale: str, citations: list[Citation] | None = None
    ) -> FieldResult:
        return make_result(
            spec,
            extracted,
            verdict=Verdict.WARNING,
            warning_code=code,
            decided_by=decided_by,
            rationale=rationale,
            reference_value=finding.reference_value,
            reference_unit=finding.reference_unit,
            citations=citations,
        )

    if not finding.found:
        return warn(
            WarningCode.EVIDENZA_NON_TROVATA,
            finding.rationale or "Nessuna evidenza trovata nei manuali.",
        )

    citations = verified_citations(finding.citations, manuals_dir)
    if not citations:
        return warn(
            WarningCode.CITAZIONE_NON_VERIFICATA,
            "La citazione fornita dall'agente non corrisponde al testo del manuale.",
        )

    if finding.judgement is Judgement.UNCLEAR:
        return warn(WarningCode.CONFLITTO, finding.rationale, citations)

    if spec.rule is None:
        verdict = Verdict.CORRETTO if finding.judgement is Judgement.MATCH else Verdict.ERRATO
        return make_result(
            spec,
            extracted,
            verdict=verdict,
            decided_by=decided_by,
            rationale=finding.rationale,
            reference_value=finding.reference_value,
            reference_unit=finding.reference_unit,
            citations=citations,
        )

    if finding.reference_value is None:
        return warn(
            WarningCode.EVIDENZA_NON_TROVATA,
            "L'agente non ha riportato un valore di riferimento.",
            citations,
        )
    if (
        spec.unit
        and finding.reference_unit
        and normalize_unit(spec.unit) != normalize_unit(finding.reference_unit)
    ):
        return warn(
            WarningCode.CONFLITTO,
            f"Unità del manuale '{finding.reference_unit}' diversa da quella del campo "
            f"'{spec.unit}'.",
            citations,
        )

    reference: Value = finding.reference_value
    if spec.type is FieldType.NUMBER:
        parsed = parse_number(finding.reference_value)
        if parsed is None:
            return warn(
                WarningCode.EVIDENZA_NON_TROVATA,
                f"Valore di riferimento non numerico: {finding.reference_value!r}.",
                citations,
            )
        reference = parsed

    if extracted.value is None:
        raise ValueError(f"campo '{spec.id}' senza valore: il precheck doveva fermarlo")
    outcome = apply_rule(spec.rule, extracted.value, reference, near_limit_ratio)
    verdict, code = _RULE_VERDICTS[outcome]
    return make_result(
        spec,
        extracted,
        verdict=verdict,
        warning_code=code,
        decided_by=decided_by,
        rationale=(
            f"Valore ciclo {format_value(extracted.value)} confrontato con riferimento "
            f"{format_value(reference)} ({_describe_rule(spec.rule)})."
        ),
        reference_value=reference,
        reference_unit=finding.reference_unit,
        citations=citations,
    )


def result_from_outcome(
    spec: FieldSpec,
    extracted: ExtractedField,
    outcome: SessionOutcome,
    *,
    manuals_dir: Path,
    near_limit_ratio: float,
) -> FieldResult:
    """Traduce l'esito di una sessione in una riga del report, con i consumi."""
    if outcome.status is SessionStatus.OK and outcome.finding is not None:
        result = decide(
            spec,
            extracted,
            outcome.finding,
            manuals_dir=manuals_dir,
            near_limit_ratio=near_limit_ratio,
        )
    elif outcome.status is SessionStatus.MAX_TURNS:
        result = make_result(
            spec,
            extracted,
            verdict=Verdict.WARNING,
            warning_code=WarningCode.BUDGET_ESAURITO,
            decided_by=DecidedBy.AGENT,
            rationale="Limite di turni raggiunto senza una risposta.",
        )
    else:
        result = make_result(
            spec,
            extracted,
            verdict=Verdict.WARNING,
            warning_code=WarningCode.ERRORE_TECNICO,
            decided_by=DecidedBy.AGENT,
            rationale=outcome.error or "Sessione agente fallita.",
        )
    return result.model_copy(update={"usage": outcome.usage})
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_decide.py -v`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/agent src/cycle_validation/verdict/decide.py tests/test_decide.py
git commit -m "feat: add session interface and final verdict logic"
```

---

### Task 7: Report JSON e Markdown

**Files:**
- Create: `src/cycle_validation/report/__init__.py`, `src/cycle_validation/report/builder.py`, `src/cycle_validation/report/json_writer.py`, `src/cycle_validation/report/markdown_writer.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: modelli (Task 1), `format_value` (Task 3).
- Produces: `builder.build_report(meta: RunMeta, results: list[FieldResult], *, duration_s: float) -> Report`; `json_writer.write_json(report: Report, path: Path) -> None`; `markdown_writer.render_markdown(report: Report) -> str`; `markdown_writer.write_markdown(report: Report, path: Path) -> None`.

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_report.py`:

```python
from datetime import UTC, datetime
from pathlib import Path

from cycle_validation.models import (
    Citation,
    DecidedBy,
    FieldResult,
    Report,
    RunMeta,
    Usage,
    Verdict,
    WarningCode,
)
from cycle_validation.report.builder import build_report
from cycle_validation.report.json_writer import write_json
from cycle_validation.report.markdown_writer import render_markdown, write_markdown

META = RunMeta(
    pdf_name="ciclo.pdf",
    pdf_sha256="a" * 64,
    started_at=datetime(2026, 11, 13, 9, 0, tzinfo=UTC),
    model="test-model",
    fields_sha256="b" * 64,
)


def results() -> list[FieldResult]:
    return [
        FieldResult(
            field_id="max_egt",
            label="EGT massima",
            cycle_value=652.0,
            cycle_unit="°C",
            reference_value=650.0,
            reference_unit="°C",
            verdict=Verdict.CORRETTO,
            rationale="Entro la tolleranza.",
            citations=[Citation(file="engine.md", line=3, quote="650 °C")],
            decided_by=DecidedBy.RULE,
            usage=Usage(input_tokens=100, output_tokens=20, cost_usd=0.002),
        ),
        FieldResult(
            field_id="oil_pressure",
            label="Pressione olio | minima",
            cycle_value=40.0,
            verdict=Verdict.WARNING,
            warning_code=WarningCode.EVIDENZA_NON_TROVATA,
            rationale="Nessuna evidenza\nnei manuali.",
            decided_by=DecidedBy.AGENT,
            usage=Usage(input_tokens=50, output_tokens=5, cost_usd=0.001),
        ),
        FieldResult(
            field_id="engine_model",
            label="Modello motore",
            cycle_value="CF34",
            reference_value="CF6",
            verdict=Verdict.ERRATO,
            rationale="Il manuale indica CF6.",
            citations=[Citation(file="engine.md", line=1, quote="CF6")],
            decided_by=DecidedBy.AGENT,
        ),
    ]


def test_build_report_computes_totals() -> None:
    totals = build_report(META, results(), duration_s=12.5).totals
    assert (totals.corretto, totals.warning, totals.errato) == (1, 1, 1)
    assert totals.input_tokens == 150
    assert totals.output_tokens == 25
    assert abs(totals.cost_usd - 0.003) < 1e-9
    assert totals.duration_s == 12.5


def test_markdown_has_summary_and_one_row_per_field() -> None:
    markdown = render_markdown(build_report(META, results(), duration_s=12.5))
    assert "# Report di validazione — ciclo.pdf" in markdown
    assert "1 corretti, 1 warning, 1 errati" in markdown
    assert "| Campo | Valore ciclo | Riferimento | Esito | Motivazione | Fonte |" in markdown
    row = "| EGT massima | 652 °C | 650 °C | CORRETTO | Entro la tolleranza. | engine.md:3 |"
    assert row in markdown
    assert "WARNING (EVIDENZA_NON_TROVATA)" in markdown


def test_markdown_escapes_pipes_and_newlines() -> None:
    markdown = render_markdown(build_report(META, results(), duration_s=1.0))
    assert "Pressione olio \\| minima" in markdown
    assert "Nessuna evidenza nei manuali." in markdown


def test_writers_create_files_and_json_round_trips(tmp_path: Path) -> None:
    report = build_report(META, results(), duration_s=12.5)
    json_path, md_path = tmp_path / "report.json", tmp_path / "report.md"
    write_json(report, json_path)
    write_markdown(report, md_path)
    assert Report.model_validate_json(json_path.read_text(encoding="utf-8")) == report
    assert md_path.read_text(encoding="utf-8") == render_markdown(report)
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_report.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.report'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/report/__init__.py`: file vuoto.

`src/cycle_validation/report/builder.py`:

```python
"""Assembla il report e calcola i totali."""

from cycle_validation.models import FieldResult, Report, RunMeta, Totals, Verdict


def build_report(meta: RunMeta, results: list[FieldResult], *, duration_s: float) -> Report:
    totals = Totals(
        corretto=sum(result.verdict is Verdict.CORRETTO for result in results),
        warning=sum(result.verdict is Verdict.WARNING for result in results),
        errato=sum(result.verdict is Verdict.ERRATO for result in results),
        input_tokens=sum(result.usage.input_tokens for result in results),
        output_tokens=sum(result.usage.output_tokens for result in results),
        cost_usd=sum(result.usage.cost_usd for result in results),
        duration_s=duration_s,
    )
    return Report(meta=meta, results=results, totals=totals)
```

`src/cycle_validation/report/json_writer.py`:

```python
"""Report in JSON: la fonte di verità del run."""

from pathlib import Path

from cycle_validation.models import Report


def write_json(report: Report, path: Path) -> None:
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
```

`src/cycle_validation/report/markdown_writer.py`:

```python
"""Report leggibile in Markdown."""

from pathlib import Path

from cycle_validation.models import FieldResult, Report, Verdict
from cycle_validation.text import format_value

_HEADER = "| Campo | Valore ciclo | Riferimento | Esito | Motivazione | Fonte |"
_DIVIDER = "|---|---|---|---|---|---|"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _verdict(result: FieldResult) -> str:
    if result.verdict is Verdict.WARNING and result.warning_code is not None:
        return f"WARNING ({result.warning_code.value})"
    return result.verdict.value


def _row(result: FieldResult) -> str:
    sources = "; ".join(f"{c.file}:{c.line}" for c in result.citations) or "—"
    cells = [
        result.label,
        format_value(result.cycle_value, result.cycle_unit),
        format_value(result.reference_value, result.reference_unit),
        _verdict(result),
        result.rationale,
        sources,
    ]
    return "| " + " | ".join(_cell(cell) for cell in cells) + " |"


def render_markdown(report: Report) -> str:
    meta, totals = report.meta, report.totals
    lines = [
        f"# Report di validazione — {meta.pdf_name}",
        "",
        f"- **Data:** {meta.started_at:%Y-%m-%d %H:%M:%S %Z}",
        f"- **Modello:** {meta.model}",
        f"- **Esiti:** {totals.corretto} corretti, {totals.warning} warning, "
        f"{totals.errato} errati",
        f"- **Token:** {totals.input_tokens} in ingresso, {totals.output_tokens} in uscita",
        f"- **Costo:** {totals.cost_usd:.4f} USD",
        f"- **Durata:** {totals.duration_s:.1f} s",
        "",
        _HEADER,
        _DIVIDER,
        *(_row(result) for result in report.results),
        "",
    ]
    return "\n".join(lines)


def write_markdown(report: Report, path: Path) -> None:
    path.write_text(render_markdown(report), encoding="utf-8")
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_report.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/report tests/test_report.py
git commit -m "feat: add JSON and Markdown report writers"
```

---

### Task 8: Hook GRASP e confinamento dei tool

**Files:**
- Create: `src/cycle_validation/agent/hooks.py`
- Test: `tests/test_hooks.py`

**Interfaces:**
- Consumes: `GraspSettings` (Task 2), `resolve_in_manuals` (Task 5).
- Produces: `ALLOWED_TOOLS = ("Read", "Grep", "Glob")`; `Decision(allowed: bool, reason: str = "")`; `check_tool_call(tool_name: str, tool_input: dict[str, Any], manuals_dir: Path, grasp: GraspSettings) -> Decision`; `PreToolUseHook = Callable[[Any, str | None, Any], Awaitable[dict[str, Any]]]`; `make_pre_tool_use_hook(manuals_dir: Path, grasp: GraspSettings) -> PreToolUseHook`.

Formato degli input dei tool di Claude Code: `Read` → `file_path`, `offset`, `limit`; `Grep` → `pattern`, `path`, `glob`, `output_mode`, `-A`, `-B`, `-C`, `context`; `Glob` → `pattern`, `path`. `path` assente significa cartella di lavoro, che l'adattatore imposta a `manuals_dir`.

Formato del rifiuto atteso dall'SDK: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}`. Un hook senza obiezioni restituisce `{}`.

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_hooks.py`:

```python
import asyncio
from pathlib import Path

import pytest

from cycle_validation.agent.hooks import check_tool_call, make_pre_tool_use_hook
from cycle_validation.config import GraspSettings

GRASP = GraspSettings()


@pytest.fixture
def manuals(tmp_path: Path) -> Path:
    directory = tmp_path / "manuals"
    directory.mkdir()
    (directory / "engine.md").write_text("EGT 650\n", encoding="utf-8")
    return directory


def test_read_with_window_inside_manuals_is_allowed(manuals: Path) -> None:
    decision = check_tool_call(
        "Read", {"file_path": "engine.md", "offset": 85, "limit": 30}, manuals, GRASP
    )
    assert decision.allowed


def test_read_with_absolute_path_inside_manuals_is_allowed(manuals: Path) -> None:
    absolute = str((manuals / "engine.md").resolve())
    assert check_tool_call("Read", {"file_path": absolute, "limit": 30}, manuals, GRASP).allowed


def test_read_without_limit_is_denied_with_grasp_instructions(manuals: Path) -> None:
    decision = check_tool_call("Read", {"file_path": "engine.md"}, manuals, GRASP)
    assert not decision.allowed
    assert "GRASP" in decision.reason
    assert "limit = 30" in decision.reason


@pytest.mark.parametrize("limit", [61, 2000, 0, -5, True, "30"])
def test_read_with_invalid_limit_is_denied(manuals: Path, limit: object) -> None:
    decision = check_tool_call("Read", {"file_path": "engine.md", "limit": limit}, manuals, GRASP)
    assert not decision.allowed


@pytest.mark.parametrize("file_path", ["../secret.md", "sub/../../secret.md"])
def test_read_outside_manuals_is_denied(manuals: Path, file_path: str) -> None:
    decision = check_tool_call("Read", {"file_path": file_path, "limit": 30}, manuals, GRASP)
    assert not decision.allowed


def test_read_with_absolute_path_outside_manuals_is_denied(manuals: Path) -> None:
    outside = str((manuals.parent / "secret.md").resolve())
    assert not check_tool_call("Read", {"file_path": outside, "limit": 30}, manuals, GRASP).allowed


def test_grep_without_path_is_allowed(manuals: Path) -> None:
    decision = check_tool_call(
        "Grep", {"pattern": "EGT|exhaust", "output_mode": "content"}, manuals, GRASP
    )
    assert decision.allowed


def test_grep_outside_manuals_is_denied(manuals: Path) -> None:
    decision = check_tool_call("Grep", {"pattern": "EGT", "path": ".."}, manuals, GRASP)
    assert not decision.allowed


def test_grep_with_huge_context_is_denied(manuals: Path) -> None:
    assert not check_tool_call("Grep", {"pattern": "EGT", "-C": 500}, manuals, GRASP).allowed


def test_grep_with_traversal_glob_is_denied(manuals: Path) -> None:
    decision = check_tool_call("Grep", {"pattern": "EGT", "glob": "../**/*.md"}, manuals, GRASP)
    assert not decision.allowed


def test_glob_inside_manuals_is_allowed(manuals: Path) -> None:
    assert check_tool_call("Glob", {"pattern": "**/*.md"}, manuals, GRASP).allowed


def test_glob_with_traversal_pattern_is_denied(manuals: Path) -> None:
    assert not check_tool_call("Glob", {"pattern": "../**/*.md"}, manuals, GRASP).allowed


@pytest.mark.parametrize("tool_name", ["Bash", "Write", "Edit", "WebFetch"])
def test_other_tools_are_denied(manuals: Path, tool_name: str) -> None:
    assert not check_tool_call(tool_name, {}, manuals, GRASP).allowed


def test_hook_returns_empty_dict_when_allowed(manuals: Path) -> None:
    hook = make_pre_tool_use_hook(manuals, GRASP)
    payload = {"tool_name": "Read", "tool_input": {"file_path": "engine.md", "limit": 30}}
    assert asyncio.run(hook(payload, "tool-1", {"signal": None})) == {}


def test_hook_returns_deny_payload(manuals: Path) -> None:
    hook = make_pre_tool_use_hook(manuals, GRASP)
    payload = {"tool_name": "Read", "tool_input": {"file_path": "engine.md"}}
    output = asyncio.run(hook(payload, "tool-1", {"signal": None}))["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert "GRASP" in output["permissionDecisionReason"]
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_hooks.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.agent.hooks'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/agent/hooks.py`:

```python
"""Hook PreToolUse: impone GRASP e confina l'agente nella cartella dei manuali."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cycle_validation.config import GraspSettings
from cycle_validation.paths import resolve_in_manuals

ALLOWED_TOOLS = ("Read", "Grep", "Glob")
_GREP_CONTEXT_KEYS = ("-A", "-B", "-C", "context")
_PATTERN_KEYS = {"Glob": ("pattern",), "Grep": ("glob",)}

PreToolUseHook = Callable[[Any, str | None, Any], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""


_ALLOW = Decision(allowed=True)


def _deny(reason: str) -> Decision:
    return Decision(allowed=False, reason=reason)


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _escapes_manuals(pattern: str) -> bool:
    return ".." in pattern or pattern.startswith(("/", "\\")) or Path(pattern).is_absolute()


def _check_read(tool_input: dict[str, Any], manuals_dir: Path, grasp: GraspSettings) -> Decision:
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or resolve_in_manuals(file_path, manuals_dir) is None:
        return _deny("Puoi leggere solo file dentro la cartella dei manuali.")
    limit = tool_input.get("limit")
    if not _is_positive_int(limit) or limit > grasp.max_limit:
        return _deny(
            "Lettura del file intero vietata (regola GRASP). Richiama Read con "
            f"offset = riga_del_match - {grasp.before} e limit = {grasp.window} "
            f"(massimo {grasp.max_limit})."
        )
    return _ALLOW


def _check_search(
    tool_name: str, tool_input: dict[str, Any], manuals_dir: Path, grasp: GraspSettings
) -> Decision:
    path = tool_input.get("path")
    if path is not None and (
        not isinstance(path, str) or resolve_in_manuals(path, manuals_dir) is None
    ):
        return _deny("Puoi cercare solo dentro la cartella dei manuali.")
    for key in _PATTERN_KEYS[tool_name]:
        pattern = tool_input.get(key)
        if isinstance(pattern, str) and _escapes_manuals(pattern):
            return _deny("I pattern di ricerca devono restare dentro la cartella dei manuali.")
    if tool_name == "Grep":
        for key in _GREP_CONTEXT_KEYS:
            value = tool_input.get(key)
            if isinstance(value, int) and value > grasp.max_limit:
                return _deny(
                    f"Contesto del grep troppo ampio: usa al massimo {grasp.max_limit} righe."
                )
    return _ALLOW


def check_tool_call(
    tool_name: str, tool_input: dict[str, Any], manuals_dir: Path, grasp: GraspSettings
) -> Decision:
    """Decide se una chiamata tool dell'agente è ammessa. Funzione pura."""
    if tool_name not in ALLOWED_TOOLS:
        return _deny(f"Tool '{tool_name}' non consentito. Usa solo Read, Grep e Glob.")
    if tool_name == "Read":
        return _check_read(tool_input, manuals_dir, grasp)
    return _check_search(tool_name, tool_input, manuals_dir, grasp)


def make_pre_tool_use_hook(manuals_dir: Path, grasp: GraspSettings) -> PreToolUseHook:
    """Adatta check_tool_call al formato degli hook del Claude Agent SDK."""

    async def hook(input_data: Any, tool_use_id: str | None, context: Any) -> dict[str, Any]:
        decision = check_tool_call(
            input_data["tool_name"], input_data.get("tool_input") or {}, manuals_dir, grasp
        )
        if decision.allowed:
            return {}
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }

    return hook
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_hooks.py -v`
Expected: 24 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/agent/hooks.py tests/test_hooks.py
git commit -m "feat: enforce GRASP paragraph reads and manuals confinement via hook"
```

---

### Task 9: Runner delle sessioni

**Files:**
- Create: `src/cycle_validation/agent/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `FieldSession`, `SessionOutcome`, `SessionStatus` (Task 6); `FieldSpec`, `ExtractedField`, `Usage` (Task 1).
- Produces: `async validate_fields(session: FieldSession, items: Sequence[tuple[FieldSpec, ExtractedField]], *, concurrency: int, retries: int, sessions_dir: Path, backoff_s: float = 2.0) -> dict[str, SessionOutcome]` — chiave = `spec.id`.

Regole: al massimo `concurrency` sessioni contemporanee. `API_ERROR` (anche da eccezione) → fino a `retries` nuovi tentativi con attesa `backoff_s × 2^tentativo`. `INVALID_OUTPUT` → un solo nuovo tentativo. `MAX_TURNS` e `OK` non si ritentano. I consumi di tutti i tentativi si sommano. La trascrizione è `sessions_dir/<field_id>.jsonl` (sovrascritta a ogni tentativo).

- [ ] **Step 1: Scrivere il test che fallisce**

`tests/test_runner.py`:

```python
import asyncio
from pathlib import Path

from cycle_validation.agent.runner import validate_fields
from cycle_validation.agent.session import SessionOutcome, SessionStatus
from cycle_validation.models import (
    AgentFinding,
    ExtractedField,
    ExtractionStatus,
    FieldSpec,
    FieldType,
    Judgement,
    Usage,
)

Step = SessionOutcome | Exception


def item(field_id: str) -> tuple[FieldSpec, ExtractedField]:
    spec = FieldSpec(id=field_id, label=field_id, type=FieldType.NUMBER)
    return spec, ExtractedField(id=field_id, status=ExtractionStatus.OK, value=1.0)


def ok(field_id: str = "a", tokens: int = 10) -> SessionOutcome:
    finding = AgentFinding(
        field_id=field_id,
        found=False,
        reference_value=None,
        reference_unit=None,
        judgement=Judgement.UNCLEAR,
        rationale="",
        citations=[],
    )
    return SessionOutcome(
        status=SessionStatus.OK, finding=finding, usage=Usage(input_tokens=tokens, turns=1)
    )


def failed(status: SessionStatus, tokens: int = 5) -> SessionOutcome:
    return SessionOutcome(status=status, usage=Usage(input_tokens=tokens, turns=1), error="boom")


class FakeSession:
    def __init__(self, script: dict[str, list[Step]], delay: float = 0.0) -> None:
        self._script = {key: list(steps) for key, steps in script.items()}
        self._delay = delay
        self.calls: list[str] = []
        self.transcripts: list[Path] = []
        self.active = 0
        self.max_active = 0

    async def run(
        self, spec: FieldSpec, extracted: ExtractedField, transcript_path: Path
    ) -> SessionOutcome:
        self.calls.append(spec.id)
        self.transcripts.append(transcript_path)
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(self._delay)
            step = self._script[spec.id].pop(0)
            if isinstance(step, Exception):
                raise step
            return step
        finally:
            self.active -= 1


def run(
    session: FakeSession,
    ids: list[str],
    tmp_path: Path,
    *,
    concurrency: int = 4,
    retries: int = 2,
) -> dict[str, SessionOutcome]:
    return asyncio.run(
        validate_fields(
            session,
            [item(field_id) for field_id in ids],
            concurrency=concurrency,
            retries=retries,
            sessions_dir=tmp_path / "sessions",
            backoff_s=0,
        )
    )


def test_returns_one_outcome_per_field(tmp_path: Path) -> None:
    session = FakeSession({"a": [ok("a")], "b": [ok("b")]})
    outcomes = run(session, ["a", "b"], tmp_path)
    assert set(outcomes) == {"a", "b"}
    assert all(outcome.status is SessionStatus.OK for outcome in outcomes.values())
    assert (tmp_path / "sessions").is_dir()
    assert tmp_path / "sessions" / "a.jsonl" in session.transcripts


def test_retries_api_errors_then_succeeds_and_sums_usage(tmp_path: Path) -> None:
    session = FakeSession({"a": [failed(SessionStatus.API_ERROR), ok("a")]})
    outcome = run(session, ["a"], tmp_path)["a"]
    assert outcome.status is SessionStatus.OK
    assert session.calls == ["a", "a"]
    assert outcome.usage.input_tokens == 15
    assert outcome.usage.turns == 2


def test_gives_up_after_configured_retries(tmp_path: Path) -> None:
    session = FakeSession({"a": [failed(SessionStatus.API_ERROR)] * 5})
    outcome = run(session, ["a"], tmp_path, retries=2)["a"]
    assert outcome.status is SessionStatus.API_ERROR
    assert len(session.calls) == 3


def test_exception_becomes_api_error(tmp_path: Path) -> None:
    session = FakeSession({"a": [RuntimeError("connessione persa")]})
    outcome = run(session, ["a"], tmp_path, retries=0)["a"]
    assert outcome.status is SessionStatus.API_ERROR
    assert outcome.error == "RuntimeError: connessione persa"


def test_invalid_output_is_retried_only_once(tmp_path: Path) -> None:
    session = FakeSession({"a": [failed(SessionStatus.INVALID_OUTPUT)] * 2 + [ok("a")]})
    outcome = run(session, ["a"], tmp_path)["a"]
    assert outcome.status is SessionStatus.INVALID_OUTPUT
    assert len(session.calls) == 2


def test_max_turns_is_not_retried(tmp_path: Path) -> None:
    session = FakeSession({"a": [failed(SessionStatus.MAX_TURNS), ok("a")]})
    outcome = run(session, ["a"], tmp_path)["a"]
    assert outcome.status is SessionStatus.MAX_TURNS
    assert len(session.calls) == 1


def test_one_failing_field_does_not_affect_the_others(tmp_path: Path) -> None:
    session = FakeSession({"a": [RuntimeError("x")], "b": [ok("b")]})
    outcomes = run(session, ["a", "b"], tmp_path, retries=0)
    assert outcomes["a"].status is SessionStatus.API_ERROR
    assert outcomes["b"].status is SessionStatus.OK


def test_concurrency_limit_is_respected(tmp_path: Path) -> None:
    ids = [f"f{number}" for number in range(6)]
    session = FakeSession({field_id: [ok(field_id)] for field_id in ids}, delay=0.02)
    run(session, ids, tmp_path, concurrency=2)
    assert session.max_active == 2
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_runner.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.agent.runner'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/agent/runner.py`:

```python
"""Esegue una sessione per campo, in parallelo, con retry sugli errori tecnici."""

import asyncio
import dataclasses
from collections.abc import Sequence
from pathlib import Path

from cycle_validation.agent.session import FieldSession, SessionOutcome, SessionStatus
from cycle_validation.models import ExtractedField, FieldSpec, Usage

_INVALID_OUTPUT_RETRIES = 1


async def _run_one(
    session: FieldSession,
    spec: FieldSpec,
    extracted: ExtractedField,
    *,
    retries: int,
    sessions_dir: Path,
    backoff_s: float,
) -> SessionOutcome:
    usage = Usage()
    api_attempts = 0
    invalid_attempts = 0
    while True:
        try:
            outcome = await session.run(spec, extracted, sessions_dir / f"{spec.id}.jsonl")
        except Exception as exc:
            outcome = SessionOutcome(
                status=SessionStatus.API_ERROR, error=f"{type(exc).__name__}: {exc}"
            )
        usage = usage + outcome.usage
        if outcome.status is SessionStatus.API_ERROR and api_attempts < retries:
            await asyncio.sleep(backoff_s * 2**api_attempts)
            api_attempts += 1
            continue
        if (
            outcome.status is SessionStatus.INVALID_OUTPUT
            and invalid_attempts < _INVALID_OUTPUT_RETRIES
        ):
            invalid_attempts += 1
            continue
        return dataclasses.replace(outcome, usage=usage)


async def validate_fields(
    session: FieldSession,
    items: Sequence[tuple[FieldSpec, ExtractedField]],
    *,
    concurrency: int,
    retries: int,
    sessions_dir: Path,
    backoff_s: float = 2.0,
) -> dict[str, SessionOutcome]:
    """Valida ogni campo in una sessione isolata. Non solleva per errori di un campo."""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(concurrency)

    async def guarded(spec: FieldSpec, extracted: ExtractedField) -> tuple[str, SessionOutcome]:
        async with semaphore:
            outcome = await _run_one(
                session,
                spec,
                extracted,
                retries=retries,
                sessions_dir=sessions_dir,
                backoff_s=backoff_s,
            )
        return spec.id, outcome

    pairs = await asyncio.gather(*(guarded(spec, extracted) for spec, extracted in items))
    return dict(pairs)
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_runner.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/agent/runner.py tests/test_runner.py
git commit -m "feat: add parallel per-field session runner with retries"
```

---

### Task 10: Adattatore Claude Agent SDK e prompt

**Files:**
- Create: `src/cycle_validation/agent/prompt.py`, `src/cycle_validation/agent/sdk_session.py`, `prompts/validator.md`
- Test: `tests/test_prompt.py`, `tests/test_sdk_session.py`, `tests/test_sdk_session_bedrock.py`

**Interfaces:**
- Consumes: `Settings` (Task 2), `format_value` (Task 3), `SessionOutcome`, `SessionStatus` (Task 6), `ALLOWED_TOOLS`, `make_pre_tool_use_hook` (Task 8), `load_settings` (Task 2), `verified_citations` (Task 5), `parse_number` (Task 3).
- Produces: `prompt.build_user_prompt(spec: FieldSpec, extracted: ExtractedField) -> str`; `prompt.finding_output_format() -> dict[str, Any]`; `sdk_session.usage_from_result(result: ResultMessage) -> Usage`; `sdk_session.outcome_from_result(result: ResultMessage | None, field_id: str) -> SessionOutcome`; `sdk_session.SdkFieldSession(settings: Settings, system_prompt: str)` con `build_options() -> ClaudeAgentOptions` e `async run(spec, extracted, transcript_path) -> SessionOutcome` (implementa `FieldSession`).

API dell'SDK verificata sulla versione 0.2.180:
- `from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ResultMessage, query`; `from claude_agent_sdk.types import HookCallback`.
- `query(*, prompt: str, options: ClaudeAgentOptions)` è un iteratore asincrono di messaggi; l'ultimo è un `ResultMessage`.
- Campi di `ClaudeAgentOptions` usati: `tools` (insieme dei tool disponibili), `allowed_tools` (auto-approvati), `system_prompt`, `model`, `effort`, `max_turns`, `cwd`, `permission_mode="dontAsk"`, `setting_sources=[]` (isola da impostazioni, plugin e hook dell'utente), `strict_mcp_config=True`, `hooks`, `output_format={"type": "json_schema", "schema": ...}`.
- Campi di `ResultMessage` usati: `subtype`, `is_error`, `errors`, `result`, `api_error_status`, `terminal_reason`, `structured_output`, `usage` (dict con `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`), `total_cost_usd`, `duration_ms`, `num_turns`. Limite di turni: `subtype == "error_max_turns"`.
- Bedrock si attiva dall'ambiente (`CLAUDE_CODE_USE_BEDROCK=1`, `AWS_REGION`, credenziali AWS), che il processo dell'SDK eredita. Il prompt caching è gestito dall'harness; si verifica con `cache_read_tokens > 0` nei consumi.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_prompt.py`:

```python
from cycle_validation.agent.prompt import build_user_prompt, finding_output_format
from cycle_validation.models import ExtractedField, ExtractionStatus, FieldSpec, FieldType


def test_user_prompt_contains_field_value_and_hints() -> None:
    spec = FieldSpec(
        id="max_egt",
        label="EGT massima",
        type=FieldType.NUMBER,
        unit="°C",
        search_hints=["EGT", "exhaust gas temperature"],
    )
    extracted = ExtractedField(id="max_egt", status=ExtractionStatus.OK, value=650.0, unit="°C")
    prompt = build_user_prompt(spec, extracted)
    assert "EGT massima" in prompt
    assert "max_egt" in prompt
    assert "650 °C" in prompt
    assert "EGT, exhaust gas temperature" in prompt


def test_user_prompt_without_optional_parts() -> None:
    spec = FieldSpec(id="engine_model", label="Modello motore", type=FieldType.STRING)
    extracted = ExtractedField(id="engine_model", status=ExtractionStatus.OK, value="CF34")
    prompt = build_user_prompt(spec, extracted)
    assert "CF34" in prompt
    assert "Unità attesa" not in prompt
    assert "Parole chiave" not in prompt


def test_output_format_is_a_closed_json_schema() -> None:
    output_format = finding_output_format()
    schema = output_format["schema"]
    assert output_format["type"] == "json_schema"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "field_id",
        "found",
        "reference_value",
        "reference_unit",
        "judgement",
        "rationale",
        "citations",
    }
```

`tests/test_sdk_session.py`:

```python
from pathlib import Path
from typing import Any

from claude_agent_sdk import ResultMessage

from cycle_validation.agent.sdk_session import SdkFieldSession, outcome_from_result
from cycle_validation.agent.session import SessionStatus
from cycle_validation.config import Settings
from cycle_validation.models import Usage

VALID_FINDING: dict[str, Any] = {
    "field_id": "id_scelto_dal_modello",
    "found": True,
    "reference_value": "650",
    "reference_unit": "°C",
    "judgement": "match",
    "rationale": "Il manuale indica 650 °C.",
    "citations": [{"file": "engine.md", "line": 3, "quote": "650 °C"}],
}


def result(**overrides: Any) -> ResultMessage:
    data: dict[str, Any] = {
        "subtype": "success",
        "duration_ms": 1500,
        "duration_api_ms": 1200,
        "is_error": False,
        "num_turns": 4,
        "session_id": "s-1",
        "total_cost_usd": 0.002,
        "usage": {
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_read_input_tokens": 900,
            "cache_creation_input_tokens": 50,
        },
        "structured_output": VALID_FINDING,
    }
    data.update(overrides)
    return ResultMessage(**data)


def test_success_maps_finding_and_usage() -> None:
    outcome = outcome_from_result(result(), "max_egt")
    assert outcome.status is SessionStatus.OK
    assert outcome.finding is not None
    assert outcome.finding.field_id == "max_egt"
    assert outcome.finding.reference_value == "650"
    assert outcome.usage == Usage(
        input_tokens=100,
        output_tokens=20,
        cache_read_tokens=900,
        cache_write_tokens=50,
        cost_usd=0.002,
        duration_s=1.5,
        turns=4,
    )


def test_no_result_message_is_an_api_error() -> None:
    assert outcome_from_result(None, "max_egt").status is SessionStatus.API_ERROR


def test_max_turns() -> None:
    outcome = outcome_from_result(
        result(subtype="error_max_turns", is_error=True, structured_output=None), "max_egt"
    )
    assert outcome.status is SessionStatus.MAX_TURNS
    assert outcome.usage.turns == 4


def test_api_error_reports_status_and_message() -> None:
    outcome = outcome_from_result(
        result(
            subtype="error_during_execution",
            is_error=True,
            errors=["throttling"],
            api_error_status=429,
            structured_output=None,
        ),
        "max_egt",
    )
    assert outcome.status is SessionStatus.API_ERROR
    assert outcome.error == "HTTP 429: throttling"


def test_missing_structured_output_is_invalid() -> None:
    outcome = outcome_from_result(result(structured_output=None), "max_egt")
    assert outcome.status is SessionStatus.INVALID_OUTPUT


def test_incomplete_structured_output_is_invalid() -> None:
    outcome = outcome_from_result(result(structured_output={"found": True}), "max_egt")
    assert outcome.status is SessionStatus.INVALID_OUTPUT


def test_options_restrict_the_agent(tmp_path: Path) -> None:
    manuals = tmp_path / "manuals"
    manuals.mkdir()
    settings = Settings(model="test-model", effort="low", manuals_dir=manuals, max_turns=7)
    options = SdkFieldSession(settings, "PROMPT DI SISTEMA").build_options()
    assert options.tools == ["Read", "Grep", "Glob"]
    assert options.allowed_tools == ["Read", "Grep", "Glob"]
    assert options.system_prompt == "PROMPT DI SISTEMA"
    assert options.model == "test-model"
    assert options.effort == "low"
    assert options.max_turns == 7
    assert Path(str(options.cwd)) == manuals.resolve()
    assert options.permission_mode == "dontAsk"
    assert options.setting_sources == []
    assert options.strict_mcp_config is True
    assert options.hooks is not None and "PreToolUse" in options.hooks
    assert options.output_format is not None
    assert options.output_format["type"] == "json_schema"
```

`tests/test_sdk_session_bedrock.py` (smoke test reale, escluso dalla suite di default):

```python
import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv

from cycle_validation.agent.sdk_session import SdkFieldSession
from cycle_validation.agent.session import SessionStatus
from cycle_validation.config import load_settings
from cycle_validation.models import ExtractedField, ExtractionStatus, FieldSpec, FieldType
from cycle_validation.text import parse_number
from cycle_validation.verdict.citations import verified_citations

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.bedrock
def test_real_session_finds_value_and_cites_it(tmp_path: Path) -> None:
    load_dotenv(REPO_ROOT / ".env")
    manuals = tmp_path / "manuals"
    manuals.mkdir()
    filler = "\n".join(f"Riga di riempimento numero {number}." for number in range(300))
    (manuals / "engine_manual.md").write_text(
        f"# Manuale motore X1\n\n{filler}\n\n## Limiti operativi\n\n"
        "La temperatura EGT massima ammessa è 650 °C.\n",
        encoding="utf-8",
    )
    settings = load_settings(REPO_ROOT / "config" / "settings.yaml").model_copy(
        update={"manuals_dir": manuals}
    )
    system_prompt = (REPO_ROOT / "prompts" / "validator.md").read_text(encoding="utf-8")
    spec = FieldSpec(
        id="max_egt",
        label="Temperatura EGT massima",
        type=FieldType.NUMBER,
        unit="°C",
        search_hints=["EGT"],
    )
    extracted = ExtractedField(id="max_egt", status=ExtractionStatus.OK, value=650.0, unit="°C")
    transcript = tmp_path / "max_egt.jsonl"

    outcome = asyncio.run(SdkFieldSession(settings, system_prompt).run(spec, extracted, transcript))

    assert outcome.status is SessionStatus.OK, outcome.error
    assert outcome.finding is not None
    assert outcome.finding.found
    assert parse_number(outcome.finding.reference_value or "") == 650.0
    assert verified_citations(outcome.finding.citations, manuals)
    assert transcript.read_text(encoding="utf-8").strip()
    assert outcome.usage.turns >= 1
```

- [ ] **Step 2: Verificare che falliscano**

Run: `uv run pytest tests/test_prompt.py tests/test_sdk_session.py -v`
Expected: FAIL con `ModuleNotFoundError` per `cycle_validation.agent.prompt` e `cycle_validation.agent.sdk_session`.

- [ ] **Step 3: Implementare prompt e adattatore**

`src/cycle_validation/agent/prompt.py`:

```python
"""Messaggio utente e schema dell'output strutturato della sessione agente."""

from typing import Any

from cycle_validation.models import AgentFinding, ExtractedField, FieldSpec
from cycle_validation.text import format_value


def finding_output_format() -> dict[str, Any]:
    return {"type": "json_schema", "schema": AgentFinding.model_json_schema()}


def build_user_prompt(spec: FieldSpec, extracted: ExtractedField) -> str:
    lines = [
        f"Campo da validare: {spec.label} (id: {spec.id})",
        f"Tipo: {spec.type.value}",
    ]
    if spec.unit:
        lines.append(f"Unità attesa: {spec.unit}")
    lines.append(f"Valore dichiarato nel ciclo: {format_value(extracted.value, extracted.unit)}")
    if spec.search_hints:
        lines.append("Parole chiave di partenza: " + ", ".join(spec.search_hints))
    lines.append(
        "Trova nei manuali il valore di riferimento per questo campo e restituisci "
        "il risultato strutturato."
    )
    return "\n".join(lines)
```

`src/cycle_validation/agent/sdk_session.py`:

```python
"""Adattatore tra FieldSession e Claude Agent SDK. Unico modulo che importa l'SDK."""

import dataclasses
import json
from pathlib import Path
from typing import Any, cast

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ResultMessage, query
from claude_agent_sdk.types import HookCallback
from pydantic import ValidationError

from cycle_validation.agent.hooks import ALLOWED_TOOLS, make_pre_tool_use_hook
from cycle_validation.agent.prompt import build_user_prompt, finding_output_format
from cycle_validation.agent.session import SessionOutcome, SessionStatus
from cycle_validation.config import Settings
from cycle_validation.models import AgentFinding, ExtractedField, FieldSpec, Usage


def usage_from_result(result: ResultMessage) -> Usage:
    raw = result.usage or {}
    return Usage(
        input_tokens=int(raw.get("input_tokens") or 0),
        output_tokens=int(raw.get("output_tokens") or 0),
        cache_read_tokens=int(raw.get("cache_read_input_tokens") or 0),
        cache_write_tokens=int(raw.get("cache_creation_input_tokens") or 0),
        cost_usd=float(result.total_cost_usd or 0.0),
        duration_s=result.duration_ms / 1000,
        turns=result.num_turns,
    )


def outcome_from_result(result: ResultMessage | None, field_id: str) -> SessionOutcome:
    """Traduce il messaggio finale dell'SDK nell'esito della sessione."""
    if result is None:
        return SessionOutcome(
            status=SessionStatus.API_ERROR, error="La sessione è terminata senza un risultato."
        )
    usage = usage_from_result(result)
    if result.subtype == "error_max_turns" or result.terminal_reason == "max_turns":
        return SessionOutcome(status=SessionStatus.MAX_TURNS, usage=usage)
    if result.is_error:
        detail = "; ".join(result.errors or []) or result.result or result.subtype
        if result.api_error_status is not None:
            detail = f"HTTP {result.api_error_status}: {detail}"
        return SessionOutcome(status=SessionStatus.API_ERROR, usage=usage, error=detail)
    try:
        finding = AgentFinding.model_validate(result.structured_output)
    except ValidationError as exc:
        return SessionOutcome(
            status=SessionStatus.INVALID_OUTPUT,
            usage=usage,
            error=f"Output dell'agente non conforme allo schema ({exc.error_count()} errori).",
        )
    return SessionOutcome(
        status=SessionStatus.OK,
        finding=finding.model_copy(update={"field_id": field_id}),
        usage=usage,
    )


def _to_jsonable(message: object) -> dict[str, Any]:
    if dataclasses.is_dataclass(message) and not isinstance(message, type):
        body = dataclasses.asdict(message)
    else:
        body = {"repr": repr(message)}
    return {"type": type(message).__name__, **body}


class SdkFieldSession:
    """Una sessione Claude Agent SDK isolata per campo, confinata nei manuali."""

    def __init__(self, settings: Settings, system_prompt: str) -> None:
        self._settings = settings
        self._system_prompt = system_prompt
        self._manuals_dir = settings.manuals_dir.resolve()

    def build_options(self) -> ClaudeAgentOptions:
        hook = make_pre_tool_use_hook(self._manuals_dir, self._settings.grasp)
        return ClaudeAgentOptions(
            tools=list(ALLOWED_TOOLS),
            allowed_tools=list(ALLOWED_TOOLS),
            system_prompt=self._system_prompt,
            model=self._settings.model,
            effort=self._settings.effort,
            max_turns=self._settings.max_turns,
            cwd=self._manuals_dir,
            permission_mode="dontAsk",
            setting_sources=[],
            strict_mcp_config=True,
            hooks={"PreToolUse": [HookMatcher(hooks=[cast(HookCallback, hook)])]},
            output_format=finding_output_format(),
        )

    async def run(
        self, spec: FieldSpec, extracted: ExtractedField, transcript_path: Path
    ) -> SessionOutcome:
        result: ResultMessage | None = None
        prompt = build_user_prompt(spec, extracted)
        with transcript_path.open("w", encoding="utf-8") as transcript:
            async for message in query(prompt=prompt, options=self.build_options()):
                line = json.dumps(_to_jsonable(message), ensure_ascii=False, default=str)
                transcript.write(line + "\n")
                if isinstance(message, ResultMessage):
                    result = message
        return outcome_from_result(result, spec.id)
```

- [ ] **Step 4: Scrivere il prompt di sistema**

`prompts/validator.md`:

````markdown
Sei un verificatore tecnico. Ricevi un campo dichiarato in un ciclo motore e devi trovare, nei manuali tecnici, il valore di riferimento per quel campo. Non decidi tu l'esito finale: il tuo compito è trovare l'evidenza e citarla con precisione.

## Corpus

I manuali sono file Markdown e JSON nella cartella di lavoro corrente. Puoi leggere solo lì dentro. Usa esclusivamente il contenuto di questi file: è vietato usare conoscenze pregresse sul motore o sul campo.

## Strumenti

Hai solo `Glob`, `Grep` e `Read`.

1. **Localizza con Grep.** Usa sempre `output_mode: "content"`, così ottieni il numero di riga di ogni match. Parti dalle parole chiave fornite, cercale in alternativa (`termine1|termine2`) e senza distinzione tra maiuscole e minuscole (`-i: true`). Se trovi troppi match aggiungi un secondo termine discriminante; se non trovi nulla prova sinonimi, sigle e la forma estesa. Lancia in parallelo le ricerche indipendenti.
2. **Leggi solo il paragrafo.** Chiama `Read` sempre con `offset` e `limit`: `offset` = riga del match meno 15, `limit` = 30. Una `Read` senza `limit` viene rifiutata. Se il paragrafo non basta, sposta `offset` di 30 righe invece di allargare la finestra.
3. **Glob solo se serve** per capire quali file esistono. Non ripeterlo.

Hai pochi turni: punta a chiudere in 3-5 round di ricerca e lettura.

## Risultato

Restituisci il risultato strutturato con questi campi:

- `field_id`: l'id del campo ricevuto.
- `found`: `true` solo se hai letto nei manuali un passaggio che stabilisce il valore di riferimento per questo campo.
- `reference_value`: il valore di riferimento. Per i campi numerici scrivi solo il numero, con il punto come separatore decimale e senza separatori delle migliaia (esempi: `650`, `12.5`). Per i campi di testo riporta il testo come compare nel manuale. `null` se `found` è `false`.
- `reference_unit`: l'unità di misura scritta nel manuale accanto al valore, oppure `null`.
- `judgement`: confronto tra il valore del ciclo e quello del manuale. `match` se coincidono, `mismatch` se sono in contrasto, `unclear` se i manuali riportano valori diversi tra loro o il confronto non è determinabile.
- `rationale`: al massimo due frasi che dicono cosa stabilisce il manuale. Non raccontare le ricerche fatte.
- `citations`: uno o più passaggi che sostengono il valore. Per ciascuno: `file` (percorso del file come restituito dagli strumenti), `line` (numero di riga del passaggio), `quote` (copia letterale di una porzione di quella riga, al massimo 200 caratteri, senza modifiche).

Regole:

- Cita solo testo che hai effettivamente letto con `Read` o visto in un risultato di `Grep`. Una citazione non letterale viene scartata.
- Se dopo aver provato sinonimi e varianti non trovi nulla, restituisci `found: false`, `reference_value: null`, `reference_unit: null`, `citations: []` e `judgement: unclear`.
- Se due manuali riportano valori diversi, cita entrambi e usa `judgement: unclear`.
````

- [ ] **Step 5: Verificare che i test offline passino**

Run: `uv run pytest tests/test_prompt.py tests/test_sdk_session.py -v`
Expected: 10 passed.

- [ ] **Step 6: Smoke test reale (solo con credenziali Bedrock)**

Prerequisiti: `.env` copiato da `.env.example` con regione e profilo validi, e in `config/settings.yaml` un `model` abilitato nell'account (verificabile con `aws bedrock list-inference-profiles`).

Run: `uv run pytest -m bedrock tests/test_sdk_session_bedrock.py -v`
Expected: 1 passed. Poi aprire `max_egt.jsonl` nella cartella temporanea indicata da pytest e controllare che ogni `Read` abbia `limit ≤ 60`.

Se le credenziali non sono disponibili su questa macchina, saltare questo step e annotarlo nel messaggio di commit: va eseguito sulla macchina aziendale prima di usare la CLI su dati reali.

- [ ] **Step 7: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/agent/prompt.py src/cycle_validation/agent/sdk_session.py prompts tests/test_prompt.py tests/test_sdk_session.py tests/test_sdk_session_bedrock.py
git commit -m "feat: add Claude Agent SDK session adapter and validator prompt"
```

---

### Task 11: Ingest del PDF con PDFium

**Files:**
- Create: `src/cycle_validation/ingest/__init__.py`, `src/cycle_validation/ingest/pdf_to_markdown.py`
- Create: `tests/conftest.py`
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: `IngestError` (Task 1).
- Produces: `ingest.pdf_to_markdown.pdf_to_markdown(pdf_path: Path) -> str`; fixture pytest `make_pdf(pages: list[str], name: str = "ciclo.pdf") -> Path` (una pagina per elemento; stringa vuota = pagina senza testo; solo caratteri latin-1).

Formato dell'output: per ogni pagina un blocco `<!-- pagina N -->`, una riga vuota e il testo della pagina; blocchi separati da una riga vuota; newline finale. Questa prima versione non ricostruisce tabelle e titoli: si decide sul layout dei PDF reali.

- [ ] **Step 1: Scrivere fixture e test che fallisce**

`tests/conftest.py`:

```python
from collections.abc import Callable
from pathlib import Path

import pytest


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(pages: list[str]) -> bytes:
    """PDF minimale con una pagina per elemento. Stringa vuota = pagina senza testo."""
    objects: list[bytes] = []
    kids = " ".join(f"{4 + 2 * index} 0 R" for index in range(len(pages)))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, text in enumerate(pages):
        operators = ["BT", "/F1 12 Tf", "72 720 Td", "14 TL"]
        operators += [f"({_escape(line)}) Tj T*" for line in text.split("\n")]
        operators.append("ET")
        stream = "\n".join(operators).encode("latin-1") if text else b""
        page = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * index} 0 R >>"
        )
        objects.append(page.encode())
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n".encode()
    output += b"0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
    output += (trailer + f"startxref\n{xref_offset}\n%%EOF\n").encode()
    return bytes(output)


@pytest.fixture
def make_pdf(tmp_path: Path) -> Callable[..., Path]:
    def _make(pages: list[str], name: str = "ciclo.pdf") -> Path:
        path = tmp_path / name
        path.write_bytes(build_pdf(pages))
        return path

    return _make
```

`tests/test_ingest.py`:

```python
from collections.abc import Callable
from pathlib import Path

import pytest

from cycle_validation.errors import IngestError
from cycle_validation.ingest.pdf_to_markdown import pdf_to_markdown


def test_extracts_text_with_page_markers(make_pdf: Callable[..., Path]) -> None:
    pdf = make_pdf(["Engine: X1\nMax EGT: 650 C", "Second page"])
    assert pdf_to_markdown(pdf) == (
        "<!-- pagina 1 -->\n\nEngine: X1\nMax EGT: 650 C\n\n<!-- pagina 2 -->\n\nSecond page\n"
    )


def test_output_has_no_carriage_returns(make_pdf: Callable[..., Path]) -> None:
    assert "\r" not in pdf_to_markdown(make_pdf(["Riga uno\nRiga due"]))


def test_pdf_without_text_is_rejected(make_pdf: Callable[..., Path]) -> None:
    with pytest.raises(IngestError, match="testo estraibile"):
        pdf_to_markdown(make_pdf(["", ""]))


def test_invalid_file_is_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    with pytest.raises(IngestError, match="Impossibile aprire"):
        pdf_to_markdown(bad)


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(IngestError, match="Impossibile aprire"):
        pdf_to_markdown(tmp_path / "assente.pdf")
```

- [ ] **Step 2: Verificare che fallisca**

Run: `uv run pytest tests/test_ingest.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'cycle_validation.ingest'`.

- [ ] **Step 3: Implementare**

`src/cycle_validation/ingest/__init__.py`: file vuoto.

`src/cycle_validation/ingest/pdf_to_markdown.py`:

```python
"""Stadio 1: PDF → Markdown con PDFium. Deterministico, nessuna chiamata LLM."""

from pathlib import Path
from typing import Any

import pypdfium2 as pdfium

from cycle_validation.errors import IngestError


def _page_text(document: Any, index: int) -> str:
    page = document[index]
    textpage = page.get_textpage()
    try:
        raw: str = textpage.get_text_bounded()
    finally:
        textpage.close()
        page.close()
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def pdf_to_markdown(pdf_path: Path) -> str:
    """Estrae il testo di ogni pagina, preceduto da un marcatore di pagina."""
    try:
        document = pdfium.PdfDocument(str(pdf_path))
    except (pdfium.PdfiumError, OSError) as exc:
        raise IngestError(f"Impossibile aprire il PDF {pdf_path}: {exc}") from exc
    try:
        pages = [_page_text(document, index) for index in range(len(document))]
    finally:
        document.close()
    if not any(pages):
        raise IngestError(
            f"Il PDF {pdf_path} non contiene testo estraibile (è una scansione?). "
            "L'OCR non è supportato."
        )
    blocks = [f"<!-- pagina {number} -->\n\n{text}" for number, text in enumerate(pages, start=1)]
    return "\n\n".join(blocks) + "\n"
```

- [ ] **Step 4: Verificare che passi**

Run: `uv run pytest tests/test_ingest.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
uv run ruff format . && uv run ruff check .
git add src/cycle_validation/ingest tests/conftest.py tests/test_ingest.py
git commit -m "feat: add PDFium-based PDF to Markdown ingest"
```

---

### Task 12: Pipeline, CLI e documentazione

**Files:**
- Create: `src/cycle_validation/extract/__init__.py`, `src/cycle_validation/extract/base.py`, `src/cycle_validation/extract/json_file.py`
- Create: `src/cycle_validation/pipeline.py`, `src/cycle_validation/cli.py`
- Create: `docs/architecture.md`
- Modify: `README.md` (sostituzione completa)
- Test: `tests/test_extract.py`, `tests/test_pipeline.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: tutto ciò che è stato prodotto nei Task 1–11.
- Produces:
  - `extract.base.FieldExtractor` — Protocol con `extract(self, cycle_markdown: str, fields: list[FieldSpec]) -> list[ExtractedField]`
  - `extract.json_file.PreExtractedFields(path: Path)` — implementa `FieldExtractor` leggendo una lista JSON di `ExtractedField`; ignora gli id non presenti in `fields`
  - `pipeline.RunPaths(root: Path)` con proprietà `cycle_md`, `fields_json`, `sessions_dir`, `report_json`, `report_md`
  - `pipeline.sha256_file(path: Path) -> str`
  - `pipeline.create_run_dir(runs_root: Path, pdf_path: Path, now: datetime) -> RunPaths` — cartella `<YYYYmmdd-HHMMSS>_<nome-pdf>`
  - `async pipeline.run_pipeline(*, pdf_path: Path, settings: Settings, fields: list[FieldSpec], fields_sha256: str, extractor: FieldExtractor, session: FieldSession, runs_root: Path, now: datetime | None = None) -> tuple[Report, RunPaths]`
  - `cli.app` — comandi `ingest PDF [--output FILE]` e `run PDF --fields-json FILE [--config-dir DIR] [--prompt FILE] [--runs-dir DIR]`. Exit code 0 se il report è prodotto, 1 per errore fatale.

- [ ] **Step 1: Scrivere i test che falliscono**

`tests/test_extract.py`:

```python
import json
from pathlib import Path

import pytest

from cycle_validation.errors import PipelineError
from cycle_validation.extract.json_file import PreExtractedFields
from cycle_validation.models import ExtractionStatus, FieldSpec, FieldType

FIELDS = [FieldSpec(id="max_egt", label="EGT massima", type=FieldType.NUMBER)]


def test_reads_fields_and_ignores_unknown_ids(tmp_path: Path) -> None:
    path = tmp_path / "campi.json"
    payload = [
        {"id": "max_egt", "status": "ok", "value": 650, "unit": "°C"},
        {"id": "non_richiesto", "status": "ok", "value": "x"},
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")
    extracted = PreExtractedFields(path).extract("markdown ignorato", FIELDS)
    assert [item.id for item in extracted] == ["max_egt"]
    assert extracted[0].status is ExtractionStatus.OK
    assert extracted[0].value == 650.0


@pytest.mark.parametrize("content", ["{non json", '[{"id": "max_egt"}]', '"una stringa"'])
def test_invalid_content_is_a_pipeline_error(tmp_path: Path, content: str) -> None:
    path = tmp_path / "campi.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(PipelineError, match="campi estratti"):
        PreExtractedFields(path).extract("", FIELDS)


def test_missing_file_is_a_pipeline_error(tmp_path: Path) -> None:
    with pytest.raises(PipelineError, match="campi estratti"):
        PreExtractedFields(tmp_path / "assente.json").extract("", FIELDS)
```

`tests/test_pipeline.py`:

```python
import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cycle_validation.agent.session import SessionOutcome, SessionStatus
from cycle_validation.config import Settings
from cycle_validation.errors import PipelineError
from cycle_validation.models import (
    AgentFinding,
    Citation,
    ExtractedField,
    ExtractionStatus,
    FieldSpec,
    FieldType,
    Judgement,
    Report,
    Rule,
    RuleKind,
    Usage,
    Verdict,
    WarningCode,
)
from cycle_validation.pipeline import run_pipeline

MANUAL_LINE = "La temperatura EGT massima ammessa è 650 °C."
NOW = datetime(2026, 11, 13, 10, 30, tzinfo=UTC)
FIELDS = [
    FieldSpec(
        id="max_egt",
        label="EGT massima",
        type=FieldType.NUMBER,
        unit="°C",
        rule=Rule(kind=RuleKind.TOLERANCE, value=5),
    ),
    FieldSpec(id="engine_model", label="Modello motore", type=FieldType.STRING),
    FieldSpec(id="oil_pressure", label="Pressione olio", type=FieldType.NUMBER),
]
EXTRACTED = [
    ExtractedField(id="max_egt", status=ExtractionStatus.OK, value=652.0, unit="°C"),
    ExtractedField(id="oil_pressure", status=ExtractionStatus.OK, value=40.0),
]


class StubExtractor:
    def __init__(self, items: list[ExtractedField]) -> None:
        self._items = items

    def extract(self, cycle_markdown: str, fields: list[FieldSpec]) -> list[ExtractedField]:
        return self._items


class ScriptedSession:
    def __init__(self, outcomes: dict[str, SessionOutcome]) -> None:
        self._outcomes = outcomes
        self.calls: list[str] = []

    async def run(
        self, spec: FieldSpec, extracted: ExtractedField, transcript_path: Path
    ) -> SessionOutcome:
        self.calls.append(spec.id)
        return self._outcomes[spec.id]


@pytest.fixture
def manuals(tmp_path: Path) -> Path:
    directory = tmp_path / "manuals"
    directory.mkdir()
    (directory / "engine.md").write_text(f"# Limiti\n\n{MANUAL_LINE}\n", encoding="utf-8")
    return directory


def outcomes() -> dict[str, SessionOutcome]:
    finding = AgentFinding(
        field_id="max_egt",
        found=True,
        reference_value="650",
        reference_unit="°C",
        judgement=Judgement.MATCH,
        rationale="Il manuale indica 650 °C.",
        citations=[Citation(file="engine.md", line=3, quote=MANUAL_LINE)],
    )
    return {
        "max_egt": SessionOutcome(
            status=SessionStatus.OK,
            finding=finding,
            usage=Usage(input_tokens=100, output_tokens=20, cost_usd=0.002, turns=3),
        ),
        "oil_pressure": SessionOutcome(
            status=SessionStatus.MAX_TURNS, usage=Usage(input_tokens=20, turns=10)
        ),
    }


def test_full_run_produces_report_and_artifacts(
    make_pdf: Callable[..., Path], manuals: Path, tmp_path: Path
) -> None:
    session = ScriptedSession(outcomes())
    settings = Settings(model="test-model", manuals_dir=manuals, retries=0)

    report, paths = asyncio.run(
        run_pipeline(
            pdf_path=make_pdf(["Max EGT: 652 C"]),
            settings=settings,
            fields=FIELDS,
            fields_sha256="b" * 64,
            extractor=StubExtractor(EXTRACTED),
            session=session,
            runs_root=tmp_path / "runs",
            now=NOW,
        )
    )

    assert [result.field_id for result in report.results] == [
        "max_egt",
        "engine_model",
        "oil_pressure",
    ]
    assert [result.verdict for result in report.results] == [
        Verdict.CORRETTO,
        Verdict.WARNING,
        Verdict.WARNING,
    ]
    assert report.results[1].warning_code is WarningCode.CAMPO_MANCANTE
    assert report.results[2].warning_code is WarningCode.BUDGET_ESAURITO
    assert sorted(session.calls) == ["max_egt", "oil_pressure"]
    assert (report.totals.corretto, report.totals.warning, report.totals.errato) == (1, 2, 0)
    assert report.totals.input_tokens == 120
    assert report.meta.pdf_name == "ciclo.pdf"
    assert report.meta.model == "test-model"
    assert len(report.meta.pdf_sha256) == 64

    assert paths.root == tmp_path / "runs" / "20261113-103000_ciclo"
    assert "Max EGT: 652 C" in paths.cycle_md.read_text(encoding="utf-8")
    assert paths.fields_json.is_file()
    assert paths.sessions_dir.is_dir()
    assert Report.model_validate_json(paths.report_json.read_text(encoding="utf-8")) == report
    assert "EGT massima" in paths.report_md.read_text(encoding="utf-8")


def test_all_fields_decided_by_precheck_never_call_the_agent(
    make_pdf: Callable[..., Path], manuals: Path, tmp_path: Path
) -> None:
    session = ScriptedSession({})
    report, _ = asyncio.run(
        run_pipeline(
            pdf_path=make_pdf(["Max EGT: 652 C"]),
            settings=Settings(model="test-model", manuals_dir=manuals),
            fields=FIELDS,
            fields_sha256="b" * 64,
            extractor=StubExtractor([]),
            session=session,
            runs_root=tmp_path / "runs",
            now=NOW,
        )
    )
    assert session.calls == []
    assert report.totals.warning == 3


@pytest.mark.parametrize("create_empty", [False, True])
def test_missing_or_empty_manuals_dir_is_fatal(
    make_pdf: Callable[..., Path], tmp_path: Path, create_empty: bool
) -> None:
    manuals = tmp_path / "manuals"
    if create_empty:
        manuals.mkdir()
    with pytest.raises(PipelineError, match="manuali"):
        asyncio.run(
            run_pipeline(
                pdf_path=make_pdf(["Max EGT: 652 C"]),
                settings=Settings(model="test-model", manuals_dir=manuals),
                fields=FIELDS,
                fields_sha256="b" * 64,
                extractor=StubExtractor(EXTRACTED),
                session=ScriptedSession({}),
                runs_root=tmp_path / "runs",
                now=NOW,
            )
        )
    assert not (tmp_path / "runs").exists()
```

`tests/test_cli.py`:

```python
from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from cycle_validation.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_ingest_prints_markdown(make_pdf: Callable[..., Path]) -> None:
    result = runner.invoke(app, ["ingest", str(make_pdf(["Max EGT: 650 C"]))])
    assert result.exit_code == 0
    assert "Max EGT: 650 C" in result.output


def test_ingest_writes_output_file(make_pdf: Callable[..., Path], tmp_path: Path) -> None:
    target = tmp_path / "ciclo.md"
    result = runner.invoke(
        app, ["ingest", str(make_pdf(["Max EGT: 650 C"])), "--output", str(target)]
    )
    assert result.exit_code == 0
    assert "Max EGT: 650 C" in target.read_text(encoding="utf-8")


def test_ingest_reports_unreadable_pdf(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    result = runner.invoke(app, ["ingest", str(bad)])
    assert result.exit_code == 1
    assert "Errore" in result.output


def test_run_requires_pre_extracted_fields(make_pdf: Callable[..., Path]) -> None:
    result = runner.invoke(
        app,
        ["run", str(make_pdf(["Max EGT: 650 C"])), "--config-dir", str(REPO_ROOT / "config")],
    )
    assert result.exit_code == 1
    assert "--fields-json" in result.output


def test_run_reports_missing_configuration(make_pdf: Callable[..., Path], tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["run", str(make_pdf(["Max EGT: 650 C"])), "--config-dir", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "Impossibile leggere" in result.output
```

- [ ] **Step 2: Verificare che falliscano**

Run: `uv run pytest tests/test_extract.py tests/test_pipeline.py tests/test_cli.py -v`
Expected: FAIL con `ModuleNotFoundError` per `cycle_validation.extract`, `cycle_validation.pipeline`, `cycle_validation.cli`.

- [ ] **Step 3: Implementare l'estrazione**

`src/cycle_validation/extract/__init__.py`: file vuoto.

`src/cycle_validation/extract/base.py`:

```python
"""Stadio 2: interfaccia dell'estrazione dei campi dal Markdown del ciclo."""

from typing import Protocol

from cycle_validation.models import ExtractedField, FieldSpec


class FieldExtractor(Protocol):
    def extract(self, cycle_markdown: str, fields: list[FieldSpec]) -> list[ExtractedField]:
        """Restituisce i campi trovati. I campi assenti possono essere omessi."""
        ...
```

`src/cycle_validation/extract/json_file.py`:

```python
"""Campi già estratti, letti da un file JSON. Usato finché manca l'estrattore reale."""

import json
from pathlib import Path

from cycle_validation.errors import PipelineError
from cycle_validation.models import ExtractedField, FieldSpec


class PreExtractedFields:
    def __init__(self, path: Path) -> None:
        self._path = path

    def extract(self, cycle_markdown: str, fields: list[FieldSpec]) -> list[ExtractedField]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError("atteso un elenco JSON")
            items = [ExtractedField.model_validate(entry) for entry in raw]
        except (OSError, ValueError) as exc:
            raise PipelineError(
                f"File dei campi estratti non valido ({self._path}): {exc}"
            ) from exc
        known = {field.id for field in fields}
        return [item for item in items if item.id in known]
```

Nota: `json.JSONDecodeError` e `pydantic.ValidationError` sono sottoclassi di `ValueError`.

- [ ] **Step 4: Implementare la pipeline**

`src/cycle_validation/pipeline.py`:

```python
"""Orchestrazione dei sei stadi. Ogni stadio lascia il proprio output nella cartella di run."""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cycle_validation.agent.runner import validate_fields
from cycle_validation.agent.session import FieldSession
from cycle_validation.config import Settings
from cycle_validation.errors import PipelineError
from cycle_validation.extract.base import FieldExtractor
from cycle_validation.ingest.pdf_to_markdown import pdf_to_markdown
from cycle_validation.models import ExtractedField, FieldResult, FieldSpec, Report, RunMeta
from cycle_validation.precheck.checks import precheck
from cycle_validation.report.builder import build_report
from cycle_validation.report.json_writer import write_json
from cycle_validation.report.markdown_writer import write_markdown
from cycle_validation.verdict.decide import result_from_outcome


@dataclass(frozen=True)
class RunPaths:
    root: Path

    @property
    def cycle_md(self) -> Path:
        return self.root / "cycle.md"

    @property
    def fields_json(self) -> Path:
        return self.root / "fields.json"

    @property
    def sessions_dir(self) -> Path:
        return self.root / "sessions"

    @property
    def report_json(self) -> Path:
        return self.root / "report.json"

    @property
    def report_md(self) -> Path:
        return self.root / "report.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_run_dir(runs_root: Path, pdf_path: Path, now: datetime) -> RunPaths:
    root = runs_root / f"{now:%Y%m%d-%H%M%S}_{pdf_path.stem}"
    try:
        root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise PipelineError(f"La cartella di run esiste già: {root}") from exc
    return RunPaths(root=root)


def _require_manuals(manuals_dir: Path) -> None:
    if not manuals_dir.is_dir() or not any(p.is_file() for p in manuals_dir.rglob("*")):
        raise PipelineError(f"Cartella dei manuali assente o vuota: {manuals_dir}")


async def run_pipeline(
    *,
    pdf_path: Path,
    settings: Settings,
    fields: list[FieldSpec],
    fields_sha256: str,
    extractor: FieldExtractor,
    session: FieldSession,
    runs_root: Path,
    now: datetime | None = None,
) -> tuple[Report, RunPaths]:
    started_at = now or datetime.now(UTC)
    clock = time.perf_counter()
    _require_manuals(settings.manuals_dir)

    # Stadio 1: ingest
    markdown = pdf_to_markdown(pdf_path)
    paths = create_run_dir(runs_root, pdf_path, started_at)
    paths.cycle_md.write_text(markdown, encoding="utf-8")

    # Stadio 2: extract
    extracted = {item.id: item for item in extractor.extract(markdown, fields)}
    paths.fields_json.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in extracted.values()],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Stadio 3: precheck
    results: dict[str, FieldResult] = {}
    pending: list[tuple[FieldSpec, ExtractedField]] = []
    for spec in fields:
        item = extracted.get(spec.id)
        decided = precheck(spec, item)
        if decided is not None:
            results[spec.id] = decided
        elif item is not None:
            pending.append((spec, item))

    # Stadio 4: validate
    outcomes = await validate_fields(
        session,
        pending,
        concurrency=settings.concurrency,
        retries=settings.retries,
        sessions_dir=paths.sessions_dir,
    )

    # Stadio 5: verdict
    for spec, item in pending:
        results[spec.id] = result_from_outcome(
            spec,
            item,
            outcomes[spec.id],
            manuals_dir=settings.manuals_dir,
            near_limit_ratio=settings.near_limit_ratio,
        )

    # Stadio 6: report
    meta = RunMeta(
        pdf_name=pdf_path.name,
        pdf_sha256=sha256_file(pdf_path),
        started_at=started_at,
        model=settings.model,
        fields_sha256=fields_sha256,
    )
    report = build_report(
        meta, [results[spec.id] for spec in fields], duration_s=time.perf_counter() - clock
    )
    write_json(report, paths.report_json)
    write_markdown(report, paths.report_md)
    return report, paths
```

- [ ] **Step 5: Implementare la CLI**

`src/cycle_validation/cli.py`:

```python
"""Interfaccia a riga di comando."""

import asyncio
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from dotenv import load_dotenv

from cycle_validation.agent.sdk_session import SdkFieldSession
from cycle_validation.config import load_fields, load_settings
from cycle_validation.errors import ConfigError, CycleValidationError, PipelineError
from cycle_validation.extract.json_file import PreExtractedFields
from cycle_validation.ingest.pdf_to_markdown import pdf_to_markdown
from cycle_validation.pipeline import run_pipeline, sha256_file

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Valida i campi di un ciclo motore contro i manuali tecnici.",
)

PdfArgument = Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="PDF del ciclo.")]


def _fail(error: CycleValidationError) -> NoReturn:
    typer.echo(f"Errore: {error}", err=True)
    raise typer.Exit(code=1)


@app.command()
def ingest(
    pdf: PdfArgument,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="File Markdown di destinazione.")
    ] = None,
) -> None:
    """Converte il PDF del ciclo in Markdown."""
    try:
        markdown = pdf_to_markdown(pdf)
    except CycleValidationError as error:
        _fail(error)
    if output is None:
        typer.echo(markdown)
    else:
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Markdown scritto in {output}")


@app.command()
def run(
    pdf: PdfArgument,
    fields_json: Annotated[
        Path | None,
        typer.Option("--fields-json", help="Campi già estratti (lista JSON di ExtractedField)."),
    ] = None,
    config_dir: Annotated[
        Path, typer.Option("--config-dir", help="Cartella con settings.yaml e fields.yaml.")
    ] = Path("config"),
    prompt_file: Annotated[
        Path, typer.Option("--prompt", help="Prompt di sistema dell'agente.")
    ] = Path("prompts/validator.md"),
    runs_dir: Annotated[Path, typer.Option("--runs-dir", help="Cartella dei run.")] = Path("runs"),
) -> None:
    """Esegue la validazione completa e scrive report.json e report.md."""
    load_dotenv()
    try:
        settings = load_settings(config_dir / "settings.yaml")
        fields_path = config_dir / "fields.yaml"
        fields = load_fields(fields_path)
        if fields_json is None:
            raise PipelineError(
                "Nessun estrattore automatico disponibile: passa i campi già estratti "
                "con --fields-json."
            )
        try:
            system_prompt = prompt_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigError(f"Impossibile leggere il prompt {prompt_file}: {exc}") from exc
        report, paths = asyncio.run(
            run_pipeline(
                pdf_path=pdf,
                settings=settings,
                fields=fields,
                fields_sha256=sha256_file(fields_path),
                extractor=PreExtractedFields(fields_json),
                session=SdkFieldSession(settings, system_prompt),
                runs_root=runs_dir,
            )
        )
    except CycleValidationError as error:
        _fail(error)
    totals = report.totals
    typer.echo(f"Report: {paths.report_md}")
    typer.echo(
        f"CORRETTO {totals.corretto} | WARNING {totals.warning} | ERRATO {totals.errato} | "
        f"costo {totals.cost_usd:.4f} USD | durata {totals.duration_s:.1f} s"
    )
```

- [ ] **Step 6: Verificare che i test passino**

Run: `uv run pytest tests/test_extract.py tests/test_pipeline.py tests/test_cli.py -v`
Expected: 5 + 4 + 5 = 14 passed.

- [ ] **Step 7: Scrivere la documentazione**

`README.md` (sostituisce la versione minima):

````markdown
# Cycle Validation

Valida i campi di un ciclo motore (PDF) contro i manuali tecnici e produce una tabella con esito `CORRETTO`, `WARNING` o `ERRATO` per ogni campo, con motivazione e fonte.

- Design: `docs/superpowers/specs/2026-11-12-cycle-validation-design.md`
- Mappa dei moduli: `docs/architecture.md`

## Requisiti

- Python ≥ 3.12 e [uv](https://docs.astral.sh/uv/)
- Credenziali AWS con accesso a Bedrock e al modello indicato in `config/settings.yaml`

## Installazione

```bash
uv sync
cp .env.example .env    # poi imposta regione e profilo AWS
```

## Dati

- `data/manuals/`: Markdown e JSON dei manuali, prodotti dalla pipeline di ingestion.
- `data/input/`: PDF dei cicli.

`data/`, `runs/` e `.env` sono esclusi da git: contengono materiale aziendale.

## Uso

```bash
# Solo conversione PDF -> Markdown
uv run cycle-validation ingest data/input/ciclo.pdf -o ciclo.md

# Validazione completa
uv run cycle-validation run data/input/ciclo.pdf --fields-json campi.json
```

Finché l'estrattore automatico non è implementato, i campi del ciclo si passano con `--fields-json`: una lista di oggetti con `id`, `status` (`ok` | `missing` | `unparseable`), `value`, `unit`, `raw_text`.

```json
[
  {"id": "max_egt", "status": "ok", "value": 652, "unit": "°C", "raw_text": "652 °C"}
]
```

Ogni run crea `runs/<data-ora>_<nome-pdf>/` con `cycle.md`, `fields.json`, `sessions/<campo>.jsonl`, `report.json` e `report.md`.

## Configurazione

- `config/settings.yaml`: modello, concorrenza, turni massimi, finestra GRASP.
- `config/fields.yaml`: campi da validare, con tipo, unità, regola e parole chiave.
- `prompts/validator.md`: prompt di sistema dell'agente.

## Sviluppo

```bash
uv run pytest                 # suite offline
uv run pytest -m bedrock      # test reali contro Bedrock (a pagamento)
uv run ruff check . && uv run ruff format --check .
uv run mypy
```
````

`docs/architecture.md`:

```markdown
# Architettura

Il design completo è in `docs/superpowers/specs/2026-11-12-cycle-validation-design.md`. Questa pagina mappa gli stadi sui moduli.

| Stadio | Modulo | Input → Output | LLM |
|---|---|---|---|
| 1 ingest | `ingest/pdf_to_markdown.py` | PDF → Markdown (`cycle.md`) | no |
| 2 extract | `extract/base.py` (interfaccia), `extract/json_file.py` | Markdown → `ExtractedField` (`fields.json`) | da decidere |
| 3 precheck | `precheck/checks.py` | `ExtractedField` → `FieldResult` oppure "serve l'agente" | no |
| 4 validate | `agent/runner.py`, `agent/sdk_session.py`, `agent/hooks.py` | campo → `SessionOutcome` (`sessions/*.jsonl`) | sì |
| 5 verdict | `verdict/decide.py`, `verdict/rules.py`, `verdict/citations.py` | `SessionOutcome` → `FieldResult` | no |
| 6 report | `report/builder.py`, `report/json_writer.py`, `report/markdown_writer.py` | `FieldResult` → `report.json`, `report.md` | no |

`pipeline.py` orchestra gli stadi; `cli.py` è l'unico punto d'ingresso.

## Principi

- **L'agente trova, il codice giudica.** L'agente restituisce valore di riferimento e citazione. Confronti numerici, tolleranze e verifica delle citazioni sono codice deterministico.
- **GRASP imposto da hook.** `agent/hooks.py` rifiuta ogni `Read` senza `limit` o con `limit` oltre soglia, e ogni accesso fuori da `manuals_dir`.
- **Una sessione per campo.** Sessioni isolate e in parallelo: un errore resta confinato a una riga, e il contesto di ogni sessione resta piccolo.
- **Un campo che fallisce è un `WARNING`, non un run fallito.** Il run si interrompe solo se non può produrre alcuna riga.
- **L'SDK sta dietro `FieldSession`.** Solo `agent/sdk_session.py` importa `claude_agent_sdk`; tutto il resto si testa offline.

## Estendere

- **Nuovo estrattore:** implementare `FieldExtractor` in `extract/` e sceglierlo in `cli.py`.
- **Nuovo tipo di regola:** aggiungere il valore a `RuleKind`, il confronto in `verdict/rules.py` e il caso in `apply_rule`.
- **Raggruppare più campi per sessione:** `FieldSpec.group` è già nello schema; cambia solo `agent/runner.py`.
```

- [ ] **Step 8: Verifica finale dell'intero progetto**

Run: `uv run ruff format . && uv run ruff check .`
Expected: `All checks passed!`

Run: `uv run mypy`
Expected: `Success: no issues found`. Se mypy segnala errori, correggerli nel codice (non con `# type: ignore` generici) e rilanciare.

Run: `uv run pytest -v`
Expected: tutti i test passano; `tests/test_sdk_session_bedrock.py` risulta deselezionato.

Run: `uv run cycle-validation --help`
Expected: elenca i comandi `ingest` e `run`.

- [ ] **Step 9: Commit**

```bash
git add src/cycle_validation/extract src/cycle_validation/pipeline.py src/cycle_validation/cli.py README.md docs/architecture.md tests/test_extract.py tests/test_pipeline.py tests/test_cli.py
git commit -m "feat: add pipeline orchestration, CLI and documentation"
```

---

## Dopo questo piano

Quando arrivano i PDF di esempio (ingresso e uscita attesa) e la documentazione dell'ingestion dei manuali, il piano successivo copre:

1. `FieldExtractor` reale (a regole se il layout del PDF è stabile, altrimenti LLM con output strutturato) e ricostruzione di tabelle nel Markdown del ciclo.
2. `config/fields.yaml` con i campi reali, regole e parole chiave.
3. Taratura di `prompts/validator.md` sulla struttura reale dei manuali (Markdown e JSON).
4. Golden set con esiti attesi, e misura di accuratezza, costo e tempo per tarare `concurrency`, `max_turns` ed `effort`.
