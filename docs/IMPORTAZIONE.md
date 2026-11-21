# Portare la v2 nel repository aziendale

Come mettere questo progetto nel repository aziendale `avioaero_datalake_cycle_validation`,
branch `feature/cycle-validation-v2`, accanto alla versione in produzione. Dopo l'importazione,
installare e provare la v2 è scritto in `docs/AZIENDA.md`.

**I messaggi pronti da incollare a Copilot, passo per passo, sono in `docs/COPILOT.md`.** Questo
file spiega le scelte e fa da riferimento.

Su ogni passo: il comando (PowerShell, Windows) e cosa devi vedere. Se vedi altro, fermati e
riporta l'output a chi ti segue.

---

## Come sarà il repository

```
avioaero_datalake_cycle_validation/
├── .github/workflows/          resta qui: GitHub legge i workflow solo dalla radice
├── buildspec.yml               resta qui e continua a costruire la v1
├── .gitignore                  quello di oggi, invariato
├── README.md                   nuovo, breve: dice cosa c'è nelle due cartelle (docs/README_RADICE.md)
├── app_cycle_validation/       VERSIONE 1, in produzione: il codice non si tocca
│   └── docs/                   i quattro .md che oggi stanno in radice
└── app_cycle_validation_v2/    VERSIONE 2: tutto questo progetto, così com'è
    ├── README.md, pyproject.toml, uv.lock, Dockerfile, .gitignore, ...
    ├── src/  tests/  config/  prompts/  eval/  examples/
    └── docs/                   AZIENDA.md, IMPORTAZIONE.md, ...
```

Perché così:

- **`app_cycle_validation/` non cambia nome né posto.** `buildspec.yml` e la pipeline di
  produzione puntano lì: spostarla vorrebbe dire cambiare il deploy. Così, se il branch arriva su
  `main`, la produzione si costruisce come prima.
- **La v2 sta tutta nella sua cartella**, con le sue dipendenze, il suo `.gitignore` e il suo
  `Dockerfile`. Le due versioni non condividono niente: si possono confrontare, e un giorno si
  cancella la v1 con una cartella sola.
- La v2 funziona da una sottocartella senza modifiche: provato, `771 passed, 2 skipped`,
  ruff e mypy puliti, `git status` pulito dopo l'installazione.

---

## 0. Copilot: solo consigli

In VS Code apri la chat di Copilot e scegli la modalità **Ask** (non *Agent* né *Edit*): in Ask
Copilot non può lanciare comandi né scrivere file. Poi incolla questo messaggio, una volta sola,
all'inizio della conversazione:

```text
Per tutta questa conversazione fai solo il consulente.

Regole:
1. Non eseguire comandi, non creare, modificare, spostare o cancellare file, non fare commit né
   push. Se ti chiedo di farlo, ricordami questa regola e dimmi invece cosa devo fare io.
2. Puoi leggere i file del workspace per rispondermi.
3. Quando mi indichi un'azione, dammi il comando esatto per PowerShell su Windows, una riga per
   comando, e dimmi cosa devo aspettarmi di vedere.
4. Le tue risposte le riporto a un'altra persona che mi segue: scrivi in modo breve e preciso,
   con percorsi esatti ed elenchi. Non riportare segreti: account AWS, ARN, URL interni,
   password e token scrivili come <omesso>.
5. Se non trovi un'informazione nei file o non sei sicuro, dillo: non supporre.
6. Non proporre modifiche al codice di app_cycle_validation/: è la versione in produzione.
```

---

## 1. Ricognizione (prima di toccare qualcosa)

Apri in VS Code la cartella del repository aziendale, sul branch `feature/cycle-validation-v2`,
e chiedi a Copilot:

```text
Dimmi, per il repository aperto:
a) l'elenco di file e cartelle in radice, e il primo livello di app_cycle_validation/
   (c'è già una cartella docs/? un README.md?);
b) a quali cartelle e file fanno riferimento buildspec.yml e i file in .github/workflows/
   (percorsi, cd, COPY, docker build, file di requisiti), e con quali branch o eventi partono
   i workflow;
c) per README.md, DOCUMENTAZIONE_TECNICA.md, EJ200_INTEGRATION_PLAN.md e
   REFACTORING_GUIDELINES.md in radice: due righe ciascuno su cosa contengono e se parlano
   della versione in produzione (app_cycle_validation) o di una versione nuova;
d) le righe del .gitignore in radice;
e) se c'è già qualcosa che si chiama app_cycle_validation_v2 o cycle_validation.
```

**Riporta la risposta a chi ti segue prima di andare avanti.** Ci si ferma se:

| Cosa dice Copilot | Perché conta |
|---|---|
| `buildspec.yml` o un workflow fanno riferimento a file in radice diversi da `app_cycle_validation/` (per esempio i `.md` o "tutta la radice") | il riordino potrebbe toccare la build |
| uno dei quattro `.md` parla della versione nuova, non di quella in produzione | va in un altro posto |
| `.gitignore` in radice ha righe come `*.pdf`, `*.json`, `eval/`, `examples/`, `docs/`, `data*` | escluderebbe file della v2 (al punto 4 lo vedi dal conteggio) |
| `app_cycle_validation/` ha già un file con lo stesso nome di uno dei quattro `.md` | lo spostamento lo sovrascriverebbe |

---

## 2. Partire puliti

```powershell
cd <percorso>\avioaero_datalake_cycle_validation
git switch feature/cycle-validation-v2
git pull
git status
git config user.email
```

Devi vedere: `Your branch is up to date`, `nothing to commit, working tree clean` e la tua email
**aziendale** (è quella che finisce nei commit; se è quella personale:
`git config user.email "<email aziendale>"`).

---

## 3. Portare la cartella della v2

Lo zip contiene già la cartella `app_cycle_validation_v2/`, solo file del repository: niente
`.venv`, niente risultati, niente materiale aziendale.

**Se hai lo zip `app_cycle_validation_v2.zip`** (quello mandato in chat), copialo in
`Downloads` e dalla radice del repository:

```powershell
Expand-Archive "$HOME\Downloads\app_cycle_validation_v2.zip" -DestinationPath .
```

**Se lo cloni da GitHub.** Il clone va in una cartella **fuori** dal repository aziendale: da
lì si prende solo il codice, non la storia (che ha commit con l'email personale e non serve al
repository aziendale). Il repository è privato: al primo comando Git chiede di accedere con
l'account GitHub **personale**.

```powershell
cd $HOME\Downloads
git clone https://github.com/DavideZanni/cycle-validation-v2.git
git -C cycle-validation-v2 archive --format=zip --prefix=app_cycle_validation_v2/ -o "$HOME\Downloads\app_cycle_validation_v2.zip" HEAD
```

Il secondo comando fa lo stesso zip mandato in chat (solo i file del repository). Poi torna nella
radice del repository aziendale ed estrai come sopra:

```powershell
cd <percorso>\avioaero_datalake_cycle_validation
Expand-Archive "$HOME\Downloads\app_cycle_validation_v2.zip" -DestinationPath .
```

Se il clone chiede l'accesso e quello personale non passa (rete o regole aziendali), usa lo zip
mandato in chat. Finito tutto, la cartella `Downloads\cycle-validation-v2` si può cancellare.

Controllo, dalla radice del repository:

```powershell
Test-Path .\app_cycle_validation_v2\pyproject.toml
Test-Path .\app_cycle_validation_v2\app_cycle_validation_v2
```

Devi vedere `True` e poi `False` (il secondo `True` vuol dire una cartella dentro l'altra: sposta
il contenuto un livello su).

**Non lanciare ancora `uv sync` né i test**: prima il commit (punto 4), così nel commit finisce
solo il codice.

---

## 4. Riordinare e fare i commit

Due commit separati, così chi guarda la storia capisce cosa è successo.

### 4.1 Documenti della v1 nella sua cartella e README nuovo in radice

```powershell
New-Item -ItemType Directory -Force app_cycle_validation\docs
git mv README.md DOCUMENTAZIONE_TECNICA.md EJ200_INTEGRATION_PLAN.md REFACTORING_GUIDELINES.md app_cycle_validation\docs\
```

Poi il `README.md` nuovo in radice, il cui testo è in `docs/README_RADICE.md` (punto 5):

```powershell
Copy-Item app_cycle_validation_v2\docs\README_RADICE.md README.md
git add README.md
git status
```

Devi vedere, sotto `Changes to be committed`: `modified: README.md`, tre
`renamed: ... -> app_cycle_validation/docs/...` e `new file: app_cycle_validation/docs/README.md`
(il vecchio README risulta "nuovo" perché in radice ce n'è di nuovo uno con lo stesso nome).
Sotto `Untracked files` solo `app_cycle_validation_v2/`. Nient'altro.

```powershell
git commit -m "docs: documentazione della v1 in app_cycle_validation/docs, README di radice per le due versioni"
```

### 4.2 La v2

```powershell
git add app_cycle_validation_v2
(git ls-files app_cycle_validation_v2).Count
```

Devi vedere **238**: sono tutti i file del progetto. Se il numero è più basso, il `.gitignore` di
radice ne esclude qualcuno: **non fare il commit**, lancia

```powershell
git status --short --ignored app_cycle_validation_v2
```

e riporta le righe che iniziano con `!!`.

Se è 238:

```powershell
git commit -m "feat: versione 2 di cycle validation in app_cycle_validation_v2"
git log --oneline -3
git status
```

Devi vedere i due commit in cima e `working tree clean`.

---

## 5. Testo del README di radice

È in `docs/README_RADICE.md` (in azienda: `app_cycle_validation_v2/docs/README_RADICE.md`) e al
punto 4.1 si copia in radice con `Copy-Item`. Una tabella con le due cartelle e il loro stato,
dove trovare la documentazione di ciascuna, e perché `buildspec.yml` e `.github/workflows/`
restano in radice.

---

## 6. Verificare che la v2 giri dal suo posto

```powershell
cd app_cycle_validation_v2
uv sync --all-groups --extra aws
uv run pytest
uv run ruff check .
uv run mypy
cd ..
git status
```

Devi vedere `771 passed, 2 skipped`, `All checks passed!`, `Success: no issues found` e, alla
fine, ancora `working tree clean` (`.venv` e cache sono ignorati dal `.gitignore` della v2). Se
`uv sync` non riesce a scaricare i pacchetti, è la rete aziendale: riporta l'errore.

Da qui in avanti tutti i comandi di `docs/AZIENDA.md` si lanciano da dentro
`app_cycle_validation_v2`.

---

## 7. Push

Solo quando i punti 4 e 6 sono andati come scritto, e se al punto 1 Copilot ha detto che i
workflow non fanno deploy da questo branch:

```powershell
git push origin feature/cycle-validation-v2
```

Poi su GitHub, scheda **Actions**: il workflow di scansione deve finire verde. Se è rosso,
riporta il messaggio.

---

## Se qualcosa non va

| Cosa vedi | Cosa fare |
|---|---|
| `git pull` dice che ci sono conflitti o modifiche locali | fermati e riporta l'output: niente `reset` né `stash` a caso |
| `git mv` dice `destination exists` | in `app_cycle_validation/docs/` c'è già un file con quel nome: riporta quale |
| il conteggio al punto 4.2 non è 238 | `.gitignore` di radice: riporta le righe `!!` |
| `Filename too long` | `git config core.longpaths true`, oppure il repository in un percorso più corto (per esempio `C:\repo\`) |
| `uv` non trovato | `pip install uv`, poi apri un terminale nuovo |
| i test falliscono dopo lo spostamento | riporta le ultime 30 righe dell'output |
| vuoi tornare indietro prima del push | `git reset --hard origin/feature/cycle-validation-v2`, poi cancella a mano la cartella `app_cycle_validation_v2` se è rimasta |
