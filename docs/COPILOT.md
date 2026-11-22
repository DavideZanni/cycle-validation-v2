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

Si prova tutto in locale, come la v1 (centralizer e login da Run and Debug), poi develop, poi
main. L'ingestion dei manuali la fai tu. Ho corretto: il secret di Redshift (nella v1 arriva da
un secret «di ambiente»), le stampe con «OPERAZIONE EVENTUALE», i caratteri strani nei blocchi,
il blocco della libreria.

1. In Copilot passa ad **Ask** (in basso nella chat): nelle foto è ancora su **Agent**.
2. Lancia **Aggiornare il codice sul PC** (sezione 2).
3. **Sezione 5.1** (Redshift): blocco A, poi blocco B.
4. **Sezione 5.2** (gratis): le stampe si leggono tutte? Cosa cambia il riordino?
5. **Sezione 5.3** (gratis): la libreria dei permessi della v1.
6. Fai a Copilot le **domande C18-C20** (sezione 3): come si avvia la v1 in locale e come si
   pubblica.
7. **Sezione 4.2**: lancia il blocco, poi fai l'ingestion dei manuali dell'elenco.
8. Lancia **Salvare nel repository aziendale** (sezione 6).
9. Se non l'hai già fatto: manda al collega del frontend il **messaggio** della sezione 4.1.

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

C1-C17 hanno già la risposta (`MEMORIA.md`, sezione 8). In basso nella chat scegli **Ask**,
non **Agent**, e togli con la **x** gli allegati che non c'entrano (per esempio un file con
accessi o password). Apri nella chat la cartella `ProgettoDocumenti`. Copia il testo così com'è.
**Manda a Claude** le foto delle risposte.

```text
Rispondi solo leggendo il codice, senza modificare né eseguire niente. Non scrivere nomi di
persone, indirizzi, account, chiavi o valori di segreti: se servono, scrivi «c'è» o «non c'è».

C18. Nei file .vscode/launch.json (e simili) come si avviano in locale il backend della cycle
     validation v1, centralizer e login? Per ognuno: modulo o comando, cartella di lavoro,
     porta, file .env usati, nomi delle variabili d'ambiente (solo i nomi).
C19. In locale, come fa il backend v1 a verificare il token del cookie? A quale servizio si
     rivolge IntrospectionValidator (nome della variabile con l'indirizzo, non il valore)? E
     da dove legge permissions.json in locale (S3 o un file)?
C20. buildspec.yml e Dockerfile della cycle validation: da quale cartella costruiscono
     l'immagine? La build parte da develop, da main o da tutti e due? Cosa cambia tra i due
     (ambienti, nomi delle immagini: solo come sono fatti, non i valori)?
```

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
- **P4. Targa «90» nell'indice** (per chi cura knowledge-index). Nel file delle targhe la
  `90` ha come funzione una frase sbagliata e le lettere accentate rovinate. Va corretta
  nell'indice (i passi sono in `MEMORIA.md`, «Da correggere nell'indice»).
- **P6. Scheda mancante.** In un ciclo «con errori» l'errore è una scheda tolta da
  un'operazione. Quando un'operazione deve avere per forza una scheda? C'è una regola (tipo di
  lavorazione, targa, parola nella descrizione)? Oggi la v2 una scheda assente la segna N/A,
  come la v1: senza una regola non può sapere che manca.
- **P7. Redshift** (solo se la sezione 5.1 dà `AccessDeniedException`). Chi gestisce AWS
  può darti la lettura dei due secret della v1 (quello «di ambiente» e quello di Redshift) e
  l'uso della Data API di Redshift (`redshift-data`)? Serve solo per le prove sul PC.

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

### 4.2 I manuali da ingestionare

I tre cicli «con errori» citano manuali che non sono nella conoscenza di prova: senza, la v2 non
può trovare gli errori. Questo blocco stampa i manuali citati dai tre cicli: sono quelli da
ingestionare (restano sul tuo schermo, non mandarli a Claude). Gratis.

```powershell
$env:UV_PYTHON = "3.14"
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
($errati | ForEach-Object { uv run cycle-validation leggi $_.FullName --profile mos } | Select-String 'fonti: (.+?) \S+ operazioni:' | ForEach-Object { $_.Matches[0].Groups[1].Value -split ', ' } | Sort-Object -Unique) -join "`n"
```

**Deve uscire:** l'elenco dei manuali, uno per riga. Fai l'ingestion di quelli, poi scrivi a
Claude a parole quanti erano e la nuova versione della conoscenza (`current.json`). Le prove sul
PC usano una fotografia della conoscenza (`foto-20261121`): dopo l'ingestion Claude prepara il
blocco per una fotografia nuova e per rilanciare i tre cicli «con errori».


---

## 5. Prove da lanciare

### 5.1 Le macchine attive da Redshift

**A cosa serve.** In ogni operazione c'è la targa della macchina. La v1 controlla che sia una
macchina attiva leggendo Redshift (il database aziendale dove c'è l'elenco delle macchine). Su
Redshift non devi creare niente: la v2 legge la stessa tabella della v1, con lo stesso secret
(utente e password che la v1 usa, salvati in AWS). Sul PC la v2 scarica l'elenco una volta in
`data\macchine_attive.json` (git lo ignora) e lo usa nelle prove.

**Blocco A: scaricare l'elenco.** Prende dal codice della v1 il nome del secret e la tabella,
legge il secret con le tue credenziali AWS e fa la query con la Data API di Redshift. Stampa
solo il numero di macchine. Gratis.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation macchine --v1 ..\app_cycle_validation
```

**Deve uscire:** `Dalla v1: nome del secret NON trovato nel codice, secret di ambiente
trovato, tabella trovata.`, poi `Nel secret di ambiente: SECRET_NAME trovato.` e infine
`Macchine attive: N (Redshift cluster). Scritte in data\macchine_attive.json`. (Come la v1:
il nome del secret di Redshift sta dentro il secret «di ambiente».)

Se esce un errore:

- `ExpiredToken` o simili: `aws sso login`, poi rilancia;
- `ResourceNotFoundException`: il secret sta in un'altra regione. Rilancia aggiungendo
  `--regione eu-west-1` (o la regione che usa la v1);
- `AccessDeniedException`: le tue credenziali non possono leggere il secret o usare la Data
  API. È la domanda P7 (sezione 4);
- `SECRET_NAME NON trovato. Campi: ...`: manda la foto (si vedono solo i nomi dei campi);
- `tabella NON trovata`: scrivi a Claude.

**Manda a Claude:** la foto.

**Blocco B: una prova con le macchine.** Solo se il blocco A ha scritto il file. Rilancia il
ciclo MOS di esempio con l'elenco delle macchine e conta gli esiti delle targhe. Qualche
centesimo.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$ciclo = (Get-ChildItem "docs/Esempio ciclo mos/*.pdf" | Select-Object -First 1).FullName
if ((Test-Path data/macchine_attive.json) -and $ciclo) { uv run cycle-validation run $ciclo --profile mos --knowledge $v --machines data/macchine_attive.json --config data/settings.yaml --out runs/mos-macchine } else { "FERMO: manca data/macchine_attive.json (blocco A)" }
if (Test-Path runs/mos-macchine/report.json) { (Get-Content runs/mos-macchine/report.json -Raw | ConvertFrom-Json).results | Where-Object { $_.check -eq 'machine_tag' } | Group-Object verdict, reason | ForEach-Object { "targhe $($_.Name): $($_.Count)" } }
```

**Deve uscire:** la riga `Ciclo ...` e poi poche righe `targhe CORRETTO, ...`,
`targhe ERRATO, ...`, `targhe WARNING, ...` con quante sono. Nessun `ERRORE_TECNICO`.

**Manda a Claude:** la foto.

### 5.2 Come si leggono tutte le stampe

Per ogni stampa di esempio e delle cartelle `cicli MOS`: come la legge la v2 adesso. Per le
stampe dove ha rimesso in ordine delle pagine, confronta la lettura con e senza riordino della
stessa stampa e mostra le prime differenze (codici mascherati). Le quattro stampe con
«OPERAZIONE EVENTUALE» ora dovrebbero leggersi. Gratis.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$radice = (Resolve-Path "..\..").Path
$tutte = @(Get-ChildItem "docs/Esempio ciclo mos/*.pdf", "docs/Esempio ciclo dr/*.pdf") + @(Get-ChildItem $radice -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue | Where-Object { $_.DirectoryName -match 'cicli MOS' }) | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $tutte) { $h = (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower(); $a = @(uv run cycle-validation leggi $f.FullName --profile mos --breve)[-1]; "$h $a"; if ($a -match 'rimesse in ordine: \d') { @(uv run cycle-validation confronta $f.FullName $f.FullName --profile mos --primo-senza-riordino) | Select-Object -First 6 | ForEach-Object { "          $_" } } }
```

**Deve uscire:** una riga per stampa (operazioni, parser, pagine rimesse in ordine). Sotto le
stampe con pagine rimesse in ordine, la riga `operazioni: N e N · differenze: K` e le prime
differenze tra prima e dopo il riordino. Nessun `NON LETTO`, tranne la stampa che non ha il
layout PVRM320 (quella la legge il modello).

**Manda a Claude:** la foto (anche in più foto).

### 5.3 La libreria dei permessi della v1

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
$dir = Join-Path $env:TEMP "cv2-sdk-firme"; Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue; New-Item -ItemType Directory $dir | Out-Null
if ($whl) { $py | Set-Content "$dir\firme.py"; uv run --no-project --with $whl python -I "$dir\firme.py" }
```

**Deve uscire:** `libreria trovata: True`, poi una riga per ognuna delle cinque cose cercate
(nome e parametri) con sotto la sua spiegazione, e alla fine i nomi delle variabili
d'ambiente. Se esce `libreria trovata: False`, chiedi a Copilot dov'è il file `.whl`. (La
prima volta si era fermato su un file `inspect.py` lasciato nella cartella TEMP: ora lo script
gira in una cartella sua.)

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
