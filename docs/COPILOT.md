# Prove della v2 sul computer aziendale

**I comandi li lanci tu, nel terminale di VS Code**, non Copilot: la policy aziendale vieta a
Copilot i file in `data/`. Il terminale deve essere nella cartella `app_cycle_validation_v2`
(il prompt finisce con `app_cycle_validation_v2>`). Ogni blocco è da copiare e incollare così
com'è. I comandi non stampano il nome del bucket: puoi mandare a Claude le foto dell'output.

**Se qualcosa va storto:**

- token scaduto (`Token has expired`, `ExpiredToken`, `SSO session`): `aws sso login`, poi
  rilancia lo stesso blocco;
- errore di certificati (`SELF_SIGNED_CERT_IN_CHAIN`, `unable to get local issuer
  certificate`): lancia questo e rilancia il blocco (vale finché non chiudi il terminale):

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## Dove siamo (21-11-2026)

Funzionano Bedrock (Claude Haiku 5.5), la copia della conoscenza da S3 e la lettura dei cicli
veri. Le prove usano **solo il sottoinsieme già ingestionato** in
`ingestion-v2-test-qa-output`: 8 capitoli del manuale SPM e 2 procedure DR. Per i documenti
che non ci sono gli esiti escono WARNING `FONTE_ASSENTE`: è giusto così, non è un errore del
programma. I manuali dei motori si ingestionano più avanti (ultima sezione).

La copia della conoscenza è già sul PC, in `eval/casi/aziendali/conoscenza/foto-20261121/`;
i cicli in `docs\Esempio ciclo mos\` e `docs\Esempio ciclo dr\` (git le ignora).

---

## Aggiornare il codice sul PC

Da lanciare **ogni volta che Claude dice di aver corretto il codice**, e prima del messaggio 9.
Copia nella cartella della v2 codice, test e documenti nuovi dal repository personale (clone
temporaneo, poi cancellato) e lancia i test.

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
```

**Deve uscire:** tutti `passed` (qualche `skipped` va bene), nessun `failed`.

---

## Messaggio 9: le due stampe DR che il parser non legge e il terzo ciclo MOS

`leggi` stampa la pagina 2 delle due stampe DR come il programma la legge dal PDF (zero
token); poi si valida il terzo ciclo MOS, che cita solo task del manuale SPM (qualche
centesimo).

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation leggi (Get-ChildItem "docs/Esempio ciclo dr/*sn.pdf").FullName --profile dr --pagina 2
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
uv run cycle-validation run (Get-ChildItem "docs/Esempio ciclo mos/*.pdf" | Select-Object -Last 1).FullName --profile mos --knowledge ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path) --config data/settings.yaml
Select-String -Path runs/ultimo/report.md -Pattern '^- (Stato|Esiti|Costo)'
Select-String -Path runs/ultimo/report.md -Pattern '^- \*\*(\S+)\*\* \S+ (.+?) \S+ (ERRATO|WARNING|CORRETTO) \((\w+)\)' | ForEach-Object { $g = $_.Matches[0].Groups; "{0,-8} {1,-22} {2,-30} {3}" -f $g[3].Value, $g[1].Value, $g[2].Value, $g[4].Value }
```

**Deve uscire:**

- per ciascuna delle due stampe DR: le righe della pagina 2 numerate (`  12 | ...`), poi
  `non letto dal parser: ... (comincia con «...»)`. **Manda a Claude** le foto di tutte le
  righe (anche più foto): servono per correggere il parser;
- il terzo ciclo MOS: `task_code` dell'operazione 005 CORRETTO (entrambi i task sono
  nell'SPM) e `operation_description` 005 giudicato dal modello. `source` resta
  FONTE_ASSENTE (il manuale del motore non è nel sottoinsieme) e le targhe ERRORE_TECNICO
  (manca l'elenco delle macchine attive).

---

## Messaggio 10: due cicli DR con le recommendation del sottoinsieme

Prova di funzionamento del ramo DR: il ciclo `rip.A6` lanciato con due serial number presi
dalla conoscenza, uno con recommendation **Repair** e uno con **Accept as is**, entrambi di una
procedura DR che è nel sottoinsieme. I serial number li sceglie il comando: non è detto che
siano quelli veri del ciclo, quindi gli esiti delle descrizioni non sono ancora una misura.
Qualche centesimo.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$presenti = (Get-Content ($v + "manifest.json") -Raw | ConvertFrom-Json).documents.code
$rec = (Get-Content ($v + "dr_recommendations.json") -Raw | ConvertFrom-Json) | Where-Object { $_.reference -in $presenti -and $_.conditions.Count -gt 0 }
$ciclo = (Get-ChildItem "docs/Esempio ciclo dr/*rip.A6.pdf" | Select-Object -First 1).FullName
foreach ($r in @(($rec | Where-Object procedure -eq 'Repair' | Select-Object -First 1), ($rec | Where-Object procedure -eq 'Accept as is' | Select-Object -First 1))) {
  "=== $($r.procedure): serial $($r.serial_number), condition $($r.conditions -join ','), procedura $($r.reference)"
  uv run cycle-validation run $ciclo --profile dr --serial-number $r.serial_number --condition ($r.conditions -join ',') --knowledge $v --config data/settings.yaml --out "runs/dr-$($r.procedure -replace ' ', '-')"
  Select-String -Path "runs/dr-$($r.procedure -replace ' ', '-')/report.md" -Pattern '^- \*\*(\S+)\*\* \S+ (.+?) \S+ (ERRATO|WARNING|CORRETTO) \((\w+)\)' | ForEach-Object { $g = $_.Matches[0].Groups; "{0,-8} {1,-22} {2,-30} {3}" -f $g[3].Value, $g[1].Value, $g[2].Value, $g[4].Value }
}
```

**Deve uscire**, per ciascuno dei due:

- **Repair**: `dr_recommendation` CORRETTO; le descrizioni delle operazioni confrontate dal
  modello con il testo della procedura DR (CORRETTO, WARNING o ERRATO a seconda di cosa dice
  la procedura); `source` FONTE_ASSENTE (manuale del motore non nel sottoinsieme);
- **Accept as is**: `dr_recommendation` ERRATO (per quella condition la riparazione non va
  fatta) e i controlli dopo non partono.

**Manda a Claude** le foto. Se sai il serial number e la condition veri di questo ciclo,
dimmeli: si rilancia con quelli e allora l'esito è una misura vera.

---

## Messaggio 11: cosa è cambiato nel repository

```powershell
git status --short
```

**Deve uscire:** solo file sotto `src/`, `tests/` e `docs/` (` M` modificati, `??` nuovi):
sono le correzioni di Claude, da salvare con un commit quando la prova è finita. Se compare
altro (per esempio `data/`, `runs/`, `eval/`), **manda a Claude** l'elenco.

---

## Più avanti: trovare i documenti da ingestionare

Quando si decide di allargare il sottoinsieme. Cerca su S3, sotto `Manufacturing AI/` e fuori
dalla cartella già ingestionata, i file dei manuali citati dai cicli scaricati, delle procedure
DR citate dalle recommendation e delle sezioni che mancano. I codici li prende dai file sul
PC. Solo lettura, nessun costo.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$manuali = uv run cycle-validation leggi (Get-ChildItem "docs/Esempio ciclo mos/*.pdf", "docs/Esempio ciclo dr/*.pdf").FullName | Select-String 'fonti: ([^\s,]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value }
$procedure = (Get-Content ($v + "dr_recommendations.json") -Raw | ConvertFrom-Json).reference
$codici = (@($manuali) + @($procedure) | Where-Object { $_ -and $_ -ne '-' } | Sort-Object -Unique | ForEach-Object { [regex]::Escape($_) }) -join '|'
$codici
aws s3 ls "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/" --recursive --region eu-south-1 | Where-Object { $_ -match "$codici|72-56-3[12]|70-32-0[02]" -and $_ -notmatch 'ingestion-v2' } | Select-Object -First 40 | ForEach-Object { $_.Substring(31) }
```

**Deve uscire:** la riga con i codici cercati, separati da `|`, poi fino a 40 percorsi di
file. **Manda a Claude** la foto: dice quali passare all'ingestion (poche sezioni, non tutti
i 2000 file). Se non esce nessun percorso, i sorgenti non sono sotto `Manufacturing AI/`: dì
a Claude da quale cartella parte la tua ingestion.
