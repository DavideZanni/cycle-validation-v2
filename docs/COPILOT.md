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

## Messaggio 6: perché il manuale non si trova

Stampa i nomi con cui la conoscenza conosce i suoi 10 documenti e le fonti e i task che il
parser ha letto dal ciclo del messaggio 5. Solo lettura, nessun costo.

```powershell
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$m = Get-Content ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path + "manifest.json") -Raw | ConvertFrom-Json
$m.documents | Select-Object key, code, kind, version, published, @{n='aliases'; e={$_.aliases -join ', '}} | Format-Table -AutoSize -Wrap
$c = Get-Content runs/ultimo/cycle.json -Raw | ConvertFrom-Json
$c.sources | Select-Object manual, task, repair_code, issue | Format-Table -AutoSize -Wrap
$c.operations | Select-Object operation_number, repair_code, machine_tag, @{n='task_codes'; e={$_.task_codes -join ', '}} | Format-Table -AutoSize -Wrap
```

**Deve uscire:** tre tabelle. La prima ha 10 righe, una per documento della conoscenza, con
`key`, `code` e gli alias. La seconda ha le fonti del ciclo, con il manuale citato. La terza ha
le 10 operazioni con i loro task code. **Manda a Claude** la foto di tutte e tre: dal confronto
tra la prima e la seconda si vede se il manuale manca davvero o se è scritto in un altro modo.

---

## Messaggio 7: niente è cambiato nel repository

```powershell
git status --short
```

**Deve uscire:** niente. Se compare un file, **manda a Claude** l'elenco: nessun comando di prova
doveva toccare file tracciati.
