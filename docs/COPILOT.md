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

Dove siamo e cosa manca per la consegna: `MEMORIA.md`, sezione 1. Qui solo i passi.

1. In Copilot passa ad **Ask** (in basso nella chat): nelle foto è ancora su **Agent** con
   **Allow all**.
2. Lancia **Aggiornare il codice sul PC** (sezione 2).
3. **5.1** la v2 in locale con login e frontend, al posto della v1. Per ora solo il
   blocco A fatto; passo B fatto, ma il nome del secret era sbagliato: lancia il
   **Controllo del passo B**, poi il passo C. Le macchine attive dal
   PC non si leggono (prova del 22-11: Redshift non si raggiunge), quindi in locale le targhe
   escono WARNING «non verificabile». È giusto così: in QA la v2 legge Redshift come la v1.
4. **Ingestion del manuale** trovato prima (uno solo), poi **5.2**: i tre cicli «con errori».
5. Lancia **Salvare nel repository aziendale** (sezione 6).
6. Se non l'hai già fatto: manda al collega del frontend il **messaggio** della sezione 4.1.

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

Nessuna domanda aperta: C1-C21 hanno la risposta (`MEMORIA.md`). Quando ne servono altre,
Claude le scrive qui. Ricorda: modalità **Ask**, togli con la **x** gli allegati che non
c'entrano, e il testo comincia sempre con «Rispondi solo leggendo il codice, senza modificare né
eseguire niente».

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
- **P7. Redshift dal PC** (facoltativa, non blocca la consegna). Dal PC la Data API di
  Redshift risponde `AccessDeniedException` su `ExecuteStatement` e la connessione diretta non
  arriva al cluster. Chi gestisce AWS può dare al tuo ruolo SSO l'uso della Data API
  (`redshift-data:ExecuteStatement`, `DescribeStatement`, `GetStatementResult`)? Servirebbe
  solo per provare le targhe sul PC; in QA la v2 legge Redshift come la v1.

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

### 5.1 La v2 in locale, al posto della v1

La v2 ora controlla token e permessi con la stessa libreria della v1 (si accende da sola quando
legge il secret della v1) e parte con lo stesso secret «di ambiente». In locale si avvia sulla
porta 8003, la stessa della v1: login e frontend non cambiano. La v1 e la v2 non possono
girare insieme (stessa porta).

Le macchine attive: dal PC Redshift non si raggiunge (prova del 22-11), quindi in locale la v2
parte con `MACHINES_SOURCE` = `nessuna` e ogni targa esce WARNING «non verificabile». In QA
e in produzione la v2 legge Redshift come la v1 (`MACHINES_SOURCE` = `diretta`).

**Blocco A: la libreria nella v2.** Fatto il 22-11: `versione 0.4.0rc2 - mancano: []`.

**Passo B: la configurazione in Run and Debug.** Apri `.vscode/launch.json` (quello nella
radice di `ProgettoDocumenti`) e aggiungi questa configurazione dentro `"configurations": [`,
dopo quella del backend della v1 (attenzione alle virgole tra una configurazione e l'altra). Al
posto delle due scritte `<...>` metti gli stessi valori della v1: `AWS_PROFILE` lo copi dalla
configurazione del backend v1; il nome del secret è quello tra virgolette in
`load_secrets("...")` di `app_backend.py` della v1, **identico**, senza aggiungere `_v2`: la
v2 usa lo stesso secret della v1. La configurazione va scritta nel file `launch.json`, non nel
terminale. **Questi valori non vanno mandati a Claude** e non vanno nel repository personale.

```json
{
  "name": "CV v2 (porta 8003)",
  "type": "debugpy",
  "request": "launch",
  "module": "uvicorn",
  "args": ["cycle_validation.api.entry:app", "--port", "8003"],
  "cwd": "${workspaceFolder}/avioaero_datalake_cycle_validation/app_cycle_validation_v2",
  "python": "${workspaceFolder}/avioaero_datalake_cycle_validation/app_cycle_validation_v2/.venv/Scripts/python.exe",
  "env": {
    "AWS_PROFILE": "<come nella configurazione della v1>",
    "CV_ENV_SECRET": "<il nome in load_secrets della v1>",
    "CYCLE_VALIDATION_CONFIG": "data/settings.yaml",
    "MACHINES_SOURCE": "nessuna",
    "CIVIL_KNOWLEDGE_POINTER": "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json",
    "EJ200_VALIDATION_ENABLED": "false",
    "CLOUDWATCH_METRICS": "false"
  }
}
```

**Controllo del passo B.** Prima prova (22-11): all'avvio `Secret '...' non leggibile o non
valido (ResourceNotFoundException)`. Il nome in `CV_ENV_SECRET` non è quello della v1. Questo
blocco lo confronta con il nome in `load_secrets` della v1 senza stamparli e, se sono diversi,
mette in `launch.json` quello della v1 (prima ne fa una copia, `launch.json.prima-di-cv2`).
Gratis.

```powershell
$env:UV_PYTHON = "3.14"
$launch = Join-Path (Resolve-Path "..\..").Path ".vscode\launch.json"
$testo = Get-Content $launch -Raw
$v1 = [regex]::Match((Get-Content ..\app_cycle_validation\app_backend.py -Raw), 'load_secrets\(\s*["'']([^"'']+)').Groups[1].Value
$m = [regex]::Match($testo, '"CV_ENV_SECRET"\s*:\s*"([^"]*)"')
"nome della v1 trovato: $([bool]$v1) · CV_ENV_SECRET in launch.json: $($m.Success) · uguali: $($m.Success -and $m.Groups[1].Value -eq $v1)"
if ($v1 -and $m.Success -and $m.Groups[1].Value -ne $v1) { Copy-Item $launch "$launch.prima-di-cv2"; Set-Content $launch ($testo.Remove($m.Groups[1].Index, $m.Groups[1].Length).Insert($m.Groups[1].Index, $v1)) -NoNewline -Encoding utf8; "CV_ENV_SECRET corretto con il nome della v1." }
```

**Deve uscire:** `nome della v1 trovato: True · CV_ENV_SECRET in launch.json: True · uguali:
False` e `CV_ENV_SECRET corretto con il nome della v1.` (oppure `uguali: True`: era già
giusto). Poi riavvia **CV v2 (porta 8003)** in Run and Debug.

`EJ200_VALIDATION_ENABLED` è spento perché in locale la conoscenza EJ200 verrebbe scaricata
sul PC (regola: resta su AWS). Il pulsante militare il frontend lo mostra lo stesso a chi ha il
permesso: se lo premi, la v2 risponde che l'EJ200 è spento. È giusto così.

**Passo C: la prova.** In Run and Debug avvia, come per la v1, **login**, **frontend** e
**CV v2 (porta 8003)** (non il backend della v1). Se per la v1 usi la voce composta «CV», qui
avvia le tre voci una per una.
Nel frontend: entra con il tuo utente, scegli il ciclo civile, MOS, carica la stampa di esempio
MOS.

**Deve uscire:** nella Debug Console di CV v2 la riga `Uvicorn running on
http://127.0.0.1:8003` e nessun errore all'avvio; nel frontend la pagina dei risultati del
ciclo, come con la v1. Le targhe sono WARNING (vedi sopra).

**Manda a Claude:** la foto della Debug Console di CV v2 dopo l'avvio e una foto
dell'intestazione dei risultati (in alto: esito e numero di errori). Se all'avvio esce
`Configurazione ... non valida`, la foto dell'elenco dei problemi (ci sono solo nomi di
variabili).

### 5.2 Dopo l'ingestion: i tre cicli «con errori»

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
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $errati) { $h = (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower(); "$h " + (@(uv run cycle-validation run $f.FullName --profile mos --knowledge $v --config data/settings.yaml --out "runs/errori-$h") -match '^Ciclo' | Select-Object -First 1); if (Test-Path "runs/errori-$h/report.json") { (Get-Content "runs/errori-$h/report.json" -Raw | ConvertFrom-Json).results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "    ERRATO op $(if ($_.target.kind -eq 'operation') { $_.target.label } else { $_.target.kind }) · $($_.check) · $($_.reason)" } } }
```

**Deve uscire:** la riga `Fotografia in ...` (solo la prima volta), poi per ognuno dei tre
cicli una riga `<impronta> Ciclo ...: N corretti, ...` e sotto le righe `ERRATO op ...`.
Claude le confronta con i 10 errori trovati da `confronta` (`MEMORIA.md`, sezione 10).

**Manda a Claude:** la foto, e scrivi a parole quanti manuali hai ingestionato.

---

## 6. Salvare nel repository aziendale

Da lanciare quando Claude dice che ci sono cose nuove da salvare (**adesso sì**: lettura delle
stampe modificate a mano, comandi `confronta` e `macchine`, accesso come la v1, macchine
attive da Redshift come la v1, documenti riordinati). Prima lancia **Aggiornare il codice sul PC**, poi questi due blocchi, uno alla
volta.

Salva solo codice, test, documenti e casi di prova della v2. I dati aziendali (`data/`,
`runs/`, `eval/casi/aziendali/`, i PDF) restano fuori: git li ignora.

**6.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici
git status --short
git commit -m "v2: accesso con chatbot_ai_sdk come la v1, secret di ambiente della v1 (CV_ENV_SECRET), macchine attive da Redshift come la v1 (MACHINES_SOURCE), stampe modificate a mano, comandi confronta e macchine, documenti riordinati"
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
