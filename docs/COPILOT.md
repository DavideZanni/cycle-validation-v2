# Messaggi per Copilot: provare la v2 sul computer aziendale

L'importazione nel repository aziendale è fatta (21-11-2026: commit `dfca303` e `7fd60ab` sul
branch `feature/cycle-validation-v2`, test, ruff e mypy verdi su Windows). Il perché delle scelte
è in `docs/IMPORTAZIONE.md`.

Qui si prova la v2 con i servizi veri, in quest'ordine: Bedrock con i cicli inventati, la
conoscenza su S3, un ciclo vero. I messaggi sono i blocchi di testo: copiali in ordine nella
chat di Copilot. Sotto ogni messaggio c'è scritto cosa deve uscire.

**Copilot lancia i comandi di prova, ma non modifica niente**: né codice, né configurazione, né
git. Se un comando fallisce, si ferma e riporta l'errore; la correzione la fa Claude, nel
repository personale, e poi si porta in azienda. I pochi file locali da preparare (impostazioni,
PDF di prova) li prepari tu a mano, nelle cartelle che git ignora.

**Dove fermarsi e mandare a Claude:** dopo il messaggio 2 (sempre), e ogni volta che un
risultato è diverso da quello scritto.

**In ogni terminale nuovo**, prima dei comandi `uv`: `$env:UV_PYTHON = "3.14"` (il progetto
chiede 3.13, sul PC c'è 3.14).

## Prima di cominciare (a mano)

1. Apri questo file nel browser:
   `https://github.com/DavideZanni/cycle-validation-v2/blob/main/docs/COPILOT.md`.
2. In VS Code apri una **nuova** conversazione di Copilot e scegli la modalità **Agent**: serve
   perché possa lanciare i comandi.
3. Le approvazioni devono restare manuali: **non** scegliere *Allow all* (né "approva sempre" o
   simili). Copilot ti mostra ogni comando prima di lanciarlo: leggilo e premi *Continue* solo
   se è uno di quelli scritti nel messaggio.
4. Se Copilot propone una modifica a un file (vedi un riquadro con *Keep* / *Undo*), premi
   **Undo** e usa il messaggio **R** (in fondo).

---

## Messaggio 1: le regole

```text
Per questa conversazione puoi lanciare comandi nel terminale, ma solo per provare il progetto.

Regole:
1. Lancia solo i comandi che ti scrivo io, uno alla volta, nell'ordine. Se pensi che ne serva
   un altro, chiedimelo prima e spiegami perché.
2. Non creare, modificare, spostare o cancellare file, in nessuna cartella. Non usare gli
   strumenti di modifica dei file. Niente git add, commit, push, reset, stash, clean, checkout,
   restore. Niente uv add, uv lock, uv pip, pip install. Gli unici file che possono nascere sono
   quelli che scrivono da soli i comandi di prova (in runs/, data/, eval/casi/aziendali/).
3. Ogni comando parte dalla cartella app_cycle_validation_v2 del repository e con Python 3.14:
   scrivilo sempre nella forma
   Set-Location <radice del repository>\app_cycle_validation_v2; $env:UV_PYTHON = "3.14"; <comando>
4. Se un comando fallisce o dà un risultato diverso da quello che ti dico, fermati. Non provare
   correzioni, non proporre modifiche al codice: riportami il comando e le ultime 40 righe
   dell'output. Le correzioni le fa un'altra persona.
5. Puoi leggere i file del workspace per rispondermi. Non modificare app_cycle_validation/: è
   la versione in produzione.
6. Nelle risposte scrivi <omesso> al posto di numeri di account AWS, ARN, chiavi, token,
   password e URL interni.

Rispondi solo "Regole chiare" se hai capito.
```

**Deve uscire:** "Regole chiare".

---

## Messaggio 2: cosa serve per collegarsi (solo lettura)

```text
#codebase
Leggi senza modificare niente. Mi servono le informazioni per collegare
app_cycle_validation_v2 agli stessi servizi che usa la versione in produzione,
app_cycle_validation/ (codice, configurazione, Dockerfile, buildspec.yml in radice):

a) quale modello Bedrock usa: l'id completo o il profilo di inferenza, scritto esattamente;
b) quale regione AWS usa per Bedrock e per S3;
c) come si chiama il bucket S3 e da dove arriva il nome (variabile d'ambiente, secret, file);
d) da dove legge l'elenco delle macchine attive (TM): database, schema, tabella, query
   esatta, e con quali variabili si collega;
e) se usa un proxy o un certificato particolare per uscire verso AWS.

Poi lancia questi comandi, uno alla volta (non serve la forma della regola 3):

aws --version
aws configure list
aws sts get-caller-identity
$env:AWS_PROFILE
$env:AWS_REGION

e dimmi cosa è uscito, con il numero di account e gli ARN come <omesso>.
```

**Deve uscire:** le risposte a)-e) e l'output dei comandi. Se `aws` non è installato o
`get-caller-identity` dà errore, va bene lo stesso: scrivilo.

**Fermati e manda a Claude** la risposta di Copilot. Il nome del bucket tienilo tu (ti serve nel
messaggio 5), a Claude scrivi `<bucket>`.

---

## Messaggio 3: impostazioni locali (a mano, senza Copilot)

Le impostazioni di prova vanno in una copia dentro `data/`, che git ignora: il file
`config/settings.yaml` del repository non si tocca. Nel **tuo** terminale, da
`app_cycle_validation_v2`, sostituendo `<id del modello>` e `<regione>` con quelli del
messaggio 2:

```powershell
New-Item -ItemType Directory -Force data
(Get-Content config/settings.yaml) -replace '^  model: haiku$', '  model: <id del modello>' -replace '^  aws_region:$', '  aws_region: <regione>' -replace '^  save_transcripts: false$', '  save_transcripts: true' | Set-Content data/settings.yaml
Select-String -Path data/settings.yaml -Pattern '^  (model|aws_region|save_transcripts|use_bedrock):'
git status --short
```

**Deve uscire:** quattro righe, con il tuo id del modello, la tua regione,
`save_transcripts: true` e `use_bedrock: true`. `git status --short` non stampa niente (la
cartella `data/` è ignorata).

`save_transcripts: true` salva in `runs/` il dialogo con il modello: serve per capire un errore.
`runs/` è ignorata da git e resta sul tuo PC.

---

## Messaggio 4: Bedrock risponde (cicli inventati)

```text
Lancia questi comandi, uno alla volta, nella forma della regola 3, e dopo ciascuno dimmi la
riga finale:

uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config data/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/mos --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config data/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/dr --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config data/settings.yaml
$env:CV_LIVE_CONFIG = "data/settings.yaml"; uv run pytest -m live
```

**Deve uscire:**
- `run`: `Ciclo completo: 10 corretti, 4 warning, 2 errati, 3 non applicabili.` in 10-30 secondi;
- `golden` MOS: `concordanza 100,0%` (va bene anche `94,7%` se l'unico caso diverso è
  `fonte_e_codice_assenti`);
- `golden` DR: `concordanza 100,0%`;
- `pytest -m live`: `1 passed`.

Se **tutte** le operazioni del `run` sono errori tecnici, il modello non risponde: credenziali,
regione o id del modello. Chiedi a Copilot:

```text
Leggi i file in runs/ultimo/transcripts/ e dimmi il primo messaggio di errore che trovi, senza
modificare niente.
```

e **manda a Claude** quello che esce. Costo di questo messaggio: pochi centesimi.

---

## Messaggio 5: la conoscenza vera su S3

Sostituisci `<bucket>` e `<regione>` (messaggio 2).

```text
Lancia questi comandi, uno alla volta, nella forma della regola 3:

uv run cycle-validation eval fotografia --bucket <bucket> --regione <regione> --prefisso "Manufacturing AI/cv3/knowledge/" --out eval/casi/aziendali/conoscenza/foto-20261121
Get-Content "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/current.json"

Dal current.json leggi la versione e lancia:

uv run cycle-validation kb-check "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/v/<versione>"

Dimmi l'output di ciascuno.
```

**Deve uscire:** la fotografia scaricata senza errori; il `current.json` con una versione; il
`kb-check` con i conteggi (documenti, task, targhe, schede…) e nessun errore.

Se la fotografia è vuota o `current.json` non c'è, la conoscenza non è ancora pubblicata in
quel percorso: **fermati e manda a Claude** l'output. Se `kb-check` fallisce, manda a Claude il
messaggio: dice quale file non va.

---

## Messaggio 6: un ciclo MOS vero

A mano: crea la cartella `docs\Esempio ciclo mos\` dentro `app_cycle_validation_v2` (git la
ignora) e mettici il PDF di un ciclo MOS che conosci bene. Poi, sostituendo il nome del file e
la versione del messaggio 5:

```text
Lancia questo comando, nella forma della regola 3:

uv run cycle-validation run "docs/Esempio ciclo mos/<file>.pdf" --profile mos --knowledge "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/v/<versione>" --config data/settings.yaml

Poi leggi runs/ultimo/report.md senza modificarlo e dimmi: i conteggi (corretti, warning,
errati, non applicabili), il tempo totale, e per ogni riga ERRATO o WARNING il numero
dell'operazione, il controllo e il motivo (il codice, per esempio FONTE_ASSENTE), senza
copiare il testo dei manuali.
```

**Deve uscire:** `Ciclo completo: ...` e il riepilogo. Senza `--machines` lo stato delle
macchine non si verifica: le righe sulle targhe escono WARNING, è previsto (l'elenco delle
macchine attive lo colleghiamo dopo, con la query del messaggio 2).

**Manda a Claude** il riepilogo di Copilot e dimmi, per le righe ERRATO e WARNING, se secondo te
l'esito è giusto: è la prima misura vera.

---

## Messaggio 7: niente è cambiato nel repository

```text
Lancia, dalla radice del repository (non serve la forma della regola 3):

git status --short

Deve non stampare niente. Dimmi cosa esce.
```

**Deve uscire:** niente. Se compare un file, **fermati e manda a Claude** l'elenco: nessun
comando di prova doveva toccare file tracciati.

---

## Riserva R: Copilot ha provato a modificare un file

Prima premi **Undo** sul riquadro della modifica. Poi:

```text
Hai provato a modificare un file. Ricorda la regola 2: non modifichi niente. Dimmi solo quale
file volevi cambiare, cosa volevi cambiare e perché, così lo riporto a chi corregge il codice.
```

Manda a Claude la risposta.
