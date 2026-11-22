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

## 1. Cosa fare adesso (22-11-2026, pomeriggio)

Dove siamo e cosa manca per la consegna: `MEMORIA.md`, sezione 1. Qui solo i passi.

1. In Copilot passa ad **Ask** (in basso nella chat): nelle foto è ancora su **Agent** con
   **Allow all**.
2. Lancia **Aggiornare il codice sul PC** (sezione 2).
3. **5.1** Redshift: blocco A, poi blocco B.
4. **5.2** la libreria dei permessi (seconda parte) e la domanda **C21** a Copilot (sezione 3).
5. **Ingestion del manuale** trovato con il blocco di prima (uno solo). Poi **5.3**: fotografia
   nuova della conoscenza e i tre cicli «con errori».
6. Lancia **Salvare nel repository aziendale** (sezione 6).
7. Se non l'hai già fatto: manda al collega del frontend il **messaggio** della sezione 4.1.

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

C1-C20 hanno già la risposta (`MEMORIA.md`). In basso nella chat scegli **Ask**, non
**Agent**, e togli con la **x** gli allegati che non c'entrano (per esempio un file con accessi
o password). Apri nella chat la cartella `ProgettoDocumenti`. Copia il testo così com'è.
**Manda a Claude** le foto delle risposte.

```text
Rispondi solo leggendo il codice, senza modificare né eseguire niente. Non scrivere nomi di
persone, indirizzi, account, chiavi o valori di segreti: se servono, scrivi «c'è» o «non c'è».

C21. Nel backend della cycle validation v1:
     a) copia tutte le righe import che prendono qualcosa da chatbot_ai_sdk (solo le righe
        import) e la chiamata completa a ServiceAccessMiddleware;
     b) nelle rotte, come si leggono utente e servizi dell'utente verificato (per esempio
        request.state..., current_user(...).qualcosa)? Copia le righe;
     c) in verify_active_TM (o dove si chiama redshift_connector.connect) da dove viene il
        database: scritto nel codice («scritto nel codice», senza il valore) oppure da quale
        variabile o chiave (il nome)?
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

---

## 5. Prove da lanciare

### 5.1 Le macchine attive da Redshift

Serve a controllare le targhe come la v1 (cos'è Redshift e perché: `MEMORIA.md`, sezione 5).
Su Redshift non devi creare niente.

**Blocco A: scaricare l'elenco.** L'ultima volta si è fermato perché nel secret di Redshift non
c'è il nome del database. Ora il comando lo cerca nel codice della v1, dove la v1 apre la
connessione. Stampa solo il numero di macchine. Gratis.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation macchine --v1 ..\app_cycle_validation
```

**Deve uscire:** `Dalla v1: ... tabella trovata, database scritto nel codice.` (oppure
`database letto dalla chiave X` e sotto `Chiave X del database: trovata.`), poi `Nel secret di
ambiente: SECRET_NAME trovato.` e infine `Macchine attive: N (Redshift cluster). Scritte in
data\macchine_attive.json`.

Se esce un errore:

- `database NON trovato` e poi `Manca il nome del database`: rispondi alla domanda C21 c)
  (sezione 3) e manda la foto. Se il nome lo conosci, puoi rilanciare aggiungendo
  `--database <nome>` (il nome resta sul tuo schermo);
- `ExpiredToken` o simili: `aws sso login`, poi rilancia;
- `ResourceNotFoundException`: rilancia aggiungendo `--regione eu-west-1` (o la regione che usa
  la v1);
- `AccessDeniedException`: è la domanda P7 (sezione 4).

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

### 5.2 La libreria dei permessi, seconda parte

La prima parte ha trovato `AuthMiddleware`, `IntrospectionValidator` e `current_user`, ma non
`ServiceAccessMiddleware` e `S3PermissionsSource`: forse il blocco ha preso un altro file
`.whl`. Questo blocco elenca tutti i file `.whl` della libreria, usa quello della cartella
`vendor` della v1 e stampa tutte le classi della parte `auth` (nomi, parametri, campi). Niente
valori. Gratis.

```powershell
$env:UV_PYTHON = "3.14"
Get-ChildItem .. -Recurse -Filter "chatbot_ai_sdk*.whl" -ErrorAction SilentlyContinue | ForEach-Object { "trovato: " + $_.Directory.Name + "\" + $_.Name }
$whl = (Get-ChildItem ..\app_cycle_validation\vendor -Filter "chatbot_ai_sdk*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
$py = @'
import dataclasses, importlib, inspect, pkgutil
import chatbot_ai_sdk as sdk
print("versione:", getattr(sdk, "__version__", "-"))
for info in pkgutil.walk_packages(sdk.__path__, sdk.__name__ + "."):
    try:
        module = importlib.import_module(info.name)
    except Exception as exc:
        print("non letto:", info.name, type(exc).__name__)
        continue
    for name, item in vars(module).items():
        if name.startswith("_") or getattr(item, "__module__", "") != module.__name__:
            continue
        if not (inspect.isclass(item) or inspect.isfunction(item)):
            continue
        try:
            print(f"{info.name}.{name}{inspect.signature(item)}")
        except (TypeError, ValueError):
            print(f"{info.name}.{name}")
        if dataclasses.is_dataclass(item):
            print("    campi:", ", ".join(f.name for f in dataclasses.fields(item)))
        print("    " + " / ".join((inspect.getdoc(item) or "-").splitlines()[:2]))
'@
$dir = Join-Path $env:TEMP "cv2-sdk-firme"; Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue; New-Item -ItemType Directory $dir | Out-Null
if ($whl) { $py | Set-Content "$dir\firme.py"; uv run --no-project --with $whl python -I "$dir\firme.py" } else { "FERMO: nessun .whl in app_cycle_validation\vendor" }
```

**Deve uscire:** le righe `trovato: ...` (i file della libreria), `versione: ...`, poi per ogni
classe o funzione il nome con i parametri e sotto la spiegazione. Cerco soprattutto
`ServiceAccessMiddleware`, `S3PermissionsSource` e `VerifiedUser` (i suoi campi). L'output è
lungo: va bene in più foto.

**Manda a Claude:** le foto di tutto l'output.

### 5.3 Dopo l'ingestion: i tre cicli «con errori»

Da lanciare **dopo** l'ingestion del manuale, quando la nuova versione è pubblicata. Fa una
fotografia nuova della conoscenza civile di prova (solo la prima volta), poi rilancia i tre
cicli «con errori» e stampa, per ognuno, il riepilogo e le righe ERRATO (operazione e
controllo, niente testi). Qualche centesimo per ciclo.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = "eval/casi/aziendali/conoscenza/foto-20261122"
if (-not (Test-Path "$foto/Manufacturing AI")) { uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1 }
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$m = if (Test-Path data/macchine_attive.json) { @("--machines", "data/macchine_attive.json") } else { @() }
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $errati) { $h = (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower(); "$h " + (@(uv run cycle-validation run $f.FullName --profile mos --knowledge $v @m --config data/settings.yaml --out "runs/errori-$h") -match '^Ciclo' | Select-Object -First 1); if (Test-Path "runs/errori-$h/report.json") { (Get-Content "runs/errori-$h/report.json" -Raw | ConvertFrom-Json).results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "    ERRATO op $(if ($_.target.kind -eq 'operation') { $_.target.label } else { $_.target.kind }) · $($_.check) · $($_.reason)" } } }
```

**Deve uscire:** la riga `Fotografia in ...` (solo la prima volta), poi per ognuno dei tre
cicli una riga `<impronta> Ciclo ...: N corretti, ...` e sotto le righe `ERRATO op ...`.
Claude le confronta con i 10 errori trovati da `confronta` (`MEMORIA.md`, sezione 10).

**Manda a Claude:** la foto, e scrivi a parole quanti manuali hai ingestionato.

---

## 6. Salvare nel repository aziendale

Da lanciare quando Claude dice che ci sono cose nuove da salvare (**adesso sì**: lettura delle
stampe modificate a mano, comandi `confronta` e `macchine`, documenti riordinati). Prima lancia
**Aggiornare il codice sul PC**, poi questi due blocchi, uno alla volta.

Salva solo codice, test, documenti e casi di prova della v2. I dati aziendali (`data/`,
`runs/`, `eval/casi/aziendali/`, i PDF) restano fuori: git li ignora.

**6.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici
git status --short
git commit -m "v2: stampe modificate a mano rimesse in ordine, titoli OPERAZIONE EVENTUALE, comandi confronta e macchine, documenti riordinati"
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
