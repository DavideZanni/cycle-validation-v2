# Messaggi per Copilot: provare la v2 sul computer aziendale

L'importazione è fatta (21-11-2026, branch `feature/cycle-validation-v2`, test verdi su Windows;
il perché delle scelte è in `docs/IMPORTAZIONE.md`). Le regole a Copilot sono già date e la
ricognizione è fatta: regione `eu-south-1`, credenziali AWS con SSO, bucket e modello della v1
nel suo `.env`.

Qui si prova la v2 con i servizi veri: Bedrock con i cicli inventati, la conoscenza su S3, un
ciclo vero. Copia i blocchi in ordine nella stessa conversazione di Copilot (modalità Agent,
**senza** *Allow all*). Sotto ogni messaggio c'è cosa deve uscire.

**Copilot lancia i comandi di prova, ma non modifica niente.** Se un comando fallisce si ferma e
riporta l'errore; la correzione la fa Claude. I file locali (impostazioni, PDF) li prepari tu a
mano, nelle cartelle che git ignora.

**Prima di incollare** sostituisci `<bucket>` con il valore di `BUCKETNAME` del `.env` della v1.
Il nome del bucket e il numero dell'account non vanno in questo file né a Claude.

**Se un comando dice che il token è scaduto** (`Token has expired`, `ExpiredToken`,
`SSO session`): lancia tu `aws sso login`, poi chiedi a Copilot di rilanciare lo stesso comando.

---

## Messaggio 1: modelli disponibili e conoscenza su S3 (solo lettura)

```text
Lancia questi comandi, uno alla volta (sono solo letture, non serve la forma della regola 3):

aws bedrock list-inference-profiles --region eu-south-1 --query "inferenceProfileSummaries[].inferenceProfileId" --output text
aws s3 ls "s3://<bucket>/Manufacturing AI/cv3/knowledge/" --region eu-south-1
aws s3 ls "s3://<bucket>/Manufacturing AI/cv3/knowledge/civil/" --region eu-south-1

Poi dimmi:
a) l'output completo del primo comando, e se contiene eu.anthropic.claude-haiku-4-5-20251001-v1:0;
b) cosa c'è sotto knowledge/ e sotto knowledge/civil/: c'è un current.json? ci sono cartelle?
Non scrivere il nome del bucket.
```

**Deve uscire:** un elenco di profili `eu.anthropic...` e il contenuto delle due cartelle.

- Se nell'elenco c'è `eu.anthropic.claude-haiku-4-5-20251001-v1:0`: nel messaggio 2 usa la
  **variante A** (Haiku, il modello per cui la v2 è tarata, costa meno).
- Se non c'è: usa la **variante B** (Sonnet 4.5, lo stesso della v1).
- Se `knowledge/civil/` non esiste o non ha `current.json`: la conoscenza della v2 non è ancora
  pubblicata. Fai lo stesso i messaggi 2 e 3, salta 4 e 5, e manda a Claude l'output.

---

## Messaggio 2: impostazioni locali (a mano, senza Copilot)

Le impostazioni di prova vanno in una copia dentro `data/`, che git ignora: `config/settings.yaml`
del repository non si tocca. Nel **tuo** terminale, da `app_cycle_validation_v2`:

```powershell
New-Item -ItemType Directory -Force data
```

**Variante A, Haiku:**

```powershell
(Get-Content config/settings.yaml) -replace '^  model: haiku$', '  model: eu.anthropic.claude-haiku-4-5-20251001-v1:0' -replace '^  aws_region:$', '  aws_region: eu-south-1' -replace '^  save_transcripts: false$', '  save_transcripts: true' | Set-Content data/settings.yaml
```

**Variante B, Sonnet 4.5:**

```powershell
(Get-Content config/settings.yaml) -replace '^  model: haiku$', '  model: eu.anthropic.claude-sonnet-4-5-20250929-v1:0' -replace '^  aws_region:$', '  aws_region: eu-south-1' -replace '^  save_transcripts: false$', '  save_transcripts: true' | Set-Content data/settings.yaml
```

Poi, in tutti e due i casi:

```powershell
Select-String -Path data/settings.yaml -Pattern '^  (model|aws_region|save_transcripts|use_bedrock):'
git status --short
```

**Deve uscire:** quattro righe con il modello scelto, `aws_region: eu-south-1`,
`use_bedrock: true`, `save_transcripts: true`. `git status --short` non stampa niente.

`save_transcripts: true` salva in `runs/` il dialogo con il modello, per capire un errore.
`runs/` è ignorata da git e resta sul tuo PC.

---

## Messaggio 3: Bedrock risponde (cicli inventati)

```text
Lancia questi comandi, uno alla volta, nella forma della regola 3, e dopo ciascuno dimmi le
ultime righe dell'output:

uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config data/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/mos --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config data/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/dr --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config data/settings.yaml
$env:CV_LIVE_CONFIG = "data/settings.yaml"; uv run pytest -m live
```

**Deve uscire:**
- `run`: `Ciclo completo: 10 corretti, 4 warning, 2 errati, 3 non applicabili.`;
- `golden` MOS: `concordanza 100,0%` (va bene anche `94,7%` se l'unico caso diverso è
  `fonte_e_codice_assenti`);
- `golden` DR: `concordanza 100,0%`;
- `pytest -m live`: `1 passed`.

Se il `run` dà molti esiti diversi, o **tutte** le operazioni sono errori tecnici, il modello
non risponde. Chiedi a Copilot:

```text
Leggi i file in runs/ultimo/transcripts/ senza modificare niente e dimmi il primo messaggio di
errore che trovi, con account e ARN come <omesso>.
```

e **manda a Claude** quello che esce, senza andare avanti. Costo del messaggio: pochi centesimi.

---

## Messaggio 4: la conoscenza vera su S3

```text
Lancia questi comandi, uno alla volta, nella forma della regola 3:

uv run cycle-validation eval fotografia --bucket <bucket> --regione eu-south-1 --prefisso "Manufacturing AI/cv3/knowledge/" --out eval/casi/aziendali/conoscenza/foto-20261121
Get-Content "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/current.json"

Dal current.json leggi la versione e lancia:

uv run cycle-validation kb-check "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/v/<versione>"

Dimmi l'output di ciascuno, senza il nome del bucket.
```

**Deve uscire:** la fotografia scaricata senza errori, il `current.json` con una versione, il
`kb-check` con i conteggi (documenti, task, targhe, schede…) e nessun errore. Se `kb-check`
fallisce, **manda a Claude** il messaggio: dice quale file non va.

---

## Messaggio 5: un ciclo MOS vero

A mano: crea la cartella `docs\Esempio ciclo mos\` dentro `app_cycle_validation_v2` (git la
ignora) e mettici il PDF di un ciclo MOS che conosci bene. Poi, sostituendo il nome del file e
la versione del messaggio 4:

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
macchine attive lo colleghiamo dopo, con la query delle macchine della v1).

**Manda a Claude** il riepilogo di Copilot e dimmi, per le righe ERRATO e WARNING, se secondo te
l'esito è giusto: è la prima misura vera.

---

## Messaggio 6: niente è cambiato nel repository

```text
Lancia, dalla radice del repository (non serve la forma della regola 3):

git status --short

Deve non stampare niente. Dimmi cosa esce.
```

**Deve uscire:** niente. Se compare un file, **manda a Claude** l'elenco: nessun comando di prova
doveva toccare file tracciati.

Poi **manda a Claude** le risposte dei messaggi 1, 3, 4 e 5.

---

## R1: Copilot ha provato a modificare un file

Prima premi **Undo** sul riquadro della modifica. Poi:

```text
Hai provato a modificare un file. Ricorda la regola 2: non modifichi niente. Dimmi solo quale
file volevi cambiare, cosa volevi cambiare e perché, così lo riporto a chi corregge il codice.
```

Manda a Claude la risposta.

---

## R2: le regole, se apri una conversazione nuova

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

Incollale come primo messaggio, in modalità **Agent**. Deve uscire "Regole chiare".
