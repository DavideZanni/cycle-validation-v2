# Cycle Validation in azienda

Tutto quello che serve sul computer aziendale, in ordine: **A** importare e collegare il
programma, **B** fare gli esperimenti sui cicli veri, **C** cosa fare se qualcosa non va. Le
migliorie future e il registro degli esperimenti stanno in `docs/MIGLIORIE.md`.

Ogni passo ha un comando e il risultato che devi vedere. Se vedi altro, fermati lì e guarda la
parte C.

---

# A. Importare e collegare

## 1. Cosa serve

| Cosa | Come controllare |
|---|---|
| Git | `git --version` |
| Python 3.12 o più recente | `python --version` |
| uv (se manca: `pip install uv`) | `uv --version` |
| Credenziali AWS aziendali (Bedrock, S3, Redshift) | le usi già per gli altri progetti |
| Docker, facoltativo | `docker --version` |

## 2. Portare il codice e installare

Il codice sta nel repository aziendale `avioaero_datalake_cycle_validation`, nella cartella
`app_cycle_validation_v2/`, accanto alla versione 1 in produzione (`app_cycle_validation/`).
Come ci è arrivato, e come rifarlo, è in `docs/IMPORTAZIONE.md`. Viaggia solo il codice: il
materiale aziendale resta in azienda.

**Tutti i comandi di questa guida si lanciano da dentro `app_cycle_validation_v2`.**

`.python-version` chiede Python 3.13 e uv usa solo il Python installato sul sistema. Se il tuo è
un altro (3.12 o più recente), dillo a uv in ogni terminale nuovo, prima dei comandi, con il tuo
numero: `$env:UV_PYTHON = "3.14"` in PowerShell. Senza, uv risponde
`No interpreter found for Python 3.13`. La suite è provata anche su 3.14.

```bash
cd app_cycle_validation_v2
uv sync --all-groups --extra aws
uv run pytest
uv run ruff check .
uv run mypy
uv run cycle-validation kb-check examples/sintetico/knowledge
```

Devi vedere: `771 passed, 2 skipped` (saltati: la prova con il modello vero e quella sulle
stampe di esempio in `docs/Esempio*/`, che parte solo se le cartelle ci sono),
`All checks passed!`, `Success: no issues found` e un elenco che finisce con
`recommendation_dr_incerte: 0`. Qui non serve né la rete né una credenziale.

## 3. Il materiale aziendale

Queste cartelle sono ignorate da git: non finiscono mai nel repository. Controlla con
`git status` che non compaiano.

| Cartella | Cosa ci va |
|---|---|
| `docs/doc_lavoro/`, ogni `docs/Esempio...` | documenti e stampe di esempio |
| `data/` | conoscenza scaricata, elenco delle macchine |
| `runs/` | risultati delle validazioni e transcript |
| `eval/casi/aziendali/`, `eval/casi/mutazioni/`, `eval/risultati/` | esperimenti sui cicli veri |
| `.env` | variabili d'ambiente, se le tieni in un file |

## 4. Configurare

### 4.1 `config/settings.yaml`

| Voce | Cosa mettere |
|---|---|
| `agent.model` | l'id del profilo di inferenza `eu.` di Claude Haiku 5.5 abilitato su Bedrock (`aws bedrock list-inference-profiles --region eu-south-1`); se non c'è ancora, Haiku 4.5. La parola `haiku` da sola può puntare a un modello non abilitato |
| `agent.use_bedrock` | `true` |
| `agent.aws_region` | la regione di Bedrock, per esempio `eu-south-1`; vuoto = quella dell'ambiente |
| `agent.transcribe_model` | un modello che vede le immagini (anche lo stesso Haiku), se i cicli arrivano come foto o scansioni. Vuoto: una foto viene rifiutata con "meno di 100 caratteri di testo" |
| `agent.transcribe_concurrency` | pagine trascritte insieme (4); abbassalo se Bedrock risponde con throttling |
| `agent.save_transcripts` | `false` nel servizio (salverebbe testo aziendale su disco); gli esperimenti lo accendono da soli |
| `agent.session_timeout_s`, `agent.extraction_timeout_s` | 90 s per sessione, 300 s per leggere il PDF; oltre, WARNING per errore tecnico |
| `module_check.dr_markers` | come si riconosce un DR dalla testata (vedi 6.3) |

### 4.2 Variabili d'ambiente del servizio

Il servizio si monta da solo da queste variabili (`src/cycle_validation/api/main.py` e
`api/production.py`): non c'è codice da scrivere. Prima di collegarsi ad AWS le controlla tutte
e, se qualcosa non va, le elenca insieme con il nome.

| Variabile | Obbligatoria | Cosa fa |
|---|---|---|
| `BUCKETNAME`, `REGION_NAME`, `FRONTEND_URL` | sì | bucket S3, regione AWS, indirizzo del frontend |
| `MACHINES_FILE` | questa o Redshift | JSON delle macchine attive: lista di targhe o `{"active": [...]}` |
| `REDSHIFT_DATABASE` | questa o il file | macchine attive da Redshift, con la Data API (nessun driver) |
| `REDSHIFT_WORKGROUP` | con Redshift Serverless | il workgroup |
| `REDSHIFT_CLUSTER_ID` | con un cluster | più `REDSHIFT_DB_USER` (credenziali IAM) oppure `REDSHIFT_SECRET_ARN` |
| `MACHINES_QUERY` | **sì** | prima colonna = targa. La tabella è quella del vecchio `verify_active_TM`: `SELECT DISTINCT work_center_cd FROM <schema>.<tabella> WHERE work_center_usage_cd = 'TO'`. La predefinita (`work_centers`) è solo un segnaposto |
| `MACHINES_TTL_S` | no | ogni quanti secondi si rilegge Redshift (900) |
| `CIVIL_KNOWLEDGE_POINTER` | no | `current.json` della conoscenza civile (predefinito `Manufacturing AI/cv3/knowledge/civil/current.json`) |
| `EJ200_KNOWLEDGE_POINTER` | no | `current.json` di EJ200 (predefinito `.../knowledge/ej200/current.json`); vuota = catalogo a chiave fissa `EJ200_CATALOG_KEY` |
| `EJ200_VALIDATION_ENABLED` | no | `false` spegne i cicli militari |
| `SECRET_NAME` | no | secret di Secrets Manager da cui prendere le variabili che mancano |
| `KNOWLEDGE_WORKDIR` | no | cartella tutta sua dove scaricare la conoscenza (predefinita: nella cartella temporanea) |
| `CYCLE_VALIDATION_CONFIG` | no | file delle impostazioni (`config/settings.yaml`) |
| `CLOUDWATCH_METRICS` | no | `false` per non pubblicare il costo su CloudWatch |
| `API_MAX_WORKERS` | no | validazioni contemporanee (6); ognuna apre fino a `agent.concurrency` sessioni |
| `API_MAX_UPLOAD_MB` | no | dimensione massima del file (50) |
| `API_INCLUDE_TRACEBACK` | no | **in produzione `false`** |
| `API_USER_HEADER`, `API_SERVICES_HEADER` | no | header con utente e servizi (`X-User`, `X-Services`) |

Il ruolo AWS deve poter usare `redshift-data:ExecuteStatement`, `DescribeStatement` e
`GetStatementResult` (più `redshift:GetClusterCredentials` per un cluster con utente). Se
Redshift all'inizio non è pronto, parti con `MACHINES_FILE`.

**Chi è l'utente.** L'accesso lo verifica il frontend: il backend legge utente e servizi dagli
header e se ne fida. Per questo **il backend deve essere raggiungibile solo dal frontend** (rete
privata, security group o gateway). Senza utente valido la risposta è 401, senza il servizio
giusto 403 (EJ200 chiede `cv_ej200` o `all`).

## 5. Prima prova con Bedrock, sui dati inventati

Dice una cosa sola: Bedrock risponde.

```bash
uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/mos --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/dr --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
uv run pytest -m live
```

Devi vedere, nell'ordine: `Ciclo completo: 10 corretti, 4 warning, 2 errati, 3 non applicabili.`
in 10-20 secondi; `concordanza 100.0%` due volte (per MOS va bene anche `94.7%` se l'unico caso
diverso è `fonte_e_codice_assenti`, vedi MIGLIORIE A2); `1 passed`. La prova `live` va
rilanciata dopo ogni aggiornamento della libreria dell'agente o del modello.

Se **tutte** le operazioni escono "errore tecnico", il modello non risponde: credenziali,
regione, `agent.model`. Il motivo preciso è in `runs/ultimo/transcripts/`.

## 6. Prova con la conoscenza vera

### 6.1 Scaricare e controllare la conoscenza

La conoscenza la pubblica knowledge-index su S3: `current.json` punta alla versione in uso,
`v/<versione>/` contiene i file. Se ne fa una copia locale, la *fotografia*, che serve anche agli
esperimenti:

```bash
uv run cycle-validation eval fotografia --bucket <BUCKETNAME> --prefisso "Manufacturing AI/cv3/knowledge/" --out eval/casi/aziendali/conoscenza/foto-AAAAMMGG
uv run cycle-validation kb-check "eval/casi/aziendali/conoscenza/foto-AAAAMMGG/Manufacturing AI/cv3/knowledge/civil/v/<versione>"
```

La versione è quella scritta in `knowledge/civil/current.json`. `kb-check` stampa i conteggi,
anche delle voci che l'indice segna come incerte, e fallisce se un file non va: va lanciato a ogni
pubblicazione nuova. Un `uncertainty.json` incoerente fa fallire `kb-check`, ma non ferma il
servizio, che ignora quella parte e lo scrive nel log.

### 6.2 Un ciclo vero da terminale

```bash
uv run cycle-validation run "docs/Esempio ciclo mos/<file>.pdf" --profile mos --knowledge "<cartella della versione>" --machines data/macchine_attive.json --config config/settings.yaml
```

Devi vedere `Ciclo completo: ...` e in `runs/ultimo` i file `report.json`, `report.md` e
`payload.json`. `report.md` è il risultato leggibile. Per un DR aggiungi
`--profile dr --serial-number <S/N> --condition 1`; per un EJ200 `--profile ej200`.

### 6.3 Cose scritte senza dati veri, da guardare una volta

| Cosa | Dove si corregge | Come ti accorgi che è sbagliata |
|---|---|---|
| Id del modello | `agent.model` | tutte le operazioni "errore tecnico" |
| Come si riconosce un DR dalla testata (visto un solo DR vero: segnalazione `Saa/nnnnn` in NOTE) | `module_check.dr_markers`; `[]` smette di distinguere MOS da DR | i DR veri rifiutati come "ciclo civile MOS" |
| Query delle macchine attive | `MACHINES_QUERY` | targhe giuste segnate "non attiva" (ERRATO) |
| La colonna TARGA della stampa è la targa da verificare | `src/cycle_validation/extract/pvrm320_report.py` | esiti sulla macchina sbagliata |
| Nomi con cui i cicli citano manuali e documenti (LEAP compresi) | `aliases.json` accanto a `current.json`, lato knowledge-index | fonti valide segnate "non trovate" |

**Attenzione alle targhe.** Una targa dei dati TM che non è nell'elenco delle macchine attive dà
ERRATO; una targa che non c'è da nessuna parte dà solo WARNING "targa sconosciuta". Se l'elenco
delle attive è incompleto escono ERRATO falsi sulle targhe dei dati TM: controlla i primi
risultati a mano.

## 7. Avviare il servizio

```bash
uv run uvicorn cycle_validation.api.entry:app --port 8000
```

oppure con Docker:

```bash
docker build -t cycle-validation .
docker run -p 8000:8000 --env-file .env cycle-validation
```

Prova: `http://127.0.0.1:8000/cycle_validation/health` risponde `{"status":"ok","code":200}`.

All'avvio il servizio scarica la conoscenza: se un file pubblicato non è valido non parte, e
l'errore dice quale. Poi rilegge `current.json` ogni 5 minuti e passa da solo alla versione
nuova, se è valida; altrimenti resta sulla precedente e lo scrive nel log. Una validazione già
partita finisce con la sua versione, e il report la indica (`knowledge_version`).

| Rotta | Cosa fa |
|---|---|
| `GET /cycle_validation/validation/options` | quali pulsanti mostrare: civile o militare, poi MOS o DR |
| `POST /cycle_validation/validation/upload` | `file`, `domain` (`civil`/`military`), `civil_type` (`mos`/`dr`), `dr_serial_number`, `dr_condition` |

Se il file non è del tipo scelto la risposta è 422 "Modulo sbagliato". Le rotte storiche
(`/upload`, `/ej200/upload`) funzionano ancora. Per chi collega il frontend: un errore imprevisto
risponde `Errore interno (<Tipo>).`; `state: succeeded` non vuol dire che ogni controllo sia
stato fatto, contano i WARNING e `_pipeline_errors`.

## 8. Confronto con il sistema attuale

Gli stessi cicli passano dal sistema attuale e da questo; per ogni differenza: uguale, meglio o
peggio. Il nuovo sostituisce il vecchio solo se nessun caso peggiora, il tempo e il costo per
ciclo non salgono e il frontend accetta la risposta senza modifiche.

---

# B. Esperimenti sui cicli veri

## 9. Come funzionano

Un esperimento è un file in `eval/varianti/` che cambia una cosa sola. Si prova sugli stessi
casi e sulla stessa fotografia della conoscenza della `baseline`, e la classifica dice se tenerlo.
Servono tre cose, uguali per tutte le varianti:

1. **la conoscenza**: la fotografia del punto 6.1. Se cambia a metà giro, il confronto non vale;
2. **i casi**: cicli veri con l'esito giusto riga per riga, controllato da chi conosce il ciclo;
3. **le varianti**.

```
eval/casi/aziendali/              ← ignorata da git: niente di qui esce dall'azienda
├── conoscenza/foto-AAAAMMGG/     la fotografia (punto 6.1)
├── macchine_attive.json          ["TM-1001", "TM-2002", ...]
├── mos/
│   ├── suite.yaml                copiato da eval/modelli/aziendali/mos/
│   └── ciclo_rettifica_01/       ciclo.pdf, ciclo.json, expected.json, revisione.md
├── dr/                           uguale, da eval/modelli/aziendali/dr/
└── ej200/                        uguale, da eval/modelli/aziendali/ej200/
```

## 10. Preparare i casi

```bash
cp -r eval/modelli/aziendali/mos eval/modelli/aziendali/dr eval/modelli/aziendali/ej200 eval/casi/aziendali/
```

In ogni `suite.yaml` correggi solo `conoscenza` (il nome della cartella della fotografia). I
puntatori sono già quelli del servizio; le targhe di EJ200 vengono dalla conoscenza civile, come
in produzione. `macchine_attive.json` è l'elenco delle targhe attive, scritte come nei cicli.

Per ogni ciclo vero una cartella con il PDF chiamato `ciclo.pdf`, poi la bozza:

```bash
uv run cycle-validation eval prepara eval/casi/aziendali/mos/ciclo_rettifica_01
```

Per un DR aggiungi `--serial-number SN-... --condition 1`. Il programma valida il ciclo una
volta e scrive `ciclo.json` (il ciclo letto), `expected.json` (gli esiti proposti, con
`"rivisto": false`) e `revisione.md` (ogni riga con spiegazione e citazione).

**La revisione la fa chi conosce il ciclo:** dove l'esito è sbagliato corregge `verdict` e
`reason` della stessa riga di `expected.json`, controlla `ciclo.json` contro la stampa
(operazioni, targhe, task, schede) e alla fine mette `"rivisto": true`. Finché è `false`, gli
esperimenti saltano il caso. Se di una riga conta solo l'esito, togli `reason`.

| `verdict` | `reason` possibili |
|---|---|
| `CORRETTO` | `VERIFICATO` |
| `ERRATO` | `CONTRADDIZIONE`, `MACCHINA_NON_ATTIVA`, `DR_NON_APPLICABILE`, `DR_NESSUNA_CORRISPONDENZA` |
| `WARNING` | `FONTE_ASSENTE`, `TARGA_SCONOSCIUTA`, `EVIDENZA_NON_TROVATA`, `VERSIONE_DIVERSA`, `PUBBLICAZIONE_PARZIALE`, `DATO_INCERTO`, `RIFERIMENTO_AMBIGUO`, `CITAZIONE_NON_VERIFICATA`, `ESTRAZIONE_NON_CONFERMATA`, `BUDGET_ESAURITO`, `ERRORE_TECNICO`, `BLOCCATO_A_MONTE` |
| `NON_APPLICABILE` | `CAMPO_ASSENTE`, `ESCLUSO_DA_REGOLA`, `NON_VERIFICATO_PER_PROFILO` |

**Quanti casi.** Pochi ma vari: 5-10 MOS, 3-5 DR, 5 EJ200, con qualche ERRATO vero (macchina
dismessa, valore sbagliato), qualche WARNING, cicli lunghi e corti. I cicli con un errore vero
sono i più preziosi.

## 11. Lanciare

```bash
uv run cycle-validation eval pipeline --casi eval/casi/aziendali --ripetizioni 3
```

Fa in ordine: verifiche del codice (test, ruff, formato, mypy: se una fallisce si ferma senza
spendere niente), poi `baseline` e ogni variante su tutti i casi rivisti, poi la classifica in
`eval/risultati/classifica.md`. Opzioni:

- `--variante effort_low` (ripetibile): solo queste, più la baseline che c'è sempre;
- `--casi eval/casi/aziendali/mos`: una sola suite;
- `--salta-verifiche`: se le hai appena fatte;
- `--ripetizioni 1`: prova veloce, senza misura della stabilità.

Per stimare tempo e costo fai prima `--variante effort_low --ripetizioni 1` su pochi casi: la
riga finale di ogni variante dice tempo mediano e costo per ciclo. La variante `sonnet` va
corretta in `eval/varianti/sonnet.yaml` con l'id Sonnet abilitato. Durante le prove i transcript
finiscono in `runs/eval/` (contengono testo aziendale, `runs/` è ignorata da git).

## 12. Leggere la classifica e decidere

Si confrontano solo prove dello stesso ambiente (per esempio `bedrock-eu-south-1`), ogni variante
con la sua prova più recente contro l'ultima `baseline`. Una variante è **scartata**, anche se più
veloce, se ha più ERRATO falsi, più errori mancati, concordanza più bassa, più righe instabili,
più esiti tecnici o un'estrazione dal PDF peggiore, oppure se ha girato su casi o conoscenza
diversi. Tra le **ammesse** vince la più veloce (tempo mediano per ciclo), a parità la meno cara.

La colonna "Estrazione" dice quante operazioni e fonti lette dal PDF sono uguali a `ciclo.json`:
se è bassa, gli errori vengono dalla lettura, non dal giudizio. Il dettaglio di ogni riga
sbagliata è nei JSON di `eval/risultati/`.

Quando una variante vince: porta la modifica in `config/settings.yaml` (o nel codice), rilancia
la pipeline per avere la nuova baseline e scrivi la decisione nel registro in fondo a
`docs/MIGLIORIE.md`.

## 13. Errori fabbricati e guasti

Quando i casi sono rivisti:

```bash
uv run cycle-validation eval mutazioni
uv run cycle-validation eval pipeline --casi eval/casi/mutazioni --salta-verifiche
```

Il primo scrive in `eval/casi/mutazioni/` copie dei casi con un difetto di esito noto: targa che
non esiste (WARNING `TARGA_SCONOSCIUTA`), task o scheda che non esistono (WARNING), più copie
innocue (spazi doppi, targhe minuscole) che non devono cambiare niente. Un difetto non trovato
conta come errore mancato.

La variante `guasti` simula servizio che non risponde, risposte storte, passi finiti e
conoscenza irraggiungibile. È giudicata a parte: **regge** se nessun guasto diventa ERRATO e
tutti i casi arrivano in fondo.

## 14. Le varianti

```yaml
nome: effort_low                 # uguale al nome del file
descrizione: meno ragionamento del modello
base: baseline                   # eredita tutto il resto
agent:                           # le stesse chiavi di config/settings.yaml
  effort: low
```

Si possono cambiare `agent`, `paths` e `module_check`. Per un prompt diverso: una cartella con i
tre prompt e `paths: {prompts_dir: ...}`.

| Variante | Cosa prova |
|---|---|
| `effort_pieno` | ragionamento predefinito del modello ovunque, da confrontare con la baseline (low nei controlli, high nel PDF) |
| `effort_low` | low anche nella lettura del PDF |
| `prompt_task_mancante` | task citato non nel manuale: giudica il modello, sapendo che manca (MIGLIORIE A2; la baseline dà WARNING subito) |
| `concorrenza_12`, `sonnet` | 12 operazioni insieme; modello più grande |
| `guasti` | robustezza, giudicata a parte |

---

# C. Se qualcosa non va

| Cosa vedi | Causa probabile | Cosa fare |
|---|---|---|
| il servizio non parte e nomina una variabile | variabile mancante o sbagliata | 4.2 |
| `Configurazione di produzione non valida` | manca la sorgente delle macchine o una variabile Redshift | 4.2 |
| `boto3 non è installato` | installato senza `--extra aws` | 2 |
| il servizio non parte e nomina un file della conoscenza | pubblicazione non valida | `kb-check` sulla versione (6.1) |
| tutte le operazioni "errore tecnico" | Bedrock non risponde | credenziali, regione, `agent.model`; transcript in `runs/` |
| "meno di 100 caratteri di testo (è una scansione?)" | il PDF è una foto | `agent.transcribe_model` |
| "Modulo sbagliato" su un file giusto | marcatori DR | 6.3, `dr_markers` |
| molte targhe ERRATO | elenco macchine incompleto o scritto diverso | 6.3, "Attenzione alle targhe" |
| molte targhe WARNING "Registro macchine non raggiungibile" | Redshift non risponde o query sbagliata | permessi `redshift-data`, `MACHINES_QUERY`; intanto `MACHINES_FILE` |
| `conoscenza non leggibile` in un esperimento | `suite.yaml` non punta alla fotografia giusta | `conoscenza` e puntatori contro le cartelle della fotografia |
| `Nessun caso rivisto`, `saltato ...: esiti attesi da rivedere` | casi ancora in bozza | revisione, punto 10 |
| `verifiche del codice fallite` | test, ruff o mypy rossi | il dettaglio è stampato sopra; nessuna prova è partita |
| `GUASTO ...` su un caso | il caso non è arrivato in fondo | il motivo è nella riga; spesso una foto senza `transcribe_model` |
| `Valori che il PDF riporta su un'altra operazione` | il modello ha messo un valore sulla riga sbagliata | transcript `extract.jsonl` in `runs/eval/` |
| `NON regge` sotto i guasti | un guasto è diventato ERRATO | difetto del codice: tieni il file di risultati |
| `casi diversi` o `conoscenza diversa` | variante e baseline su dati diversi | rilancia la baseline sugli stessi casi e fotografia |

**Cosa non toccare.** Sono ciò che rende affidabile il risultato e costano millisecondi: la
verifica che i valori letti compaiano nel PDF, la verifica che ogni citazione del modello esista
nel manuale a quella riga, l'esito deciso dal codice e non dal modello, un guasto che dà WARNING
e mai ERRATO.

**Regole scelte senza dati veri, da rivedere con chi conosce i cicli.**

| Regola di oggi | Se è sbagliata |
|---|---|
| DR: un serial number con una sola recommendation vale per qualunque condition | si applica una recommendation a una condition non prevista |
| DR: `Accept as is` e `Reject` riconosciuti solo scritti così | una variante di scrittura passa come riparazione normale |
| DR: nessuna recommendation trovata = ERRATO | dati DR incompleti danno ERRATO invece di WARNING |
| Scheda presente ma famiglia del motore non riconosciuta = CORRETTO, con nota | passa una scheda di un'altra famiglia |
| MOS: la fonte è l'OEM del piè di pagina più il task letto dalle NOTE | note scritte in altro modo danno fonti mancanti |
| EJ200: le fonti sono i codici RDR, RN ed EF nel testo (dopo la sigla, o RN/EF da soli) | una fonte scritta in un altro modo non viene trovata |
| Stesso numero di operazione = stessa operazione, anche su pagine diverse | due operazioni distinte diventano una |
| Si leggono solo la prima SCHEDA e il primo SP.ORIG / SP.FIAT di ogni operazione | le successive non vengono controllate |
| EJ200: il paragrafo citato si legge solo accanto al codice (`PAR.`, `FIG.`, `TAB.`, `STEP`…) | un paragrafo scritto altrove non viene mostrato |
| PDF misto testo e scansione: si legge solo il testo | le operazioni delle pagine scansionate mancano, senza avviso |
| Oltre il 20% di parole della descrizione assenti dal PDF: niente modello, WARNING | soglia da tarare sui PDF veri |
| Chi ha solo `cv_ej200` può usare anche le rotte civili | accesso più largo del voluto |
| Elenco delle macchine attive vuoto = "registro non disponibile" (WARNING) | — è voluto: un guasto non diventa ERRATO |
