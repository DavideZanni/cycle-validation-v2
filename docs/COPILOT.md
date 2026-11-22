# Lavorare sul PC aziendale

Questo è il file da usare sul PC. Dentro ci sono:

1. cosa fare adesso;
2. i comandi da lanciare (blocchi da copiare e incollare);
3. le domande per Copilot;
4. le domande per le persone e il messaggio per il collega del frontend.

Tutto quello che sappiamo già (PC, regole, problemi risolti) è in `docs/MEMORIA.md`.

**Come si lancia un blocco.** Apri il terminale di VS Code nella cartella
`app_cycle_validation_v2` (la riga finisce con `app_cycle_validation_v2>`). Copia il blocco
intero e incollalo. Poi guarda **Deve uscire** e manda a Claude la foto indicata in **Manda a
Claude**.

**Se qualcosa va storto:**

- c'è scritto `Token has expired`, `ExpiredToken` o `SSO session`: lancia `aws sso login`, poi
  rilancia lo stesso blocco;
- c'è scritto `SELF_SIGNED_CERT_IN_CHAIN` o `unable to get local issuer certificate`: lancia
  questa riga, poi rilancia il blocco (vale finché non chiudi il terminale):

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## 1. Cosa fare adesso (22-11-2026, notte)

Gli errori tecnici erano tutti sulla targa (il registro delle macchine sul PC non è collegato:
è previsto). Le stampe «con errori» sono state modificate a mano e hanno le righe fuori ordine
dentro il PDF: ora la v2 le rimette in ordine. Copilot ha risposto a C15-C17.

1. In Copilot passa ad **Ask** (in basso nella chat).
2. Lancia **Aggiornare il codice sul PC** (sezione 2).
3. Lancia la **sezione 5.1**: blocchi A e B gratis, blocco C qualche centesimo.
4. Lancia la **sezione 5.2** (gratis): com'è fatta la libreria dei permessi della v1.
5. Lancia **Salvare nel repository aziendale** (sezione 6).
6. Se non l'hai già fatto: manda al collega del frontend il **messaggio** della sezione 4.1.
7. Quando capita: fai le **domande alle persone** (sezione 4).

---

## 2. Aggiornare il codice sul PC

Da lanciare **ogni volta che Claude dice di aver cambiato qualcosa**. Prende dal repository
personale il codice, i test, i documenti e i casi di prova, li copia nella cartella della v2 e
lancia i test. Toglie anche i documenti vecchi che non servono più. Non tocca i dati
aziendali.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
robocopy "$tmp\src" src /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\tests" tests /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\docs" docs /E /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\eval\casi\sintetici" eval\casi\sintetici /E /NFL /NDL /NJH /NJS /NP
Remove-Item docs\AMBIENTE_AZIENDALE.md, docs\DOMANDE_APERTE.md, docs\FORMATO_CONOSCENZA.md, docs\IMPORTAZIONE.md, docs\README_RADICE.md -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tmp
uv run pytest -q
```

**Deve uscire:** tutti `passed` (qualche `skipped` va bene), nessun `failed`.

**Manda a Claude:** la foto solo se c'è un `failed`.

---

## 3. Domande per Copilot

Per ora nessuna: Copilot ha risposto a C1-C17 (`MEMORIA.md`, sezione 8). Quando ci saranno:
in basso nella chat scegli **Ask**, non **Agent**, e togli con la **x** gli allegati che non
c'entrano (per esempio un file con accessi o password).

---

## 4. Domande per le persone

Queste Copilot non le sa: la risposta non è nel codice. Chiedile quando capita e scrivi a
Claude la risposta a parole (senza codici veri).

- **P1. Task «70-».** I task che cominciano con `70-` stanno sempre nel manuale SPM (le pratiche
  standard)? C'è un altro gruppo di task con la stessa regola?
- **P2. Operazione 060 del ciclo DR.** In una prova la v2 ha segnato come sbagliata
  l'operazione 060 del ciclo DR (condition 3). Era davvero sbagliata? Il dettaglio è in
  `runs\dr-condition-3\report.md`: fallo guardare a chi conosce il ciclo, non mandarlo a
  Claude.
- **P3. Cicli MOS «con errori»** (a chi li ha dati). Sono 3 cicli dati già segnati come
  sbagliati, e non sappiamo quali sono gli errori. Se il confronto con la stampa giusta (prova
  5.1, passo A) li trova, questa domanda non serve. Altrimenti: quali sono gli errori, e in
  quali operazioni? E i manuali che citano sono nella conoscenza di prova? (Il 22-11 la v2 non
  ha trovato quello del primo ciclo, quindi non ha potuto confrontare le operazioni.)
- **P4. Targa «90» nell'indice** (per chi cura knowledge-index). Nel file delle targhe la
  `90` ha come funzione una frase sbagliata e le lettere accentate rovinate. Va corretta
  nell'indice (i passi sono in `MEMORIA.md`, «Da correggere nell'indice»).
- **P6. Scheda mancante.** In un ciclo «con errori» l'errore è una scheda tolta da
  un'operazione. Quando un'operazione deve avere per forza una scheda? C'è una regola (tipo di
  lavorazione, targa, parola nella descrizione)? Oggi la v2 una scheda assente la segna N/A,
  come la v1: senza una regola non può sapere che manca.
- **P5. Dove gira la v1** (per chi gestisce AWS o il gateway). Il backend della v1 è
  un'immagine Docker in ECR, ma dove gira (ECS o altro)? Chi configura il gateway che manda
  `/cycle_validation` al backend? Serve per mettere la v2 accanto e provare i cicli EJ200
  dentro AWS.

### 4.1 Messaggio per il collega del frontend

Oggi il pulsante **Confirm** resta spento se serial number o condition sono vuoti. La v2 non
ne ha più bisogno. Mandagli questo messaggio (Teams o mail):

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

## 5. Prove da lanciare

### 5.1 I tre cicli MOS «con errori», con le righe rimesse in ordine

**Blocco A: tutte le stampe si leggono ancora?** Legge con il parser le stampe di esempio e
quelle delle cartelle `cicli MOS`, e per ognuna scrive quante operazioni trova e quali pagine
ha dovuto rimettere in ordine. Gratis.

```powershell
$env:UV_PYTHON = "3.14"
$radice = (Resolve-Path "..\..").Path
$tutte = @(Get-ChildItem "docs/Esempio ciclo mos/*.pdf", "docs/Esempio ciclo dr/*.pdf") + @(Get-ChildItem $radice -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue | Where-Object { $_.DirectoryName -match 'cicli MOS' }) | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $tutte) { $o = uv run cycle-validation leggi $f.FullName --profile mos; $r = ($o | Select-String "pagine rimesse") -replace '.*: ', ''; $n = ($o | Select-String "operazioni: (\d+)").Matches.Groups[1].Value; $x = $o | Select-String "non letto"; (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower() + "  operazioni: " + $(if ($n) { $n } else { "-" }) + "  pagine rimesse in ordine: " + $(if ($r) { $r } else { "nessuna" }) + $(if ($x) { "  NON LETTO" } else { "" }) }
```

**Deve uscire:** una riga per stampa. Le stampe normali: `pagine rimesse in ordine: nessuna`.
Le tre «con errori» (`298bc28e`, `c5ff3cd6`, `f355dc3c`): qualche pagina rimessa in ordine e
nessun `NON LETTO`.

**Manda a Claude:** la foto (anche in più foto).

**Blocco B: dove sono gli errori.** Lo stesso confronto di prima, ora con le righe in ordine.
Gratis.

```powershell
$env:UV_PYTHON = "3.14"
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($e in $errati) { $codice = ($e.Name -split ' ')[0]; "=== con errori " + (Get-FileHash $e.FullName).Hash.Substring(0, 8).ToLower(); Get-ChildItem $radice -Recurse -Filter "$codice*.pdf" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch 'con errori' } | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $g = $_.Group[0]; "--- giusto? " + (Get-FileHash $g.FullName).Hash.Substring(0, 8).ToLower(); uv run cycle-validation confronta $g.FullName $e.FullName --profile mos } }
```

**Deve uscire:** per ogni ciclo «con errori», sotto ogni `--- giusto?` il confronto. Poche
differenze = è la sua stampa giusta.

**Manda a Claude:** la foto di tutto l'output (anche in più foto).

**Blocco C: cosa trova la v2.** Rilancia la v2 sui tre cicli. Gli errori tecnici sulla targa ci
saranno ancora (registro delle macchine non collegato sul PC). Qualche centesimo per ciclo.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($e in $errati) { $out = "runs/mos-errori2-" + (Get-FileHash $e.FullName).Hash.Substring(0, 8).ToLower(); "=== $out"; uv run cycle-validation run $e.FullName --profile mos --knowledge $v --config data/settings.yaml --out $out; $j = Get-Content "$out/report.json" -Raw | ConvertFrom-Json; "  fonti: " + (($j.results | Where-Object { $_.check -eq 'source' } | ForEach-Object { "$($_.verdict) $($_.reason)" }) -join ', '); "  errati: " + (($j.results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "$($_.target.label) $($_.check)" }) -join ', '); "  warning: " + (($j.results | Where-Object { $_.verdict -eq 'WARNING' } | Group-Object reason | ForEach-Object { "$($_.Name) $($_.Count)" }) -join ', ') }
```

**Deve uscire:** per ognuno dei 3 cicli la riga `Ciclo ...` con i conteggi e le tre righe
fonti, errati, warning.

**Manda a Claude:** la foto di tutto l'output.

### 5.2 La libreria dei permessi della v1

La v1 controlla utente e permessi con una libreria interna (un file `.whl` nella cartella
`vendor`), che Copilot non può aprire. Questo blocco la cerca e stampa solo i nomi: le classi
che la v1 usa, i loro parametri, le prime righe della loro spiegazione e i nomi delle variabili
d'ambiente che legge (i nomi, non i valori). Serve a far usare alla v2 lo stesso controllo
della v1. Gratis.

```powershell
$env:UV_PYTHON = "3.14"
$whl = (Get-ChildItem .. -Recurse -Filter "chatbot_ai_sdk*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
"libreria trovata: " + [bool]$whl
$py = @'
import importlib, inspect, pkgutil, re
import chatbot_ai_sdk as sdk
wanted = {"AuthMiddleware", "ServiceAccessMiddleware", "S3PermissionsSource", "IntrospectionValidator", "current_user"}
env = set()
for info in pkgutil.walk_packages(sdk.__path__, sdk.__name__ + "."):
    try:
        module = importlib.import_module(info.name)
        source = inspect.getsource(module)
    except Exception as exc:
        print("non letto:", info.name, type(exc).__name__)
        continue
    env |= set(re.findall(r"(?:environ(?:\.get)?\(|environ\[|getenv\()\s*[\"'](\w+)", source))
    for name, item in vars(module).items():
        if name in wanted and getattr(item, "__module__", "") == module.__name__:
            print(f"{info.name}.{name}{inspect.signature(item)}")
            print("    " + " / ".join((inspect.getdoc(item) or "-").splitlines()[:3]))
print("variabili d'ambiente:", ", ".join(sorted(env)) or "-")
'@
if ($whl) { $py | Set-Content "$env:TEMP\sdk_firme.py"; uv run --no-project --with $whl python "$env:TEMP\sdk_firme.py" }
```

**Deve uscire:** `libreria trovata: True`, poi una riga per ognuna delle cinque cose cercate
(nome e parametri) con sotto la sua spiegazione, e alla fine i nomi delle variabili
d'ambiente. Se esce `libreria trovata: False`, chiedi a Copilot dov'è il file `.whl`.

**Manda a Claude:** la foto di tutto l'output.

---

## 6. Salvare nel repository aziendale

Da lanciare quando Claude dice che ci sono cose nuove da salvare (**adesso sì**: il comando
`confronta` e i documenti aggiornati). Prima lancia **Aggiornare il
codice sul PC**, poi questi due blocchi, uno alla volta.

Salva solo codice, test, documenti e casi di prova della v2. I dati aziendali (`data/`,
`runs/`, `eval/casi/aziendali/`, i PDF) restano fuori: git li ignora.

**6.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici
git status --short
git commit -m "v2: DR con serial number e condition facoltativi (anche dalla stampa), accept as is blocca; risposta adattata al frontend; documenti riorganizzati"
```

**Deve uscire:** in `git status` solo righe sotto `src/`, `tests/`, `docs/`,
`eval/casi/sintetici/` (`M` cambiato, `A` nuovo, `D` tolto); poi il riepilogo del commit.

**6.2 Push**

Manda il commit su GitHub, ma solo se sei sul branch giusto e se nel commit non c'è niente fuori
dalle cartelle previste. Altrimenti scrive `FERMO` e non fa niente.

```powershell
$branch = git branch --show-current
$fuori = git show --name-only --format= HEAD | Where-Object { $_ -and $_ -notmatch '^app_cycle_validation_v2/(src|tests|docs|eval/casi/sintetici)/' }
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
usare `--force`, manda la foto a Claude. Se il commit dice `nothing to commit`, era già tutto
salvato: lancia lo stesso il push.

---

## 7. Più avanti: trovare i documenti da ingestionare

**Non adesso**: per ora si prova solo con la conoscenza già ingestionata. Quando si deciderà di
aggiungere documenti, questo blocco cerca su S3 i file dei manuali citati dai cicli e delle
procedure DR che mancano. Legge soltanto, non costa niente.

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

**Deve uscire:** una riga con i codici cercati, separati da `|`, poi fino a 40 percorsi di file.

**Manda a Claude:** la foto. Claude dice quali file passare all'ingestion (poche sezioni, non
tutti i 2000 file). Se non esce nessun percorso, scrivi a Claude da quale cartella parte la tua
ingestion.
