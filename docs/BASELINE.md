# Baseline ed esperimenti

**Stato:** metodo e strumento di misura pronti (`eval/`); il registro si riempie con le prove.

## A cosa serve

La baseline è una versione del programma che sappiamo funzionare, con i suoi numeri misurati.
Ogni modifica (un esperimento, un aggiornamento, una miglioria di `docs/MIGLIORIE.md`) si prova
contro di lei: stesse prove, stessi casi, prima e dopo. Si tiene la modifica solo se non
peggiora niente.

## La baseline di oggi

Codice: ramo `main` più le correzioni del 14 novembre 2026 (hook di `StructuredOutput`, extra
`aws`, `.gitignore` per le cartelle di esempio). Quando le correzioni sono nel repository, la
versione si fissa con un'etichetta git `baseline-v1`.

Numeri misurati sul computer personale, modello Claude Haiku con login locale (non Bedrock),
impostazioni predefinite (`effort` predefinito, concorrenza 6, soglia "in linea" 150 righe).

| Prova | Concordanza | Costo | Tempo |
|---|---|---|---|
| Test automatici (modello finto) | 558 su 558 | 0 | 22 s |
| Golden MOS, in linea | 19 su 19 (a volte 18: caso ambiguo, vedi MIGLIORIE A2) | 0,0038 USD | 31 s |
| Golden MOS, ricerca forzata | 19 su 19 | 0,0050 USD | 33 s |
| Golden DR | 29 su 29 | 0,0008 USD | 5 s |
| Golden EJ200 | 22 su 22 | 0,0065 USD | 39 s |
| Ciclo di esempio da 4 operazioni | esiti attesi | 0,0038 USD | 12,7 s |

**I numeri valgono solo nello stesso ambiente.** In azienda il modello passa da Bedrock, con
altre latenze e altri prezzi: la prima cosa da fare lì è rifare questa tabella. Quella diventa
la baseline aziendale.

## Come si fa un esperimento

Con la cartella `eval/` (istruzioni in `eval/README.md`; sui dati veri `docs/ESPERIMENTI_AZIENDA.md`).
`uv run cycle-validation eval pipeline` fa i passi 2-4 da solo. Uno per uno:

1. Scrivi una variante in `eval/varianti/` che cambia **una sola cosa** rispetto a `baseline`.
   Se serve codice nuovo, entra in `src/` dietro le interfacce che esistono già e la variante
   lo sceglie per nome: il codice vecchio resta e si può sempre confrontare.
2. Lancia i test: `uv run pytest`. Devono passare tutti.
3. Lancia `baseline` e la variante con le stesse ripetizioni (almeno **tre**: il modello non
   risponde sempre uguale):
   `uv run cycle-validation eval esegui --variante eval/varianti/<nome>.yaml --ripetizioni 3`.
4. `uv run cycle-validation eval classifica` scrive `eval/risultati/classifica.md`: dice se la variante
   supera i paletti (ERRATO falsi, errori mancati, concordanza, stabilità, esiti tecnici,
   estrazione dal PDF) e di
   quanto cambiano tempo e costo.
5. Se vince, la modifica va in `config/settings.yaml` o nel codice di `main`, la baseline avanza
   (`baseline-v2`) e si scrive la decisione nel registro qui sotto.

## Registro degli esperimenti

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione |
|---|---|---|---|---|---|---|
| 2026-11-14 | `effort: low` (prova veloce, una volta sola) | — | MOS 18-19 su 19 | -30% | -27% per sessione | da ripetere con il metodo sopra |
| 2026-11-14 | `effort: low`, casi sintetici, 3 ripetizioni, login locale | `effort_low` | 99,5% (come baseline) | -22% | -9% | ammessa e più veloce; da confermare su Bedrock con casi veri |
| 2026-11-14 | concorrenza 12 | `concorrenza_12` | 99,0% | -17% | uguale | scartata: concordanza più bassa |
| 2026-11-14 | modello Sonnet | `sonnet` | 98,6% | ×10 | -17% | scartata: concordanza più bassa, costo |

## Da fare nel prossimo passo

1. ~~Uno strumento di misura unico~~: fatto, è `cycle-validation eval` (`eval/README.md`).
2. **La prova con il modello vero** (`pytest -m live`, MIGLIORIE A5).
3. **Un esempio di ciclo DR.** Davide lo fornirà. Andrà in `docs/Esempio ciclo DR/` (cartella
   ignorata da git) con il risultato atteso scritto da chi conosce il ciclo. Serve a:
   - confermare come si riconosce un DR dalla testata (`module_check.dr_markers`);
   - provare il parser di layout anche sul DR (MIGLIORIE A6 e B5);
   - aggiungere un caso DR vero alle prove della baseline.
4. **Casi veri** per MOS ed EJ200, con gli esiti attesi campo per campo: i casi di oggi sono
   inventati e dicono se la meccanica regge, non se il giudizio tecnico è giusto. Come
   prepararli: `docs/ESPERIMENTI_AZIENDA.md` (bozza con `eval prepara`, revisione di un esperto).
