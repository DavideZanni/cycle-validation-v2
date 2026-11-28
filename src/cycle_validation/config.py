"""Impostazioni e profili, validati al caricamento con messaggi che dicono cosa correggere."""

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from cycle_validation.domain.check import CheckName
from cycle_validation.errors import ConfigError


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentSettings(_Strict):
    """Sessioni dell'agente. `model` è un alias o l'id completo del profilo di inferenza."""

    model: str = "haiku"
    # Ragionamento dei controlli. None = predefinito del modello. low: circa -30% di costo a
    # parità di esiti sui casi di prova (MIGLIORIE B2, da confermare su Bedrock).
    effort: Literal["low", "medium", "high"] | None = "low"
    # Ragionamento per la lettura del PDF. None = come `effort`. high: con low la lettura era
    # peggiore.
    extraction_effort: Literal["low", "medium", "high"] | None = "high"
    use_bedrock: bool = True
    aws_region: str | None = None
    # Modello Bedrock che trascrive immagini e PDF senza testo. None = disattivato.
    transcribe_model: str | None = None
    # Pagine scansionate mandate insieme al trascrittore (MIGLIORIE B3). Il limite vero sono le
    # quote Bedrock: con molti utenti insieme le chiamate sono API_MAX_WORKERS per questo.
    transcribe_concurrency: int = Field(default=4, ge=1, le=16)
    max_turns: int = Field(default=10, ge=1, le=50)
    inline_max_turns: int = Field(default=3, ge=1, le=10)
    extraction_max_turns: int = Field(default=3, ge=1, le=10)
    concurrency: int = Field(default=6, ge=1, le=32)
    retries: int = Field(default=2, ge=0, le=5)
    retry_backoff_s: float = Field(default=2.0, ge=0)
    invalid_output_retries: int = Field(default=1, ge=0, le=3)
    # Tempo massimo di una sessione dei controlli e della lettura del PDF (MIGLIORIE A4).
    # Oltre, WARNING per errore tecnico invece di un'attesa senza fine. None = nessun limite.
    session_timeout_s: float | None = Field(default=90, gt=0, le=600)
    extraction_timeout_s: float | None = Field(default=300, gt=0, le=1800)
    read_limit: int = Field(default=40, ge=5, le=200)
    read_window: int = Field(default=30, ge=5, le=200)
    read_before: int = Field(default=15, ge=0, le=100)
    grep_max_context: int = Field(default=10, ge=0, le=50)
    inline_max_lines: int = Field(default=150, ge=0, le=2000)
    citation_window: int = Field(default=3, ge=0, le=20)
    # Dire al modello che i task citati non sono nel manuale e che il testo è quello delle
    # fonti del ciclo (MIGLIORIE A2). Vale solo con `skip_missing_task` spento: variante
    # `prompt_task_mancante`.
    missing_task_note: bool = False
    # Task citato che il manuale non ha: WARNING subito, senza chiamare il modello (MIGLIORIE
    # B6, scelta il 20-11-2026 al posto di A2). Una sessione in meno.
    skip_missing_task: bool = True
    # Descrizione in due lingue: il modello confronta con il testo di riferimento l'italiano e
    # l'inglese separatamente; se una sola delle due dice altro, è una contraddizione. Variante
    # `lingue_separate` (24-11-2026): la base, spenta, mancava 18 negazioni tolte su 21.
    # Accesa nella base il 26-11-2026 insieme a `itemized_check` (variante `elementi_e_lingue`:
    # 19 errori stabili contro 17 e mai visti 3 contro 1 sul piccolo, 3 prove, 0 falsi errori,
    # +15% di costo). Il valore predefinito vale anche per `data/settings.yaml` sul PC.
    separate_languages: bool = True
    # Prima di giudicare il modello scompone la descrizione in elementi tecnici (lavorazione,
    # valori, limiti, divieti, materiali) e li controlla uno per uno. Variante
    # `elementi_uno_per_uno` (24-11-2026); accesa nella base il 26-11-2026 (vedi sopra).
    itemized_check: bool = True
    # Se il primo giudizio è «non verificabile» (WARNING EVIDENZA_NON_TROVATA), una seconda
    # sessione cerca con Grep e Read in tutti i documenti citati dal ciclo, non solo nel task
    # dell'operazione. Variante `seconda_ricerca` (25-11-2026): i due errori noti sempre
    # mancati uscivano in tutte le 36 prove del 24-11 con EVIDENZA_NON_TROVATA. Costa solo
    # sulle operazioni non verificabili.
    search_when_unverifiable: bool = False
    # Le definizioni generali di un manuale di pratiche standard (per esempio «indicazione
    # lineare = lunghezza almeno 3 volte la larghezza») valgono solo dove non ci sono limiti
    # specifici: se l'unica differenza è con una di queste, `non_verificabile` (WARNING) e non
    # `contraddetto`. Variante `definizioni_generali` (26-11-2026): «4 volte» del manuale del
    # motore contro «3 volte» dell'SPM dava un falso errore sulla stampa giusta (P7) e su un
    # ciclo vero, e ERRATO giusti ma per il motivo sbagliato.
    general_definitions_note: bool = False
    # Il modello confronta la parte italiana e quella inglese della descrizione **tra loro**,
    # senza manuale: una negazione, un limite, un materiale o un valore diversi tra le due lingue
    # sono un ERRATO INCOERENZA_LINGUE (citazioni ritrovate nel testo, conferma come gli altri
    # ERRATO). Vale anche dove il manuale manca. Variante `lingue_tra_loro` (26-11-2026 sera):
    # negazioni tolte in una lingua mancate con EVIDENZA_NON_TROVATA o FONTE_ASSENTE. Costa una
    # sessione corta per ogni operazione scritta in due lingue. Nella base dal 27-11-2026 sera,
    # solo nella versione stretta (campagna finale: `finale` vince, P12: i 3 ERRATO in più sui
    # cicli veri sono errori veri della stampa).
    compare_languages: bool = True
    # Con `compare_languages`: la versione stretta (I15, 27-11-2026). Il modello segnala solo
    # una negazione in una lingua sola o un limite al contrario, e il codice lo ritrova nelle
    # parole copiate (una negazione in una citazione sola; due limiti di verso opposto). Nasce
    # dalla campagna del 26-27-11: `lingue_tra_loro` trovava 10 errori in più ma prendeva per
    # errore le traduzioni libere (11-13 falsi errori a prova). Variante `lingue_stretta`. Nella
    # base dal 27-11-2026 sera (dentro `finale`).
    compare_languages_strict: bool = True
    # Nei cicli DR la procedura della D.R. (la deroga, documenti DR_PROC delle recommendation
    # applicabili) va al modello **insieme** ai task trovati, con una nota: per quel pezzo vale
    # più del manuale. Oggi arriva solo se nessun task si trova. Variante `procedura_dr`
    # (26-11-2026 sera): ERRATO su 895167b9 005 falso (il manuale manda a sostituire, la deroga
    # citata nella 005 autorizza la raccordatura) e il «4 volte» di 2d724fba 050 che viene dalla
    # D.R. (Copilot). Nella base dal 27-11-2026 (campagna del 26-27-11: toglie il falso errore di
    # 895167b9 005, 0 falsi errori, stessi errori stabili; quelli che perde erano trovati per il
    # motivo sbagliato, «il manuale vieta la raccordatura»).
    dr_procedure_always: bool = True
    # Un'operazione di processo speciale (lubrificante secco, rivestimenti, attacco chimico,
    # liquidi penetranti) senza scheda: WARNING SCHEDA_FORSE_MANCANTE, mai ERRATO. Le altre
    # operazioni senza scheda restano N/A. P6, decisa il 26-11-2026; nella base dal 27-11 (dà
    # solo WARNING, non cambia gli errori trovati). MIGLIORIE I9.
    special_process_sheet: bool = True
    # Nelle operazioni d'ispezione (FPI, controllo visivo...) al modello va anche la sezione
    # INSPECTION del manuale del motore citato dalle fonti del ciclo, con una nota: per i
    # criteri d'ispezione vale quella, non le definizioni generali dell'SPM. P7 e P8 (26-11):
    # la stampa giusta 04ecaabe op. 050 e il ciclo vero 2d724fba dicono «4 volte» come il
    # manuale del motore, la v2 confrontava con il «3 volte» generico dell'SPM e dava ERRATO.
    # Variante `fonte_ispezione` (I8, 27-11-2026). Nella base dal 27-11-2026 sera, dentro
    # `finale` (da sola pari alla base: non toglie del tutto il caso P7, P12).
    inspection_source: bool = True
    # Il modello può rispondere `fuori_tema` quando il testo di riferimento non tratta affatto
    # il tipo di operazione (presa in carico, versamento, preservazione, documenti): esito N/A
    # FUORI_TEMA con la spiegazione, invece di WARNING EVIDENZA_NON_TROVATA. Nasce dalle prove
    # dal frontend del 27-11-2026: 6 operazioni su 9 WARNING «il testo non ne parla», dove la
    # v1 dice OK senza controllare. Non trova e non toglie errori: cambia come si mostra
    # «non c'è niente da confrontare». Dentro la variante `finale` (I16); nella base dal
    # 27-11-2026 sera.
    out_of_scope: bool = True
    # Con `out_of_scope`: se la descrizione ha un limite o un divieto, «fuori tema» non vale.
    # WARNING EVIDENZA_NON_TROVATA e una seconda ricerca in tutti i documenti del ciclo, solo su
    # queste operazioni (MG45, 27-11 notte): una negazione tolta in tutte e due le lingue finiva
    # N/A FUORI_TEMA (copia cieca `negazione_due_lingue`).
    prudent_out_of_scope: bool = True
    # «Almeno N» contro «più di N» (solo il caso uguale a N) non è una contraddizione: una nota
    # nel prompt dell'operazione. Regola decisa dall'utente il 27-11-2026 sera (P12: 04ecaabe
    # 050, l'italiano «almeno 4 volte», l'inglese e il manuale «più di 4»). Variante
    # `schede_e_limiti`, nella base dal 27-11 notte.
    boundary_limits_note: bool = True
    # La scheda coerente con l'operazione (H18, 27-11-2026 sera), decisa dal codice: scheda di
    # un altro motore, materiale della scheda diverso da quello della descrizione, task della
    # scheda che il manuale non ha (ma ne ha della stessa famiglia), scheda che l'indice non ha
    # (ma ne ha con lo stesso prefisso): ERRATO. Variante `schede_e_limiti`, nella base dal
    # 27-11 notte (campagna 4e: 34 contro 30 sul piccolo, 23 contro 18 sul grande, 0 falsi).
    sheet_consistency: bool = True
    # Differenze tra le lingue trovate dal codice, senza modello (27-11 notte): lo stesso numero
    # con un limite di verso opposto («superiore a 4X» contro «not to exceed 4X», MG75) e
    # un'azione diversa («rimosso» contro «blended», MG47). ERRATO INCOERENZA_LINGUE. Provato sul
    # testo delle 14 stampe della v1: 5 errori veri, nessun falso errore.
    languages_from_code: bool = True
    # Tutte le operazioni citano lo stesso DR («D.R. CASE #...»): quello delle recommendation del
    # serial number o, senza, il primo citato nella stampa. Un DR diverso: ERRATO DR_DIVERSO
    # (MG76, 27-11 notte; sulle 14 stampe della v1: 895167b9 030, nessun falso errore).
    dr_consistency: bool = True
    # Una contraddizione (ERRATO) si conferma con altrettante sessioni uguali: resta ERRATO
    # solo se la ritrovano tutte, altrimenti WARNING GIUDIZIO_INSTABILE. Su un ciclo DR vero
    # lo stesso confronto dava ERRATO 3 volte su 6 (21-11-2026). Costa solo sugli ERRATO.
    # 0 = nessuna conferma.
    confirm_contradiction: int = Field(default=2, ge=0, le=5)
    # Tempo massimo dei controlli con il modello di una validazione, in secondi (MG53, 27-11
    # notte): sotto i 600 s del backend. Le sessioni che non finiscono in tempo diventano
    # WARNING per errore tecnico e il report esce con quello che c'è. None = nessun limite.
    validation_timeout_s: float | None = Field(default=480, gt=0)
    # Il task citato è di un altro stadio (MG48, 28-11): il titolo del ciclo dice uno stadio
    # («... STAGE 7») e l'intestazione del task nel manuale dice solo stadi diversi («STAGE 6
    # ... INSPECTION»): ERRATO TASK_ALTRO_STADIO, dal codice. Lo fa la v1 (con il modello). Si
    # confrontano solo intestazioni dello stesso modulo (LPT con LPT...). Variante
    # `altro_stadio`.
    task_stage_check: bool = False
    # Come si chiama il modello (MG54, 28-11). `sdk`: Claude Agent SDK, cioè Claude Code avviato
    # per ogni sessione (circa 3-5 s di avvio ciascuna). `diretta`: l'SDK `anthropic` chiama
    # Bedrock direttamente (`agent/direct_session.py`); Read e Grep li esegue la v2 con le
    # stesse regole. Variante `diretta`; nella base dal 28-11 (campagna 4j: stessi errori di
    # `quasi_finale`, costo -37%, tempo -55% sul piccolo e -53% sul grande).
    session_backend: Literal["sdk", "diretta"] = "diretta"
    # Con `diretta`: l'id del modello su Bedrock (per esempio un profilo `eu.anthropic...`).
    # None = `model` (sul PC è già l'id completo; l'alias `haiku` vale solo per l'SDK).
    direct_model: str | None = None
    # Con `diretta`: come si arriva a Bedrock. `boto3` (predefinito dal 28-11): `invoke_model`
    # di boto3, la stessa rete che sul PC funziona per S3. `httpx`: il client HTTP dell'SDK
    # `anthropic` (sul PC la prima prova ha dato `APIConnectionError`).
    direct_transport: Literal["boto3", "httpx"] = "boto3"
    # Con `diretta`: prezzi in dollari per milione di token, per il costo nel report. Listino
    # di Haiku 5.5; la fattura di Bedrock può essere diversa. La scrittura in cache costa 1,25
    # volte l'ingresso, la lettura 0,1 volte.
    direct_input_price: float = Field(default=0.10, ge=0)
    direct_output_price: float = Field(default=0.50, ge=0)
    # Con `diretta`: punti di cache di Bedrock (MG56, 28-11) su istruzioni, strumenti e storia
    # della sessione. Nella variante `diretta` (la cache non cambia le risposte); nella base dal
    # 28-11.
    direct_cache: bool = True
    # Il testo di riferimento prima della domanda, in un blocco che si può tenere in cache
    # (MG59, 28-11): le operazioni che citano lo stesso task lo pagano una volta. Cambia
    # l'ordine del prompt (prima il manuale, poi l'operazione). Variante `testo_comune`.
    shared_reference_first: bool = False
    # Il confronto tra le due lingue di più operazioni in una sola sessione (MG55, 28-11): una
    # sessione ogni `language_batch_size` operazioni invece di una per operazione. Rischio: il
    # modello mescola le operazioni (il codice ritrova comunque le citazioni nella lingua
    # giusta di ogni operazione). 0 = spento. Variante `lingue_insieme`; nella base dal 28-11
    # (campagna 4j: stessi errori di `diretta`, 0 falsi errori, costo -43% sul piccolo e -48%
    # sul grande contro `quasi_finale`, meno falsi OK: 0,7 a prova contro 1,0).
    language_batch_size: int = Field(default=8, ge=0, le=30)
    # Regole finali (MG83, 28-11): lavorano sugli esiti già fatti, dopo tutti i controlli
    # (`verdict/final_rules.py`). Si possono rigiocare sulle prove fatte (`eval rigioca`, 0 $).
    # Vuoto = nessuna. Nella base dal 28-11: `fonte_assente_una_volta` (MG83: sul grande 8,9 →
    # 5,3 WARNING per ciclo, stessi errori) e, dal 28-11 pomeriggio, `parola_limite_contro_citazione`
    # (MG87b, rigiocata sulle prove di `lingue_insieme`: falsi OK sul piccolo 0,7 → 0,3 a
    # prova, 0 falsi errori in più sul piccolo e sul grande).
    final_rules: list[str] = Field(
        default_factory=lambda: ["fonte_assente_una_volta", "parola_limite_contro_citazione"]
    )

    @field_validator("final_rules")
    @classmethod
    def _known_rules(cls, value: list[str]) -> list[str]:
        from cycle_validation.verdict.final_rules import RULES  # qui: niente import circolari

        unknown = [name for name in value if name not in RULES]
        if unknown:
            raise ValueError(f"regole finali sconosciute: {', '.join(unknown)}")
        return value

    # Testo delle sessioni su disco: contiene cicli e manuali. Spento nel servizio, acceso
    # negli esperimenti (eval/varianti/baseline.yaml).
    save_transcripts: bool = False


class PathSettings(_Strict):
    """Percorsi relativi alla cartella da cui si lancia lo strumento."""

    profiles_dir: Path = Path("config/profiles")
    prompts_dir: Path = Path("prompts")
    knowledge_dir: Path = Path("data/knowledge")
    runs_dir: Path = Path("runs")
    machines_file: Path | None = None


class ModuleCheckSettings(_Strict):
    """Riconoscimento del tipo di ciclo dalla testata, per rifiutare il modulo sbagliato."""

    enabled: bool = True
    # Valori del campo PROGETTO che identificano un ciclo militare e uno civile.
    military_projects: list[str] = Field(default_factory=lambda: ["EJ200"])
    civil_projects: list[str] = Field(default_factory=lambda: ["GENX", "LEAP"])
    # Espressioni regolari che, in testata, identificano un ciclo DR. Vuoto = MOS e DR
    # non vengono distinti. Sull'unica stampa DR reale vista (16/11/2026) la testata non dice
    # "DR": lo distingue il numero di segnalazione difetti in NOTE (`Saa/nnnnn-...`), dove
    # un MOS porta il task del manuale. Da riconfermare su altri DR.
    dr_markers: list[str] = Field(
        default_factory=lambda: [
            r"\bDR\b",
            r"DEPARTURE\s+RECOMMENDATION",
            r"\bS\d{2}/\d{4,6}\b",
        ]
    )

    @field_validator("dr_markers")
    @classmethod
    def _valid_patterns(cls, value: list[str]) -> list[str]:
        for pattern in value:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"espressione regolare non valida '{pattern}': {exc}") from exc
        return value


class Settings(_Strict):
    agent: AgentSettings = Field(default_factory=AgentSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    module_check: ModuleCheckSettings = Field(default_factory=ModuleCheckSettings)


class FileLimits(_Strict):
    require_pdf_header: bool = True
    max_bytes: int | None = Field(default=None, ge=1)
    max_pages: int | None = Field(default=None, ge=1)
    # Tetto delle pagine da trascrivere con il modello (scansioni): vale anche per i profili
    # senza `max_pages`, perché ogni pagina è un rendering e una chiamata a pagamento.
    max_transcribed_pages: int = Field(default=60, ge=1)
    min_chars: int = Field(default=100, ge=0)
    required_text: list[str] = Field(default_factory=list)


class ProfileConfig(_Strict):
    """Un profilo dichiara limiti sul file, controlli attivi e regole di dominio."""

    name: str
    enabled: bool = True
    disabled_reason: str = ""
    file_limits: FileLimits = Field(default_factory=FileLimits)
    checks: list[CheckName]
    blocking_checks: list[CheckName] = Field(default_factory=list)
    requires_selectors: bool = False
    reference_mode: Literal["task", "document"] = "task"
    document_order: list[str] = Field(default_factory=list)
    verify_process_sheet: bool = True
    excluded_sheet_prefixes: list[str] = Field(default_factory=list)
    engine_families: list[str] = Field(default_factory=list)
    extraction_prompt: str = "extract_cycle.md"
    layout_extractor: Literal["none", "pvrm320"] = "none"


def _describe(error: ValidationError, origin: Path) -> str:
    lines = [f"Configurazione non valida in {origin}:"]
    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"]) or "(radice)"
        lines.append(f"  - {field}: {item['msg']}")
    return "\n".join(lines)


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Impossibile leggere {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML non valido in {path}: {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} deve contenere una mappa chiave: valore.")
    return loaded


def load_settings(path: Path | None = None) -> Settings:
    """Carica le impostazioni. Senza file valgono i valori predefiniti."""
    if path is None:
        return Settings()
    if not path.is_file():
        raise ConfigError(f"File di configurazione non trovato: {path}")
    try:
        return Settings.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ConfigError(_describe(exc, path)) from exc


def available_profiles(profiles_dir: Path) -> list[str]:
    return sorted(item.stem for item in profiles_dir.glob("*.yaml"))


def load_profile(name: str, profiles_dir: Path) -> ProfileConfig:
    path = profiles_dir / f"{name}.yaml"
    if not path.is_file():
        known = ", ".join(available_profiles(profiles_dir)) or "nessuno"
        raise ConfigError(f"Profilo '{name}' non trovato in {profiles_dir}. Disponibili: {known}.")
    try:
        profile = ProfileConfig.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ConfigError(_describe(exc, path)) from exc
    unknown = [check for check in profile.blocking_checks if check not in profile.checks]
    if unknown:
        names = ", ".join(unknown)
        raise ConfigError(f"{path}: blocking_checks cita controlli non attivi: {names}.")
    return profile
