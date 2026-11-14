# Esperimenti: cartella `eval/` (specifica, primo giro)

Data: 2026-11-14. Stato: approvata da Davide (base subito; mutazioni e guasti simulati dopo).

## Obiettivo

Confrontare alternative del sistema (impostazioni, modelli, in seguito codice nuovo) sugli
stessi casi, con un solo comando, e decidere con regole scritte se un'alternativa è migliore
della baseline. Un esperimento è un file, non un ramo git.

## Cosa entra nel primo giro

- cartella `eval/` con `README.md`, `varianti/`, `casi/`, `risultati/` (ignorata da git),
  `classifica.md` (in git);
- varianti in YAML con ereditarietà (`base:`);
- comando `cycle-validation eval esegui` e `cycle-validation eval classifica`;
- casi sintetici: il golden di oggi, spostato da `tests/golden/` a `eval/casi/sintetici/`
  (una sola copia, usata sia dai test sia dagli esperimenti);
- varianti: `baseline`, `effort_low`, `concorrenza_12`, `sonnet`.

Fuori dal primo giro: mutazioni, guasti simulati, casi aziendali annotati (la cartella è
prevista e ignorata da git), confronto in ombra, `prompt_task_mancante` (richiede una modifica
in `checks/operation.py`), `bedrock_diretto` (richiede una nuova `AgentSession`).

## Variante

```yaml
nome: effort_low
descrizione: meno ragionamento del modello
base: baseline          # facoltativo: eredita tutto dalla variante base
agent:                  # sovrascrive solo queste chiavi di settings.yaml
  effort: low
```

Campi: `nome` (uguale al nome del file), `descrizione`, `base`, `config` (file di impostazioni
di partenza, solo nella radice della catena, predefinito `config/settings.yaml`), `sessione`
(nome dell'implementazione di `AgentSession`, oggi solo `sdk`), e le sezioni di
`settings.yaml` (`agent`, `paths`, `module_check`) come sovrascritture parziali. La fusione è
ricorsiva sulle mappe. Chiavi sconosciute, basi mancanti e cicli di ereditarietà sono errori
di configurazione con messaggio chiaro. Le impostazioni risultanti si validano con `Settings`.

L'opzione `--config` del comando sostituisce il file di partenza della radice: serve per
usare la stessa variante con una copia locale delle impostazioni (per esempio
`use_bedrock: false` sul PC personale).

## Casi

Una suite è una cartella con `suite.yaml` e un caso per sottocartella (formato del golden:
`ciclo.json`, `expected.json`, `ciclo.pdf` facoltativo).

```yaml
conoscenza: examples/sintetico/knowledge   # percorso relativo alla radice del progetto
tipo_conoscenza: locale                    # locale | ej200
macchine: examples/sintetico/macchine_attive.json
```

`ej200` legge catalogo e testi da una cartella con la struttura delle chiavi S3
(`LocalDirObjectStore`). La conoscenza sintetica EJ200 dei test viene esportata in
`eval/casi/sintetici/ej200/conoscenza/`; un test controlla che resti identica alle fixture.

`--casi` accetta una suite o una cartella di suite (predefinito `eval/casi/sintetici`).

## Esecuzione

`cycle-validation eval esegui --variante eval/varianti/effort_low.yaml --ripetizioni 3`

Per ogni ripetizione e ogni caso si esegue la pipeline vera (l'estrazione legge `ciclo.json`,
come nel golden). Un caso che solleva un'eccezione non ferma la prova: si registra come guasto.
Si scrive `eval/risultati/<AAAAMMGG-HHMMSS>_<variante>.json` con:

- intestazione: variante, descrizione, impostazioni risolte, ambiente, commit git (e se la
  working tree è sporca), versione dei prompt, versione dello strumento, data, ripetizioni;
- per ogni caso e ripetizione: righe attese e ottenute (controllo, bersaglio, esito, motivo),
  esiti in più rispetto all'atteso, stato del ciclo, tempi per fase, consumi, sessioni in linea
  e con ricerca, errori di pipeline, citazioni (esiti decisi dal modello con prova verificata
  e con `CITAZIONE_NON_VERIFICATA`), eventuale guasto.

L'ambiente è `--ambiente`, oppure si deduce: `bedrock-<regione>` se `use_bedrock`, altrimenti
`login-locale`.

Per misurare l'avvio dell'agente, `Usage` guadagna due campi: `api_duration_ms` (tempo del
modello, da `ResultMessage.duration_api_ms`) e `wall_ms` (durata della sessione misurata
attorno alla chiamata all'SDK). Avvio per sessione = (`wall_ms` − `api_duration_ms`) / sessioni.

## Misure

Calcolate da `classifica` sui file grezzi, così si possono rifare senza rilanciare.

1. Qualità: concordanza (totale e per controllo); ERRATO falsi (ERRATO ottenuto dove l'atteso
   non è ERRATO, più ERRATO su bersagli non previsti); errori mancati (atteso ERRATO, ottenuto
   altro); citazioni verificate in percentuale. Valori medi per ripetizione.
2. Stabilità: una riga è instabile se nelle ripetizioni compaiono esiti o motivi diversi;
   si contano righe e casi instabili. Con una sola ripetizione la stabilità è "n/d".
3. Tempo e costo: tempo per ciclo mediano e peggiore; mediana per fase (lettura, estrazione,
   controlli); avvio medio dell'agente per sessione; dollari e token medi per ciclo.
4. Robustezza: esiti con `ERRORE_TECNICO`, `BUDGET_ESAURITO`, `ESTRAZIONE_NON_CONFERMATA`,
   errori di pipeline e casi falliti con eccezione, per ripetizione.

## Classifica

Si confrontano solo prove dello stesso ambiente. Per ogni ambiente il riferimento è la prova
più recente della variante `baseline`; per ogni altra variante conta la sua prova più recente.

Paletti (basta superarne uno per essere scartata):

- ERRATO falsi in più;
- errori mancati in più;
- concordanza più bassa (aggiunto rispetto alla proposta: senza, una variante che risponde
  sempre WARNING passerebbe i paletti ed essere veloce la porterebbe in testa);
- più righe instabili (solo se entrambe hanno almeno 2 ripetizioni);
- più esiti tecnici (errore tecnico, budget, estrazione, guasti).

Le ammesse si ordinano per tempo mediano per ciclo, poi per costo. La tabella mostra anche il
caso peggiore e la differenza percentuale dalla baseline. `classifica` scrive
`eval/classifica.md` e lo stampa.

## Requisiti di codice

TDD; test con la sessione finta, nessuna rete; `ruff` e `mypy` verdi; nessun materiale
aziendale nei file in git. I test esistenti del golden restano e leggono la nuova cartella.
