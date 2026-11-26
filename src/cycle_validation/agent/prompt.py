"""Prompt e schema dell'output per il giudizio su un'operazione."""

import hashlib
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cycle_validation.config import AgentSettings
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.errors import ConfigError
from cycle_validation.kb.documents import numbered_lines
from cycle_validation.kb.port import TaskLocation
from cycle_validation.verdict.citations import Citation

OPERATION_PROMPT_FILE = "operation_check.md"


class Judgement(StrEnum):
    COERENTE = "coerente"
    CONTRADDETTO = "contraddetto"
    NON_VERIFICABILE = "non_verificabile"


class OperationJudgement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    judgement: Judgement
    rationale: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)


def judgement_schema() -> dict[str, Any]:
    """Schema JSON dell'output: chiuso, senza campi opzionali, adatto all'output strutturato."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["judgement", "rationale", "citations"],
        "properties": {
            "judgement": {"type": "string", "enum": [item.value for item in Judgement]},
            "rationale": {"type": "string"},
            "citations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["file", "line", "quote"],
                    "properties": {
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "quote": {"type": "string"},
                    },
                },
            },
        },
    }


class LanguagesVerdict(StrEnum):
    UGUALI = "uguali"
    DIVERSE = "diverse"


class LanguagesJudgement(BaseModel):
    """Le due lingue della descrizione dicono la stessa cosa? (`agent.compare_languages`)"""

    model_config = ConfigDict(extra="ignore")

    languages: LanguagesVerdict
    rationale: str = Field(min_length=1)
    italian_quote: str = ""
    english_quote: str = ""


def languages_schema() -> dict[str, Any]:
    """Schema JSON del confronto tra le due lingue: chiuso, come `judgement_schema`."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["languages", "rationale", "italian_quote", "english_quote"],
        "properties": {
            "languages": {"type": "string", "enum": [item.value for item in LanguagesVerdict]},
            "rationale": {"type": "string"},
            "italian_quote": {"type": "string"},
            "english_quote": {"type": "string"},
        },
    }


LANGUAGES_SYSTEM_PROMPT = (
    "Controlli i cicli di lavorazione per la riparazione di motori aeronautici. La descrizione "
    "di un'operazione è scritta in italiano e in inglese, e le due lingue devono dare "
    "all'operatore le stesse istruzioni. Confronti solo le due lingue tra loro: non hai il "
    "manuale e non ti serve. Rispondi solo con l'output strutturato richiesto."
)


def build_languages_prompt(italian: str, english: str) -> str:
    """La domanda del confronto tra le due lingue (variante `lingue_tra_loro`, 26-11 sera)."""
    return (
        f"## Descrizione in italiano\n\n{italian.strip()}\n\n"
        f"## Descrizione in inglese\n\n{english.strip()}\n\n"
        "## Domanda\n\n"
        "Le due lingue danno all'operatore le stesse istruzioni tecniche? Rispondi `diverse` "
        "solo se una lingua chiede qualcosa di diverso dall'altra, per esempio:\n"
        "- una negazione o un divieto che c'è in una lingua sola («non», «not», «do not», "
        "«never»);\n"
        "- un limite al contrario (minimo e massimo, almeno e al massimo, sopra e sotto);\n"
        "- un materiale, un prodotto, un pezzo, una zona, un attrezzo o una lavorazione "
        "diversi;\n"
        "- un valore, una classe, una quantità o un codice diversi.\n\n"
        "Non sono differenze: una traduzione libera, un ordine diverso delle parole, "
        "abbreviazioni e sinonimi, unità di misura convertite, un riferimento (per esempio "
        "«vedi op. 25») o una nota scritti in una lingua sola, refusi che non cambiano il "
        "senso. Nel dubbio rispondi `uguali`.\n\n"
        "Se rispondi `diverse`, copia in `italian_quote` e in `english_quote` le poche parole "
        "delle due lingue che non coincidono, identiche al testo qui sopra, e scrivi in "
        "`rationale` che cosa cambia. Se rispondi `uguali`, lascia vuote le due citazioni."
    )


def load_prompt(prompts_dir: Path, name: str) -> str:
    path = prompts_dir / name
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ConfigError(f"Prompt non trovato: {path} ({exc})") from exc


def prompt_version(*texts: str) -> str:
    """Impronta dei prompt usati: entra nel report e rende confrontabili i run."""
    digest = hashlib.sha256("\n---\n".join(texts).encode("utf-8"))
    return digest.hexdigest()[:12]


LANGUAGES_NOTE = (
    "La descrizione è la stessa operazione scritta in due lingue. Confronta con il testo di "
    "riferimento **ognuna delle due parti, separatamente**: se anche una sola delle due dice "
    "qualcosa di incompatibile con il testo (un valore diverso, una negazione aggiunta o tolta, "
    "una parola che cambia la lavorazione o il materiale), il giudizio è `contraddetto`: nella "
    "spiegazione scrivi quale lingua e che cosa cambia, e cita la frase del testo che lo "
    "dimostra. Una traduzione con parole diverse ma con lo stesso contenuto tecnico non è una "
    "contraddizione."
)


ITEMS_NOTE = (
    "Prima di giudicare, scomponi la descrizione nei suoi elementi tecnici: la lavorazione, "
    "ogni valore con la sua unità, ogni limite (minimo, massimo, almeno, al massimo), ogni "
    "divieto o negazione, i materiali e gli attrezzi. Per **ognuno** cerca nel testo di "
    "riferimento che cosa dice. Se anche un solo elemento è incompatibile con il testo (un "
    "valore diverso, un limite invertito, un divieto diventato un permesso o il contrario, un "
    "materiale diverso), il giudizio è `contraddetto`: nella spiegazione scrivi quale elemento "
    "e cita la frase che lo dimostra. Un elemento che il testo non nomina non è una "
    "contraddizione."
)


GENERAL_DEFINITIONS_NOTE = (
    "Attenzione alle **definizioni generali** del testo di riferimento, cioè le regole scritte "
    "per tutti i casi (per esempio che cosa si intende per indicazione lineare, o un rapporto "
    "tra lunghezza e larghezza). Un manuale di pratiche standard vale solo dove non ci sono "
    "limiti specifici: il ciclo può prendere i suoi criteri dal manuale d'ispezione del motore o "
    "da una D.R., che valgono di più. Se l'unica differenza tra la descrizione e il testo è un "
    "criterio diverso da una definizione generale, rispondi `non_verificabile` e scrivi nella "
    "spiegazione quale definizione è diversa. Resta `contraddetto` se il testo dà un limite "
    "specifico per questa operazione o per questo pezzo, e se una delle due lingue dice "
    "qualcosa di diverso dall'altra (una negazione, un valore, un materiale)."
)


DR_PROCEDURE_NOTE = (
    "Il ciclo è una **D.R.** (deroga): tra i testi di riferimento c'è la procedura della D.R. "
    "per questo pezzo, che vale più del manuale. Se il manuale vieta, limita o manda a "
    "sostituire qualcosa che la procedura della D.R. autorizza o descrive in altro modo, vale "
    "la procedura della D.R.: non è una contraddizione. Resta `contraddetto` se la descrizione "
    "contraddice la procedura della D.R., o il manuale dove la D.R. non dice niente."
)


def _header(
    cycle: Cycle,
    operation: Operation,
    facts: Sequence[str],
    missing_tasks: Sequence[str],
    languages: tuple[str, str] | None = None,
    itemized: bool = False,
    general_definitions: bool = False,
    dr_procedure: bool = False,
) -> list[str]:
    lines = [
        f"Operazione {operation.operation_number}",
        f"Descrizione nel ciclo: {operation.operation_description}",
    ]
    if languages is not None:
        italian, english = languages
        lines += [f"Parte in italiano: {italian}", f"Parte in inglese: {english}", LANGUAGES_NOTE]
    if itemized:
        lines.append(ITEMS_NOTE)
    if general_definitions:
        lines.append(GENERAL_DEFINITIONS_NOTE)
    if dr_procedure:
        lines.append(DR_PROCEDURE_NOTE)
    if operation.task_codes:
        lines.append(f"Task code citati: {', '.join(operation.task_codes)}")
    if missing_tasks:
        lines.append(
            f"I task code citati ({', '.join(missing_tasks)}) non sono nel manuale. Il testo di "
            "riferimento qui sotto è quello dei task delle fonti del ciclo: giudica la "
            "descrizione su questo testo, la differenza di codice è già segnalata a parte."
        )
    if cycle.engine_model:
        lines.append(f"Motore: {cycle.engine_model}")
    if facts:
        lines.append("Fatti già verificati dal codice (non vanno cercati):")
        lines.extend(f"- {fact}" for fact in facts)
    return lines


SECOND_SEARCH_NOTE = (
    "Una prima verifica, solo sul testo del task citato dall'operazione, non ha trovato il "
    "passo che parla di questa operazione. Qui hai **tutti i documenti citati dal ciclo**: "
    "cerca con Grep le parole chiave della descrizione (la lavorazione, i valori con la loro "
    "unità, i materiali, gli attrezzi; in inglese, se il documento è in inglese) e giudica sul "
    "passo che trovi. Se nemmeno così trovi un passo che ne parli, rispondi `non_verificabile`."
)


def _where(location: TaskLocation) -> str:
    label = f"task {location.task}" if location.task else "documento intero"
    return f"{location.document.path} ({label}, righe {location.line_start}-{location.line_end})"


def build_operation_prompt(
    cycle: Cycle,
    operation: Operation,
    facts: Sequence[str],
    locations: Sequence[TaskLocation],
    *,
    inline: bool,
    settings: AgentSettings,
    missing_tasks: Sequence[str] = (),
    languages: tuple[str, str] | None = None,
    second_search: bool = False,
    dr_procedure: bool = False,
) -> str:
    """`languages`: le due parti della descrizione, se vanno giudicate separatamente
    (`AgentSettings.separate_languages`). `second_search`: è la seconda ricerca, nei documenti
    interi, dopo un primo giudizio «non verificabile» (`AgentSettings.search_when_unverifiable`).
    `dr_procedure`: tra i testi c'è la procedura della D.R. insieme ai task
    (`AgentSettings.dr_procedure_always`)."""
    lines = _header(
        cycle,
        operation,
        facts,
        missing_tasks,
        languages,
        itemized=settings.itemized_check,
        general_definitions=settings.general_definitions_note,
        dr_procedure=dr_procedure,
    )
    if second_search:
        lines.append(SECOND_SEARCH_NOTE)
    lines.append("")
    if inline:
        lines.append("Testo di riferimento, con il numero di riga di ciascun file:")
        for location in locations:
            lines.append("")
            lines.append(f"File: {_where(location)}")
            lines.extend(
                numbered_lines(location.document.path, location.line_start, location.line_end)
            )
        lines.append("")
        lines.append("Non hai tool: giudica sul testo qui sopra.")
    else:
        lines.append("Documenti di riferimento, da consultare con Grep e Read:")
        lines.extend(f"- {_where(location)}" for location in locations)
        lines.append("")
        lines.append(
            "Cerca con Grep (path = file), poi leggi con Read solo il paragrafo: "
            f"offset = riga del match - {settings.read_before}, limit = {settings.read_window}."
        )
    lines.append("Nelle citazioni usa il percorso del file così come è scritto qui.")
    return "\n".join(lines)
