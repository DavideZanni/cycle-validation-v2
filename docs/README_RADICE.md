# avioaero_datalake_cycle_validation

Validazione dei cicli di riparazione. Il repository contiene due versioni, una per cartella;
non condividono codice né dipendenze.

| Cartella | Cosa contiene | Stato |
|---|---|---|
| `app_cycle_validation/` | versione 1 | in produzione: la costruisce `buildspec.yml` |
| `app_cycle_validation_v2/` | versione 2: MOS, DR ed EJ200 in una pipeline sola, esiti decisi dal codice, citazioni verificate, suite di test offline | in prova, non ancora in produzione |

- Versione 1: documentazione in `app_cycle_validation/docs/`.
- Versione 2: `app_cycle_validation_v2/README.md`; installazione, configurazione ed esperimenti
  in `app_cycle_validation_v2/docs/AZIENDA.md`.

`buildspec.yml` e `.github/workflows/` restano in radice perché CodeBuild e GitHub li cercano lì.
