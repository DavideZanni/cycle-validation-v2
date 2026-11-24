"""Variante di un esperimento: un file YAML che eredita da un'altra variante e cambia poche chiavi.

```yaml
nome: effort_low
descrizione: meno ragionamento del modello
ipotesi: il ragionamento lungo non serve a confrontare due testi brevi
atteso: stessi errori stabili, costo per ciclo più basso
base: baseline
agent:
  effort: low
```

`descrizione` (cosa cambia), `ipotesi` (perché dovrebbe migliorare) e `atteso` (cosa deve
cambiare nei numeri) sono la proposta: il report della prova li riporta accanto ai risultati.

La radice della catena (senza `base`) indica il file di impostazioni di partenza (`config`).
Le sezioni `agent`, `paths` e `module_check` si fondono ricorsivamente su quelle impostazioni.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cycle_validation.config import Settings, load_settings
from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.faults import Faults

DEFAULT_CONFIG = Path("config/settings.yaml")
# Implementazioni di AgentSession che una variante può scegliere per nome.
SESSIONS = ("sdk",)


class VariantFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=1)
    descrizione: str = ""
    ipotesi: str = ""
    atteso: str = ""
    base: str | None = None
    config: Path | None = None
    sessione: str | None = None
    # Guasti simulati (vedi `evaluation/faults.py`): la prova verifica la robustezza.
    guasti: Faults | None = None
    agent: dict[str, Any] = Field(default_factory=dict)
    paths: dict[str, Any] = Field(default_factory=dict)
    module_check: dict[str, Any] = Field(default_factory=dict)

    def overrides(self) -> dict[str, Any]:
        sections = {"agent": self.agent, "paths": self.paths, "module_check": self.module_check}
        return {key: value for key, value in sections.items() if value}


@dataclass(frozen=True)
class Variant:
    name: str
    description: str
    path: Path
    settings: Settings
    session: str
    # Nomi dalla radice alla variante stessa.
    chain: list[str]
    faults: Faults | None = None
    hypothesis: str = ""
    expected: str = ""


def _merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read(path: Path) -> VariantFile:
    if not path.is_file():
        raise ConfigError(f"Variante non trovata: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        variant = VariantFile.model_validate(raw)
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML non valido in {path}: {exc}") from exc
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in item['loc']) or '(radice)'}: {item['msg']}"
            for item in exc.errors()
        )
        raise ConfigError(f"Variante non valida in {path}: {problems}") from exc
    if variant.nome != path.stem:
        raise ConfigError(f"{path}: il nome '{variant.nome}' deve coincidere con il file.")
    if variant.base is not None and variant.config is not None:
        raise ConfigError(
            f"{path}: 'config' vale solo nella variante radice (senza 'base'); qui eredita."
        )
    if variant.sessione is not None and variant.sessione not in SESSIONS:
        raise ConfigError(
            f"{path}: sessione '{variant.sessione}' sconosciuta. Disponibili: {', '.join(SESSIONS)}."
        )
    return variant


def _chain(path: Path) -> list[VariantFile]:
    """Dalla radice alla variante richiesta."""
    chain: list[VariantFile] = []
    seen: list[str] = []
    current: Path | None = path
    while current is not None:
        variant = _read(current)
        if variant.nome in seen:
            raise ConfigError(f"Ereditarietà a ciclo: {' -> '.join([*seen, variant.nome])}.")
        seen.append(variant.nome)
        chain.insert(0, variant)
        current = None if variant.base is None else path.parent / f"{variant.base}.yaml"
    return chain


def load_variant(
    path: Path, *, config_override: Path | None = None, project_root: Path | None = None
) -> Variant:
    """`config_override` sostituisce il file di impostazioni della radice; `project_root` è la
    cartella da cui si risolve un `config` relativo (predefinita: quella corrente)."""
    chain = _chain(path)
    root = chain[0]
    if config_override is not None:
        config: Path | None = config_override
    else:
        config = root.config or DEFAULT_CONFIG
        if not config.is_absolute() and project_root is not None:
            config = project_root / config
    data = load_settings(config).model_dump()
    session = "sdk"
    faults: Faults | None = None
    for variant in chain:
        data = _merge(data, variant.overrides())
        session = variant.sessione or session
        faults = variant.guasti or faults
    try:
        settings = Settings.model_validate(data)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in item['loc'])}: {item['msg']}" for item in exc.errors()
        )
        raise ConfigError(f"Impostazioni non valide nella variante {path}: {problems}") from exc
    last = chain[-1]
    return Variant(
        name=last.nome,
        description=last.descrizione,
        path=path,
        settings=settings,
        session=session,
        chain=[item.nome for item in chain],
        faults=faults,
        hypothesis=last.ipotesi,
        expected=last.atteso,
    )
