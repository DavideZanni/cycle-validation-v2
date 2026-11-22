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

## 1. Cosa fare adesso (22-11-2026, sera)

Il salvataggio nel repository aziendale è fatto. I PDF «con errori» sono 3 cicli diversi (ognuno
in due cartelle) e nessuno sa quali sono gli errori: un comando nuovo li trova confrontando ogni
stampa «con errori» con la stessa stampa giusta, se c'è.

1. In Copilot passa ad **Ask** (in basso nella chat). Nelle foto è ancora su **Agent** con
   **Allow all** acceso.
2. Lancia **Aggiornare il codice sul PC** (sezione 2).
3. Lancia la **sezione 5.1**: prima il passo A (gratis), poi il passo B (qualche centesimo).
4. Fai a Copilot le **domande C15-C17** (sezione 3): chi vede il pulsante militare.
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

Le domande C1-C14 hanno già la risposta (`MEMORIA.md`, sezione 8). In basso nella chat
scegli **Ask**, non **Agent**, e togli con la **x** gli allegati che non c'entrano (per esempio
un file con accessi o password). Apri nella chat la cartella del frontend e quella della v1.
Copia il testo qui sotto così com'è. **Manda a Claude** le foto delle risposte.

```text
Rispondi solo leggendo il codice, senza modificare niente. Non scrivere nomi di persone,
indirizzi, chiavi o segreti: se servono, scrivi «c'è» o «non c'è».

C15. Nel frontend, chi vede il pulsante «EJ200 cycle (military)»? Lo vedono tutti, oppure
     solo alcuni utenti? Se solo alcuni: da dove viene l'informazione (gruppi o ruoli
     dell'SSO, una lista, una chiamata a un'API)? Indica file e funzione.
C16. Quali header manda il frontend al backend della cycle validation, oltre a `sso`? C'è un
     header con i permessi o i servizi dell'utente? Come si chiamano e che valori possono
     avere (solo i nomi dei valori, per esempio «cv», non gli utenti)?
C17. Il backend della v1 controlla i permessi sulle rotte `/cycle_validation/ej200/...`? Se
     sì, dove e con quale regola? Un utente senza permesso che chiama quelle rotte cosa
     riceve?
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
- **P3. Cicli MOS «con errori»** (a chi li ha dati). Sono 3 cicli dati già segnati come
  sbagliati, e non sappiamo quali sono gli errori. Se il confronto con la stampa giusta (prova
  5.1, passo A) li trova, questa domanda non serve. Altrimenti: quali sono gli errori, e in
  quali operazioni? E i manuali che citano sono nella conoscenza di prova? (Il 22-11 la v2 non
  ha trovato quello del primo ciclo, quindi non ha potuto confrontare le operazioni.)
- **P4. Targa «90» nell'indice** (per chi cura knowledge-index). Nel file delle targhe la
  `90` ha come funzione una frase sbagliata e le lettere accentate rovinate. Va corretta
  nell'indice (i passi sono in `MEMORIA.md`, «Da correggere nell'indice»).
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

### 5.1 I tre cicli MOS «con errori»

**Passo A: dove sono gli errori.** Per ogni stampa «con errori» cerca in `ProgettoDocumenti` la
stampa con lo stesso nome senza `con errori` e le confronta con il comando `confronta`: dice in
quali operazioni e in quali campi sono diverse. Non chiama il modello e non costa niente. I
codici escono mascherati (lettere → `A`, cifre → `9`); delle descrizioni stampa solo i pezzi che
cambiano.

```powershell
$env:UV_PYTHON = "3.14"
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
"Cicli con errori diversi: " + @($errati).Count
foreach ($e in $errati) { $nome = $e.Name -replace '\s*con errori', ''; $giusto = Get-ChildItem $radice -Recurse -Filter $nome -ErrorAction SilentlyContinue | Select-Object -First 1; "=== " + (Get-FileHash $e.FullName).Hash.Substring(0, 8).ToLower(); if ($giusto) { uv run cycle-validation confronta $giusto.FullName $e.FullName --profile mos } else { "  manca la stampa giusta" } }
```

**Deve uscire:** `Cicli con errori diversi: 3`, poi per ognuno una riga `=== ` con l'impronta e
sotto `operazioni: N e N · differenze: K` con l'elenco delle differenze (fonte o operazione,
campo, valori mascherati). Se esce `manca la stampa giusta`, per quel ciclo il confronto non si
può fare.

**Manda a Claude:** la foto di tutto l'output (anche in più foto).

**Passo B: cosa trova la v2 sui tre cicli.** Costa qualche centesimo per ciclo.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($e in $errati) { $out = "runs/mos-errori-" + (Get-FileHash $e.FullName).Hash.Substring(0, 8).ToLower(); "=== $out"; uv run cycle-validation run $e.FullName --profile mos --knowledge $v --config data/settings.yaml --out $out; $j = Get-Content "$out/report.json" -Raw | ConvertFrom-Json; "  fonti: " + (($j.results | Where-Object { $_.check -eq 'source' } | ForEach-Object { "$($_.verdict) $($_.reason)" }) -join ', '); "  errati: " + (($j.results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "$($_.target.label) $($_.check)" }) -join ', '); "  warning: " + (($j.results | Where-Object { $_.verdict -eq 'WARNING' } | Group-Object reason | ForEach-Object { "$($_.Name) $($_.Count)" }) -join ', ') }
```

**Deve uscire:** per ognuno dei 3 cicli una riga `=== runs/mos-errori-...`, la riga `Ciclo ...`
con i conteggi, e tre righe: esito delle fonti, operazioni segnate ERRATO (con il controllo),
warning contati per motivo.

**Manda a Claude:** la foto di tutto l'output (anche in più foto).

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
