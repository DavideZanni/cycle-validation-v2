# Istruzioni per Claude

Prima di lavorare con l'utente sulle prove aziendali leggi `docs/MEMORIA.md`: è la memoria del
progetto (chi fa cosa, PC aziendale, Copilot, pipeline, frontend, stato delle prove, problemi
già visti, decisioni prese). Prima di analizzare un problema guarda lì se è già risolto; quando
impari qualcosa di nuovo, aggiungilo lì. Le regole che non si discutono:

- Si lavora su `main` del repository personale: niente branch.
- Claude non ha accesso al PC aziendale: l'utente lancia nel terminale di VS Code (PowerShell 7)
  i blocchi di `docs/COPILOT.md` e manda le foto. Copilot non modifica il codice e non può
  leggere `data/` (content exclusion dell'organizzazione: non si aggira).
- `docs/COPILOT.md`: blocchi PowerShell pronti da copiare, ognuno con
  `$env:UV_PYTHON = "3.14"`, poi *Deve uscire* e *Manda a Claude*; le parti fatte si tolgono.
- Il repository è pubblico: mai nome del bucket, account, host, matricola, codici di manuali,
  numeri DR, serial o part number veri. Unica eccezione: `docs/CONFRONTO_V1_14_CICLI.md`
  (la v1 sui 14 cicli noti e il testo originale delle stampe, con i codici veri), che il
  responsabile dell'utente ha permesso di tenere nel repository pubblico (27-11): Claude lo
  usa, ma in quello che scrive lui restano impronte e numeri di operazione. Valori inventati negli esempi; i comandi leggono i
  codici dai file sul PC. Nelle foto può comparire il nome del bucket: non ripeterlo.
- Documenti e output EJ200 restano su AWS EU: nessuna copia locale della conoscenza EJ200.
- Prima di ogni commit: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src`.
- Si scrive in italiano, in modo molto semplice. In `docs/` restano quattro file:
  `DOCUMENTAZIONE.md` (com'è fatto e come funziona tutto il progetto, anche installare,
  configurare e avviare il servizio), `COPILOT.md` (lavoro sul PC e domande aperte),
  `MEMORIA.md` (la storia: non si toglie niente), `MIGLIORIE.md`. Niente file
  nuovi in `docs/` senza motivo: si aggiunge a uno di questi. In più c'è
  `CONFRONTO_V1_14_CICLI.md`, messo dall'utente: è un dato, non si modifica.
- Quando cambia come funziona il programma (regole, controlli, comandi, impostazioni, rotte),
  si aggiorna `docs/DOCUMENTAZIONE.md` nello stesso commit.
- Regole fisse dell'utente (dettagli in `docs/MEMORIA.md`, sezione 7): mai scrivere (repository,
  documenti, chat) nome utente Windows o matricola, nomi di colleghi, nome dell'azienda o del
  repository aziendale, oltre ai codici veri; i manuali si chiamano M1…M6, le impronte di 8
  caratteri vanno bene. Mai chiedere né guardare i file degli errori nascosti, i `report.md`,
  i `prestazioni.md` interi, i `transcripts`, `runs/manuali-da-ingestionare.txt`. Nel diff di
  ogni commit niente numeri di 6 o più cifre e niente sigle dei codici veri (le lettere
  G-E-K dei manuali GE e T-E-C-P-R, scritte attaccate).
- Se nelle foto Copilot è su **Agent** (spesso con «Allow all»), ricordare all'utente di
  rimetterlo su **Ask**.
- Le cose da fare per l'utente si scrivono in ordine, ognuna con il paragrafo di `COPILOT.md`,
  *Deve uscire* e *Mandami*. Lo stato del lavoro e il piano verso la presentazione sono in
  `docs/MEMORIA.md`, sezione 0.
