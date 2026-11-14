# Classifica degli esperimenti

Scritta da `cycle-validation eval classifica` il 2026-11-14T15:11: non modificare a mano.
Si confrontano solo prove dello stesso ambiente. Come leggerla: `eval/README.md`.

## Ambiente: login-locale

Riferimento: `baseline`, prova `20261114-145944_baseline.json` (3 ripetizioni, 17 casi). Le percentuali tra parentesi sono la differenza dalla baseline.

### Ammesse, dalla più veloce

| # | Variante | Concordanza | ERRATO falsi | Errori mancati | Righe instabili | Esiti tecnici | Tempo mediano per ciclo | Caso peggiore | Costo per ciclo (USD) | Token per ciclo | Avvio agente per sessione | Citazioni verificate | Ripetizioni | Prova |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `effort_low` | 99,5% | 0 | 0 | 1 (1 casi) | 0 | 4,3 s (-9%) | mos/fonte_e_codice_assenti 5,8 s | 0,0005 (-22%) | 2860 | 1,1 s | 100,0% | 3 | 1f1eed0 · 2026-11-14T15:05:38 |
| 2 | `baseline` | 99,5% | 0 | 0 | 1 (1 casi) | 0 | 4,8 s | mos/fonte_e_codice_assenti 6,4 s | 0,0006 | 2791 | 0,5 s | 100,0% | 3 | 1f1eed0 · 2026-11-14T15:02:46 |

### Scartate

- `concorrenza_12`: concordanza più bassa (99,0% contro 99,5%).
- `sonnet`: concordanza più bassa (98,6% contro 99,5%).

### Concordanza per controllo

| Variante | dr_recommendation | machine_tag | operation_description | process_sheet | source | stato | task_code |
|---|---|---|---|---|---|---|---|
| `effort_low` | 100,0% | 100,0% | 97,2% | 100,0% | 100,0% | 100,0% | 100,0% |
| `baseline` | 100,0% | 100,0% | 97,2% | 100,0% | 100,0% | 100,0% | 100,0% |
| `concorrenza_12` | 100,0% | 100,0% | 94,4% | 100,0% | 100,0% | 100,0% | 100,0% |
| `sonnet` | 100,0% | 100,0% | 91,7% | 100,0% | 100,0% | 100,0% | 100,0% |
