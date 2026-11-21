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

## Messaggio 7: quale ciclo DR provare

Solo lettura, nessun costo. Stampa tre cose: come il ciclo MOS del messaggio 5 scrive i task
(per controllare che il parser li legga interi), le recommendation DR della conoscenza (serial
number, condition, procedura, task) e i nomi dei cicli DR su S3.

```powershell
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
Select-String -Path runs/ultimo/cycle.json -Pattern 'TASK.{0,40}' -AllMatches | ForEach-Object { $_.Matches.Value }
(Get-Content ($v + "dr_recommendations.json") -Raw | ConvertFrom-Json) | Select-Object serial_number, @{n='conditions'; e={$_.conditions -join ','}}, procedure, reference, @{n='tasks'; e={$_.tasks -join ', '}} | Format-Table -AutoSize -Wrap
aws s3 ls "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/cicli DR/" --region eu-south-1 | ForEach-Object { $_.Substring(31) }
```

**Deve uscire:** le righe con `TASK` e il codice com'è scritto nel ciclo, una tabella di 23
recommendation, l'elenco dei PDF in `cicli DR/`. **Manda a Claude** la foto (anche più di una se
l'elenco è lungo) e, se lo sai, di quale serial number e condition è ciascun ciclo DR: il nome
del file da solo non lo dice.

---

## Messaggio 8: niente è cambiato nel repository

```powershell
git status --short
```

**Deve uscire:** niente. Se compare un file, **manda a Claude** l'elenco: nessun comando di prova
doveva toccare file tracciati.
