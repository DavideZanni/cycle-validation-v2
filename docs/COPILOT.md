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

Da lanciare **ogni volta che Claude dice di aver corretto il codice**.
Copia nella cartella della v2 codice, test, documenti e casi sintetici nuovi dal repository
personale (clone temporaneo, poi cancellato) e lancia i test. `eval\casi\aziendali` non si
tocca.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
robocopy "$tmp\src" src /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\tests" tests /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\docs" docs /E /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\eval\casi\sintetici" eval\casi\sintetici /E /NFL /NDL /NJH /NJS /NP
Remove-Item -Recurse -Force $tmp
uv run pytest -q
```

**Deve uscire:** tutti `passed` (qualche `skipped` va bene), nessun `failed`.

---

## Fatto finora (21-11-2026)

- **Cicli MOS**: terzo ciclo `7 corretti, 16 warning, 0 errati, 14 non applicabili`, 0,0058 USD.
  Le righe che dipendono dal manuale del motore escono FONTE_ASSENTE (giusto).
- **Ciclo DR `CON sn`, letto dal parser** (messaggio 11), serial number preso dalla stampa:

| Condition | Recommendation | Esito | Costo |
|---|---|---|---|
| 1 | Repair | `5 corretti, 15 warning, 0 errati`; `extraction_integrity` e `dr_recommendation` CORRETTO | 0,0097 USD, 9 sessioni |
| 2 | Accept as is | `dr_recommendation` ERRATO (`DR_NON_APPLICABILE`), il resto bloccato: regola cambiata, vedi messaggio 17 | 0 USD |
| 3 | Repair | identico alla condition 1 | 0,0057 USD, 9 sessioni |

  Descrizioni: 005, 040, 050, 060 CORRETTO; 010, 020, 030, 080, 090 `EVIDENZA_NON_TROVATA`.
  Restano WARNING le targhe (registro macchine non collegato), la scheda dell'op. 050 (non è
  tra le 94 schede) e il manuale del motore. Con il ciclo letto dal modello (messaggio 10)
  l'op. 060 usciva ERRATO `CONTRADDIZIONE`; letta dal parser è CORRETTO.
- **Messaggio 12**: il parser legge tutte le stampe DR. La descrizione dell'op. 060 è uguale
  nelle due letture: l'ERRATO non viene da una lettura sbagliata del testo, ma da quello con
  cui è stato confrontato (messaggio 13). `git status`: solo file sotto `src/`, `tests/`,
  `docs/`.
- **Messaggio 13**: i due run hanno confrontato l'op. 060 con **lo stesso documento**, la
  procedura DR, alla stessa pagina: il run col ciclo letto dal modello cita una riga e dice
  ERRATO, quello col parser cita quella riga e la precedente e dice CORRETTO. Differenze
  d'ingresso: col modello l'op. 060 non ha il repair code e il ciclo ha fonti in più (i due
  casi DR, il riferimento SA).
- **Messaggio 14**: stesso ingresso, esiti diversi. Con la lettura del modello ERRATO 2 volte
  su 3, con quella del parser 1 su 3: il modello oscilla sull'op. 060. Corretto nel codice: un
  ERRATO della descrizione ora si rifà con 2 sessioni uguali e resta ERRATO solo se lo
  ritrovano tutte; altrimenti WARNING `GIUDIZIO_INSTABILE`, da guardare a mano.
- **Messaggio 15**: la conferma funziona. Tre run della condition 3: op. 060 CORRETTO,
  CORRETTO, WARNING `GIUDIZIO_INSTABILE` (la prima sessione ha detto ERRATO, le 2 conferme non
  l'hanno ritrovato tutte); 0 errati, 9-11 sessioni, 0,007-0,011 USD per run.
- **Messaggi 16 e 17**: le 2 procedure DR della conoscenza sono solo procedure di riparazione
  (16 righe, circa 1.250 caratteri): «accept as is», «reject», «condition» non ci sono mai. La
  disposizione per condition sta solo nelle recommendation. Corretto nel codice (domanda 17):
  `Accept as is` ora dà WARNING `DR_SENZA_RIPARAZIONE` e gli altri controlli proseguono senza
  la procedura di riparazione come riferimento; `Reject` resta ERRATO e blocca.
- **Messaggio 18**: condition 2 con la regola nuova: `dr_recommendation` WARNING
  `DR_SENZA_RIPARAZIONE`, 0 errati, 20 warning, 0 sessioni, 0 USD. Tutte le descrizioni
  `FONTE_ASSENTE`: senza la procedura di riparazione resta solo il manuale del motore, che non
  c'è. Stato `parziale` per il registro macchine non collegato, come nelle altre condition.
  Questo ciclo cita il caso DR e le sue operazioni 040-060 seguono la procedura di riparazione:
  è un ciclo di riparazione, e con `Accept as is` il WARNING chiede giustamente di guardarlo.
- **Salvataggio (21-11-2026)**: tutte le correzioni fin qui sono nel repository aziendale,
  commit e push su `feature/cycle-validation-v2` riusciti, niente da mandare.

---

## Da fare nei prossimi giorni

1. Frontend visto (22-11-2026, foto della v1 in QA): scelta civile/EJ200, poi DR sì/no; per il
   DR serial number e condition (domanda 18), poi il PDF. Esito: «Validation Passed», tabella
   *Sources* (Repair Code, Type, Reference, Task, Feedback) e tabella *Operations* (Op. / TM /
   Task Code / Scheda Feedback, con OK e N/A). Sono gli stessi campi di `payload.json` della v2
   (`legacy_payload.py`). Da fare: mostrare nel frontend un `payload.json` della v2, per
   vedere come appaiono WARNING ed ERRATO.
2. Prima prova di un ciclo **EJ200**: non è ancora mai stata fatta con servizi veri. Documenti
   e output EJ200 devono restare su AWS EU, quindi niente copia della conoscenza EJ200 sul PC e
   niente report EJ200 in `runs\`. Prima di lanciare, Claude scrive il blocco che legge la
   conoscenza direttamente da S3, e insieme si decide dove far girare il ciclo e dove scrivere
   l'output (per esempio l'ambiente SageMaker della guida aziendale).
3. Rifare le prove dei tre cicli, MOS, DR ed EJ200, con il formato dell'output del frontend.

---

## Ancora aperte (da chiedere a chi conosce i cicli, quando capita)

- domanda 17 di `docs/DOMANDE_APERTE.md`: con «accept as is» esiste un ciclo DR, e con quali
  operazioni? con «reject» un ciclo di riparazione è sempre sbagliato?
- l'ERRATO dell'op. 060 (in `runs\dr-condition-3\report.md`) aveva ragione? Non mandare il
  file.

---

## Salvare le correzioni nel repository aziendale

Da lanciare quando Claude dice che ci sono correzioni nuove da salvare (per ora è tutto
salvato). Prima lancia **Aggiornare il codice sul PC**, poi questo; il messaggio del commit lo
aggiorna Claude. Mette nel commit solo codice, test, documenti e
casi sintetici della v2; `data/`, `runs/`, `eval/casi/aziendali/` e i PDF restano fuori perché
git li ignora. Poi fa il push sul branch `feature/cycle-validation-v2`, ma solo se sei su quel
branch e se nel commit non è entrato niente fuori da quelle cartelle.

Due blocchi: prima il commit, poi il push. Se il commit è già fatto, lancia solo il secondo.

**1. Commit**

```powershell
git add src tests docs eval/casi/sintetici
git status --short
git commit -m "v2: correzioni dalle prove sul PC"
```

**Deve uscire:** in `git status` solo righe `M ` e `A ` sotto `src/`, `tests/`, `docs/`,
`eval/casi/sintetici/`; poi il riepilogo del commit (`[feature/cycle-validation-v2 ...]`).

**2. Push**

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

**Deve uscire:** le righe del push (`feature/cycle-validation-v2 -> feature/cycle-validation-v2`),
l'ultimo commit e `## feature/cycle-validation-v2...origin/feature/cycle-validation-v2` senza
`[ahead ...]`.

Se esce `FERMO`, oppure il push è rifiutato (`rejected`, `fetch first`), **non insistere e non
usare `--force`**: manda a Claude la foto. Se il commit dice `nothing to commit`, le correzioni
erano già salvate: lancia lo stesso il push, manda solo quello che manca.

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
