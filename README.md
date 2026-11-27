# Cycle Validation v2

Validazione dei cicli di riparazione (MOS, DR, EJ200) contro manuali e dati strutturati.
Una pipeline, tre profili: `ingest → extract → integrity → check → consolidate → report`.

Il codice trova il dove (documento e righe), l'agente confronta, il codice verifica la citazione
e assegna l'esito. Tutto ciò che è esterno (S3, Redshift, Bedrock) sta
dietro una porta con un'implementazione di prova: la suite gira offline.

```bash
uv sync --all-groups --extra aws
uv run pytest                      # suite completa, offline
uv run ruff check .
uv run cycle-validation kb-check examples/sintetico/knowledge
uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json \
    --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json
uv run cycle-validation golden eval/casi/sintetici/mos --knowledge examples/sintetico/knowledge \
    --machines examples/sintetico/macchine_attive.json
```

`run` senza `--cycle-json` estrae il ciclo con il modello (serve Bedrock). Gli smoke test reali
vanno eseguiti dove ci sono le credenziali.

Documenti (in `docs/`, scritti in modo semplice):

- `docs/DOCUMENTAZIONE.md`: com'è fatto e come funziona tutto il progetto, nei dettagli
  (pipeline, controlli, esiti, conoscenza, servizio, comandi, prove, pubblicazione);
- `docs/COPILOT.md`: il file per lavorare sul PC aziendale: cosa fare adesso, i comandi da
  lanciare, le domande per Copilot e per chi conosce i cicli;
- `docs/MEMORIA.md`: tutto quello che sappiamo già: PC, regole, come funziona la v2, frontend,
  problemi già visti, decisioni prese;
- `docs/MIGLIORIE.md`: tutte le migliorie, provate e da fare, in una tabella;

