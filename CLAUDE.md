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
  numeri DR, serial o part number veri. Valori inventati negli esempi; i comandi leggono i
  codici dai file sul PC. Nelle foto può comparire il nome del bucket: non ripeterlo.
- Documenti e output EJ200 restano su AWS EU: nessuna copia locale della conoscenza EJ200.
- Prima di ogni commit: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src`.
- Si scrive in italiano, in modo molto semplice. In `docs/` restano quattro file: `COPILOT.md`
  (lavoro sul PC e domande aperte), `MEMORIA.md`, `MIGLIORIE.md`, `AZIENDA.md` (guida tecnica).
  Niente file nuovi in `docs/` senza motivo: si aggiunge a uno di questi.
