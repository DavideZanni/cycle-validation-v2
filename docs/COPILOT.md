# Messaggi per Copilot: provare la v2 sul computer aziendale

L'importazione è fatta (21-11-2026, branch `feature/cycle-validation-v2`, test verdi su Windows;
il perché delle scelte è in `docs/IMPORTAZIONE.md`). Le regole a Copilot sono già date e la
ricognizione è fatta: regione `eu-south-1`, credenziali AWS con SSO.

Qui si prova la v2 con i servizi veri: Bedrock con i cicli inventati, la conoscenza su S3, un
ciclo vero. **Tutto è da copiare e incollare così com'è**, niente da sostituire. Il messaggio 1
lo lanci tu nel tuo terminale; gli altri li incolli nella stessa conversazione di Copilot
(modalità Agent, **senza** *Allow all*). Sotto ogni messaggio c'è cosa deve uscire.

**Copilot lancia i comandi di prova, ma non modifica niente.** Se un comando fallisce si ferma e
riporta l'errore; la correzione la fa Claude.

**Se un comando dice che il token è scaduto** (`Token has expired`, `ExpiredToken`,
`SSO session`): lancia tu `aws sso login`, poi chiedi a Copilot di rilanciare lo stesso comando.

---

## Messaggio 1: impostazioni locali (tu, nel tuo terminale)

Nel terminale di VS Code, dalla radice del repository aziendale. I comandi scrivono solo in
`app_cycle_validation_v2/data/`, che git ignora: `config/settings.yaml` non si tocca. Il nome
del bucket lo prendono dal `.env` della v1 e resta sul tuo PC.

Il modello lo scelgono da soli tra quelli che Bedrock offre a Milano, in quest'ordine:
**Claude Haiku 5.5** (il più recente), poi Haiku 4.5, poi Sonnet 4.5 (quello della v1). Solo
profili `eu.`: i dati restano in Europa. Lo stesso modello legge anche foto e scansioni
(`transcribe_model`), così i cicli scansionati non vengono più rifiutati.

```powershell
cd app_cycle_validation_v2
$env:UV_PYTHON = "3.14"
New-Item -ItemType Directory -Force data | Out-Null
(Select-String -Path ..\app_cycle_validation\.env -Pattern '^BUCKETNAME=(.+)$').Matches[0].Groups[1].Value.Trim().Trim('"') | Set-Content data/bucket.txt
$ids = @((aws bedrock list-inference-profiles --region eu-south-1 --query "inferenceProfileSummaries[].inferenceProfileId" --output text) -split '\s+' | Where-Object { $_ })
$modello = @(($ids -match '^eu\.anthropic\.claude-haiku-5-5') + ($ids -match '^eu\.anthropic\.claude-haiku-4-5') + 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0')[0]
"Modelli Claude disponibili: $($ids -match 'claude-(haiku|sonnet|opus)')"
"Modello scelto: $modello"
(Get-Content config/settings.yaml) -replace '^  model: haiku$', "  model: $modello" -replace '^  transcribe_model:$', "  transcribe_model: $modello" -replace '^  aws_region:$', '  aws_region: eu-south-1' -replace '^  save_transcripts: false$', '  save_transcripts: true' | Set-Content data/settings.yaml
Test-Path data/bucket.txt
Select-String -Path data/settings.yaml -Pattern '^  (model|transcribe_model|aws_region|save_transcripts|use_bedrock):'
git status --short
```

**Deve uscire:**
- l'elenco dei modelli Claude disponibili e `Modello scelto: eu.anthropic.claude-haiku-5-5...`;
- `True`;
- cinque righe: `model:` e `transcribe_model:` con il modello scelto, `aws_region: eu-south-1`,
  `use_bedrock: true`, `save_transcripts: true`;
- `git status --short` non stampa niente.

**Se il modello scelto non è Haiku 5.5**, Bedrock a Milano non lo offre ancora al vostro account:
le prove vanno avanti lo stesso con quello scelto, ma **manda a Claude** la riga "Modelli Claude
disponibili". Per avere Haiku 5.5 va chiesto a chi gestisce l'account AWS di abilitarlo
(Bedrock → *Model access*) per `eu-south-1`; poi rilanci questo messaggio da `$ids = ...`.

Se `Select-String` sul `.env` dà errore (`Cannot index into a null array`), nel `.env` non c'è
`BUCKETNAME`: fermati e dillo a Claude. Se `aws bedrock` dà errore di token: `aws sso login` e
rilancia da `$ids = ...`.

`save_transcripts: true` salva in `runs/` il dialogo con il modello, per capire un errore;
`runs/` è ignorata da git e resta sul tuo PC.

---

## Messaggio 2: la conoscenza della v2 è pubblicata? (Copilot, solo lettura)

```text
Lancia questi comandi, uno alla volta, nella forma della regola 3:

aws s3 ls "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/cv3/knowledge/" --region eu-south-1
aws s3 ls "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/cv3/knowledge/civil/" --region eu-south-1

Dimmi cosa c'è sotto knowledge/ e sotto knowledge/civil/: c'è un current.json? ci sono
cartelle? Non scrivere il nome del bucket.
```

**Deve uscire:** sotto `civil/` un `current.json` e una cartella `v/`. Se `civil/` non esiste o
non ha `current.json`, la conoscenza della v2 non è ancora pubblicata: fai il messaggio 3, salta
il 4 e il 5, e manda a Claude l'output.

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
non risponde. Incolla a Copilot:

```text
Leggi i file in runs/ultimo/transcripts/ senza modificare niente e dimmi il primo messaggio di
errore che trovi, con account e ARN come <omesso>.
```

e **manda a Claude** quello che esce, senza andare avanti. Costo del messaggio: pochi centesimi.

---

## Messaggio 4: la conoscenza vera su S3

```text
Lancia questi comandi, uno alla volta, nella forma della regola 3, e dimmi l'output di
ciascuno senza il nome del bucket:

uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --regione eu-south-1 --prefisso "Manufacturing AI/cv3/knowledge/" --out eval/casi/aziendali/conoscenza/foto-20261121
Get-Content "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/current.json"
uv run cycle-validation kb-check ("eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/" + (Get-Content "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/current.json" | ConvertFrom-Json).path)
```

**Deve uscire:** `Fotografia in ...: N oggetti`, il `current.json` con `version` e `path`, il
`kb-check` con i conteggi (documenti, task, targhe, schede…) e nessun errore. Se `kb-check`
fallisce, **manda a Claude** il messaggio: dice quale file non va.

---

## Messaggio 5: un ciclo MOS vero

A mano: dentro `app_cycle_validation_v2` crea la cartella `docs\Esempio ciclo mos\` (git la
ignora) e mettici **un solo** PDF, un ciclo MOS che conosci bene. Poi incolla a Copilot:

```text
Lancia questo comando, nella forma della regola 3:

uv run cycle-validation run (Get-ChildItem "docs/Esempio ciclo mos/*.pdf" | Select-Object -First 1).FullName --profile mos --knowledge ("eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/" + (Get-Content "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/cv3/knowledge/civil/current.json" | ConvertFrom-Json).path) --config data/settings.yaml

Poi leggi runs/ultimo/report.md senza modificarlo e dimmi: i conteggi (corretti, warning,
errati, non applicabili), il tempo totale, e per ogni riga ERRATO o WARNING il numero
dell'operazione, il controllo e il motivo (il codice, per esempio FONTE_ASSENTE), senza
copiare il testo dei manuali.
```

**Deve uscire:** `Ciclo completo: ...` e il riepilogo. Senza elenco delle macchine attive le
righe sulle targhe escono WARNING: è previsto, l'elenco lo colleghiamo dopo.

**Manda a Claude** il riepilogo e dimmi, per le righe ERRATO e WARNING, se secondo te l'esito è
giusto: è la prima misura vera.

---

## Messaggio 6: niente è cambiato nel repository

```text
Lancia, dalla radice del repository (non serve la forma della regola 3):

git status --short

Deve non stampare niente. Dimmi cosa esce.
```

**Deve uscire:** niente. Se compare un file, **manda a Claude** l'elenco: nessun comando di prova
doveva toccare file tracciati.

Poi **manda a Claude** le risposte dei messaggi 2, 3, 4 e 5.

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
