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

**Dove siamo.** La v2 gira in locale con login e frontend. Il 23-11 sera, sui 7 cicli «con
errori», trova almeno un errore in ognuno: circa 8 dei 12 errori noti, con 0 falsi errori nelle
3 stampe giuste. Gli errori che mancano chiedono documenti che non ci sono (manuale d'ispezione
del motore, due REPAIR della sezione 72-56-31, capitolo 70-23 dell'SPM) o risposte delle persone
(P6, P7, P8). Le migliorie si provano e si scelgono con il blocco 2.3. Quello che è stato fatto
e visto finora è in `MEMORIA.md`.

**In ordine:**

1. **Aggiornare** (2.1) e **Salvare** (2.2).
2. **La base:** due prove con `$nome = "base"` (2.3 A), poi il riepilogo (2.3 C).
3. **Prove dal frontend** (2.4) e **messaggio** al collega (3.2), se non l'hai già mandato.
4. **Domande** alle persone (3.1): P6, P7, P8.
5. **I file mancanti:** cercali dove prendi i manuali; se li trovi, 2.5.
6. **Quando lo decidi tu:** pull request verso `develop` e prova in QA (sezione 4).

Quando Claude dice di aver cambiato il codice: **Aggiornare** (2.1). Se è una miglioria: due
prove con il suo nome (2.3 A) e il riepilogo (2.3 C).

---

## 2. Blocchi

### 2.1 Aggiornare il codice sul PC

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

### 2.2 Salvare nel repository aziendale

Dopo **Aggiornare**. Salva sul ramo `feature/cycle-validation-v2`: `develop` (QA) e `main` non
cambiano finché non apri tu la pull request. I dati aziendali restano fuori (git li ignora).

**Commit:**

```powershell
git add src tests docs eval/casi/sintetici eval/varianti eval/modelli config prompts pyproject.toml uv.lock README.md .gitignore Dockerfile ../buildspec.yml
if (Test-Path vendor) { git add vendor }
git status --short
git commit -m "v2: fonti per riparazione, subtask, task SPM, controllo delle due lingue, prove con metriche"
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

### 2.3 Prove delle migliorie: lanciare, vedere i risultati, scegliere

Una **prova** fa girare la v2 sui 10 cicli (i 7 «con errori» e i 3 giusti) e li confronta con
gli **12 errori noti** scritti in `eval/errori-noti.yaml`. Ogni prova ha la sua cartella in
`runs\prove\<data>-<nome>\` con:

- `prestazioni.md`: il **report della prova** (punteggio con tutte le metriche, ciclo per ciclo,
  errore per errore, ERRATO da verificare, costo, token, tempo);
- `prova.json`: gli stessi numeri, per il riepilogo;
- una cartella per ciclo con il `report.json` completo.

Dopo ogni prova si aggiorna da solo `runs\prove\riepilogo.md`: il **report finale** con tutte
le prove: **scelta migliore**, **classifica delle varianti** con la decisione per ognuna, tabella
delle prove, errore per errore in quali prove è stato trovato, falsi errori.

**Quando:** la prima volta **due prove** con `$nome = "base"` (il punto di partenza); poi, per
ogni miglioria, **Aggiornare** (2.1) e **due prove** con il nome della miglioria. Due prove con
lo stesso nome sono una *variante*: il modello non risponde sempre uguale, e la regola vuole
almeno due ripetizioni.

**Come si sceglie** (lo fa da solo il riepilogo, sezione «Scelta migliore»):

| Metrica | Cosa misura | Regola |
|---|---|---|
| Falsi errori | ERRATO nelle 3 stampe giuste | deve essere **0**, altrimenti scartata |
| Cicli non eseguiti | cicli andati in errore | deve essere 0 |
| Tempo del ciclo più lento | il frontend aspetta 11 minuti | sotto **10 minuti** |
| Costo per ciclo | dollari per ciclo | non più del **doppio** della base |
| **Stabili** | errori noti trovati in **tutte** le prove della variante | 1° criterio: più alto è meglio; mai meno della base |
| Trovati (minimo, media) | errori noti trovati in ogni prova, su 12 | 2° e 3° criterio |
| Da verificare | ERRATO nei cicli con errori fuori dalla lista | 4°: meno è meglio |
| Warning per ciclo giusto | lavoro a mano lasciato su un ciclo senza errori | 5°: meno è meglio |
| Costo, tempo | per ciclo | 6° e 7°: meno è meglio |
| Precisione | trovati / tutti gli ERRATO | solo da guardare |

Una variante **si tiene** se è valida, ha almeno 2 prove, non ha meno errori stabili della base
e sta sopra la base in classifica. Dettagli in `MIGLIORIE.md`.

**A. Lanciare una prova** (costa come 10 cicli, qualche minuto). Cambia solo `$nome`:

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$nome = "base"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$radice = (Resolve-Path "..\..").Path
$dieci = Get-ChildItem $radice -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*errori*" -or (Get-FileHash $_.FullName).Hash.Substring(0, 8).ToLower() -in @("4e64d49a", "8bdb25d5", "04ecaabe") } | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
uv run cycle-validation eval prova @($dieci.FullName) --nome $nome --knowledge $v --config data/settings.yaml
```

**Deve uscire:** una riga per ciclo (`<impronta> errori: trovati ... · mancati ... · ERRATO in
più ...`), poi `Prova «...»: errori noti trovati N su 12 · falsi errori ... · costo ...` e i
percorsi dei due report. Il 23-11 sera (prima delle prove) erano circa **8 su 12** e **0 falsi
errori**.

**B. Vedere il report dell'ultima prova** (gratis). Si apre in VS Code già impaginato:

```powershell
$ultima = Get-ChildItem runs/prove -Directory | Sort-Object Name | Select-Object -Last 1; code "$($ultima.FullName)/prestazioni.md"
```

Poi nella finestra del file premi **Ctrl+Shift+V** (anteprima). Per una prova più vecchia:
`code runs/prove/<cartella>/prestazioni.md`.

**C. Vedere il report finale con tutte le prove, la classifica e la scelta migliore** (gratis):

```powershell
code runs/prove/riepilogo.md
```

Anche qui **Ctrl+Shift+V**. Per vederlo nel terminale invece: `Get-Content runs/prove/riepilogo.md`.

**D. Rifare il report finale** (gratis; serve solo se hai cancellato o spostato una prova):

```powershell
$env:UV_PYTHON = "3.14"; uv run cycle-validation eval riepilogo
```

**E. Elenco delle prove fatte** (gratis): `Get-ChildItem runs/prove -Directory | Select-Object Name`

Per **togliere** una prova dal riepilogo: cancella la sua cartella in `runs\prove\` e lancia D.

**Manda a Claude:** la foto dell'output di A e dell'anteprima di `riepilogo.md`.

### 2.4 Prove dal frontend

Avvia la voce composta **«CV v2»**, poi apri `http://localhost:3000`. Ogni ciclo costa qualche
centesimo. Le targhe escono sempre WARNING: dal PC Redshift non si raggiunge.

1. **I tre cicli «con errori»** (MOS): gli ERRATO devono essere quelli del report della prova (2.3 B).
2. **Il ciclo MOS più lungo:** misura il tempo fino al risultato. Deve stare sotto i 10 minuti
   (il frontend aspetta al massimo 11).
3. **Un DR con serial number e condition**, poi lo stesso **senza** (se Confirm non si accende,
   salta).
4. **File sbagliato:** un DR scegliendo MOS. Deve uscire «Modulo sbagliato».
5. **Storico:** riapri una chat di prima, rinominala, cancellala.
6. **Download** del CSV dei risultati.

**Manda a Claude:** la foto dell'intestazione dei risultati di ogni prova, e il tempo della prova
2 a parole. Se qualcosa non va: foto del frontend e del log di CV v2.

### 2.5 Dopo una nuova ingestion

Quando hai caricato manuali nuovi (per esempio i file che mancano): **fotografia** della
conoscenza (A, va su AWS), **lista dei manuali** (B, gratis), poi una prova (2.3 A) con
`$nome = "conoscenza-<data>"`, due volte.

**A. Fotografia della conoscenza.** Scarica la conoscenza civile di prova pubblicata e la
controlla. La prova (2.3) e la lista dei manuali usano da sole l'ultima fotografia.

```powershell
$env:UV_PYTHON = "3.14"
$foto = "eval/casi/aziendali/conoscenza/foto-" + (Get-Date -Format "yyyyMMdd-HHmm")
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; "versione pubblicata: " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; uv run cycle-validation kb-check ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path)
```

**Deve uscire:** `Fotografia in ...`, una `versione pubblicata` diversa da
`v/20261123T142517Z/` e i conteggi di `kb-check` senza righe `Errore:`.

**B. La lista dei manuali.** Gratis: non chiama il modello e non va su AWS. Legge tutte le
stampe dei cicli e cerca ogni task citato come lo cerca la v2. Per ogni manuale dice `c'è`, `manca` o `c'è, ma mancano N task`, e per
i task che mancano dice perché. Sullo schermo i manuali sono M1, M2, ...; i codici veri restano
nel file `runs\manuali-da-ingestionare.txt`.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; "conoscenza: " + (Split-Path -Leaf $foto) + " · " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation manuali (Resolve-Path "..\..").Path --conoscenza $v --errori 298bc28e=005,035 --errori c5ff3cd6=040 --errori f355dc3c=010,030,040,050
```

**Deve uscire:** una riga per manuale (`M1: ...`). Il 23-11 alle 17:20 M1 aveva 3 task mancanti
e M2 (SPM) 1. Con i file nuovi devono scendere.

**Manda a Claude:** la foto dello schermo (non quella del file).

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
- **P7. Indicazione lineare nell'ispezione FPI** (ciclo f355dc3c e la sua stampa giusta, op.
  050): il ciclo dice «lunga almeno **4** volte la larghezza», l'SPM «**3** volte o più». Il ciclo
  segue un'altra regola (manuale del motore) o è da correggere? La v2 oggi lo segna ERRATO.
- **P8. Riparazione senza task in testata** (c5ff3cd6, nota «applicazione lubrificante secco»;
  298bc28e): quale task del manuale vale per le operazioni che non ne citano uno?

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
