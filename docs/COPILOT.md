# Messaggi per Copilot: importare la v2 nel repository aziendale

Questo file contiene, in ordine, tutti i messaggi da incollare nella chat di Copilot per portare
la v2 nel repository aziendale `avioaero_datalake_cycle_validation`, nella cartella
`app_cycle_validation_v2/`, accanto alla versione in produzione. Il perché delle scelte è in
`docs/IMPORTAZIONE.md`.

**Come funziona.** Copilot non esegue niente: per ogni messaggio ti dice i comandi e cosa devi
vedere, i comandi li lanci tu nel terminale. Sotto ogni messaggio c'è scritto cosa deve uscire.
Se esce altro, usi il messaggio **R1** (in fondo) e non vai avanti finché non è chiaro.

**Dove fermarsi e mandare a Claude:** dopo il messaggio 2 (sempre), quando un controllo non dà
il risultato scritto, e alla fine (messaggio 10).

---

## Prima di cominciare (a mano, senza Copilot)

1. Apri VS Code sulla cartella del repository aziendale (`File → Apri cartella`).
2. Apri un terminale: `Terminale → Nuovo terminale`. Deve essere **PowerShell** e il percorso
   deve essere la radice del repository (quella con `buildspec.yml`).
3. Clona il repository personale in `Downloads`, fuori dal repository aziendale (al primo
   comando Git chiede l'accesso: usa l'account GitHub **personale**):

   ```powershell
   git clone --branch ccr-80f7e33d-6p52sg https://github.com/DavideZanni/cycle-validation-v2.git "$HOME\Downloads\cycle-validation-v2"
   ```

   Se è già clonato, aggiornalo:
   `git -C "$HOME\Downloads\cycle-validation-v2" pull`.
4. Apri questo file: `File → Apri file → Downloads\cycle-validation-v2\docs\COPILOT.md`. I
   messaggi sono i blocchi di testo: copia **tutto** il blocco, dalla prima all'ultima riga.
5. Apri la chat di Copilot e scegli la modalità **Ask** (non *Agent* né *Edit*). Usa una
   conversazione sola dall'inizio alla fine, così Copilot si ricorda le regole.

---

## Messaggio 1: le regole

```text
Per tutta questa conversazione fai solo il consulente.

Regole:
1. Non eseguire comandi, non creare, modificare, spostare o cancellare file, non fare commit né
   push. Se ti chiedo di farlo, ricordami questa regola e dimmi invece cosa devo fare io.
2. Puoi leggere i file del workspace per rispondermi.
3. Quando mi indichi un'azione, dammi il comando esatto per PowerShell su Windows, un comando
   per blocco, e dimmi cosa devo aspettarmi di vedere.
4. Le tue risposte le riporto a un'altra persona che mi segue: scrivi in modo breve e preciso,
   con percorsi esatti ed elenchi. Non riportare segreti: account AWS, ARN, URL interni,
   password e token scrivili come <omesso>.
5. Se non trovi un'informazione nei file o non sei sicuro, dillo: non supporre.
6. Non proporre modifiche al codice di app_cycle_validation/: è la versione in produzione.
7. Quando ti do io i comandi da lanciare, non sostituirli con altri: controllali rispetto al
   repository, dimmi se qualcosa non va e spiegami cosa fanno e cosa devo vedere.
8. Non proporre mai git reset, git stash, git clean, git push --force o cancellazioni, a meno
   che non te lo chieda io esplicitamente.

Rispondi solo "Regole chiare" se hai capito.
```

**Deve uscire:** "Regole chiare" (o simile).

---

## Messaggio 2: ricognizione

```text
#codebase
Prima di cambiare qualsiasi cosa ho bisogno di conoscere il repository aperto. Dimmi:

a) l'elenco di file e cartelle in radice (anche quelli che iniziano con il punto), e il primo
   livello di app_cycle_validation/: c'è già una cartella docs/? c'è un README.md? ci sono file
   chiamati DOCUMENTAZIONE_TECNICA.md, EJ200_INTEGRATION_PLAN.md o REFACTORING_GUIDELINES.md?
b) buildspec.yml: a quali cartelle e file fa riferimento (percorsi, cd, COPY, docker build,
   file di requisiti, artefatti). Fa riferimento a qualcosa in radice che non sia
   app_cycle_validation/?
c) i file in .github/workflows/: per ciascuno, con quali eventi e branch parte, cosa fa, e se
   può fare un deploy o pubblicare qualcosa con un push sul branch feature/cycle-validation-v2;
d) README.md, DOCUMENTAZIONE_TECNICA.md, EJ200_INTEGRATION_PLAN.md e REFACTORING_GUIDELINES.md
   in radice: due righe ciascuno su cosa contengono e se parlano della versione in produzione
   (app_cycle_validation) o di una versione nuova. Qualche altro file del repository fa
   riferimento a questi quattro file con il loro percorso?
e) tutte le righe del .gitignore in radice;
f) se esiste già qualcosa che si chiama app_cycle_validation_v2 o cycle_validation;
g) se c'è un Dockerfile, un requirements.txt o un pyproject.toml in radice o in
   app_cycle_validation/, e dove.

Rispondi con le lettere a)-g), in elenco.
```

**FERMATI QUI.** Copia tutta la risposta di Copilot e mandala a Claude. Vai avanti solo quando
Claude conferma la struttura.

---

## Messaggio 3: partire puliti

```text
Ora devo partire da una situazione pulita. Questi sono i comandi che lancerò nel terminale,
dalla radice del repository:

git switch feature/cycle-validation-v2
git pull
git status
git config user.email
Test-Path .\app_cycle_validation_v2

Controllali e dimmi cosa devo vedere dopo ciascuno.
```

**Deve uscire:**
- `git switch`: `Already on 'feature/cycle-validation-v2'` oppure `Switched to branch ...`;
- `git pull`: `Already up to date.` oppure l'elenco dei file aggiornati, senza la parola
  `CONFLICT`;
- `git status`: `Your branch is up to date with 'origin/feature/cycle-validation-v2'` e
  `nothing to commit, working tree clean`;
- `git config user.email`: la tua email **aziendale**. Se è quella personale, prima di
  continuare: `git config user.email "<email aziendale>"` (vale solo per questo repository);
- `Test-Path`: `False`.

---

## Messaggio 4: portare la cartella della v2

```text
Devo portare un progetto da un altro repository dentro questo, nella cartella
app_cycle_validation_v2, senza la sua storia git. L'ho già clonato in
$HOME\Downloads\cycle-validation-v2 (fuori da questo repository). Questi sono i comandi che
lancerò dalla radice di questo repository:

git -C "$HOME\Downloads\cycle-validation-v2" pull
git -C "$HOME\Downloads\cycle-validation-v2" archive --format=zip --prefix=app_cycle_validation_v2/ -o "$HOME\Downloads\app_cycle_validation_v2.zip" HEAD
Expand-Archive "$HOME\Downloads\app_cycle_validation_v2.zip" -DestinationPath .
Test-Path .\app_cycle_validation_v2\pyproject.toml
Test-Path .\app_cycle_validation_v2\app_cycle_validation_v2
Test-Path .\app_cycle_validation_v2\.git
git status --short

Il secondo comando crea uno zip con i soli file del repository clonato, tutti dentro la cartella
app_cycle_validation_v2/. Controllali e dimmi cosa devo vedere dopo ciascuno. Non devo ancora
installare niente né lanciare test.
```

**Deve uscire:**
- `pull`: `Already up to date.` o l'elenco dei file aggiornati;
- `archive` ed `Expand-Archive`: niente, oppure una barra di avanzamento;
- i tre `Test-Path`: `True`, `False`, `False`;
- `git status --short`: una riga sola, `?? app_cycle_validation_v2/`.

Se `Expand-Archive` dice che un file esiste già, la cartella c'era da un tentativo precedente:
fermati e manda a Claude.

---

## Messaggio 5: documenti della v1 nella sua cartella e README nuovo in radice

```text
Ora sposto i quattro documenti che stanno in radice dentro app_cycle_validation/docs/ e metto in
radice un README nuovo che spiega le due cartelle. Il testo del README nuovo è già pronto nel
file app_cycle_validation_v2/docs/README_RADICE.md. Questi sono i comandi che lancerò dalla
radice:

New-Item -ItemType Directory -Force app_cycle_validation\docs
git mv README.md DOCUMENTAZIONE_TECNICA.md EJ200_INTEGRATION_PLAN.md REFACTORING_GUIDELINES.md app_cycle_validation/docs/
Copy-Item app_cycle_validation_v2\docs\README_RADICE.md README.md
git add README.md
git status

Controllali rispetto al repository (in particolare che in app_cycle_validation/docs/ non ci
siano già file con gli stessi nomi) e dimmi cosa devo vedere dopo ciascuno.
```

**Deve uscire** dopo `git status`, sotto `Changes to be committed`, esattamente queste cinque
righe (l'ordine può cambiare):

```text
modified:   README.md
renamed:    DOCUMENTAZIONE_TECNICA.md -> app_cycle_validation/docs/DOCUMENTAZIONE_TECNICA.md
renamed:    EJ200_INTEGRATION_PLAN.md -> app_cycle_validation/docs/EJ200_INTEGRATION_PLAN.md
new file:   app_cycle_validation/docs/README.md
renamed:    REFACTORING_GUIDELINES.md -> app_cycle_validation/docs/REFACTORING_GUIDELINES.md
```

e sotto `Untracked files` solo `app_cycle_validation_v2/`. Il `README.md` risulta *modified* e
il vecchio *new file* in `docs/` perché in radice ce n'è di nuovo uno con lo stesso nome: è
giusto così.

Se `git mv` dice `destination exists` o `not under version control`: fermati e manda a Claude.

---

## Messaggio 6: primo commit

```text
Il git status è quello atteso. Questi sono i comandi per il primo commit:

git commit -m "docs: documentazione della v1 in app_cycle_validation/docs, README di radice per le due versioni"
git show --stat --oneline HEAD

Dimmi cosa devo vedere.
```

**Deve uscire:** `5 files changed`, con i quattro file in `app_cycle_validation/docs/` e
`README.md`. Nessun file di codice.

---

## Messaggio 7: aggiungere la v2 e secondo commit

```text
Ora aggiungo la cartella app_cycle_validation_v2. Prima del commit voglio controllare che git
prenda tutti i file: devono essere 238. Se il .gitignore in radice ne esclude qualcuno, il
numero è più basso. Questi sono i comandi:

git add app_cycle_validation_v2
(git ls-files app_cycle_validation_v2).Count
git status --short --ignored app_cycle_validation_v2

Dimmi cosa devo vedere. Se il conteggio non è 238 dimmi di fermarmi.
```

**Deve uscire:** `238`, e `git status --short --ignored` con sole righe che iniziano con `A `
(nessuna riga che inizia con `!!`).

**Se non è 238: non fare il commit.** Manda a Claude il numero e le righe che iniziano con `!!`.

Se è 238:

```text
Il conteggio è 238 e non ci sono righe con !!. Questi sono i comandi per il secondo commit:

git commit -m "feat: versione 2 di cycle validation in app_cycle_validation_v2"
git log --oneline -3
git status

Dimmi cosa devo vedere.
```

**Deve uscire:** `238 files changed`; in `git log` i tuoi due commit in cima; `git status` con
`Your branch is ahead of 'origin/feature/cycle-validation-v2' by 2 commits` e
`nothing to commit, working tree clean`.

---

## Messaggio 8: verificare che la v2 funzioni dal suo posto

```text
#codebase
Ora installo la v2 e lancio i suoi controlli, da dentro app_cycle_validation_v2. Leggi
app_cycle_validation_v2/pyproject.toml e app_cycle_validation_v2/.python-version. Questi sono i
comandi che lancerò:

python --version
uv --version
cd app_cycle_validation_v2
uv sync --all-groups --extra aws
uv run pytest
uv run ruff check .
uv run mypy
uv run cycle-validation kb-check examples/sintetico/knowledge
cd ..
git status

Dimmi cosa devo vedere dopo ciascuno. uv è configurato per usare solo il Python installato sul
sistema: se il mio Python non è la versione scritta in .python-version, dimmi cosa fare.
```

**Deve uscire:**
- `python --version`: `Python 3.13.x` o più recente. Se è `3.12.x`, prima di `uv sync` lancia
  `$env:UV_PYTHON = "3.12"` (vale finché il terminale è aperto). Se è più vecchio, o `python` non
  c'è: fermati e manda a Claude;
- `uv --version`: un numero di versione. Se `uv` non c'è: `pip install uv`, poi chiudi e riapri
  il terminale e torna nella radice;
- `uv sync`: finisce con `Installed ... packages`, senza errori. Se non riesce a scaricare (errori
  di rete, certificati, proxy), è la rete aziendale: fermati e manda a Claude l'errore;
- `uv run pytest`: l'ultima riga è `771 passed, 2 skipped`;
- `uv run ruff check .`: `All checks passed!`;
- `uv run mypy`: `Success: no issues found in 89 source files`;
- `kb-check`: un elenco di conteggi che finisce con `recommendation_dr_incerte: 0`;
- `git status` (dalla radice): ancora `nothing to commit, working tree clean`. La cartella
  `.venv` e le cache non devono comparire: le ignora il `.gitignore` della v2.

I test sono stati provati su Linux, non su Windows. Se qualcuno fallisce, **non** correggere
niente: manda a Claude le ultime 40 righe dell'output di `pytest`.

---

## Messaggio 9: push

Solo se i messaggi 4-8 sono andati come scritto e, nel messaggio 2, Copilot ha detto che un push
su `feature/cycle-validation-v2` non fa deploy.

```text
Tutti i controlli sono andati come previsto. #codebase Ricontrolla in .github/workflows/ che un
push sul branch feature/cycle-validation-v2 non faccia deploy né pubblichi niente, poi conferma
il comando:

git push origin feature/cycle-validation-v2

Dimmi cosa devo vedere, e cosa controllare dopo su GitHub.
```

**Deve uscire:** una riga come `abc1234..def5678  feature/cycle-validation-v2 -> feature/cycle-validation-v2`.
Se il push è rifiutato (`rejected`, `fetch first`): qualcun altro ha scritto sul branch.
Fermati e manda a Claude, **niente** `--force`.

Dopo, nel browser, sul repository aziendale:
- branch `feature/cycle-validation-v2`: in radice ci sono `app_cycle_validation/`,
  `app_cycle_validation_v2/`, `.github/`, `.gitignore`, `README.md`, `buildspec.yml`; il README
  mostrato sotto è quello nuovo con la tabella delle due cartelle; la scritta
  `This branch is ... commits ahead of main` ha 2 commit in più di prima (prima era 1);
- scheda **Actions**: il workflow partito con il push deve finire con la spunta verde. Se è
  rosso, apri il passo fallito e manda a Claude il messaggio.

---

## Messaggio 10: riepilogo per Claude

```text
Fammi un riepilogo di quello che abbiamo fatto, per riportarlo a chi mi segue: i commit creati
(hash e messaggio), il risultato di ogni controllo (conteggio dei file, pytest, ruff, mypy,
kb-check, git status, push), e qualunque cosa sia andata diversamente dal previsto.
```

Manda il riepilogo a Claude, con l'esito della scheda Actions.

---

## Pulizia (a mano, alla fine)

Chiudi questo file in VS Code (ne trovi una copia in `app_cycle_validation_v2/docs/COPILOT.md`),
poi:

```powershell
Remove-Item -Recurse -Force "$HOME\Downloads\cycle-validation-v2"
Remove-Item "$HOME\Downloads\app_cycle_validation_v2.zip"
```

Cancellano solo il clone e lo zip in `Downloads`, non il repository aziendale.

---

## Messaggi di riserva

### R1: un comando ha dato un risultato diverso

```text
Ho lanciato questo comando:
<incolla il comando>

e ho visto questo:
<incolla tutto l'output>

Mi aspettavo: <scrivi cosa diceva il file>.
Spiegami cosa vuol dire e cosa è successo. Non propormi comandi che cambiano, spostano o
cancellano qualcosa: dimmi solo cosa riportare a chi mi segue per decidere.
```

Poi manda a Claude il comando, l'output e la risposta di Copilot.

### R2: Copilot ha proposto comandi diversi da quelli del messaggio

```text
Hai proposto comandi diversi da quelli che ti ho dato. Ricorda la regola 7: controlla i miei
comandi, dimmi se c'è un problema concreto e quale, ma non sostituirli.
```

### R3: tornare indietro prima del push

Solo se qualcosa è andato storto **prima** del messaggio 9 e Claude ti ha detto di ripartire da
capo.

```text
Devo annullare i commit locali di oggi e tornare allo stato del branch remoto, prima del push.
Questi sono i comandi che lancerò dalla radice:

git status
git log --oneline -5
git reset --hard origin/feature/cycle-validation-v2
Remove-Item -Recurse -Force .\app_cycle_validation_v2
git status

Spiegami cosa fa ciascuno, cosa si perde e cosa devo vedere alla fine.
```

**Deve uscire** alla fine: `nothing to commit, working tree clean` e i quattro `.md` di nuovo in
radice. Poi riparti dal messaggio 3.
