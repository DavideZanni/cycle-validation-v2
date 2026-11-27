"""Esito di un controllo: cosa è stato verificato, con quale risultato e su quale prova."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cycle_validation.domain.cycle import Operation, Source


class Verdict(StrEnum):
    CORRETTO = "CORRETTO"
    WARNING = "WARNING"
    ERRATO = "ERRATO"
    NON_APPLICABILE = "NON_APPLICABILE"


class Reason(StrEnum):
    VERIFICATO = "VERIFICATO"

    CONTRADDIZIONE = "CONTRADDIZIONE"
    MACCHINA_NON_ATTIVA = "MACCHINA_NON_ATTIVA"
    DR_NON_APPLICABILE = "DR_NON_APPLICABILE"
    DR_NESSUNA_CORRISPONDENZA = "DR_NESSUNA_CORRISPONDENZA"
    # codice completo che non compare nel manuale, che ha i task della stessa famiglia
    TASK_INESISTENTE = "TASK_INESISTENTE"
    # la descrizione italiana e quella inglese dicono numeri diversi
    INCOERENZA_LINGUE = "INCOERENZA_LINGUE"
    # il task accanto all'operazione è della stessa famiglia di quello della testata, ma
    # diverso (H17, 27-11 sera): la stampa si contraddice
    TASK_DIVERSO_DALLA_TESTATA = "TASK_DIVERSO_DALLA_TESTATA"
    # la stessa operazione ha targhe diverse su pagine diverse (H19, 27-11 sera)
    MACCHINE_DIVERSE = "MACCHINE_DIVERSE"
    # la scheda è di un'altra famiglia di motore (H18, `sheet_consistency`)
    SCHEDA_ALTRO_MOTORE = "SCHEDA_ALTRO_MOTORE"
    # il materiale del trattamento della scheda non è quello della descrizione (H18)
    SCHEDA_MATERIALE_DIVERSO = "SCHEDA_MATERIALE_DIVERSO"
    # la scheda non è nell'indice, che ha altre schede con lo stesso prefisso (H18)
    SCHEDA_INESISTENTE = "SCHEDA_INESISTENTE"

    EVIDENZA_NON_TROVATA = "EVIDENZA_NON_TROVATA"
    FONTE_ASSENTE = "FONTE_ASSENTE"
    TARGA_SCONOSCIUTA = "TARGA_SCONOSCIUTA"
    VERSIONE_DIVERSA = "VERSIONE_DIVERSA"
    PUBBLICAZIONE_PARZIALE = "PUBBLICAZIONE_PARZIALE"
    DATO_INCERTO = "DATO_INCERTO"
    RIFERIMENTO_AMBIGUO = "RIFERIMENTO_AMBIGUO"
    CITAZIONE_NON_VERIFICATA = "CITAZIONE_NON_VERIFICATA"
    # una contraddizione che le verifiche di conferma non hanno ritrovato
    GIUDIZIO_INSTABILE = "GIUDIZIO_INSTABILE"
    # DR senza serial number, o senza la condition che serve a scegliere: gli altri controlli
    # proseguono, la recommendation va guardata a mano
    DR_NON_VERIFICATA = "DR_NON_VERIFICATA"
    ESTRAZIONE_NON_CONFERMATA = "ESTRAZIONE_NON_CONFERMATA"
    # operazione di processo speciale senza scheda: scheda mancante, un avviso e mai un errore
    # (P6, 27-11; regola confermata dall'utente il 27-11 sera)
    SCHEDA_FORSE_MANCANTE = "SCHEDA_FORSE_MANCANTE"
    BUDGET_ESAURITO = "BUDGET_ESAURITO"
    ERRORE_TECNICO = "ERRORE_TECNICO"
    BLOCCATO_A_MONTE = "BLOCCATO_A_MONTE"

    CAMPO_ASSENTE = "CAMPO_ASSENTE"
    ESCLUSO_DA_REGOLA = "ESCLUSO_DA_REGOLA"
    NON_VERIFICATO_PER_PROFILO = "NON_VERIFICATO_PER_PROFILO"
    # il controllo è spento per configurazione (registro delle macchine non collegato sul PC)
    CONTROLLO_SPENTO = "CONTROLLO_SPENTO"
    # il testo di riferimento non tratta il tipo di operazione: niente da confrontare (I16)
    FUORI_TEMA = "FUORI_TEMA"


_ERRATO = (
    Reason.CONTRADDIZIONE,
    Reason.MACCHINA_NON_ATTIVA,
    Reason.DR_NON_APPLICABILE,
    Reason.DR_NESSUNA_CORRISPONDENZA,
    Reason.TASK_INESISTENTE,
    Reason.INCOERENZA_LINGUE,
    Reason.TASK_DIVERSO_DALLA_TESTATA,
    Reason.MACCHINE_DIVERSE,
    Reason.SCHEDA_ALTRO_MOTORE,
    Reason.SCHEDA_MATERIALE_DIVERSO,
    Reason.SCHEDA_INESISTENTE,
)
_NON_APPLICABILE = (
    Reason.CAMPO_ASSENTE,
    Reason.ESCLUSO_DA_REGOLA,
    Reason.NON_VERIFICATO_PER_PROFILO,
    Reason.CONTROLLO_SPENTO,
    Reason.FUORI_TEMA,
)


def _verdict_of(reason: Reason) -> Verdict:
    if reason is Reason.VERIFICATO:
        return Verdict.CORRETTO
    if reason in _ERRATO:
        return Verdict.ERRATO
    if reason in _NON_APPLICABILE:
        return Verdict.NON_APPLICABILE
    return Verdict.WARNING


REASON_VERDICT: dict[Reason, Verdict] = {reason: _verdict_of(reason) for reason in Reason}


class WarningKind(StrEnum):
    """Due tipi di WARNING (H15, 27-11 sera). «Da guardare»: un dubbio vero, che una persona
    deve guardare (citazione non ritrovata, giudizio instabile, scheda mancante, dato
    incerto). «Non controllabile»: il programma non ha potuto controllare (manca il documento,
    il testo non ne parla, errore tecnico). Non cambia l'esito: cambia come si mostra."""

    DA_GUARDARE = "da_guardare"
    NON_CONTROLLABILE = "non_controllabile"


_NOT_CHECKABLE = (
    Reason.FONTE_ASSENTE,
    Reason.EVIDENZA_NON_TROVATA,
    Reason.PUBBLICAZIONE_PARZIALE,
    Reason.DR_NON_VERIFICATA,
    Reason.BUDGET_ESAURITO,
    Reason.ERRORE_TECNICO,
)


def warning_kind(reason: Reason) -> WarningKind | None:
    """Il tipo di WARNING del motivo; None se il motivo non dà un WARNING."""
    if REASON_VERDICT[reason] is not Verdict.WARNING:
        return None
    return WarningKind.NON_CONTROLLABILE if reason in _NOT_CHECKABLE else WarningKind.DA_GUARDARE


class CheckName(StrEnum):
    EXTRACTION_INTEGRITY = "extraction_integrity"
    DR_RECOMMENDATION = "dr_recommendation"
    SOURCE = "source"
    TASK_CODE = "task_code"
    MACHINE_TAG = "machine_tag"
    PROCESS_SHEET = "process_sheet"
    OPERATION_DESCRIPTION = "operation_description"


class TargetKind(StrEnum):
    CYCLE = "cycle"
    SOURCE = "source"
    OPERATION = "operation"


class Target(BaseModel):
    """A cosa si riferisce un esito: il ciclo, la fonte n, l'operazione n."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: TargetKind
    index: int | None = None
    label: str = ""

    @classmethod
    def cycle(cls) -> Self:
        return cls(kind=TargetKind.CYCLE, label="ciclo")

    @classmethod
    def source(cls, index: int, source: Source) -> Self:
        label = source.manual if source.task is None else f"{source.manual} / {source.task}"
        return cls(kind=TargetKind.SOURCE, index=index, label=label)

    @classmethod
    def operation(cls, index: int, operation: Operation) -> Self:
        return cls(kind=TargetKind.OPERATION, index=index, label=operation.operation_number)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_key: str
    version: str | None = None
    page: int | None = None
    line: int | None = None
    quote: str = ""


class Usage(BaseModel):
    """Consumi delle sessioni dell'agente. Zero per i controlli decisi dal codice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    # Tempo del modello (API) e durata reale della sessione, avvio del processo compreso:
    # la differenza è il costo fisso dell'agente.
    api_duration_ms: int = 0
    wall_ms: int = 0
    turns: int = 0
    sessions: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
            duration_ms=self.duration_ms + other.duration_ms,
            api_duration_ms=self.api_duration_ms + other.api_duration_ms,
            wall_ms=self.wall_ms + other.wall_ms,
            turns=self.turns + other.turns,
            sessions=self.sessions + other.sessions,
        )


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    check: CheckName
    target: Target
    verdict: Verdict
    reason: Reason
    rationale: str
    evidence: tuple[Evidence, ...] = ()
    decided_by: Literal["code", "agent"] = "code"
    usage: Usage = Field(default_factory=Usage)

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        if REASON_VERDICT[self.reason] is not self.verdict:
            raise ValueError(f"Il motivo {self.reason} non appartiene all'esito {self.verdict}.")
        needs_proof = self.verdict in (Verdict.CORRETTO, Verdict.ERRATO)
        if self.decided_by == "agent" and needs_proof and not self.evidence:
            raise ValueError(
                f"Un esito {self.verdict} deciso dall'agente richiede una citazione verificata."
            )
        return self
