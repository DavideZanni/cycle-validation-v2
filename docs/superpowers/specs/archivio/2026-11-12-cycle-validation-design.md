# Cycle Validation — Design

> **SUPERATO.** Scritto prima di avere la documentazione del sistema attuale. Sostituito da `docs/superpowers/specs/2026-11-13-cycle-validation-v2-design.md`.

**Data:** 2026-11-12
**Stato:** design approvato per sezioni, in attesa di revisione finale
**Ambito:** nuovo progetto (greenfield). Non dipende dal repository `ge-aero/avioaero_datalake_cycle_validation`, che non è accessibile da questa macchina.

## 1. Obiettivo

Un utente carica un PDF che descrive un ciclo relativo a un motore. Il sistema estrae dal PDF un insieme fisso di campi e, per ciascuno, verifica il valore contro i manuali tecnici, già convertiti in Markdown e JSON da una pipeline di ingestion esistente. Il risultato è una tabella con una riga per campo e un esito: `CORRETTO`, `WARNING` o `ERRATO`.

Priorità, in ordine: affidabilità degli esiti, velocità del run, costo minimo.

## 2. Decisioni prese

| Tema | Decisione |
|---|---|
| Harness agente | Claude Agent SDK (Python) su AWS Bedrock, modello Haiku |
| Tool dell'agente | Solo `Glob`, `Grep`, `Read`, in sola lettura, confinati alla cartella dei manuali |
| Politica di lettura | GRASP (GRanularity-Aware Search Policy): lettura a paragrafo attorno al match del grep, mai il file intero. Imposta da hook, non solo dal prompt |
| Campi da validare | Lista fissa in `config/fields.yaml` |
| Granularità agente | Una sessione isolata per campo, sessioni in parallelo |
| Esecuzione | CLI locale; la logica sta in una libreria riusabile |
| Output | `report.json` (fonte di verità) e `report.md` |
| Estrazione PDF | PDFium (`pypdfium2`) → Markdown, poi estrattore dietro interfaccia |

## 3. Architettura

Sei stadi in sequenza. Ogni stadio legge e scrive file nella cartella del run, così ogni passaggio è ispezionabile e il run può ripartire da uno stadio intermedio.

```
ciclo.pdf
   │
[1 ingest]     PDFium → Markdown                     deterministico, 0 token
[2 extract]    Markdown → campi secondo fields.yaml  dietro interfaccia FieldExtractor
[3 precheck]   controlli senza LLM                   0 token
[4 validate]   una sessione Haiku per campo          in parallelo, solo campi che superano il precheck
[5 verdict]    regole applicate dal codice           confronto numerico, verifica citazioni
[6 report]     report.json + report.md
```

### 3.1 Stadio 1 — ingest

Converte il PDF in Markdown con `pypdfium2`, conservando il numero di pagina di ogni blocco. Se il PDF non contiene testo estraibile (scansione), il run si interrompe con un errore esplicito. L'OCR è fuori ambito.

### 3.2 Stadio 2 — extract

Riempie lo schema definito in `fields.yaml` a partire dal Markdown. L'interfaccia è:

```python
class FieldExtractor(Protocol):
    def extract(self, cycle_markdown: str, fields: list[FieldSpec]) -> list[ExtractedField]: ...
```

L'implementazione (parser a regole oppure chiamata LLM con output strutturato) si sceglie dopo aver visto i PDF reali. Il resto della pipeline dipende solo dall'interfaccia. Si preferisce il parser a regole se il formato del PDF è stabile, perché è gratuito e ripetibile.

### 3.3 Stadio 3 — precheck

Decide senza LLM i casi che non richiedono giudizio:

- campo assente → `WARNING` / `CAMPO_MANCANTE` (tutti i campi di `fields.yaml` sono obbligatori)
- valore non interpretabile nel tipo dichiarato → `WARNING` / `CAMPO_MANCANTE`
- unità diversa da quella dichiarata e non convertibile → `WARNING` / `CAMPO_MANCANTE`

I campi decisi qui non arrivano all'agente.

### 3.4 Stadio 4 — validate

Per ogni campo rimasto parte una sessione Claude Agent SDK:

- **Prompt di sistema** unico (`prompts/validator.md`), identico per tutte le sessioni, così il prompt caching di Bedrock lo riusa.
- **Messaggio utente**: specifica del campo (id, label, tipo, unità, `search_hints`) e valore estratto dal ciclo.
- **Tool ammessi**: `Glob`, `Grep`, `Read`. Tutti gli altri disabilitati.
- **Output strutturato**: `AgentFinding` (vedi §5).
- **Limiti**: `max_turns` per sessione e concorrenza massima, entrambi in `settings.yaml`.

L'agente ha un compito ristretto: trovare nei manuali il valore di riferimento per il campo e citarne la fonte. Esprime un giudizio (`match` / `mismatch` / `unclear`) solo per i campi senza `rule`.

**Hook `PreToolUse` (GRASP e confinamento):**

- `Read` senza `limit`, o con `limit` sopra `grasp.max_limit` → negato, con messaggio che indica di usare `offset = riga_match − grasp.before` e `limit = grasp.window`.
- `Read`, `Grep`, `Glob` con path fuori dalla cartella dei manuali → negato.

Gli hook sono funzioni pure `(tool_name, tool_input, settings) → allow | deny(motivo)`, testabili senza rete.

La trascrizione di ogni sessione è salvata in `runs/<run>/sessions/<field_id>.jsonl`.

### 3.5 Stadio 5 — verdict

Il codice, non il modello, assegna l'esito finale:

1. **Evidenza assente.** `found = false` → `WARNING` / `EVIDENZA_NON_TROVATA`.
2. **Verifica citazioni.** Per ogni citazione riapre `file` alla riga `line` e controlla che `quote` sia presente (confronto normalizzato su spazi e maiuscole, entro 3 righe dalla riga indicata). Se nessuna citazione è verificata → `WARNING` / `CITAZIONE_NON_VERIFICATA`.
3. **Evidenze in conflitto.** `judgement = unclear` (manuali discordi o confronto non determinabile) → `WARNING` / `CONFLITTO`, per tutti i campi.
4. **Campi con `rule`.** L'agente riporta il valore di riferimento come testo; Python lo interpreta e lo confronta con `cycle_value`:
   - valore di riferimento assente, o non numerico per un campo `number` → `WARNING` / `EVIDENZA_NON_TROVATA`
   - unità del manuale diversa da quella del campo → `WARNING` / `CONFLITTO` (nessuna conversione di unità)
   - dentro la regola → `CORRETTO`
   - dentro la tolleranza ma nell'ultimo 10% del margine → `WARNING` / `AL_LIMITE` (soglia `near_limit_ratio`)
   - fuori → `ERRATO`
5. **Campi senza `rule`.** `match` → `CORRETTO`, `mismatch` → `ERRATO`.
6. `CORRETTO` ed `ERRATO` richiedono almeno una citazione verificata. Senza, l'esito è `WARNING`.

I numeri di riferimento sono accettati solo nella forma `123` o `123.45`. Ogni altra forma (virgola, separatori delle migliaia) produce `WARNING`, perché l'interpretazione sarebbe ambigua.

### 3.6 Stadio 6 — report

Scrive `report.json` e `report.md` nella cartella del run.

## 4. Struttura del progetto

Python ≥ 3.12 (3.13 in locale), layout `src/`, `uv`, `pydantic`, `typer`, `pypdfium2`, `claude-agent-sdk`, `pytest`, `ruff`, `mypy`.

```
<radice progetto>/
├── pyproject.toml
├── README.md
├── .env.example                 # AWS_REGION, profilo AWS, CLAUDE_CODE_USE_BEDROCK
├── .gitignore                   # data/, runs/, .env
├── config/
│   ├── settings.yaml
│   └── fields.yaml
├── prompts/
│   └── validator.md
├── src/cycle_validation/
│   ├── cli.py                   # comandi: run, ingest
│   ├── pipeline.py              # orchestra gli stadi
│   ├── config.py                # carica e valida i due YAML
│   ├── models.py                # contratti dati
│   ├── errors.py                # errori fatali
│   ├── text.py                  # normalizzazione testo/unità, parsing numeri
│   ├── paths.py                 # confinamento dei path nella cartella dei manuali
│   ├── results.py               # costruzione di FieldResult
│   ├── ingest/pdf_to_markdown.py
│   ├── extract/
│   │   ├── base.py              # interfaccia FieldExtractor
│   │   └── json_file.py         # campi già estratti letti da JSON (finché manca l'estrattore)
│   ├── precheck/checks.py
│   ├── agent/
│   │   ├── session.py           # interfaccia FieldSession, SessionOutcome
│   │   ├── runner.py            # sessioni per campo, parallelismo, retry
│   │   ├── hooks.py             # GRASP + confinamento path
│   │   ├── prompt.py            # messaggio utente e schema dell'output strutturato
│   │   └── sdk_session.py       # adattatore Claude Agent SDK
│   ├── verdict/
│   │   ├── rules.py
│   │   ├── citations.py
│   │   └── decide.py            # esito finale da finding + regole + citazioni
│   └── report/
│       ├── builder.py
│       ├── json_writer.py
│       └── markdown_writer.py
├── tests/                       # un file test_<modulo>.py per modulo
├── docs/
│   ├── architecture.md
│   └── superpowers/specs/, plans/
├── data/                        # fuori da git
│   ├── input/                   # PDF dei cicli
│   └── manuals/                 # Markdown/JSON prodotti dalla pipeline di ingestion
└── runs/                        # fuori da git
    └── <timestamp>_<nome-pdf>/
        ├── cycle.md
        ├── fields.json
        ├── sessions/<field_id>.jsonl
        ├── report.json
        └── report.md
```

`data/` e `runs/` contengono materiale aziendale e non entrano mai in git.

## 5. Contratti dati

### 5.1 `config/fields.yaml`

```yaml
fields:
  - id: max_egt                  # chiave stabile
    label: "Temperatura EGT massima"
    type: number                 # number | string
    unit: "°C"                   # opzionale
    group: null                  # opzionale, riservato a un futuro raggruppamento
    rule:                        # opzionale
      kind: tolerance            # tolerance (solo number) | exact
      value: 5
      mode: absolute             # absolute | percent
    search_hints: ["EGT", "exhaust gas temperature"]
```

Il campo `max_egt` è solo illustrativo. L'elenco reale si compila sui PDF di esempio. Altri tipi (`date`, `enum`) e regole (`range`) si aggiungono quando un campo reale li richiede.

### 5.2 `config/settings.yaml`

| Chiave | Default | Significato |
|---|---|---|
| `model` | `anthropic.claude-haiku-5-5` (da verificare nell'account Bedrock) | modello delle sessioni |
| `effort` | `low` | livello di ragionamento; `null` per i modelli che non lo supportano |
| `manuals_dir` | `data/manuals` | unica cartella leggibile dall'agente |
| `concurrency` | 8 | sessioni in parallelo |
| `max_turns` | 10 | turni massimi per sessione |
| `retries` | 2 | nuovi tentativi su errore Bedrock |
| `grasp.before` | 15 | righe prima del match |
| `grasp.window` | 30 | `limit` suggerito |
| `grasp.max_limit` | 60 | `limit` massimo ammesso dall'hook |
| `near_limit_ratio` | 0.10 | soglia per `AL_LIMITE` |

### 5.3 Modelli

**`ExtractedField`** — `id`, `raw_text`, `value` (tipizzato o `null`), `unit`, `source` (pagina e riga nel Markdown del ciclo), `status` (`ok` | `missing` | `unparseable`).

**`AgentFinding`** — `field_id`, `found` (bool), `reference_value` (testo, come scritto nel manuale), `reference_unit`, `judgement` (`match` | `mismatch` | `unclear`; `unclear` vale per tutti i campi, `match` e `mismatch` solo senza `rule`), `rationale` (massimo 2 frasi), `citations: [{file, line, quote}]`. `file` è relativo alla cartella dei manuali.

**`FieldResult`** — `field_id`, `label`, `cycle_value`, `cycle_unit`, `reference_value`, `reference_unit`, `verdict`, `warning_code`, `rationale`, `citations`, `decided_by` (`precheck` | `rule` | `agent`), `usage` (token input, token output, token di cache letti e scritti, costo in USD, durata, turni).

**`verdict`**: `CORRETTO` | `WARNING` | `ERRATO`.

**`warning_code`** (presente solo con `WARNING`): `EVIDENZA_NON_TROVATA`, `CAMPO_MANCANTE`, `CONFLITTO`, `AL_LIMITE`, `BUDGET_ESAURITO`, `CITAZIONE_NON_VERIFICATA`, `ERRORE_TECNICO`.

### 5.4 Report

**`report.json`** — metadati del run (nome e hash SHA-256 del PDF, data, modello, hash di `fields.yaml`), lista di `FieldResult`, totali (conteggio per esito, token, costo, durata).

**`report.md`** — intestazione con i totali e tabella:

`Campo | Valore ciclo | Riferimento | Esito | Motivazione | Fonte`

## 6. Gestione degli errori

Un problema su un campo produce una riga `WARNING`, non un run fallito. Il run si interrompe solo per errori che impediscono di produrre qualunque riga.

| Situazione | Comportamento |
|---|---|
| PDF illeggibile o senza testo | Run interrotto, exit code 1 |
| `fields.yaml` o `settings.yaml` non validi | Run interrotto prima di ogni chiamata, exit code 1 |
| Cartella manuali assente o vuota | Run interrotto, exit code 1 |
| Campo assente o non interpretabile | `WARNING` / `CAMPO_MANCANTE` |
| Throttling o errore Bedrock | `retries` tentativi con attesa esponenziale, poi `WARNING` / `ERRORE_TECNICO` |
| Output agente non conforme allo schema | 1 nuovo tentativo, poi `WARNING` / `ERRORE_TECNICO` |
| `max_turns` raggiunto | `WARNING` / `BUDGET_ESAURITO` |
| Chiamata tool vietata | Negata dall'hook con istruzione correttiva; la sessione continua |
| Citazione non riscontrata | `WARNING` / `CITAZIONE_NON_VERIFICATA` |

Exit code: 0 se il report è stato prodotto, qualunque siano gli esiti; 1 per errore fatale.

## 7. Test

- **Unit, offline:** ingest (su PDF di fixture), precheck, regole di confronto, verifica citazioni, hook, writer, caricamento configurazione.
- **Runner:** testato con una sessione finta dietro interfaccia; copre parallelismo, retry, timeout di turni, output non conforme.
- **Pipeline end-to-end offline:** estrattore e sessione finti, verifica del report prodotto.
- **Golden set (manuale, contro Bedrock):** PDF di esempio con esiti attesi campo per campo. Misura accuratezza degli esiti, costo e durata. Si rilancia a ogni modifica di prompt, `fields.yaml` o `settings.yaml`. Marcato `pytest -m bedrock`, escluso dalla suite di default.

## 8. Fuori ambito

- OCR di PDF scansionati
- Escalation automatica a un modello più grande sui `WARNING`
- Indici, embedding o knowledge graph dei manuali
- Cache dei risultati tra run
- API HTTP e integrazione nella pipeline datalake (la libreria è predisposta, l'involucro no)
- Export Excel

## 9. Dipendenze da input non ancora disponibili

Questi punti si chiudono quando arrivano i PDF di esempio (ingresso e uscita attesa) e la documentazione della pipeline di ingestion dei manuali. Nessuno cambia l'architettura.

| Punto | Dipende da |
|---|---|
| Implementazione di `FieldExtractor` (regole o LLM) | formato dei PDF del ciclo |
| Ricostruzione di tabelle e titoli nel Markdown del ciclo (la prima versione produce il testo di ogni pagina con un marcatore di pagina) | layout dei PDF del ciclo |
| Contenuto di `fields.yaml` | PDF del ciclo e tabella di uscita attesa |
| `search_hints` e testo di `prompts/validator.md` | struttura di Markdown e JSON dei manuali |
| Uso dei JSON dei manuali oltre al Markdown | documentazione dell'ingestion |
| Valori definitivi di `concurrency` e `max_turns` | numero di campi per ciclo e misure sul golden set |

## 10. Ordine di costruzione

1. Scheletro del progetto, configurazione, modelli, CLI vuota.
2. Verdict (regole e citazioni), precheck, report: logica pura, completamente testabile oggi.
3. Hook GRASP e runner dell'agente con sessione finta.
4. Ingest PDFium.
5. Con gli input reali: `FieldExtractor`, `fields.yaml`, prompt, golden set e taratura.

I passi 1–4 non dipendono dagli input mancanti.
