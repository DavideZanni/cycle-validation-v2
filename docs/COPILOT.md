# Prove della v2 sul computer aziendale

L'importazione è fatta (21-11-2026, branch `feature/cycle-validation-v2`, test verdi su Windows;
il perché delle scelte è in `docs/IMPORTAZIONE.md`). Regione `eu-south-1`, credenziali AWS con SSO.

Qui si prova la v2 con i servizi veri: Bedrock con i cicli inventati, la conoscenza su S3, un
ciclo vero. **Tutto è da copiare e incollare così com'è**, niente da sostituire.

**I comandi li lanci tu, nel terminale di VS Code**, non Copilot: la policy aziendale vieta a
Copilot i file in `data/` (bucket e impostazioni), ed è giusto così. Dal messaggio 2 in poi il
terminale deve essere nella cartella `app_cycle_validation_v2` (il prompt finisce con
`app_cycle_validation_v2>`), come dopo il messaggio 1. I comandi non stampano il nome del
bucket: puoi mandare a Claude le foto dell'output.

**Se un comando dice che il token è scaduto** (`Token has expired`, `ExpiredToken`,
`SSO session`): `aws sso login`, poi rilancia lo stesso blocco.

---

## Fatto

Messaggio 1 (impostazioni locali): `data/settings.yaml` usa `eu.anthropic.claude-haiku-5-5` per
`model` e `transcribe_model`, `data/bucket.txt` c'è. Il blocco originale è nella storia di git
(commit 7e57e4d), se servisse rifarlo.

---

## Messaggio 2: dov'è la conoscenza della v2 (fatto)

Fatto il 21-11-2026. La conoscenza della versione di prova è sotto
`Manufacturing AI/ingestion-v2-test-qa-output/knowledge/`: `civil/current.json` (versione del
19-11, con `manifest.json`) ed `ej200/current.json` (con `catalog.json`). I cicli veri sono in
`Manufacturing AI/cicli MOS/` e `Manufacturing AI/cicli DR/`. I messaggi 4 e 5 usano questi
percorsi.

---

## Messaggio 3: Bedrock risponde (fatto)

Fatto il 21-11-2026 con Claude Haiku 5.5 su Bedrock (`eu-south-1`), senza problemi di
certificati: `run` sul ciclo inventato `Ciclo completo: 10 corretti, 4 warning, 2 errati, 3 non
applicabili.`; golden MOS 100,0% (19/19, 0,0033 USD, 22 s); golden DR 100,0% (29/29,
0,0007 USD, 6 s); `pytest -m live` 1 passed. Il blocco è nella storia di git (commit 4488c1e),
se servisse rifarlo.

**Se nei messaggi 4 e 5 compare un errore di certificati** (`SELF_SIGNED_CERT_IN_CHAIN`,
`unable to get local issuer certificate`): lancia questo e rilancia il blocco; vale finché non
chiudi il terminale:

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## Messaggio 4: la conoscenza vera su S3 (fatto)

Fatto il 21-11-2026: la copia è in `eval/casi/aziendali/conoscenza/foto-20261121/` (62 oggetti,
civil ed ej200). `kb-check` della versione civil `20261119T141528Z` senza errori: 10 documenti,
13 task, 104 targhe, 94 schede, 23 recommendation DR, nessuna incerta; i conteggi coincidono con
`current.json`. Il blocco è nella storia di git (commit 700e073), se servisse rifarlo.

---

## Messaggio 5: un ciclo MOS vero (fatto)

Fatto il 21-11-2026 sul primo dei tre PDF che finiscono con `A1.pdf`. Il ciclo è letto bene dal
parser di layout (10 operazioni, zero token), ma `Ciclo parziale: 2 corretti, 20 warning,
0 errati, 15 non applicabili.`, 0 sessioni, 0 USD: il manuale citato dal ciclo non è stato
trovato nella conoscenza (`source` FONTE_ASSENTE), quindi non è partito nessun confronto con il
modello. Le targhe escono ERRORE_TECNICO perché manca l'elenco delle macchine attive: previsto.
Il blocco è nella storia di git (commit e327f66), se servisse rifarlo.

---

## Messaggio 6: perché il manuale non si trova (fatto)

Fatto il 21-11-2026. La versione di prova della conoscenza ha 10 documenti: 8 capitoli del
manuale SPM (pratiche standard, capitolo 70) e 2 procedure DR. Il manuale del motore citato dal
ciclo MOS del messaggio 5 non c'è: FONTE_ASSENTE era giusto. Questa conoscenza è fatta per i
cicli DR di quelle due procedure, quindi la prova vera va fatta su uno di quelli.

---

## Messaggio 7: quale ciclo DR provare (fatto)

Fatto il 21-11-2026. Due cose trovate:

- il parser tagliava i task: il ciclo scrive `TASK 70-xx-xx-xxx-xxx` e ne restavano le prime
  tre coppie, che non corrispondono a nessun task del manuale. **Corretto**;
- i task del capitolo 70 (pratiche standard) stanno nel manuale SPM, ma il programma li cercava
  solo nel manuale del motore citato dal ciclo. **Ora li cerca anche nell'SPM** (domanda 16 in
  `docs/DOMANDE_APERTE.md`, da confermare).

Le 23 recommendation DR della conoscenza citano cinque procedure DR, di cui due sono nella
conoscenza; in `cicli DR/` ci sono 10 PDF.

---

## Messaggio 8: portare le correzioni sul PC e rileggere i cicli

Copia nella cartella della v2 il codice, i test e i documenti nuovi dal repository personale
(clone temporaneo, poi cancellato), lancia i test, scarica i cicli DR in
`docs\Esempio ciclo dr\` (git la ignora) e li legge con il parser: **zero token**, nessun
modello. Alla fine rilancia il ciclo MOS del messaggio 5, che adesso trova i task SPM:
qualche centesimo.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
robocopy "$tmp\src" src /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\tests" tests /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\docs" docs /E /NFL /NDL /NJH /NJS /NP
Remove-Item -Recurse -Force $tmp
uv run pytest -q
aws s3 cp "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/cicli DR/" "docs/Esempio ciclo dr/" --recursive --region eu-south-1 --only-show-errors
uv run cycle-validation leggi (Get-ChildItem "docs/Esempio ciclo dr/*.pdf").FullName --profile dr
uv run cycle-validation leggi (Get-ChildItem "docs/Esempio ciclo mos/*.pdf").FullName
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
uv run cycle-validation run (Get-ChildItem "docs/Esempio ciclo mos/*.pdf" | Select-Object -First 1).FullName --profile mos --knowledge ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path) --config data/settings.yaml
Select-String -Path runs/ultimo/report.md -Pattern '^- (Stato|Esiti|Costo)'
Select-String -Path runs/ultimo/report.md -Pattern '^- \*\*(\S+)\*\* \S+ (.+?) \S+ (ERRATO|WARNING|CORRETTO) \((\w+)\)' | ForEach-Object { $g = $_.Matches[0].Groups; "{0,-8} {1,-22} {2,-30} {3}" -f $g[3].Value, $g[1].Value, $g[2].Value, $g[4].Value }
```

**Deve uscire:**

- `pytest`: tutti `passed` (qualche `skipped` va bene), nessun `failed`;
- `leggi`, per ogni PDF: il nome, poi `riparazione · fonti · operazioni` e i `task` letti
  per intero (cinque gruppi, nella forma `72-xx-xx-xxx-xxx`). Un PDF che non è una stampa
  PVRM320 dice `non letto dal parser`: va bene;
- il ciclo MOS: adesso `task_code` dell'operazione 005 trova il task SPM, e
  `operation_description` 005 è giudicato dal modello (costo sopra zero, 1 sessione). Il
  manuale del motore resta assente, quindi `source` e l'operazione 010 restano FONTE_ASSENTE.

**Manda a Claude** le foto: dall'elenco dei task si vede quali cicli DR vanno con quali
recommendation, e quindi con quale serial number e condition lanciarli.

---

## Messaggio 9: cosa è cambiato nel repository

```powershell
git status --short
```

**Deve uscire:** solo file sotto `src/`, `tests/` e `docs/` (` M` modificati, `??` nuovi, per
esempio `tests/test_standard_practices.py`): sono le correzioni del messaggio 8, da salvare
con un commit quando la prova è finita. Se compare altro (per esempio `data/`, `runs/`,
`eval/`), **manda a Claude** l'elenco.
