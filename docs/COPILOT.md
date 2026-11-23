# Lavorare sul PC aziendale

Qui ci sono solo il punto in cui siamo, cosa manca e i blocchi da lanciare. Tutto il resto (PC,
regole, problemi già risolti, decisioni) è in `docs/MEMORIA.md`.

**Come si lancia un blocco.** Apri il terminale di VS Code nella cartella
`app_cycle_validation_v2` (la riga finisce con `app_cycle_validation_v2>`). Copia il blocco
intero e incollalo. Poi guarda **Deve uscire** e manda a Claude la foto di **Manda a Claude**.

**Se qualcosa va storto:**

- c'è scritto `Token has expired`, `ExpiredToken` o `SSO session`: lancia `aws sso login`, poi
  rilancia lo stesso blocco;
- c'è scritto `SELF_SIGNED_CERT_IN_CHAIN` o `unable to get local issuer certificate`: lancia
  questa riga, poi rilancia il blocco (vale finché non chiudi il terminale):

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

**Copilot** sempre in modalità **Ask** (in basso nella chat), non Agent: può leggere e lanciare
prove, ma il codice lo cambia solo Claude.

---

## 1. Dove siamo e cosa manca (22-11-2026)

**Fatto:** la v2 gira in locale al posto della v1, con login e frontend (`Validation Passed`
sul ciclo MOS di esempio). Il comando `qa` ha scritto un Dockerfile e un buildspec giusti
(controllati il 22-11).

**Cosa manca, nell'ordine:**

1. **Aggiornare** (sezione 2): porta sul PC il comando nuovo `manuali`.
2. **Lista dei manuali** da ingestionare (4.2): tutti quelli che servono ai cicli di prova.
3. **Salvare** (sezione 3), sul ramo feature. QA non cambia.
4. **Ingestion** dei manuali della lista (la fai tu, con l'ingestion aziendale), poi **4.3**.
5. **Prove in locale dal frontend** (4.1), meglio dopo l'ingestion.
6. **Messaggio** al collega del frontend (5.1), se non l'hai già mandato.
7. **Più avanti, quando lo decidi tu:** pull request verso `develop` e prova in QA
   (sezione 6).

---

## 2. Aggiornare il codice sul PC

Da lanciare **ogni volta che Claude dice di aver cambiato qualcosa**. Prende il codice dal
repository personale, lo copia nella cartella della v2 e lancia i test. In `src`, `tests`,
`prompts`, `eval\casi\sintetici` ed `eval\varianti` toglie i file che nel repository personale
non ci sono più. In `docs` toglie i vecchi file `.md`. Scrive `tolto: ...` per ognuno. Non tocca
i dati aziendali (`data/`, `runs/`, `eval/casi/aziendali/`), il Dockerfile, `vendor/` e
`config/settings.azienda.yaml`.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
$qui = (Get-Location).ProviderPath; $mirror = "src", "tests", "prompts", "eval\casi\sintetici", "eval\varianti"
$ok = (Test-Path "$tmp\src\cycle_validation\cli.py") -and ((Split-Path -Leaf $qui) -eq "app_cycle_validation_v2"); if (-not $ok) { "FERMO: download non riuscito o terminale non nella cartella app_cycle_validation_v2. Niente cambiato." }
if ($ok) { $tolti = @(foreach ($d in $mirror) { if (Test-Path $d) { Get-ChildItem $d -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and -not (Test-Path -LiteralPath (Join-Path $tmp $_.FullName.Substring($qui.Length + 1))) } } }) + @(Get-ChildItem docs -File -Filter *.md | Where-Object { -not (Test-Path -LiteralPath "$tmp\docs\$($_.Name)") }); $tolti | ForEach-Object { "tolto: " + $_.FullName.Substring($qui.Length + 1); Remove-Item -LiteralPath $_.FullName -Force } }
if ($ok) { foreach ($p in "docs\superpowers", "eval\README.md") { if (Test-Path $p) { Remove-Item -Recurse -Force $p; "tolto: $p" } } }
if ($ok) { foreach ($d in $mirror) { robocopy "$tmp\$d" $d /MIR /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null }; foreach ($d in "docs", "config", "eval\modelli") { robocopy "$tmp\$d" $d /E /NFL /NDL /NJH /NJS /NP | Out-Null } }
if ($ok) { Copy-Item "$tmp\pyproject.toml", "$tmp\uv.lock", "$tmp\README.md", "$tmp\.gitignore" . -Force }
if ($ok) { Get-ChildItem src, tests -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force; Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache -ErrorAction SilentlyContinue }
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
uv run pytest -q
```

**Deve uscire:** forse qualche riga `tolto: ...`, poi tutti `passed` (qualche `skipped` va
bene), nessun `failed`. Se esce `FERMO`, non è cambiato niente: controlla la cartella del
terminale e rilancia.

**Manda a Claude:** la foto delle righe `tolto:` (se ci sono) e del risultato dei test.

**Chat di Claude lasciate dalle validazioni (una volta, dopo Aggiornare).** Ogni validazione
lanciata sul PC (Bedrock, non Copilot) lasciava una chat per operazione nella cartella delle chat
di Claude Code (`.claude\projects` nella tua cartella utente). Per questo il pannello di Claude
in VS Code ne mostra tante con i nomi delle operazioni. Dopo Aggiornare la v2 non le scrive
più. Questo blocco **sposta** (non cancella) quelle vecchie in `.claude\chat-validazioni-v2`:
solo le cartelle della v2 (`...cycle-validation-v2...`) e della conoscenza scaricata dal servizio
in locale (`...cycle-validation-knowledge...`). Le tue chat di Claude delle altre cartelle
restano dove sono.

```powershell
$chat = Join-Path $HOME ".claude\projects"; $via = Join-Path $HOME ".claude\chat-validazioni-v2"; New-Item -ItemType Directory -Force $via | Out-Null
$v2 = @(Get-ChildItem $chat -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'cycle-validation-v2|cycle-validation-knowledge' }); "cartelle della v2: " + $v2.Count + " · chat: " + @($v2 | ForEach-Object { Get-ChildItem $_.FullName -Filter *.jsonl }).Count
$v2 | ForEach-Object { Move-Item $_.FullName (Join-Path $via $_.Name) -Force }; "rimaste in projects: " + @(Get-ChildItem $chat -Directory -ErrorAction SilentlyContinue).Count + " cartelle"
```

**Deve uscire:** `cartelle della v2: N · chat: N` e `rimaste in projects: N cartelle`. Chiudi e
riapri il pannello di Claude: le chat delle operazioni non ci sono più. Se ne vedi ancora, manda
a Claude la foto del pannello. Se un giorno non servono più, cancella la cartella
`chat-validazioni-v2`.

---

## 3. Salvare nel repository aziendale

Da lanciare dopo **Aggiornare**, quando Claude dice che ci sono cose nuove da salvare (**adesso
sì**). Salva sul ramo `feature/cycle-validation-v2`. `develop` (QA) e `main` non cambiano finché
non apri tu la pull request. I dati aziendali (`data/`, `runs/`, `eval/casi/aziendali/`, i PDF)
restano fuori, perché git li ignora. I file tolti da Aggiornare risultano `D`: vengono tolti anche
dal repository aziendale.

**3.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici eval/varianti eval/modelli config prompts pyproject.toml uv.lock README.md .gitignore Dockerfile ../buildspec.yml
if (Test-Path vendor) { git add vendor }
git status --short
git commit -m "v2: pulizia dei file vecchi, comando qa per la pubblicazione, documenti aggiornati"
```

**Deve uscire:** in `git status` righe solo sotto le cartelle e i file del `git add` (`M`
cambiato, `A` nuovo, `D` tolto), poi il riepilogo del commit. Niente sotto `data/` o `runs/`.

**3.2 Push.** Manda il commit su GitHub, ma solo se sei sul ramo giusto e se nel commit non c'è
niente fuori dalle cartelle previste. Altrimenti scrive `FERMO` e non fa niente.

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

**Deve uscire:** la riga del push (`feature/cycle-validation-v2 -> feature/cycle-validation-v2`),
l'ultimo commit e `## feature/cycle-validation-v2...origin/feature/cycle-validation-v2` senza
`[ahead ...]`.

**Se esce `FERMO`, o il push è rifiutato** (`rejected`, `fetch first`): non insistere e non
usare `--force`. Manda la foto a Claude. Se il commit dice `nothing to commit`, era già tutto
salvato: lancia lo stesso il push.

---

## 4. Prove in locale

### 4.1 Dal frontend

Avvia la voce composta **«CV v2»** (oppure **login**, **app_frontend** e **CV v2 (porta 8003)**
a mano), poi apri `http://localhost:3000`. Ogni ciclo costa qualche centesimo. Le targhe escono
sempre WARNING e non contano: dal PC Redshift non si raggiunge.

Prove, nell'ordine (salta quelle che non puoi fare):

1. **I tre cicli «con errori»**, MOS. Conta corretti, warning ed errati: devono essere come
   nel blocco 4.3.
2. **Il ciclo MOS più lungo** che hai: misura il tempo dall'invio al risultato. Deve stare sotto
   i 10 minuti, perché il frontend aspetta al massimo 11.
3. **Un DR con serial number e condition**, poi **lo stesso DR senza**. Se il pulsante Confirm
   non si accende senza i due campi, salta la seconda parte.
4. **File sbagliato:** un DR caricato scegliendo MOS. Deve uscire «Modulo sbagliato».
5. **Pulsante militare** (se lo vedi): deve dire che i cicli EJ200 sono spenti. In locale è
   giusto così.
6. **Storico:** riapri una chat di prima dall'elenco a sinistra, rinominala, poi cancellala.
7. **Download** del CSV dei risultati.

**Manda a Claude:** per ogni prova la foto dell'intestazione dei risultati (o del messaggio), e
scrivi a parole il tempo della prova 2. Se qualcosa non va, manda la foto del frontend e quella
del log di CV v2 nel terminale.

### 4.2 La lista dei manuali da ingestionare

Gratis: non chiama il modello e non va su AWS. Il blocco:

- cerca **tutte le stampe di ciclo** in `ProgettoDocumenti` (esempi MOS e DR, cartelle
  `cicli MOS`, cicli «con errori» e giusti) e le legge con il parser (le copie uguali contano
  una volta; i PDF che non sono cicli li salta);
- prende tutti i manuali, i capitoli e i task che i cicli citano;
- li confronta con l'ultima fotografia della conoscenza di prova: per ognuno dice `c'è`,
  `manca` o `c'è, ma mancano N task`;
- mette in cima i manuali che servono per i 10 errori noti dei cicli «con errori» (la scheda
  tolta dell'op. 030 di `c5ff3cd6` non c'entra: è la domanda P6).

Sullo schermo i manuali escono come M1, M2, ... (senza codici). La lista vera (codici,
edizione, capitoli, task e i file dei cicli che li citano) finisce nel file
`runs\manuali-da-ingestionare.txt`, che il blocco apre in VS Code. Il file resta sul PC (git
ignora `runs/`).

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; "conoscenza: " + (Split-Path -Leaf $foto) + " · " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation manuali (Resolve-Path "..\..").Path --conoscenza $v --errori 298bc28e=005,035 --errori c5ff3cd6=040 --errori f355dc3c=010,030,040,050
code runs\manuali-da-ingestionare.txt
```

**Deve uscire:**

1. `conoscenza: foto-... · v/...`;
2. `Stampe: N file, N diverse; cicli letti: N; non lette: N`;
3. `Manuali citati: N; da ingestionare: N.`, poi una riga per manuale
   (`M1: manca · N cicli · N task in N capitoli · serve per N errori (...)`) e forse la riga
   `task senza manuale nelle fonti del ciclo` (di solito i task `70-` del manuale SPM).

Poi si apre il file con la lista.

**Cosa ingestionare:** tutti i manuali con stato `manca` o `c'è, ma mancano ...`, solo i
capitoli scritti nel file. Se non c'è tempo per tutti, parti dall'alto: prima quelli con
`serve per ... errori`.

**Manda a Claude:** la foto dello schermo (non quella del file).

### 4.3 Dopo l'ingestion: i tre cicli «con errori»

Da lanciare **dopo** l'ingestion del manuale, quando la nuova versione è pubblicata. Il blocco
**non fa l'ingestion**: quella la fai prima tu.

Il blocco:

- fa una fotografia nuova della conoscenza civile di prova;
- stampa la versione pubblicata accanto a quella del 21-11;
- rilancia i tre cicli «con errori» e, per ognuno, stampa il riepilogo e le righe ERRATO.

Ogni ciclo costa qualche centesimo. L'ultima prova (22-11) aveva la versione del 19-11, cioè
l'ingestion non era ancora pubblicata, e ha dato 0 errati.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = "eval/casi/aziendali/conoscenza/foto-" + (Get-Date -Format "yyyyMMdd-HHmm")
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$prima = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json"
"versione pubblicata: " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path + " · il 21-11: " + $(if (Test-Path $prima) { (Get-Content $prima | ConvertFrom-Json).path } else { "?" })
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $errati) { $h = (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower(); "$h " + (@(uv run cycle-validation run $f.FullName --profile mos --knowledge $v --config data/settings.yaml --out "runs/errori-$h") -match '^Ciclo' | Select-Object -First 1); if (Test-Path "runs/errori-$h/report.json") { (Get-Content "runs/errori-$h/report.json" -Raw | ConvertFrom-Json).results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "    ERRATO op $(if ($_.target.kind -eq 'operation') { $_.target.label } else { $_.target.kind }) · $($_.check) · $($_.reason)" } } }
```

**Deve uscire:**

1. la riga `Fotografia in ...`;
2. la riga `versione pubblicata: ... · il 21-11: ...`, con due versioni **diverse**;
3. per ognuno dei tre cicli una riga `<impronta> Ciclo ...: N corretti, ...`, e sotto le righe
   `ERRATO op ...`.

Claude le confronta con i 10 errori conosciuti.

**Manda a Claude:** la foto, e scrivi a parole quanti manuali hai ingestionato.

---

## 5. Domande per le persone

Copilot non può rispondere, perché la risposta non è nel codice. Chiedile quando capita e scrivi
a Claude la risposta a parole (senza codici veri).

- **P1. Task «70-».** I task che cominciano con `70-` stanno sempre nel manuale SPM (le pratiche
  standard)? C'è un altro gruppo di task con la stessa regola?
- **P2. Operazione 060 del ciclo DR.** In una prova la v2 ha segnato come sbagliata
  l'operazione 060 del ciclo DR (condition 3). Era davvero sbagliata? Il dettaglio è in
  `runs\dr-condition-3\report.md`: fallo guardare a chi conosce il ciclo, non mandarlo a
  Claude.
- **P4. Targa «90» nell'indice** (per chi cura knowledge-index). Nel file delle targhe la `90`
  ha una frase sbagliata come funzione, e le lettere accentate sono rovinate. Va corretta
  nell'indice (i passi sono in `MEMORIA.md`, «Da correggere nell'indice»).
- **P6. Scheda mancante.** In un ciclo «con errori» l'errore è una scheda tolta da
  un'operazione. Quando un'operazione deve avere per forza una scheda? C'è una regola (tipo di
  lavorazione, targa, parola nella descrizione)? Oggi la v2 segna N/A una scheda assente, come
  la v1: senza una regola non può sapere che manca.
- **P7. Redshift dal PC** (facoltativa). Chi gestisce AWS può dare al tuo ruolo SSO l'uso della
  Data API di Redshift (`redshift-data:ExecuteStatement`, `DescribeStatement`,
  `GetStatementResult`)? Servirebbe solo per provare le targhe sul PC. In QA la v2 legge Redshift
  come la v1.

### 5.1 Messaggio per il collega del frontend

Oggi il pulsante **Confirm** resta spento se serial number o condition sono vuoti, ma la v2 non
ha più bisogno di quei due campi. Manda al collega questo messaggio (Teams o mail):

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

## 6. QA (più avanti)

La v2 è pronta per QA: il Dockerfile e il buildspec sono già scritti e salvati sul ramo feature.
Finché il ramo non arriva su `develop`, QA resta sulla v1. Se prima ti serve portare su
`develop` altro lavoro dello stesso ramo, lancia prima `qa --torna-alla-v1` (6.2) e salva.

**Attenzione:** quando il ramo arriverà su `main`, anche la produzione passerà alla v2. Prima
serve una prova QA riuscita.

**6.1 Pull request e prova.** Apri come al solito la pull request da
`feature/cycle-validation-v2` verso `develop`. Quando è unita, CodeBuild costruisce la v2 e QA
la usa al posto della v1. Poi, dal frontend QA (pagina *Cycle Validation*), prova un ciclo MOS e
un ciclo DR. Qui le targhe si controllano davvero.

**Manda a Claude:** la foto dell'intestazione dei risultati di tutti e due (esito, numero di
errori) e, se ci sono, le righe delle targhe.

**6.2 Se la v2 in QA non parte o non risponde:** si torna alla v1 con questo blocco, poi
Salvare e pull request verso `develop`.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --torna-alla-v1
```

**Deve uscire:** `buildspec: percorsi rimessi sulla v1: N.`

**6.3 Accendere i cicli militari** (dopo una prova 6.1 riuscita). Poi Salvare e pull request.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --conoscenza-civile "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json" --ej200 --conoscenza-ej200 "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/ej200/current.json"
```

**Se Claude dice che `qa` o le impostazioni sono cambiati:** rilancia lo stesso comando (senza
`--ej200` finché i cicli militari sono spenti), poi Salvare.
