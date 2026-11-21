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

## Messaggio 3: Bedrock risponde (cicli inventati)

Quattro comandi; il primo impiega qualche minuto. Costo: pochi centesimi.

```powershell
$env:UV_PYTHON = "3.14"
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

**Se il `run` dà esiti molto diversi** (per esempio `Ciclo parziale` con tanti warning), il
modello non risponde. Non andare avanti: lancia questo, che mostra i primi errori del dialogo
con il modello con i numeri di account coperti, e manda a Claude la foto:

```powershell
Get-ChildItem runs/ultimo/transcripts/*.jsonl | Select-String -Pattern 'error|denied|certificate|expired|not found' | Select-Object -First 5 | ForEach-Object { $t = $_.Line -replace '\d{12}', '<omesso>'; $t.Substring(0, [Math]::Min(400, $t.Length)) }
```

**Se l'errore parla di certificati** (`SELF_SIGNED_CERT_IN_CHAIN`, `unable to get local issuer
certificate`, `certificate verify failed`): è il proxy aziendale (Zscaler), che la v1 gestisce con
`zscaler.pem`. Lancia questo e poi rilancia il messaggio 3; vale finché non chiudi il terminale:

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## Messaggio 4: la conoscenza vera su S3

Scarica sul tuo PC una copia della conoscenza (in `eval/casi/aziendali/`, che git ignora) e la
controlla. Solo lettura su S3.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --regione eu-south-1 --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/" --out eval/casi/aziendali/conoscenza/foto-20261121
Get-Content ($kb + "current.json")
uv run cycle-validation kb-check ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path)
```

**Deve uscire:** `Fotografia in ...: N oggetti`, il `current.json` con `version` e `path`, il
`kb-check` con i conteggi (documenti, task, targhe, schede…) e nessun `Errore:`. Se `kb-check`
fallisce, **manda a Claude** la foto: dice quale file non va.

---

## Messaggio 5: un ciclo MOS vero

Scarica da `cicli MOS/` il ciclo che finisce con `A1.pdf` nella cartella
`docs\Esempio ciclo mos\` (git la ignora), lo valida con la conoscenza del messaggio 4 e
stampa il riepilogo. Il primo comando svuota prima quella cartella, così dentro c'è un solo
PDF. Qualche minuto; costo: pochi centesimi.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
Remove-Item "docs/Esempio ciclo mos/*.pdf" -ErrorAction SilentlyContinue
aws s3 cp "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/cicli MOS/" "docs/Esempio ciclo mos/" --recursive --exclude "*" --include "*A1.pdf" --region eu-south-1 --only-show-errors
Get-ChildItem "docs/Esempio ciclo mos/*.pdf" | Select-Object Name
uv run cycle-validation run (Get-ChildItem "docs/Esempio ciclo mos/*.pdf" | Select-Object -First 1).FullName --profile mos --knowledge ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path) --config data/settings.yaml
Select-String -Path runs/ultimo/report.md -Pattern '^- (Stato|Esiti|Costo)'
Select-String -Path runs/ultimo/report.md -Pattern '^- \*\*(\S+)\*\* \S+ (.+?) \S+ (ERRATO|WARNING) \((\w+)\)' | ForEach-Object { $g = $_.Matches[0].Groups; "{0,-8} {1,-22} {2,-30} {3}" -f $g[3].Value, $g[1].Value, $g[2].Value, $g[4].Value }
```

**Deve uscire:** il nome del PDF scaricato (uno solo), `Ciclo completo: ...` (o `parziale`), lo
stato, gli esiti e il costo, poi una riga per ogni ERRATO o WARNING: esito, controllo,
operazione o fonte, motivo (per esempio `FONTE_ASSENTE`). Senza elenco delle macchine attive le
righe sulle targhe escono WARNING: è previsto, l'elenco lo colleghiamo dopo.

Il dettaglio completo, con le citazioni dei manuali, è in `runs/ultimo/report.md`: aprilo tu in
VS Code, ma non mandarlo a Claude.

**Manda a Claude** la foto delle righe e dimmi, per ogni ERRATO e WARNING, se secondo te l'esito è
giusto: è la prima misura vera. Per provare un altro ciclo cambia `A1.pdf` nel comando
`aws s3 cp` (per esempio `A3.pdf`) e rilancia il blocco.

I cicli DR vogliono anche il serial number e la repair condition: li proviamo dopo.

---

## Messaggio 6: niente è cambiato nel repository

```powershell
git status --short
```

**Deve uscire:** niente. Se compare un file, **manda a Claude** l'elenco: nessun comando di prova
doveva toccare file tracciati.

Poi **manda a Claude** le foto dei messaggi 2, 3, 4 e 5.
