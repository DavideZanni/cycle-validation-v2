"""Errori del dominio. Ogni errore porta un messaggio leggibile da chi usa lo strumento."""


class CycleValidationError(Exception):
    """Base di tutti gli errori previsti."""


class ConfigError(CycleValidationError):
    """Configurazione assente o non valida."""


class IngestError(CycleValidationError):
    """Il file caricato non è un PDF utilizzabile."""

    def __init__(self, message: str, http_status: int = 422) -> None:
        super().__init__(message)
        self.http_status = http_status


class WrongModuleError(IngestError):
    """Il file caricato è un ciclo di tipo diverso da quello scelto (MOS, DR, militare)."""


class ExtractionError(CycleValidationError):
    """Il ciclo non è stato estratto o non contiene operazioni."""


class KnowledgeError(CycleValidationError):
    """La knowledge base non è caricabile: il run non può partire."""


class SourceUnavailableError(CycleValidationError):
    """Una sorgente non risponde durante un controllo: l'esito diventa un warning."""


class SelectionError(CycleValidationError):
    """La scelta iniziale (civile o militare, MOS o DR) è mancante o incoerente."""


class ProfileUnavailableError(CycleValidationError):
    """Il profilo richiesto esiste ma non è ancora attivo."""
