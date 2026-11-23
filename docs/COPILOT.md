# Lavorare sul PC aziendale

Qui ci sono solo cosa fare adesso e i blocchi da lanciare. Tutto il resto (PC, regole, problemi
già risolti, decisioni, risultati delle prove) è in `docs/MEMORIA.md`.

**Come si lancia un blocco.** Apri il terminale di VS Code nella cartella
`app_cycle_validation_v2` (la riga finisce con `app_cycle_validation_v2>`). Copia il blocco
intero e incollalo. Poi guarda **Deve uscire** e manda a Claude la foto.

**Se qualcosa va storto:**

- `Token has expired`, `ExpiredToken` o `SSO session`: lancia `aws sso login`, poi rilancia il
  blocco;
- `SELF_SIGNED_CERT_IN_CHAIN` o `unable to get local issuer certificate`: lancia questa riga,
  poi rilancia il blocco (vale finché non chiudi il terminale):

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

**Copilot** sempre in modalità **Ask**, non Agent: può leggere e lanciare prove, ma il codice lo
cambia solo Claude.

---

## 1. Cosa fare adesso (23-11-2026)

**Dove siamo.** La v2 gira in locale con login e frontend. Oggi: ingestion di 10 manuali
(versione `v/20261123T142517Z/`) e correzione della v2 per i titoli GE `CIR <sezione>, REPAIR
00N`. Per il manuale principale mancano ancora i due REPAIR della sezione 72-56-31 citati solo in
una frase (file con `-09-001` e `-09-003` nel nome): **sul PC non ci sono**. Manca anche il
capitolo 70-23 dell'SPM.

**In ordine:**

1. **Perché non trova gli errori noti** (blocco 2.1b, gratis): 2.1 del 23-11 alle 16:15 dà
   ancora 0 errati.
2. **Salvare** (blocco 2.5): il codice è cambiato dall'ultimo salvataggio.
3. **I file mancanti:** cercali dove prendi i manuali (i due REPAIR e il capitolo 70-23
   dell'SPM). Se li trovi: ingestion, poi blocchi 2.2, 2.3 e 2.1.
4. **Prove dal frontend** (2.6).
5. **Messaggio** al collega del frontend (3.2), se non l'hai già mandato.
6. **Domande** alle persone (3.1), quando capita.
7. **Più avanti, quando lo decidi tu:** pull request verso `develop` e prova in QA (sezione 4).

Quando Claude dice di aver cambiato il codice: prima **Aggiornare** (2.4).

---

## 2. Blocchi

### 2.1 I cicli con errori

Rilancia i 7 cicli con «errori» nel nome del file, con l'ultima fotografia della conoscenza, e
stampa per ognuno il riepilogo e le righe ERRATO. Ogni ciclo costa qualche centesimo.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; "conoscenza: " + (Split-Path -Leaf $foto) + " · " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $errati) { $h = (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower(); "$h " + (@(uv run cycle-validation run $f.FullName --profile mos --knowledge $v --config data/settings.yaml --out "runs/errori-$h") -match '^Ciclo' | Select-Object -First 1); if (Test-Path "runs/errori-$h/report.json") { (Get-Content "runs/errori-$h/report.json" -Raw | ConvertFrom-Json).results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "    ERRATO op $(if ($_.target.kind -eq 'operation') { $_.target.label } else { $_.target.kind }) · $($_.check) · $($_.reason)" } } }
```

**Deve uscire:** `conoscenza: foto-... · v/...`, poi per ognuno dei 7 cicli una riga
`<impronta> Ciclo ...: N corretti, ...` e sotto le eventuali righe `ERRATO op ...`.

**Manda a Claude:** la foto.

### 2.1b Perché non trova gli errori noti

Gratis: legge i report di 2.1, non rilancia niente. Per le 7 operazioni con un errore noto dei
tre cicli «con errori» (più la 030 con la scheda tolta) stampa ogni controllo: esito, motivo,
chi l'ha deciso (codice o modello) e l'inizio della spiegazione.

```powershell
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$noti = [ordered]@{ "298bc28e" = @("005", "035"); "c5ff3cd6" = @("030", "040"); "f355dc3c" = @("010", "030", "040", "050") }
foreach ($h in $noti.Keys) { $r = Get-Content "runs/errori-$h/report.json" -Raw | ConvertFrom-Json; foreach ($op in $noti[$h]) { "$h op $op"; $r.results | Where-Object { $_.target.kind -eq 'operation' -and $_.target.label.TrimStart('0') -eq $op.TrimStart('0') } | ForEach-Object { $t = "$($_.rationale)" -replace '\s+', ' '; "    $($_.check) · $($_.verdict) · $($_.reason) · $($_.decided_by) · " + $t.Substring(0, [Math]::Min(150, $t.Length)) } } }
```

**Deve uscire:** per ognuna delle 9 operazioni una riga `<impronta> op ...` e sotto una riga per
controllo (`task_code`, `machine_tag`, `process_sheet`, `operation_description`, ...).

**Manda a Claude:** la foto (anche due, se non sta in uno schermo).

### 2.2 Fotografia della conoscenza (dopo ogni ingestion)

Scarica la conoscenza civile di prova pubblicata e la controlla. I blocchi 2.1 e 2.3 usano da
soli l'ultima fotografia.

```powershell
$env:UV_PYTHON = "3.14"
$foto = "eval/casi/aziendali/conoscenza/foto-" + (Get-Date -Format "yyyyMMdd-HHmm")
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; "versione pubblicata: " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; uv run cycle-validation kb-check ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path)
```

**Deve uscire:** `Fotografia in ...`, una `versione pubblicata` diversa da
`v/20261123T142517Z/` e i conteggi di `kb-check` senza righe `Errore:`.

### 2.3 La lista dei manuali

Gratis: non chiama il modello e non va su AWS. Legge tutte le stampe dei cicli e cerca ogni task
citato come lo cerca la v2. Per ogni manuale dice `c'è`, `manca` o `c'è, ma mancano N task`, e per
i task che mancano dice perché. Sullo schermo i manuali sono M1, M2, ...; i codici veri restano
nel file `runs\manuali-da-ingestionare.txt`.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; "conoscenza: " + (Split-Path -Leaf $foto) + " · " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation manuali (Resolve-Path "..\..").Path --conoscenza $v --errori 298bc28e=005,035 --errori c5ff3cd6=040 --errori f355dc3c=010,030,040,050
```

**Deve uscire:** una riga per manuale (`M1: ...`). Il 23-11 alle 16:00 M1 aveva 5 task mancanti
(2 sono solo sezioni, ed è giusto; 3 sono i due REPAIR che mancano). Con i file nuovi devono
scendere.

**Manda a Claude:** la foto dello schermo (non quella del file).

### 2.4 Aggiornare il codice sul PC

Da lanciare **ogni volta che Claude dice di aver cambiato qualcosa**. Prende il codice dal
repository personale, lo copia nella cartella della v2 (toglie i file che non ci sono più) e
lancia i test. Non tocca i dati aziendali (`data/`, `runs/`, `eval/casi/aziendali/`), il
Dockerfile, `vendor/` e `config/settings.azienda.yaml`.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
$qui = (Get-Location).ProviderPath; $mirror = "src", "tests", "prompts", "eval\casi\sintetici", "eval\varianti"
$ok = (Test-Path "$tmp\src\cycle_validation\cli.py") -and ((Split-Path -Leaf $qui) -eq "app_cycle_validation_v2"); if (-not $ok) { "FERMO: download non riuscito o terminale non nella cartella app_cycle_validation_v2. Niente cambiato." }
if ($ok) { $tolti = @(foreach ($d in $mirror) { if (Test-Path $d) { Get-ChildItem $d -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and -not (Test-Path -LiteralPath (Join-Path $tmp $_.FullName.Substring($qui.Length + 1))) } } }) + @(Get-ChildItem docs -File -Filter *.md | Where-Object { -not (Test-Path -LiteralPath "$tmp\docs\$($_.Name)") }); $tolti | ForEach-Object { "tolto: " + $_.FullName.Substring($qui.Length + 1); Remove-Item -LiteralPath $_.FullName -Force } }
if ($ok) { foreach ($d in $mirror) { robocopy "$tmp\$d" $d /MIR /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null }; foreach ($d in "docs", "config", "eval\modelli") { robocopy "$tmp\$d" $d /E /NFL /NDL /NJH /NJS /NP | Out-Null } }
if ($ok) { Copy-Item "$tmp\pyproject.toml", "$tmp\uv.lock", "$tmp\README.md", "$tmp\.gitignore" . -Force }
if ($ok) { Get-ChildItem src, tests -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force; Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache -ErrorAction SilentlyContinue }
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
uv run pytest -q
```

**Deve uscire:** forse qualche riga `tolto: ...`, poi tutti `passed` (qualche `skipped` va
bene), nessun `failed`. Se esce `FERMO`, non è cambiato niente: controlla la cartella del
terminale e rilancia.

**Manda a Claude:** la foto del risultato dei test (e delle righe `tolto:`, se ci sono).

### 2.5 Salvare nel repository aziendale

Dopo **Aggiornare**. Salva sul ramo `feature/cycle-validation-v2`: `develop` (QA) e `main` non
cambiano finché non apri tu la pull request. I dati aziendali restano fuori (git li ignora).

**Commit:**

```powershell
git add src tests docs eval/casi/sintetici eval/varianti eval/modelli config prompts pyproject.toml uv.lock README.md .gitignore Dockerfile ../buildspec.yml
if (Test-Path vendor) { git add vendor }
git status --short
git commit -m "v2: task dei manuali GE trovati nel testo (titoli CIR, sezioni SPM), comando manuali"
```

**Deve uscire:** in `git status` righe solo sotto le cartelle del `git add` (`M` cambiato, `A`
nuovo, `D` tolto), niente sotto `data/` o `runs/`; poi il riepilogo del commit.

**Push** (solo sul ramo giusto e con i file previsti, altrimenti scrive `FERMO`):

```powershell
$branch = git branch --show-current
$fuori = git show --name-only --format= HEAD | Where-Object { $_ -and $_ -notmatch '^app_cycle_validation_v2/(src|tests|docs|eval/casi/sintetici|eval/varianti|eval/modelli|config|prompts|vendor)/|^app_cycle_validation_v2/(pyproject\.toml|uv\.lock|README\.md|\.gitignore|Dockerfile)$|^buildspec\.yml$' }
if ($branch -ne "feature/cycle-validation-v2") {
  "FERMO: sei sul branch '$branch', non su feature/cycle-validation-v2. Niente push."
} elseif ($fuori) {
  "FERMO: nell'ultimo commit ci sono file fuori dalle cartelle previste. Niente push:"; $fuori
} else {
  git push origin feature/cycle-validation-v2; git log --oneline -1; git status -sb | Select-Object -First 1
}
```

**Deve uscire:** la riga del push, l'ultimo commit e
`## feature/cycle-validation-v2...origin/feature/cycle-validation-v2` senza `[ahead ...]`.

**Se esce `FERMO` o il push è rifiutato:** non insistere e non usare `--force`, manda la foto a
Claude. Se il commit dice `nothing to commit`, lancia lo stesso il push.

### 2.6 Prove dal frontend

Avvia la voce composta **«CV v2»**, poi apri `http://localhost:3000`. Ogni ciclo costa qualche
centesimo. Le targhe escono sempre WARNING: dal PC Redshift non si raggiunge.

1. **I tre cicli «con errori»** (MOS): corretti, warning ed errati come nel blocco 2.1.
2. **Il ciclo MOS più lungo:** misura il tempo fino al risultato. Deve stare sotto i 10 minuti
   (il frontend aspetta al massimo 11).
3. **Un DR con serial number e condition**, poi lo stesso **senza** (se Confirm non si accende,
   salta).
4. **File sbagliato:** un DR scegliendo MOS. Deve uscire «Modulo sbagliato».
5. **Storico:** riapri una chat di prima, rinominala, cancellala.
6. **Download** del CSV dei risultati.

**Manda a Claude:** la foto dell'intestazione dei risultati di ogni prova, e il tempo della prova
2 a parole. Se qualcosa non va: foto del frontend e del log di CV v2.

---

## 3. Persone

### 3.1 Domande

Copilot non può rispondere. Chiedile quando capita e scrivi a Claude la risposta a parole (senza
codici veri).

- **P1. Task «70-».** Stanno sempre nel manuale SPM? C'è un altro gruppo di task con la stessa
  regola?
- **P2. Operazione 060 del ciclo DR** (condition 3): la v2 l'ha segnata sbagliata. Lo era
  davvero? Dettaglio in `runs\dr-condition-3\report.md`, da far guardare a chi conosce il ciclo.
- **P4. Targa «90»** (per chi cura l'indice): funzione sbagliata e lettere accentate rovinate. I
  passi sono in `MEMORIA.md`, «Da correggere nell'indice».
- **P6. Scheda mancante.** Quando un'operazione deve avere per forza una scheda? Senza una regola
  la v2 (come la v1) non può sapere che manca.

### 3.2 Messaggio per il collega del frontend

```text
Ciao! Per la v2 di Cycle Validation il serial number e le DR condition diventano facoltativi
(il serial number, se manca, si prende dalla stampa del ciclo).

In CycleValidationPage.tsx il pulsante Confirm resta spento se uno dei due campi è vuoto: si
può lasciarlo attivo anche con i campi vuoti? Le due caselle possono restare, con la scritta
"facoltativo".

Il backend v2 accetta dr_serial_number e dr_condition vuoti (stringa vuota, null o lista
vuota) sia in POST /cycle_validation/conversation sia nel form di
POST /cycle_validation/upload. Tutto il resto resta uguale: stessi indirizzi, stessi campi,
stessa risposta.
```

**Scrivi a Claude** la risposta del collega, a parole.

---

## 4. QA (più avanti)

Il Dockerfile e il buildspec per la v2 sono già sul ramo feature. Finché il ramo non arriva su
`develop`, QA resta sulla v1. **Attenzione:** quando arriverà su `main`, anche la produzione
passerà alla v2: prima serve una prova QA riuscita.

1. **Pull request** da `feature/cycle-validation-v2` verso `develop`. Quando è unita, dal
   frontend QA prova un ciclo MOS e un DR (qui le targhe si controllano davvero). Manda a Claude
   la foto dell'intestazione dei risultati.
2. **Se la v2 in QA non parte:** torna alla v1, poi Salvare e pull request.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --torna-alla-v1
```

3. **Cicli militari** (dopo una prova QA riuscita), poi Salvare e pull request:

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --conoscenza-civile "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json" --ej200 --conoscenza-ej200 "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/ej200/current.json"
```

Se Claude dice che `qa` è cambiato, rilancia lo stesso comando (senza `--ej200` finché i cicli
militari sono spenti), poi Salvare.
