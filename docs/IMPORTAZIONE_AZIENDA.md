# Portare Cycle Validation sul computer aziendale

Questa è l'unica guida che ti serve. Sostituisce `INSTALLAZIONE_AZIENDA.md` e
`PASSAGGIO_AZIENDA.md`.

**Come si usa.** Fai i passi in ordine. Ogni passo ha un comando e il risultato che devi vedere.
Se vedi qualcosa di diverso, fermati a quel passo e guarda la tabella "Se qualcosa non va" in
fondo.

**Le migliorie** stanno in `docs/MIGLIORIE.md`. **Come provare le modifiche** sta in
`docs/BASELINE.md`.

---

## Cosa è già stato provato (14 novembre 2026)

Prove fatte sul computer personale, senza materiale aziendale verso l'esterno.

| Prova | Risultato |
|---|---|
| Test automatici | 558 superati |
| Controllo dello stile del codice (`ruff`) | nessun problema |
| Ciclo di esempio, **con un modello vero** | esiti giusti: la quota sbagliata (46 mm invece di 45 mm) è trovata e citata alla riga giusta |
| Casi di prova MOS, DR, EJ200, **con un modello vero** | MOS 19 su 19, DR 29 su 29, EJ200 22 su 22 |
| Servizio web: scelte, permessi, errori | risposte giuste per ogni caso |
| "Modulo sbagliato" con le due stampe vere | bloccato in tutti e tre i casi provati |
| Lettura delle due stampe vere, senza modello | numero del ciclo, 11 operazioni e schede uguali al risultato atteso |

Il modello vero era Claude Haiku, raggiunto con il login di Claude del computer personale e
**solo con i dati inventati di esempio**. In azienda si passa da Bedrock: cambia la strada, non
il programma.

**Un errore trovato e corretto.** Quando il testo del manuale è lungo, il modello lo cerca da
solo con due strumenti (`Grep` e `Read`). Un controllo di sicurezza bloccava anche lo strumento
con cui il modello consegna la risposta. Così ogni verifica su un testo lungo finiva in
"errore tecnico": tutti i cicli EJ200 e i task MOS lunghi. Ora è corretto e provato con il
modello vero.

**Due sistemazioni pratiche.** `boto3` (la libreria per S3 e Bedrock) ora si installa con il
progetto, al Passo 2. E ogni cartella `docs/Esempio...` è ignorata da git: prima una cartella
`docs/Esempio ciclo DR/` sarebbe finita nel repository.

**Cosa non si è potuto provare qui:** Bedrock, S3, Redshift, l'accesso aziendale, la lettura
di foto e scansioni, un ciclo DR vero. Sono i passi 5, 6 e 8 di questa guida.

---

## Passo 0. Cosa ti serve

| Cosa | A cosa serve | Come controllare |
|---|---|---|
| Git | scaricare il codice | `git --version` |
| Python 3.12 o più recente | far girare il programma | `python --version` |
| uv | installare le librerie | `uv --version` |
| Credenziali AWS aziendali | Bedrock, S3, Redshift | le usi già per gli altri progetti |
| Docker (facoltativo) | avviare il servizio come in produzione | `docker --version` |

Se manca `uv`, scrivi: `pip install uv`.

## Passo 1. Portare il codice

Scegli **una** delle due strade.

**Strada A, da GitHub.** Va bene se dal computer aziendale apri GitHub con il tuo account.

```bash
git clone https://github.com/DavideZanni/cycle-validation-v2.git
cd cycle-validation-v2
```

**Strada B, con un file zip.** Va bene se GitHub è bloccato. Sul computer personale, nella
cartella del progetto:

```bash
git archive --format=zip --output=cycle-validation-v2.zip main
```

Porta lo zip sul computer aziendale, estrailo, entra nella cartella.

In tutte e due le strade viaggia **solo il codice**. Il materiale aziendale non viaggia: in
azienda lo hai già.

## Passo 2. Installare

```bash
uv sync --all-groups --extra aws
```

Devi vedere: nasce la cartella `.venv`, nessun errore. `--extra aws` installa `boto3`, la
libreria per parlare con S3 e Bedrock: senza, la lettura delle foto e il collegamento a S3 non
funzionano.

## Passo 3. Controllare che il codice sia arrivato intero

Qui non serve né la rete né una credenziale.

```bash
uv run pytest
uv run ruff check .
uv run cycle-validation kb-check examples/sintetico/knowledge
```

Devi vedere:

1. `558 passed`;
2. `All checks passed!`;
3. un elenco che finisce con `recommendation_dr: 3`.

Poi prova `mypy`, che sul computer personale non parte:

```bash
uv run mypy
```

Se trova errori, annotali e vai avanti: non bloccano il funzionamento.

## Passo 4. Mettere il materiale aziendale

Crea queste cartelle dentro il progetto e mettici il materiale. Git le ignora: non finiranno mai
nel repository.

| Cartella | Cosa ci va |
|---|---|
| `docs/doc_lavoro/` | documenti di lavoro |
| `docs/Esempio ciclo mos/` | stampe MOS di esempio |
| `docs/Esempio EJ200/` | stampe EJ200 di esempio |
| `docs/Esempio ciclo DR/` | stampe DR di esempio (quando le avrai). Ogni cartella `docs/Esempio...` è ignorata |
| `data/` | conoscenza scaricata (manuali, targhe, schede) |
| `runs/` | risultati delle validazioni |
| `.env` | variabili d'ambiente, se le tieni in un file |

Controllo: scrivi `git status`. Non deve comparire nessuno di questi file.

## Passo 5. Configurare

### 5.1 Il file `config/settings.yaml`

| Voce | Cosa mettere |
|---|---|
| `agent.model` | l'id del modello Haiku abilitato su Bedrock nell'account aziendale. Meglio l'id completo o il profilo di inferenza della regione: la parola `haiku` da sola può puntare a un modello non abilitato |
| `agent.use_bedrock` | `true` (lascialo così) |
| `agent.aws_region` | la regione di Bedrock, per esempio `eu-south-1`. Vuoto = quella dell'ambiente |
| `agent.transcribe_model` | **importante, vedi sotto** |
| `agent.save_transcripts` | `true` mentre provi; `false` nel servizio, perché salva su disco il testo dei cicli e dei manuali |
| `module_check.dr_markers` | come si riconosce un ciclo DR dalla testata: vedi il Passo 8 |

**Foto e scansioni.** Le due stampe di esempio in `docs/Esempio ...` sono **foto**: dentro non
c'è testo. Il programma le legge solo se `agent.transcribe_model` contiene un modello che vede le
immagini (per esempio lo stesso Haiku). Se resta vuoto, una foto viene rifiutata con il messaggio
"contiene meno di 100 caratteri di testo (è una scansione?)". Se in produzione i cicli arrivano
come PDF stampati dal sistema (con testo dentro), puoi lasciarlo vuoto.

### 5.2 Le variabili d'ambiente del servizio

Obbligatorie (senza queste il servizio non parte e ti dice quale manca):

| Variabile | Cosa mettere |
|---|---|
| `BUCKETNAME` | il bucket S3 |
| `REGION_NAME` | la regione AWS |
| `FRONTEND_URL` | l'indirizzo del frontend |

Facoltative:

| Variabile | Se non la metti | Cosa fa |
|---|---|---|
| `API_MAX_UPLOAD_MB` | 50 | dimensione massima del file caricato |
| `EJ200_VALIDATION_ENABLED` | attivo | accende o spegne i cicli militari |
| `EJ200_CATALOG_KEY` | percorso standard | dove sta il catalogo EJ200 su S3 |
| `API_INCLUDE_TRACEBACK` | attivo | **in produzione spegnilo** (`false`) |
| `SECRET_NAME` | vuoto | secret da cui leggere le variabili |

`API_MAX_WORKERS` viene letta ma oggi non fa niente.

## Passo 6. Prima prova con il modello vero, senza dati aziendali

Questa prova dice una cosa sola: Bedrock risponde. Usa i dati inventati del progetto, quindi la
puoi fare subito, prima di collegare S3 e Redshift.

```bash
uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
```

Devi vedere, in 10-20 secondi:

```
Ciclo completo: 10 corretti, 4 warning, 2 errati, 3 non applicabili.
```

Poi i casi di prova:

```bash
uv run cycle-validation golden eval/casi/sintetici/mos --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/dr --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
```

Devi vedere `concordanza 100.0%` per tutti e due. Per MOS va bene anche `94.7%`, se l'unico caso
diverso è `fonte_e_codice_assenti`: è un caso ambiguo noto, il modello a volte risponde WARNING
invece di CORRETTO (spiegato in `docs/MIGLIORIE.md`, punto A2).

Se invece **tutte** le operazioni escono WARNING con "errore tecnico", il modello non risponde:
controlla credenziali, regione e `agent.model`. Il motivo preciso sta nei file in
`runs/ultimo/transcripts/`.

## Passo 7. Collegare i servizi aziendali

È l'unico pezzo di codice da scrivere in azienda, perché servono i client aziendali. Va nella
funzione `build_services` di `src/cycle_validation/api/main.py`. Deve costruire queste cose:

| Cosa | Con che cosa | Classe già pronta |
|---|---|---|
| Archivio dei file (sessioni, feedback) | client `s3` di boto3 | `S3ObjectStore(client, bucket)` |
| Testo dei manuali civili | la cartella di markdown e JSON pubblicata su S3 dalla tua ingestion | `SnapshotManualSource(store, prefisso, cartella_di_lavoro)` |
| Targhe, schede, recommendation DR | i JSON su S3 | `RemoteKnowledgeBase(versione, store, manuali)` |
| Catalogo e testi EJ200 | catalogo su S3 | `Ej200Catalog` e `Ej200KnowledgeBase` |
| Macchine attive | Redshift, oppure un file JSON | `redshift_machine_registry(connect)` oppure `load_machine_registry(file)` |
| Accesso degli utenti | SDK aziendale `chatbot_ai_sdk.auth` | un `AuthBackend` (oppure lasciare l'accesso al frontend, come hai deciso) |
| Costo su CloudWatch (facoltativo) | client `cloudwatch` | `CloudWatchMetrics(client)` |

Le classi esistono e sono provate con dati finti: vanno solo create con i client veri. Come
esempio di montaggio guarda `tests/api_support.py`, che fa la stessa cosa con pezzi finti.

All'avvio chiama `preload()` sulla conoscenza: se un file su S3 ha una forma diversa da quella
attesa, l'errore esce subito e dice quale file e quale campo.

Questo passo lo possiamo scrivere insieme in azienda: bastano i nomi dei prefissi S3 e la query
Redshift.

## Passo 8. Prima prova con un ciclo vero

Prima scarica la conoscenza in una cartella locale (stesso formato che c'è su S3) e controllala:

```bash
uv run cycle-validation kb-check data/<cartella della conoscenza>
```

Poi un ciclo vero da terminale:

```bash
uv run cycle-validation run "docs/Esempio ciclo mos/<file>.pdf" --profile mos --knowledge data/<cartella della conoscenza> --machines data/<macchine attive>.json --config config/settings.yaml
```

Devi vedere una riga come `Ciclo completo: ...` e, in `runs/ultimo`, i file `report.json`,
`report.md` e `payload.json`. Apri `report.md`: è il risultato leggibile.

Per un DR aggiungi `--profile dr --serial-number <S/N> --condition 1`. Per un EJ200 scrivi
`--profile ej200`.

### Cose da confermare con i dati veri

Queste parti sono state scritte senza dati aziendali. Vanno guardate una volta, con un esempio
vero.

| Cosa | Dove si corregge | Come ti accorgi che è sbagliata |
|---|---|---|
| Id del modello Haiku | `agent.model` | tutte le operazioni escono "errore tecnico" |
| Come si riconosce un DR dalla testata | `module_check.dr_markers` | i cicli DR veri vengono rifiutati come "ciclo civile MOS" |
| Formato della cartella dei manuali su S3 | `src/cycle_validation/kb/snapshot.py` | `preload()` dà errore sul `manifest.json` |
| Nomi dei campi nei JSON di targhe, schede, DR | `FieldMap` in `src/cycle_validation/kb/structured.py` | `preload()` dà errore con il nome del campo |
| Percorso dei testi EJ200 su S3 | `DEFAULT_TEXT_PREFIX` in `src/cycle_validation/kb/ej200.py` | i documenti EJ200 risultano "nessun testo su S3" |
| Elenco delle macchine attive | la query Redshift | targhe giuste segnate "non attiva" (ERRATO) |
| La colonna TARGA della stampa è la targa da verificare | `src/cycle_validation/extract/pvrm320_report.py` | esiti sulla macchina sbagliata |

Per il DR c'è una via d'uscita rapida: lascia `dr_markers` vuoto (`dr_markers: []`). Il programma
smette di distinguere MOS da DR e controlla solo civile contro militare.

**Attenzione alle targhe.** Una targa che non è nell'elenco delle macchine attive dà ERRATO.
Se l'elenco è incompleto o scrive le targhe in un altro modo (per esempio `AB/123` contro 
`AB123`), escono molti ERRATO falsi. Controlla i primi risultati a mano.

## Passo 9. Avviare il servizio

In locale:

```bash
uv run uvicorn cycle_validation.api.entry:app --port 8000
```

Prova: apri `http://127.0.0.1:8000/cycle_validation/health`. Devi vedere `{"status":"ok","code":200}`.

Con Docker:

```bash
docker build -t cycle-validation .
docker run -p 8000:8000 --env-file .env cycle-validation
```

Le due rotte per il frontend nuovo:

| Rotta | Cosa fa |
|---|---|
| `GET /cycle_validation/validation/options` | dice quali pulsanti mostrare: civile o militare, poi MOS o DR |
| `POST /cycle_validation/validation/upload` | riceve il file e la scelta, restituisce il risultato |

Campi di `validation/upload`: `file`, `domain` (`civil` o `military`), `civil_type` (`mos` o
`dr`, solo civile), `dr_serial_number` e `dr_condition` (solo DR). Se il file non è del tipo
scelto, la risposta è 422 "Modulo sbagliato". Le rotte storiche (`/upload`, `/ej200/upload`)
funzionano ancora come prima.

## Passo 10. Confronto con il sistema attuale

Ultimo passo, quando tutto il resto funziona. Fai passare gli stessi cicli dal sistema attuale e
da questo. Per ogni differenza scrivi: uguale, meglio o peggio. Il nuovo sistema sostituisce il
vecchio solo se:

1. nessun caso è peggiorato;
2. il tempo per ciclo non è più lungo;
3. il costo per ciclo non è più alto;
4. il frontend accetta la risposta senza modifiche.

## Passo 11. Esperimenti sui cicli veri

Per misurare il programma sui cicli veri e provare le varianti (meno ragionamento, più
concorrenza, un altro modello) c'è una guida a parte: `docs/ESPERIMENTI_AZIENDA.md`. In breve: una
fotografia della conoscenza da S3, i cicli veri con gli esiti controllati da un esperto, e un
comando (`eval pipeline`) che verifica il codice, fa girare tutto e scrive la classifica.

---

## Se qualcosa non va

| Cosa vedi | Causa probabile | Cosa fare |
|---|---|---|
| `Il cablaggio di produzione non è configurato` | manca il Passo 7 | scrivere `build_services` |
| il servizio non parte e nomina una variabile | manca una variabile | Passo 5.2 |
| tutte le operazioni "errore tecnico" | Bedrock non risponde | credenziali, regione, `agent.model`; leggere `runs/ultimo/transcripts/` |
| "meno di 100 caratteri di testo (è una scansione?)" | il PDF è una foto | impostare `agent.transcribe_model` |
| "Modulo sbagliato" su un file giusto | marcatori DR da correggere | Passo 8, `dr_markers` |
| molte targhe ERRATO | elenco macchine incompleto o scritto diverso | Passo 8, "Attenzione alle targhe" |
| una validazione dura minuti | troppe chiamate in fila | `docs/MIGLIORIE.md` |

## Cosa non toccare

Questi controlli costano millisecondi e sono ciò che rende affidabile il risultato:

- la verifica che i valori letti compaiano davvero nel PDF;
- la verifica che ogni citazione del modello esista davvero nel manuale, a quella riga;
- l'esito deciso dal codice, non dal modello;
- un controllo che fallisce per un guasto dà WARNING, mai ERRATO.

## Appendice. Regole scelte senza dati veri, da rivedere con chi conosce i cicli

Il codice le applica oggi così. Se una è sbagliata, la correzione è piccola, ma va decisa da chi
conosce i cicli.

| Regola di oggi | Se è sbagliata |
|---|---|
| DR: se il serial number ha una sola recommendation, vale qualunque sia la condition | si applica una recommendation a una condition non prevista |
| DR: `Accept as is` e `Reject` sono riconosciuti solo scritti esattamente così | una variante di scrittura passa come riparazione normale |
| DR: nessuna recommendation trovata = ERRATO | dati DR incompleti danno ERRATO invece di WARNING |
| Scheda presente ma famiglia del motore non riconosciuta = CORRETTO, con nota | una scheda di un'altra famiglia passa |
| MOS: la fonte è l'OEM del piè di pagina più il task letto dalle NOTE | note scritte in un altro modo danno fonti mancanti |
| EJ200: le fonti sono solo i codici RDR nel testo | RN ed EF non vengono confrontati |
| Stesso numero di operazione = stessa operazione, anche su pagine diverse | due operazioni distinte diventano una |
| Si verificano solo la prima SCHEDA e il primo SP.ORIG di ogni operazione | le successive non vengono controllate |
| PDF con pagine di testo e pagine scansionate: si legge solo il testo | le operazioni delle pagine scansionate mancano, senza avviso |
| Se più del 20% delle parole della descrizione non è nel PDF, l'operazione non va al modello (WARNING) | soglia da tarare sui PDF veri |
| Chi ha solo il permesso `cv_ej200` può usare anche le rotte civili | accesso più largo del voluto |

Comportamenti da conoscere per chi collega il frontend:

- un errore imprevisto risponde `Errore interno (<Tipo>).`, non il testo dell'eccezione;
- un elenco di macchine attive vuoto vale come "Redshift non disponibile" (WARNING), non come
  "tutte le macchine sono ferme";
- `state: succeeded` non vuol dire che ogni controllo è stato fatto: guardare i WARNING e
  `_pipeline_errors`.
