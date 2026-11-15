# Esperimenti sul computer aziendale

Guida passo passo per far girare gli esperimenti sui **dati veri**: manuali, targhe e cicli
aziendali. Il programma va già installato e provato come in `docs/IMPORTAZIONE_AZIENDA.md`
(Passi 1-6).

## L'idea in breve

Per confrontare le varianti servono tre cose, sempre le stesse per tutte:

1. **la conoscenza**: manuali, targhe, schede, recommendation DR. Se ne fa una *fotografia*,
   cioè una copia datata da S3. Tutte le varianti leggono la stessa fotografia: se un manuale
   cambiasse a metà giro, il confronto non varrebbe più;
2. **i casi**: cicli veri (il PDF) con l'esito giusto riga per riga, controllato da chi
   conosce il ciclo;
3. **le varianti**: i file in `eval/varianti/`.

Poi un comando fa tutto: verifica il codice, fa girare baseline e varianti, scrive la
classifica.

```
eval/casi/aziendali/           ← tutto qui dentro è ignorato da git
├── conoscenza/
│   └── foto-20261120-0930/    la fotografia della conoscenza (copia di S3)
├── macchine_attive.json       l'elenco delle targhe attive
├── mos/
│   ├── suite.yaml             copiato da eval/modelli/aziendali/mos/
│   ├── ciclo_rettifica_01/
│   │   ├── ciclo.pdf          la stampa vera
│   │   ├── ciclo.json         il ciclo letto dal PDF, controllato (riferimento)
│   │   ├── expected.json      gli esiti giusti
│   │   └── revisione.md       la tabella per chi controlla
│   └── ...
├── dr/                        uguale, da eval/modelli/aziendali/dr/
└── ej200/                     uguale, da eval/modelli/aziendali/ej200/
```

**Regola d'oro:** niente di `eval/casi/aziendali/` e di `eval/risultati/` va in git o fuori
dall'azienda. Git li ignora già; controlla con `git status` che non compaiano mai.

## Passo 1. La fotografia della conoscenza

Serve sapere dove la tua ingestion v2 pubblica i file su S3. Ti servono tre cose:

| Cosa | Esempio | Dove guardarlo |
|---|---|---|
| bucket | `nome-bucket` | la variabile `BUCKETNAME` del servizio |
| prefisso dei manuali civili | `Manufacturing AI/exports/manuali/` | cartella con `manifest.json`, `documents/`, `tasks.json` |
| prefissi dei dati strutturati | `structured/TM/`, `structured/SP/`, `structured/DR/` | JSON di targhe, schede, recommendation DR |
| prefisso EJ200 (se serve) | `Manufacturing AI/exports/ej200_publication/` | catalogo e testi delle pubblicazioni |

Poi, con le credenziali AWS dell'ambiente (le stesse del servizio):

```bash
uv sync --extra aws
uv run cycle-validation eval fotografia --bucket nome-bucket \
  --prefisso "Manufacturing AI/exports/manuali/" \
  --prefisso structured/TM/ --prefisso structured/SP/ --prefisso structured/DR/ \
  --prefisso "Manufacturing AI/exports/ej200_publication/" \
  --out eval/casi/aziendali/conoscenza/foto-20261120-0930
```

Il comando copia solo quei prefissi e scrive `fotografia.json` (data, origine, numero di
oggetti). La versione della fotografia entra in ogni risultato: la classifica confronta solo
prove fatte sulla **stessa** fotografia. Quando la conoscenza cambia, fai una fotografia nuova
in una cartella nuova e rilancia anche la baseline.

In alternativa, se hai l'AWS CLI, `aws s3 sync s3://bucket/prefisso cartella/prefisso` per
ogni prefisso dà lo stesso risultato (senza `fotografia.json`: la versione sarà il nome della
cartella).

## Passo 2. Le macchine attive

Il controllo delle targhe chiede quali macchine sono attive. Esporta l'elenco dal sistema delle
macchine in `eval/casi/aziendali/macchine_attive.json`, una lista di targhe:

```json
["TM-1001", "TM-2002", "TM-3003"]
```

Va bene anche `{"active": [...]}`. Le targhe devono essere scritte come nei cicli (vedi
"Attenzione alle targhe" nel Passo 8 di `docs/IMPORTAZIONE_AZIENDA.md`). Se `suite.yaml` nomina
il file e il file non c'è, la prova si ferma con "Registro macchine non leggibile". Se togli la
riga `macchine` da `suite.yaml`, il controllo delle targhe dà WARNING su tutto: utile solo per
provare il resto.

## Passo 3. Le suite

Copia i modelli:

```bash
mkdir -p eval/casi/aziendali
cp -r eval/modelli/aziendali/mos eval/modelli/aziendali/dr eval/modelli/aziendali/ej200 eval/casi/aziendali/
```

In ogni `suite.yaml` correggi:

- `conoscenza`: il nome della cartella della fotografia;
- `manuali`, `targhe`, `schede`, `dr` (oppure `catalogo` e `testi` per EJ200): i prefissi veri
  dentro la fotografia. Sono quelli del Passo 1;
- `estrazione`: lascia `dal_pdf`, così si prova tutto il percorso, lettura del PDF compresa.

Controllo veloce che la conoscenza si legga: il primo comando del Passo 4 si ferma subito, prima
di qualunque chiamata al modello, se la fotografia non è leggibile, e dice perché.

## Passo 4. I casi: bozza e revisione

Per ogni ciclo vero crea una cartella con dentro il PDF, chiamato `ciclo.pdf`:

```bash
mkdir eval/casi/aziendali/mos/ciclo_rettifica_01
cp "percorso/della/stampa.pdf" eval/casi/aziendali/mos/ciclo_rettifica_01/ciclo.pdf
```

Poi chiedi al programma una bozza:

```bash
uv run cycle-validation eval prepara eval/casi/aziendali/mos/ciclo_rettifica_01
```

Per un DR aggiungi `--serial-number SN-... --condition 1`.

Il programma valida il ciclo una volta e scrive tre file:

- `ciclo.json`: il ciclo come l'ha letto dal PDF;
- `expected.json`: i suoi esiti come proposta, con `"rivisto": false`;
- `revisione.md`: una tabella con ogni riga, la spiegazione e la citazione dal manuale.

**La revisione la fa una persona che conosce il ciclo**, riga per riga:

1. apri `revisione.md`;
2. dove l'esito non è giusto, correggi `verdict` e `reason` della stessa riga in `expected.json`
   (le righe sono nello stesso ordine);
3. controlla `ciclo.json` contro la stampa: operazioni, targhe, task, schede. Fa da riferimento
   per misurare quanto bene il programma legge i PDF;
4. quando hai finito, in `expected.json` metti `"rivisto": true`.

Finché `rivisto` è `false` gli esperimenti saltano il caso, e lo dicono: una bozza non
controllata misurerebbe il programma contro se stesso.

**Quanti casi.** Meglio pochi ma vari che tanti uguali. Per partire: 5-10 cicli MOS, 3-5 DR,
5 EJ200, scelti in modo da avere tutti i tipi di esito: almeno qualche ERRATO vero (una
macchina dismessa, un valore sbagliato), qualche WARNING, cicli lunghi e corti. I cicli con un
errore vero sono i più preziosi: sono quelli che misurano gli errori mancati.

Valori possibili per `verdict`: `CORRETTO`, `WARNING`, `ERRATO`, `NON_APPLICABILE`. Per
`reason`, vedi la tabella dei motivi in `docs/GUIDA_VALIDAZIONE_SEMPLICE.md`. Se di una riga
conta solo l'esito, togli `reason` e si confronta solo `verdict`.

## Passo 5. Le impostazioni dell'ambiente

Le varianti partono da `config/settings.yaml`, già configurato al Passo 5 dell'importazione
(modello Bedrock, regione, `transcribe_model` se i cicli sono foto o scansioni). La variante
`sonnet` usa la parola `sonnet`: in azienda va sostituita in `eval/varianti/sonnet.yaml` con
l'id del profilo di inferenza Sonnet abilitato.

Durante le prove `agent.save_transcripts: true` salva in `runs/eval/<prova>/` il testo delle sessioni:
utile per capire un esito strano, ma contiene testo aziendale. `runs/` è ignorata da git.

## Passo 6. La pipeline

```bash
uv sync --all-groups --extra aws
uv run cycle-validation eval pipeline --casi eval/casi/aziendali --ripetizioni 3
```

Fa, in ordine:

1. **verifiche del codice**: test, ruff, formato, mypy. Se una fallisce si ferma, senza
   spendere niente sul modello;
2. **prove**: la baseline, poi ogni variante di `eval/varianti/`, su tutti i casi rivisti, tre
   volte. Stampa una riga per caso, così vedi a che punto è;
3. **classifica**: scritta in `eval/risultati/classifica.md` e stampata.

Opzioni utili:

- `--variante effort_low --variante concorrenza_12`: solo queste (la baseline c'è sempre);
- `--casi eval/casi/aziendali/mos`: una sola suite;
- `--salta-verifiche`: salta il punto 1 (per esempio se l'hai appena fatto);
- `--ripetizioni 1`: una prova veloce, ma senza misura della stabilità.

**Tempo e costo.** Dipendono da quante operazioni hanno i cicli. Fai prima una prova con
`--variante effort_low --ripetizioni 1` su pochi casi: la riga finale di ogni variante dice
tempo mediano e costo per ciclo, e da lì stimi il giro completo (varianti × casi × ripetizioni).

## Passo 7. Leggere la classifica

`eval/risultati/classifica.md` ha, per ogni ambiente (per esempio `bedrock-eu-south-1`):

- le **ammesse**, dalla più veloce: hanno passato i paletti;
- le **scartate**, con il motivo: più ERRATO falsi, più errori mancati, concordanza più bassa,
  più righe instabili, più esiti tecnici, estrazione dal PDF peggiore, oppure casi o
  conoscenza diversi dalla baseline;
- la concordanza **per controllo**, per vedere dove una variante sbaglia.

La colonna "Estrazione" dice quante operazioni e fonti il programma ha letto dal PDF uguali a
`ciclo.json`. Se è bassa, gli errori vengono dalla lettura del PDF, non dal giudizio.

Il dettaglio di ogni riga sbagliata sta nella riga finale di ogni variante, e nei file JSON di
`eval/risultati/`.

## Passo 8. Decidere

Una variante vince se è tra le ammesse e più veloce o meno cara della baseline. Allora:

1. porta la modifica in `config/settings.yaml` (o nel codice);
2. rilancia la pipeline: la nuova baseline è il nuovo riferimento;
3. scrivi la decisione nel registro di `docs/BASELINE.md`.

## Passo 9. Errori fabbricati e guasti

Pochi cicli veri hanno un errore, ma servono proprio quelli per sapere se il programma li
trova. Quando i casi del Passo 4 sono rivisti:

```bash
uv run cycle-validation eval mutazioni
uv run cycle-validation eval pipeline --casi eval/casi/mutazioni --salta-verifiche
```

Il primo comando scrive in `eval/casi/mutazioni/` (ignorata da git) copie dei casi con un
difetto di cui il programma sa l'esito: una targa che non esiste (atteso ERRATO), un task o una
scheda che non esistono (atteso WARNING), più copie con modifiche innocue (spazi doppi, targhe in
minuscolo) che non devono cambiare niente. Il dettaglio è in `eval/README.md`, sezione
"Mutazioni". Se un difetto non viene trovato, la classifica lo conta come errore mancato.

La variante `guasti` simula il servizio che non risponde, le risposte storte, i passi finiti e
la conoscenza irraggiungibile. Gira con le altre nella pipeline, ma è giudicata a parte, sotto
"Prove con guasti simulati": deve **reggere**, cioè nessun guasto deve diventare ERRATO. Costa
meno della baseline, perché le sessioni guaste non chiamano il modello.

## Passo 10. Le varianti di questo giro

| Variante | Cosa prova | Da guardare |
|---|---|---|
| `effort_low` | meno ragionamento ovunque | era ammessa sui casi sintetici, ma sul ciclo di prova leggeva peggio il PDF (87,5%) |
| `effort_low_controlli` | meno ragionamento nei controlli, pieno nella lettura del PDF | se tiene la velocità di `effort_low` senza perdere estrazione |
| `prompt_task_mancante` | dice al modello quando il task citato non è nel manuale | la concordanza del controllo `operation_description` e le righe instabili |
| `guasti` | robustezza | "regge" |

Da questo giro il programma controlla anche due cose della lettura del PDF:

- un trattino o un "n/a" al posto di un codice (per esempio "Targa -") vuol dire **codice
  assente**, non un codice che si chiama "-". Prima la targa "-" diventava ERRATO "macchina non
  attiva": era l'ERRATO falso di `effort_low` sul ciclo di prova;
- se una targa, un task o una scheda letti per un'operazione nel PDF stanno sulla riga di
  un'altra operazione, l'estrazione non è confermata e l'esito è WARNING, non ERRATO. Se il PDF
  non è scritto riga per riga (per esempio a colonne), il controllo non giudica.

## Se qualcosa non va

| Messaggio | Cosa vuol dire | Cosa fare |
|---|---|---|
| `conoscenza non leggibile` | la fotografia non ha i file attesi | controlla i prefissi in `suite.yaml` contro le cartelle della fotografia |
| `Registro macchine non leggibile` | manca `macchine_attive.json` o non è una lista | Passo 2 |
| `manifest.json non trovato sotto ...` | il prefisso `manuali` è sbagliato | deve puntare alla cartella che contiene `manifest.json` |
| `Nessun caso rivisto` | tutti i casi hanno `"rivisto": false` | finisci la revisione del Passo 4 |
| `saltato ...: esiti attesi da rivedere` | quel caso è ancora una bozza | come sopra |
| `verifiche del codice fallite` | test, ruff o mypy rossi | il dettaglio è stampato sopra; nessuna prova è partita |
| `GUASTO ...` su un caso | quel caso non è arrivato in fondo | il motivo è nella riga; spesso il PDF (foto senza `transcribe_model`) |
| molti `esiti tecnici` | il modello non risponde o va in timeout | credenziali, regione, `agent.model`; i transcript in `runs/eval/` |
| `non è stata scritta dal generatore di mutazioni` | la cartella di `--out` contiene file tuoi | scegli un'altra cartella: il comando non tocca file che non ha scritto |
| `Valori che il PDF riporta su un'altra operazione` | il modello ha attribuito un valore alla riga sbagliata | guarda il transcript `extract.jsonl` in `runs/eval/`; se succede spesso, la variante legge male |
| `NON regge` sotto i guasti simulati | un guasto è diventato ERRATO, o un caso non è arrivato in fondo | è un difetto del codice: segnalalo con il file di risultati |
| `casi diversi` o `conoscenza diversa` | la variante e la baseline non hanno girato sugli stessi dati | rilancia la baseline sugli stessi casi e sulla stessa fotografia |
