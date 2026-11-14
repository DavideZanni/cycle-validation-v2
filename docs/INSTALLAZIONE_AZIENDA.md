# Portare Cycle Validation sul computer aziendale

Guida in due parti:

1. come installare e avviare il progetto sul computer aziendale;
2. come ridurre il tempo di una validazione.

Ogni passo ha un comando e il risultato che devi vedere. Se il risultato è diverso, fermati lì.

---

## Parte 1. Installazione

### Passo 0. Cosa ti serve

| Cosa | A cosa serve | Come controllare |
|---|---|---|
| Git | scaricare il codice | `git --version` |
| Python 3.12 o più recente | far girare il progetto | `python --version` |
| uv | installare le librerie | `uv --version` |
| Credenziali AWS aziendali | S3, Bedrock, Redshift | le hai già per gli altri progetti |

Se `uv` manca: `pip install uv`.

### Passo 1. Portare il codice

Scegli una delle due strade.

**Strada A: da GitHub** (se dal computer aziendale raggiungi GitHub con il tuo account).

```bash
git clone https://github.com/DavideZanni/cycle-validation-v2.git
cd cycle-validation-v2
```

**Strada B: con un file zip** (se GitHub non è raggiungibile). Sul computer personale, dentro la
cartella del progetto:

```bash
git archive --format=zip --output=cycle-validation-v2.zip main
```

Porta lo zip sul computer aziendale, estrailo ed entra nella cartella.

Con tutte e due le strade viaggia **solo il codice**. Il materiale aziendale non viaggia mai: sul
computer aziendale lo hai già.

### Passo 2. Installare le librerie

```bash
uv sync --all-groups
```

Risultato atteso: nasce la cartella `.venv` e non ci sono errori.

### Passo 3. Controllare che funzioni, senza rete

```bash
uv run pytest
uv run ruff check .
uv run cycle-validation kb-check examples/sintetico/knowledge
```

Risultato atteso: tutti i test superati, `All checks passed!`, e un elenco che finisce con
`recommendation_dr: 3`.

Se questo passo riesce, il codice è arrivato intero. Qui non serve ancora nessuna credenziale.

### Passo 4. Mettere il materiale aziendale

Crea queste cartelle dentro il progetto e mettici il materiale. Git le ignora: non finiranno mai
in un commit.

| Cartella | Cosa ci va |
|---|---|
| `docs/doc_lavoro/` | documenti di lavoro |
| `docs/Esempio ciclo mos/` | stampe MOS di esempio |
| `docs/Esempio EJ200/` | stampe EJ200 di esempio |
| `data/` | dati esportati (manuali, targhe, schede) |
| `runs/` | risultati delle validazioni |
| `.env` | variabili d'ambiente, se le tieni in un file |

Controllo: dopo aver copiato i file, `git status` non deve mostrarne nessuno.

### Passo 5. Configurare

**Variabili d'ambiente obbligatorie** (senza queste il servizio non parte):

| Variabile | Cosa metterci |
|---|---|
| `BUCKETNAME` | il bucket S3 |
| `REGION_NAME` | la regione AWS, per esempio `eu-south-1` |
| `FRONTEND_URL` | l'indirizzo del frontend |

**Variabili facoltative** (hanno già un valore predefinito):

| Variabile | Predefinito | Significato |
|---|---|---|
| `API_MAX_UPLOAD_MB` | 50 | dimensione massima del file caricato |
| `EJ200_VALIDATION_ENABLED` | attivo | accende o spegne il percorso militare |
| `EJ200_CATALOG_KEY` | percorso standard | dove sta il catalogo EJ200 su S3 |
| `API_INCLUDE_TRACEBACK` | attivo | in produzione conviene spegnerlo |
| `SECRET_NAME` | vuoto | secret da cui leggere le variabili |

**File `config/settings.yaml`**, le voci da guardare:

| Voce | Cosa fare |
|---|---|
| `agent.model` | mettere l'id del modello Haiku abilitato nell'account aziendale |
| `agent.aws_region` | la regione di Bedrock, se diversa da quella dell'ambiente |
| `agent.transcribe_model` | lasciare vuoto se i cicli arrivano come PDF con testo |
| `agent.concurrency` | quante operazioni controllare insieme (vedi Parte 2) |
| `module_check.dr_markers` | come si riconosce un ciclo DR dalla stampa (vedi Passo 9) |

### Passo 6. Collegare i servizi veri

È l'unico pezzo di codice ancora da scrivere, perché richiede i client aziendali. Sta in
`src/cycle_validation/api/main.py`, nella funzione `build_services`. Deve costruire quattro cose:

| Cosa | Con che cosa | Classe già pronta |
|---|---|---|
| Archivio dei file | client `s3` di boto3 | `S3ObjectStore` |
| Testo dei manuali | la cartella di markdown e JSON su S3 | `SnapshotManualSource` |
| Dati strutturati (targhe, schede, DR) | i JSON su S3 | `RemoteKnowledgeBase` |
| Macchine attive | Redshift, oppure un file JSON | `redshift_machine_registry` o `load_machine_registry` |

Le classi esistono e sono provate con dati finti: vanno solo create con i client veri. All'avvio
chiama `preload()`: se un file su S3 ha una forma inattesa, l'errore esce subito e dice quale file.

### Passo 7. Prima prova vera, da riga di comando

Prima di avviare il servizio, prova un ciclo vero da terminale. Qui il modello viene chiamato
davvero, quindi servono le credenziali AWS attive.

```bash
uv run cycle-validation run "docs/Esempio ciclo mos/<file>.pdf" --profile mos \
    --knowledge data/<cartella della conoscenza> --machines data/<macchine attive>.json
```

Risultato atteso: una riga come `Ciclo parziale: 8 corretti, 2 warning, ...` e i file
`report.json`, `report.md` e `payload.json` in `runs/ultimo`.

Se tutte le operazioni escono WARNING con `ERRORE_TECNICO`, il modello non è raggiungibile:
controlla credenziali, regione e `agent.model`.

Per un DR aggiungi `--profile dr --serial-number <S/N> --condition 1`. Per un EJ200 `--profile ej200`.

### Passo 8. Avviare il servizio

In locale:

```bash
uv run uvicorn cycle_validation.api.entry:app --port 8000
```

Con Docker:

```bash
docker build -t cycle-validation .
docker run -p 8000:8000 --env-file .env cycle-validation
```

Le due rotte che servono al frontend nuovo:

| Rotta | Cosa fa |
|---|---|
| `GET /cycle_validation/validation/options` | dice quali scelte mostrare (civile o militare, MOS o DR) |
| `POST /cycle_validation/validation/upload` | riceve la scelta e il file, restituisce il risultato |

### Passo 9. Cose da confermare con dati veri

Queste parti sono state scritte senza poterle provare su dati aziendali. Vanno controllate una
volta, con un esempio vero.

| Cosa | Dove si corregge | Come accorgersi che è sbagliata |
|---|---|---|
| Come si riconosce un DR dalla stampa | `module_check.dr_markers` in `config/settings.yaml` | i cicli DR veri vengono rifiutati come "ciclo civile MOS" |
| Formato della cartella dei manuali su S3 | `src/cycle_validation/kb/snapshot.py` | `preload()` dà errore sul `manifest.json` |
| Percorso dei testi EJ200 su S3 | `DEFAULT_TEXT_PREFIX` in `src/cycle_validation/kb/ej200.py` | i documenti EJ200 risultano "nessun testo su S3" |
| Nomi dei campi nei JSON di targhe, schede, DR | `FieldMap` in `src/cycle_validation/kb/structured.py` | `preload()` dà errore con il nome del campo |
| Id del modello Haiku | `agent.model` | tutte le operazioni escono `ERRORE_TECNICO` |

Per il primo punto c'è una via d'uscita rapida: lasciare `dr_markers` vuoto. Il sistema smette di
distinguere MOS da DR e controlla solo civile contro militare.

### Se qualcosa non va

| Sintomo | Causa probabile |
|---|---|
| `Il cablaggio di produzione non è configurato` | manca il Passo 6 |
| il servizio non parte e nomina una variabile | manca una variabile del Passo 5 |
| `Modulo sbagliato` su un file giusto | marcatori del Passo 9 da correggere |
| una validazione dura minuti | vedi Parte 2 |

---

## Parte 2. Ridurre il tempo di una validazione

### Dove va il tempo

Misure fatte sul computer personale, senza modello vero.

| Cosa | Tempo |
|---|---|
| Tutto il codice, ciclo da 40 operazioni | 30 millisecondi |
| Tutto il codice, ciclo da 120 operazioni | circa 100 millisecondi |
| Avvio di una sessione dell'agente, prima che il modello risponda | circa 4,8 secondi |

Il codice non pesa. Il tempo è, per ogni operazione del ciclo: avvio dell'agente più risposta del
modello. Per andare più veloci bisogna fare meno avvii, più operazioni insieme, meno chiamate.

### Le migliorie, dalla più utile

**1. Chiamata diretta al modello per i testi corti.** Oggi ogni operazione avvia un processo
dell'agente, anche quando il testo del manuale è già dentro la domanda e non serve cercare nulla.
Con una chiamata diretta a Bedrock quell'avvio di circa 4,8 secondi sparisce. L'agente con `Read`
e `Grep` resta solo per i documenti lunghi. È il guadagno più grande e richiede di scrivere codice.

**2. Più operazioni insieme.** Oggi se ne controllano 6 alla volta (`agent.concurrency`). Con una
risposta simulata di 3 secondi, un ciclo da 40 operazioni dura:

| Operazioni insieme | Durata |
|---|---|
| 1 | 120 secondi |
| 6 (oggi) | 21 secondi |
| 12 | 12 secondi |
| 20 | 6 secondi |

Si cambia in una riga. Il limite vero sono le quote di Bedrock dell'account: va alzato a piccoli
passi guardando se compaiono errori. Conviene farlo dopo la miglioria 1, perché oggi ogni
operazione in più è un processo pesante in più.

**3. Leggere il DR senza modello.** I cicli MOS ed EJ200 vengono letti da un parser, senza
modello. Il DR viene ancora letto dal modello: una chiamata in più per ciclo. Si attiva con una
riga nel profilo `config/profiles/dr.yaml`, ma va provato prima su una stampa DR vera.

**4. Un tempo massimo per sessione.** Oggi non c'è: se una sessione si blocca, tutta la
validazione resta ferma. Non accelera il caso normale, ma evita le attese senza fine.

**5. Non trascrivere se non serve.** La trascrizione di foto e scansioni costa una chiamata per
pagina. Se i cicli arrivano sempre come PDF con testo, `agent.transcribe_model` resta vuoto.

### Cosa misurare in azienda

Ogni validazione scrive i suoi tempi in `report.json`, alla voce `timings_ms` (`ingest`,
`extract`, `checks`, `total`). Prima di cambiare qualcosa, annota questi numeri su tre o quattro
cicli veri. Dopo ogni miglioria, rifai la stessa misura sugli stessi cicli: è l'unico modo per
sapere quanto ha reso.

### Cosa non toccare per andare più veloci

Questi controlli costano millisecondi e sono ciò che rende affidabile il risultato:

- la verifica che i valori letti compaiano davvero nel PDF;
- la verifica che ogni citazione del modello esista nel manuale;
- l'esito deciso dal codice, non dal modello.
