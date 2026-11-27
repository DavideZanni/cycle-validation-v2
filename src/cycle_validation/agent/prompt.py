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
    # solo con `agent.out_of_scope` (I16): il testo non tratta il tipo di operazione
    FUORI_TEMA = "fuori_tema"


class OperationJudgement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    judgement: Judgement
    rationale: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)


def judgement_schema(out_of_scope: bool = False) -> dict[str, Any]:
    """Schema JSON dell'output: chiuso, senza campi opzionali, adatto all'output strutturato.
    `fuori_tema` si può rispondere solo con `out_of_scope` (`agent.out_of_scope`, I16)."""
    allowed = [item.value for item in Judgement if out_of_scope or item is not Judgement.FUORI_TEMA]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["judgement", "rationale", "citations"],
        "properties": {
            "judgement": {"type": "string", "enum": allowed},
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
    # solo nella versione stretta (`agent.compare_languages_strict`)
    kind: str = ""


# Tipi di differenza della versione stretta: solo questi possono diventare ERRATO.
STRICT_KINDS = ("negazione", "limite", "nessuna")


def languages_schema(strict: bool = False) -> dict[str, Any]:
    """Schema JSON del confronto tra le due lingue: chiuso, come `judgement_schema`. Nella
    versione stretta anche il tipo della differenza."""
    schema: dict[str, Any] = {
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
    if strict:
        schema["required"].append("kind")
        schema["properties"]["kind"] = {"type": "string", "enum": list(STRICT_KINDS)}
    return schema


LANGUAGES_SYSTEM_PROMPT = (
    "Controlli i cicli di lavorazione per la riparazione di motori aeronautici. La descrizione "
    "di un'operazione è scritta in italiano e in inglese, e le due lingue devono dare "
    "all'operatore le stesse istruzioni. Confronti solo le due lingue tra loro: non hai il "
    "manuale e non ti serve. Rispondi solo con l'output strutturato richiesto."
)


def build_strict_languages_prompt(italian: str, english: str) -> str:
    """La domanda della versione stretta (variante `lingue_stretta`, 27-11): solo negazioni e
    limiti al contrario. Le parole copiate devono contenere la negazione o i due limiti: il
    codice li ritrova lì (`checks/languages.strict_difference`)."""
    return (
        f"## Descrizione in italiano\n\n{italian.strip()}\n\n"
        f"## Descrizione in inglese\n\n{english.strip()}\n\n"
        "## Domanda\n\n"
        "Una delle due lingue dice all'operatore il **contrario** dell'altra? Cerca solo due "
        "cose:\n"
        "- `negazione`: una negazione o un divieto che c'è in una lingua sola («non», «mai», "
        "«vietato», «not», «never», «do not»), che cambia quello che l'operatore deve fare;\n"
        "- `limite`: un limite al contrario (minimo in una lingua e massimo nell'altra, "
        "«almeno» e «al massimo», «superiore a» e «not to exceed», sopra e sotto).\n\n"
        "Tutto il resto **non** è una differenza da segnalare: traduzioni libere, titoli e "
        "nomi delle operazioni detti in modo diverso, una lingua più dettagliata dell'altra, "
        "frasi o note in una lingua sola, sinonimi, un nome generico e uno specifico dello "
        "stesso materiale o attrezzo, codici scritti con o senza lettere davanti, numeri e "
        "unità di misura (li controlla già il programma). Nel dubbio rispondi `uguali` e "
        "`nessuna`.\n\n"
        "Se rispondi `diverse`, scrivi in `kind` il tipo (`negazione` o `limite`) e copia in "
        "`italian_quote` e in `english_quote` le poche parole delle due lingue che non "
        "coincidono, identiche al testo qui sopra e **con** la parola della negazione o del "
        "limite. Scrivi in `rationale` che cosa cambia per l'operatore. Se rispondi `uguali`, "
        "`kind` è `nessuna` e le due citazioni restano vuote."
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


INSPECTION_NOTE = (
    "Tra i testi di riferimento c'è la **sezione d'ispezione del manuale del motore** (titolo "
    "con INSPECTION). Per i criteri d'ispezione (che cosa è un'indicazione, i limiti, i "
    "rapporti tra lunghezza e larghezza, le zone) vale questa: le definizioni generali di un "
    "manuale di pratiche standard valgono solo dove il manuale del motore non dice niente. "
    "Resta `contraddetto` se la descrizione contraddice la sezione d'ispezione, o se una delle "
    "due lingue dice qualcosa di diverso dall'altra."
)


BOUNDARY_NOTE = (
    "Un limite scritto con «almeno N» (at least N) in un punto e con «più di N» (more than N) "
    "in un altro, cioè una differenza **solo sul caso uguale a N**, non è una contraddizione: "
    "giudica gli altri elementi come se dicessero la stessa cosa. Resta `contraddetto` se il "
    "numero è diverso o se il limite è al contrario (almeno contro al massimo, più di contro "
    "meno di)."
)


OUT_OF_SCOPE_NOTE = (
    "Se il testo di riferimento **non tratta affatto il tipo di operazione** descritto (per "
    "esempio la descrizione è una presa in carico, una movimentazione, un versamento, una "
    "preservazione o la compilazione di documenti, e il testo parla di una lavorazione o di "
    "un'ispezione), rispondi `fuori_tema`: non c'è niente da confrontare. Nella spiegazione "
    "scrivi di che cosa parla il testo. Usa invece `non_verificabile` se il testo parla della "
    "stessa lavorazione o della stessa ispezione ma non basta per decidere un elemento. Mai "
    "`fuori_tema` se il testo dice qualcosa di incompatibile con la descrizione."
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
    inspection: bool = False,
    out_of_scope: bool = False,
    boundary: bool = False,
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
    if inspection:
        lines.append(INSPECTION_NOTE)
    if out_of_scope:
        lines.append(OUT_OF_SCOPE_NOTE)
    if boundary:
        lines.append(BOUNDARY_NOTE)
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
    inspection: bool = False,
) -> str:
    """`languages`: le due parti della descrizione, se vanno giudicate separatamente
    (`AgentSettings.separate_languages`). `second_search`: è la seconda ricerca, nei documenti
    interi, dopo un primo giudizio «non verificabile» (`AgentSettings.search_when_unverifiable`).
    `dr_procedure`: tra i testi c'è la procedura della D.R. insieme ai task
    (`AgentSettings.dr_procedure_always`). `inspection`: tra i testi c'è la sezione d'ispezione
    del manuale del motore (`AgentSettings.inspection_source`)."""
    lines = _header(
        cycle,
        operation,
        facts,
        missing_tasks,
        languages,
        itemized=settings.itemized_check,
        general_definitions=settings.general_definitions_note,
        dr_procedure=dr_procedure,
        inspection=inspection,
        out_of_scope=settings.out_of_scope,
        boundary=settings.boundary_limits_note,
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
