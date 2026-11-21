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

## Messaggio 9: stampe DR e terzo ciclo MOS (fatto)

Fatto il 21-11-2026. Terzo ciclo MOS: `7 corretti, 16 warning, 0 errati, 14 non applicabili`,
3 sessioni, 0,0058 USD. I task delle operazioni 005, 030 e 040 sono tutti nell'SPM
(CORRETTO); descrizioni 005 e 030 CORRETTO, 040 WARNING `EVIDENZA_NON_TROVATA` (il modello
non ha trovato nel testo la conferma); le altre FONTE_ASSENTE (manuale del motore assente).
Le due stampe DR: dopo il banner di fine pagina `*** C O N T I N U A ***` c'è il seguito del
testo della riga NOTE; il parser ora lo attacca alla NOTE. Una delle due stampe scrive il caso
DR e il serial number del pezzo: `leggi` ora li stampa.

---

## Messaggio 10: il ciclo DR con il serial number scritto nella stampa

Fatto il 21-11-2026 fino a `leggi`: test verdi, copia EJ200 cancellata (`False`). Le due stampe
DR passano la pagina 2 ma si fermano a pagina 5 (`blocco senza numero di operazione`,
comincia con «SUPERFICI RACCORDATE.»), e per questo `leggi` non stampava il serial number:
ora lo stampa comunque.

Prima il blocco **Aggiornare il codice sul PC** in cima a questo file (se il test
`test_a_new_version_is_picked_up_after_the_check_interval` fallisce con `WinError 5`, rilancia
solo `uv run pytest -q`). Poi questo: stampa la pagina 5 delle due stampe DR (zero token), poi
lancia la stampa `CON sn` con il suo serial number, una volta per ogni condition che la
conoscenza ha per quel serial number. Finché il parser non legge la pagina 5, `run` estrae il
ciclo con il modello: qualche centesimo per run.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation leggi (Get-ChildItem "docs/Esempio ciclo dr/*sn.pdf").FullName --profile dr --pagina 5
$ciclo = (Get-ChildItem "docs/Esempio ciclo dr/*CON sn.pdf" | Select-Object -First 1).FullName
$sn = ((uv run cycle-validation leggi $ciclo --profile dr) | Select-String 'S/N (\S+)$').Matches[0].Groups[1].Value
"serial number letto dalla stampa: $sn"
$rec = (Get-Content ($v + "dr_recommendations.json") -Raw | ConvertFrom-Json) | Where-Object { $_.serial_number -eq $sn -and $_.conditions.Count -gt 0 }
foreach ($r in $rec) {
  $c = $r.conditions -join ','
  $out = "runs/dr-condition-$($r.conditions -join '-')"
  "=== condition $c, recommendation $($r.procedure)"
  uv run cycle-validation run $ciclo --profile dr --serial-number $sn --condition $c --knowledge $v --config data/settings.yaml --out $out
  Select-String -Path "$out/report.md" -Pattern '^- Costo'
  Select-String -Path "$out/report.md" -Pattern '^- \*\*(\S+)\*\* \S+ (.+?) \S+ (ERRATO|WARNING|CORRETTO) \((\w+)\)' | ForEach-Object { $g = $_.Matches[0].Groups; "{0,-8} {1,-22} {2,-30} {3}" -f $g[3].Value, $g[1].Value, $g[2].Value, $g[4].Value }
}
```

**Deve uscire:**

- per ciascuna delle due stampe DR: le righe della pagina 5 numerate (`  12 | ...`), la riga
  `dr: caso ... · S/N ...` (solo per `CON sn`) e `non letto dal parser: ...`. **Manda a
  Claude** le foto di tutte le righe della pagina 5: servono per correggere il parser;
- `serial number letto dalla stampa: ...` (non vuoto);
- per ogni condition (`=== condition ...`):
  - recommendation **Repair**: `dr_recommendation` CORRETTO e le descrizioni confrontate dal
    modello con il testo della procedura DR, che è nel sottoinsieme (CORRETTO, WARNING o
    ERRATO); `source` FONTE_ASSENTE (manuale del motore assente);
  - recommendation **Accept as is**: `dr_recommendation` ERRATO (per quella condition la
    riparazione non va fatta) e i controlli dopo non partono.

**Manda a Claude** le foto e, se lo sai, quale condition è quella vera di questo pezzo: per
quella l'esito è una misura vera. Le righe ERRATO e WARNING delle descrizioni le puoi leggere
per intero in `runs\dr-condition-...\report.md`, con la citazione della procedura.

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
