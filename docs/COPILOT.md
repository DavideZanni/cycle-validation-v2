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

## Fatto finora (21-11-2026)

- **Cicli MOS**: terzo ciclo `7 corretti, 16 warning, 0 errati, 14 non applicabili`, 0,0058 USD.
  Le righe che dipendono dal manuale del motore escono FONTE_ASSENTE (giusto).
- **Ciclo DR `CON sn`, letto dal parser** (messaggio 11), serial number preso dalla stampa:

| Condition | Recommendation | Esito | Costo |
|---|---|---|---|
| 1 | Repair | `5 corretti, 15 warning, 0 errati`; `extraction_integrity` e `dr_recommendation` CORRETTO | 0,0097 USD, 9 sessioni |
| 2 | Accept as is | `dr_recommendation` ERRATO (`DR_NON_APPLICABILE`), il resto bloccato: giusto | 0 USD |
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

---

## Messaggio 15: la conferma degli ERRATO sull'op. 060

Prima il blocco **Aggiornare il codice sul PC** in cima a questo file. Poi questo: rilancia tre
volte la condition 3 con il ciclo letto dal parser (`--cycle-json`, nessuna lettura nuova).
Circa 4 centesimi in tutto.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$ciclo = (Get-ChildItem "docs/Esempio ciclo dr/*CON sn.pdf" | Select-Object -First 1).FullName
$sn = ((uv run cycle-validation leggi $ciclo --profile dr) | Select-String 'S/N (\S+)$').Matches[0].Groups[1].Value
foreach ($i in 1..3) {
  $out = "runs/conferma-060-$i"
  uv run cycle-validation run $ciclo --profile dr --serial-number $sn --condition 3 --knowledge $v --config data/settings.yaml --cycle-json "runs/dr-parser-condition-3/cycle.json" --out $out | Out-Null
  $rep = Get-Content "$out/report.json" -Raw | ConvertFrom-Json
  $r = $rep.results | Where-Object { $_.check -eq 'operation_description' -and $_.target.label -match '^0?60$' }
  "{0}  {1,-9} {2,-20} errati {3}  conferme {4}  sessioni {5}  costo {6:N4}" -f $i, $r.verdict, $r.reason, $rep.counts.errato, $rep.session_modes.conferma, $rep.usage.sessions, $rep.usage.cost_usd
}
```

**Deve uscire:** tre righe. L'op. 060 esce CORRETTO (`VERIFICATO`) oppure WARNING
(`GIUDIZIO_INSTABILE`); ERRATO solo se la contraddizione è ritrovata tre volte su tre.
`conferme 2` compare solo nei run in cui la prima sessione ha detto ERRATO.

**Manda a Claude** la foto. Resta la domanda che solo tu puoi decidere: apri
`runs\dr-condition-3\report.md`, cerca `060` nella sezione delle descrizioni, leggi la
spiegazione dell'ERRATO e dimmi **se ha ragione** e su quale punto (limite in mm, classe del
penetrante, ingrandimento, altro). Non mandare il file.

---

## Salvare le correzioni nel repository aziendale

Quando vuoi (le prove finora sono andate bene). Mette nel commit solo codice, test e documenti
della v2; `data/`, `runs/`, `eval/casi/aziendali/` e i PDF restano fuori perché git li
ignora. Il push lo fai come al solito sul branch `feature/cycle-validation-v2`.

```powershell
git add src tests docs
git status --short
git commit -m "v2: parser PVRM320 per le stampe DR, task del capitolo 70 nell'SPM, procedura DR citata come caso, conferma degli ERRATO, comando leggi"
```

**Deve uscire:** in `git status` solo righe `M ` e `A ` sotto `src/`, `tests/`, `docs/`; poi
il riepilogo del commit.

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
