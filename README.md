# Cycle Validation v2

Validazione dei cicli di riparazione (MOS, DR, EJ200) contro manuali e dati strutturati.
Una pipeline, tre profili: `ingest → extract → integrity → check → consolidate → report`.

Il codice trova il dove (documento e righe), l'agente confronta, il codice verifica la citazione
e assegna l'esito. Tutto ciò che è esterno (S3, Redshift, Bedrock, autenticazione) sta
dietro una porta con un'implementazione di prova: la suite gira offline.

```bash
uv sync
uv run pytest                      # suite completa, offline
uv run ruff check .
uv run cycle-validation kb-check examples/sintetico/knowledge
uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json \
    --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json
uv run cycle-validation golden tests/golden/mos --knowledge examples/sintetico/knowledge \
    --machines examples/sintetico/macchine_attive.json
```

`run` senza `--cycle-json` estrae il ciclo con il modello (serve Bedrock). Gli smoke test reali
vanno eseguiti dove ci sono le credenziali.

Documenti: `docs/superpowers/specs` (design), `docs/superpowers/plans` (piani e avanzamento),
`docs/superpowers/COMPLETION_REPORT.md` (moduli, test, punti di aggancio alla produzione).
