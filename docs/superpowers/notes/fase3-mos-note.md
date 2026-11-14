# Fase 3 (MOS) — note di lavoro

## Cosa giudicano i prompt attuali
Non leggibili da questa macchina (`src/prompts/use_cases/*.yaml` non è disponibile). `legacy_prompts.py`
legge quei file quando ci sono (`load_use_cases`) e `describe_use_cases` ne produce la tabella
(caso d'uso, variabili, ruolo): da lanciare dove i file esistono.

Decisione presa senza i prompt: la sessione per operazione giudica **solo la descrizione**
dell'operazione contro il testo del task. Esistenza e applicabilità di task, targa e scheda
restano controlli a codice. Se dai prompt attuali risultasse che `task_codes_validation`,
`TM_validation` o `SP_validation` valutano anche la *pertinenza* (per esempio: la funzione della
macchina è adatta alla lavorazione), la pertinenza entra nel prompt di `operation_check.md` come
aspetto aggiuntivo, senza altre sessioni: i fatti (funzione della macchina, trattamento della
scheda) sono già nel messaggio (`checks/operation.py::_facts`).

## Parser di layout o LLM
Non decidibile senza PDF reali. Sono pronti entrambi i pezzi: `LlmCycleExtractor` (default) e
`FallbackCycleExtractor(primary, fallback)` per mettere un parser di layout davanti all'LLM.
Il parser di layout MOS non è stato scritto: inventarne uno su un layout sintetico non
direbbe nulla sui documenti reali.

## Misura
`cycle-validation golden DIR` stampa concordanza, costo, tempo e quota di sessioni "in linea".
Il golden set sintetico è in `tests/golden/mos` (3 casi) e `tests/golden/dr` (5 casi, uno per ramo).
