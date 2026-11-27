# Cicli di riparazione e risultati Cycle Validation v1

**Confronto v1 su 14 stampe con errori noti · ambiente QA**

| Metrica | Valore |
|---|---|
| Cicli analizzati | **14** |
| Validati | **10** |
| Interrotti (DR) | **3** |
| Caricamento fallito | **1** |
| Segnalazioni v1 sui validati | **34** |

> **Riservato.** Contiene il testo originale dei cicli, inclusi codici reali. Il nome a impronta non anonimizza il contenuto: verificare le autorizzazioni prima di condividerlo.

*Generato il 27/11/2026 · fonti: PDF originali e CSV esportati dalla v1 nella cartella `runs/v1-confronto`*

---

## Indice

| Sezione | Pagina originale |
|---|---|
| [Come leggere il documento](#come-leggere-il-documento) | 3 |
| [Riepilogo dei 14 cicli](#riepilogo-dei-14-cicli) | 3 |
| [Risultati dei 14 cicli](#risultati-dei-14-cicli) | 4 |
| [Appendice — Testo originale dei cicli](#appendice--testo-originale-dei-cicli) | 36 |

### Elenco dei 14 cicli

| # | Impronta | Codice ciclo | Descrizione | Stato | Errori v1 | Risultati | Testo originale |
|---:|---|---|---|---|---:|---|---|
| 1 | `04ecaabe` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validato | 2 | [Ciclo 04ecaabe](#ciclo-04ecaabe) (p. 4) | [Testo 04ecaabe](#testo-originale-04ecaabe) (p. 36) |
| 2 | `22f586bb` | `GXPR-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validazione interrotta (dati DR) | 1 | [Ciclo 22f586bb](#ciclo-22f586bb) (p. 6) | [Testo 22f586bb](#testo-originale-22f586bb) (p. 44) |
| 3 | `298bc28e` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Caricamento fallito | n.d. | [Ciclo 298bc28e](#ciclo-298bc28e) (p. 8) | [Testo 298bc28e](#testo-originale-298bc28e) (p. 50) |
| 4 | `2d724fba` | `GXRC-72560010A100-1` | GENX-1B LPT BLADE STAGE 6 | Validato | 2 | [Ciclo 2d724fba](#ciclo-2d724fba) (p. 9) | [Testo 2d724fba](#testo-originale-2d724fba) (p. 55) |
| 5 | `38960731` | `GXRC-72560011-270-2` | GENX-2B LPT BLADE STAGE 6 | Validato | 7 | [Ciclo 38960731](#ciclo-38960731) (p. 11) | [Testo 38960731](#testo-originale-38960731) (p. 63) |
| 6 | `4e64d49a` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validato | 1 | [Ciclo 4e64d49a](#ciclo-4e64d49a) (p. 14) | [Testo 4e64d49a](#testo-originale-4e64d49a) (p. 71) |
| 7 | `5ff17062` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validato | 5 | [Ciclo 5ff17062](#ciclo-5ff17062) (p. 16) | [Testo 5ff17062](#testo-originale-5ff17062) (p. 76) |
| 8 | `737dec71` | `GXPR-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validazione interrotta (dati DR) | 1 | [Ciclo 737dec71](#ciclo-737dec71) (p. 19) | [Testo 737dec71](#testo-originale-737dec71) (p. 84) |
| 9 | `895167b9` | `GXPR-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validazione interrotta (dati DR) | 1 | [Ciclo 895167b9](#ciclo-895167b9) (p. 21) | [Testo 895167b9](#testo-originale-895167b9) (p. 90) |
| 10 | `8bdb25d5` | `GXRC-72560010A100-1` | GENX-1B LPT BLADE STAGE 6 | Validato | 3 | [Ciclo 8bdb25d5](#ciclo-8bdb25d5) (p. 23) | [Testo 8bdb25d5](#testo-originale-8bdb25d5) (p. 96) |
| 11 | `8d3c673c` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validato | 5 | [Ciclo 8d3c673c](#ciclo-8d3c673c) (p. 25) | [Testo 8d3c673c](#testo-originale-8d3c673c) (p. 101) |
| 12 | `c5ff3cd6` | `GXRC-72560010A100-1` | GENX-1B LPT BLADE STAGE 6 | Validato | 4 | [Ciclo c5ff3cd6](#ciclo-c5ff3cd6) (p. 29) | [Testo c5ff3cd6](#testo-originale-c5ff3cd6) (p. 111) |
| 13 | `e9b74c84` | `GXRC-72560011-270-2` | GENX-2B LPT BLADE STAGE 6 | Validato | 3 | [Ciclo e9b74c84](#ciclo-e9b74c84) (p. 31) | [Testo e9b74c84](#testo-originale-e9b74c84) (p. 116) |
| 14 | `f355dc3c` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | Validato | 2 | [Ciclo f355dc3c](#ciclo-f355dc3c) (p. 34) | [Testo f355dc3c](#testo-originale-f355dc3c) (p. 121) |

---

## Come leggere il documento

- **Validato:** La v1 ha completato l'analisi; le segnalazioni sono quelle prodotte dalla v1.
- **Validazione interrotta (dati DR):** La v1 si è fermata per serial number, condition o dati DR mancanti: il conteggio non è confrontabile.
- **Caricamento fallito:** La v1 non ha prodotto risultati: lo zero nel CSV non significa «nessun errore».
- **Error / Warning / OK / N/A:** Esito della v1 per ogni fonte, operazione e controllo. I Warning sono elencati a parte e non rientrano nel conteggio degli errori.

> Le segnalazioni v1 sono riportate senza modifiche e **non sono verificate**: alcune possono essere falsi positivi, per esempio quando il testo dice che il riferimento è corretto. Le aree contate sono: Fonti (manuali e DR), Operazione (testo), Macchina (TM), Task code e Scheda. Il testo originale dei PDF, estratto automaticamente, è in appendice; impaginazione e grafica possono differire dagli originali.

---

## Riepilogo dei 14 cicli

| Impronta | Codice ciclo | Descrizione | Rip. | Stato | Errori v1 | Fonti | Operazione | Macchina (TM) | Task code | Scheda | Warning |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `04ecaabe` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A1 | Validato | 2 | 1 | 0 | 0 | 0 | 1 | 0 |
| `22f586bb` | `GXPR-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A6 | Validazione interrotta (dati DR) | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `298bc28e` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A3 | Caricamento fallito | n.d. | — | — | — | — | — | — |
| `2d724fba` | `GXRC-72560010A100-1` | GENX-1B LPT BLADE STAGE 6 | A1 | Validato | 2 | 0 | 1 | 0 | 0 | 1 | 0 |
| `38960731` | `GXRC-72560011-270-2` | GENX-2B LPT BLADE STAGE 6 | A1 | Validato | 7 | 0 | 3 | 1 | 1 | 2 | 0 |
| `4e64d49a` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A3 | Validato | 1 | 1 | 0 | 0 | 0 | 0 | 2 |
| `5ff17062` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A1 | Validato | 5 | 0 | 3 | 0 | 1 | 1 | 1 |
| `737dec71` | `GXPR-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A6 | Validazione interrotta (dati DR) | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `895167b9` | `GXPR-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A6 | Validazione interrotta (dati DR) | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `8bdb25d5` | `GXRC-72560010A100-1` | GENX-1B LPT BLADE STAGE 6 | A2 | Validato | 3 | 0 | 1 | 1 | 0 | 1 | 0 |
| `8d3c673c` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A4 | Validato | 5 | 0 | 2 | 1 | 0 | 2 | 10 |
| `c5ff3cd6` | `GXRC-72560010A100-1` | GENX-1B LPT BLADE STAGE 6 | A2 | Validato | 4 | 0 | 2 | 1 | 0 | 1 | 0 |
| `e9b74c84` | `GXRC-72560011-270-2` | GENX-2B LPT BLADE STAGE 6 | A3 | Validato | 3 | 0 | 2 | 0 | 1 | 0 | 5 |
| `f355dc3c` | `GXRC-72560010A190-1` | GENX-1B LPT BLADE STAGE 7 | A1 | Validato | 2 | 0 | 1 | 0 | 1 | 0 | 2 |
| **Totale** | | | | | **37** | **5** | **15** | **4** | **4** | **9** | **20** |

*Nei cicli interrotti l'unica segnalazione è il messaggio di interruzione della v1, contato tra le Fonti.*

---

## Risultati dei 14 cicli

### Ciclo 04ecaabe
- **Sottotitolo:** `GXRC-72560010A190-1 · GENX-1B LPT BLADE STAGE 7`
- **Codice ciclo:** `GXRC-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Validato`
- **Errori v1:** `2 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `14-10-2025`
- **Riparazioni:** `A1 – BLENDING 70-42-00-350-002`
- **Tipo operazione (v1):** `Blending`
- **Pagine originali:** `11`
- **File/CSV:** `File: 04ecaabe.pdf · cycle_validation_04ecaabe_1795786608868.csv · testo originale a pagina 36`

#### Segnalazioni v1
1. **Fonte Manual GEK112862 · Fonti**
   Error found: Incorrect task code. The task 72-56-32-200-801 refers to LPT Stage 7 blade inspection, which is correct for this MOS cycle. The previous feedback incorrectly stated this was wrong. Source: manual GEK112862, task 72-56-32-200-801 is the correct inspection task for Stage 7 blades.
2. **Op. 040 · Scheda**
   Error found: Incorrect task code. The task cited is '70-24-00-110-033', but the correct task for tabNumber 'CPEC522-BR' (local swab etching on parts made of titanium aluminide base alloy) is '70-24-01 Class I'. Source: Process sheet documents show CPEC522-BR corresponds to task 70-24-01 Class I, not 70-24-00-110-033.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A1 | Manual | GEK9250 | — | 70-42-00-350-002 | OK |
| A1 | Manual | GEK112862 | — | 72-56-32-200-801 | Error |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | identification of the blade: identify and number the defects to be blended with red wax pencil. use the defect report of the repair GXTR-72560010A190-1 RIP.B1. if there isn't an approved DR on this component use the following limits: maximum number of blends for one blade is 4, maximum number of blends on trailing edge is 2, maximum number of blends on leading edge is 2. ref. task 72-56-32-200-801 figure 801 (sheet 3). create a folder in U:\TECPR MICROSCOPIO named as this OL with the defects pictures. if this repair is combined with others, create a sub-folder and rename it: A1 | ZC/457 | 72-56-32-200-801 | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 030 | blend only the defects identified in OP.10. N.B.: do not use abrasives that includes a vitrified bond matrix. requirements: 1) remove the minimum amount of parent material to remove the defect. 2) the length of the blended area should be at least 10 times the depth. 3) spacing between two blending repairs must be at least 1.5X the largest repair semi-length. 4) blended area should maintain approximately the original contour of the blade and the roughness of the adjacent areas. | BA/766 | 70-42-00-350-002 | — | OK |
| 040 | swab etch the blended areas. base material: gamma tial. etchant: class I | BA/662 | — | CPEC522-BR · 70-24-00-110-033 · classe I | Error Scheda |
| 050 | local FPI inspection of the blended areas. acceptability limits: (1)indications less than 0.015 inch (0.38 mm) are non-interpretable and need not to be evaluated. (2) no interpretable linear indication is permitted, unless specified differently. (3) no through indications are permitted. (4) magnification not to exceed 4X can be used for reference purposes only. note: a linear indication is defined as one having a length of more than 4 times its width. | I1439 | — | SLP-05 · 70-32-03-230-002 · classe D | OK |
| 060 | visual inspection of the blended areas with magnification 10X. verify the complete removal of the defects identified in OP.10 and requirements of the technical data sheet. | ZC/095 | — | — | OK |
| 070 | preservare componente come da sezione DT preservazione richiamata in testata O.L. | BA/777 | — | — | OK |
| 075 | do a general visual inspection of the part and a check of the related documentation. compilare come da modulo BQP.08.42.06 - "CHECKLIST FINAL INSPECTION". | ZC/095 | — | — | OK |

---

### Ciclo 22f586bb
- **Sottotitolo:** `GXPR-72560010A190-1 · GENX-1B LPT BLADE STAGE 7`
- **Codice ciclo:** `GXPR-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Validazione interrotta (dati DR)`
- **Errori v1:** `1 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `28-01-2026`
- **Riparazioni:** `A6 – S25/04343-BLENDING DIFETT`
- **Tipo operazione (v1):** `Defects blending`
- **Pagine originali:** `9`
- **File/CSV:** `File: 22f586bb.pdf · cycle_validation_22f586bb_1795787433739.csv · testo originale a pagina 44`

#### Segnalazioni v1
> **Validazione interrotta.** La v1 non ha valutato le operazioni: la segnalazione sotto è il motivo dell'interruzione.

1. **Fonte DR Case 02251702 · Fonti**
   Error found: both serial number and repair condition missing in MOS cycle. Exiting validation process. Provide these info to correctly validate against DR data.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A6 | DR Case | 02251702 | — | — | Error |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | repair in accordance with dr. identification of the blade. record p/n and s/n of the blade. create a new folder in u:\tecpr microscopio\genx with the pictures of the defects to be blended and name it as the ol. record the min depth of defects to be blended. | ZC/454 | — | — | non valutata |
| 020 | handling of the part to the repair area. | PREC01 | — | — | non valutata |
| 030 | blend the defects indicated in the technical inspection, according to d.r. case #02251703. see photos in the folder:u:\tecpr microscopio\genx. remove a minimum amount of material, ensuring a surface finish after blending equivalent to the adjacent surface finish.remove till 0.2 inch. blow the part with clean and dry air. | BA/098 | 70-42-00 | — | non valutata |
| 040 | visual check of the repaired areas to verify complete removal of the defect. take photos of repaired areas and save them in the folder named as ol in u:\tecpr microscopio\genx. | ZC/095 | — | — | non valutata |
| 050 | swab etch all areas. parent material: inco718. | BA/662 | — | CPEC525-BR · 70-24-01-110-034 · classe A | non valutata |
| 060 | local fpi inspection of the blended areas. seviceable limit: indications less than 0.38 mm are not interpretable and need not to be evaluated. linear or through indications are permitted, unless specified differently. magnification not to exceed 4x can be used for reference purposes only. note: linear indications are indications that are at least four times longer than they are wide. | I1439 | — | SLP-10 · 70-32-02-230-001 · classe D | non valutata |
| 080 | preserve component in accordance with work instruction sheet, referred in headline ol. | BA/777 | — | — | non valutata |
| 090 | do a general visual inspection of the part and a check of related documentation. | ZC/095 | — | — | non valutata |

---

### Ciclo 298bc28e
- **Sottotitolo:** `GXRC-72560010A190-1 · GENX-1B LPT BLADE STAGE 7`
- **Codice ciclo:** `GXRC-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Caricamento fallito`
- **Errori v1:** `n.d. errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `11-11-2025`
- **Riparazioni:** `A3 – RIMOZ. METALLO IN RILIEVO`
- **Tipo operazione (v1):** `non riportato`
- **Pagine originali:** `8`
- **File/CSV:** `File: 298bc28e.pdf · cycle_validation_298bc28e_1795787585917.csv · testo originale a pagina 50`

#### Segnalazioni v1
> **Nessun risultato.** Il caricamento nella v1 è fallito; il CSV non contiene fonti né operazioni.

---

### Ciclo 2d724fba
- **Sottotitolo:** `GXRC-72560010A100-1 · GENX-1B LPT BLADE STAGE 6`
- **Codice ciclo:** `GXRC-72560010A100-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 6`
- **Stato:** `Validato`
- **Errori v1:** `2 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `14-10-2025`
- **Riparazioni:** `A1 – BLENDING 70-42-00-350-002`
- **Tipo operazione (v1):** `Blending`
- **Pagine originali:** `11`
- **File/CSV:** `File: 2d724fba.pdf · cycle_validation_2d724fba_1795786027307.csv · testo originale a pagina 55`

#### Segnalazioni v1
1. **Op. 030 · Operazione**
   Error found: (1) Operation states 'do not use abrasives that includes a vitrified bond matrix' without specifying material type. Correction: This restriction applies specifically to titanium alloys and titanium rotating parts. For gamma TiAl blades (LPT Stage 6), this caution should be explicitly stated as applicable to the blade material. Source: manual GEK9250, task 70-42-00-350-002. (2) Operation states 'spacing between two blending repairs must be at least 1.5x the largest repair semi-length'. Correction: According to manual specifications, the distance between two blends must be a minimum of 7.5 times the blend depth of the larger blend, not 1.5x the semi-length. Source: manual GEK112862, task 72-56-31-300-804, Figure 902.
2. **Op. 040 · Scheda**
   Error found: 1) Task code '70-24-00-110-033' does not match the source documents. The correct task for CPEC522-BR (local swab etching on gamma TiAl base alloy) is '70-24-01 Class I'. 2) Class information is missing. The correct class is 'Class I'. Correction: scheda should be {"tabNumber": "CPEC522-BR", "task": "70-24-01", "class": "I"}. Source: Process sheet documents.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A1 | Manual | GEK9250 | — | 70-42-00-350-002 | OK |
| A1 | Manual | GEK112862 | — | 72-56-31-200-801 | OK |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | identification of the blade: identify and number the defects to be blended with red wax pencil. use the defect report of the repair GXTR-72560010A100-1 RIP.B1. if there isn't an approved dr on this component use the following limits: maximum number of blends for one blade is 4, maximum number of blends on trailing edge is 2, maximum number of blends on leading edge is 2. ref. task 72-56-31-200-801 figure 801 (sheet 3). create a folder in u:\tecpr microscopio named as this ol with the defects pictures. if this repair is combined with others, create a sub-folder and rename it: a1 | ZC/457 | 72-56-31-200-801 | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 030 | blend only the defects identified in op.10. n.b.: do not use abrasives that includes a vitrified bond matrix. requirements: 1) remove the minimum amount of parent material to remove the defect. 2) the length of the blended area should be at least 10 times the depth. 3) spacing between two blending repairs must be at least 1.5x the largest repair semi-length. 4) blended area should maintain approximately the original contour of the blade and the roughness of the adjacent areas. | BA/766 | 70-42-00-350-002 | — | Error Operazione |
| 040 | swab etch the blended areas. base material: gamma tial. etchant: class i | BA/662 | 70-24-00-110-033 | CPEC522-BR · 70-24-00-110-033 | Error Scheda |
| 050 | local fpi inspection of the blended areas. acceptability limits: (1)indications less than 0.015 inch (0.38 mm) are non-interpretable and need not to be evaluated. (2) no interpretable linear indication is permitted, unless specified differently. (3) no through indications are permitted. (4) magnification not to exceed 4x can be used for reference purposes only. note: a linear indication is defined as one having a length of more than 4 times its width. | I1439 | 70-32-03-230-002 | SLP-05 · 70-32-03-230-002 · classe D | OK |
| 060 | visual inspection of the blended areas with magnification 10x. verify the complete removal of the defects identified in op.10 and requirements of the technical data sheet. | ZC/095 | — | — | OK |
| 070 | preservare componente come da sezione dt preservazione richiamata in testata o.l. | BA/777 | — | — | OK |
| 075 | do a general visual inspection of the part and a check of the related documentation. compilare come da modulo bqp.08.42.06 - "checklist final inspection". | ZC/095 | — | — | OK |

---

### Ciclo 38960731
- **Sottotitolo:** `GXRC-72560011-270-2 · GENX-2B LPT BLADE STAGE 6`
- **Codice ciclo:** `GXRC-72560011-270-2`
- **Descrizione:** `GENX-2B LPT BLADE STAGE 6`
- **Stato:** `Validato`
- **Errori v1:** `7 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `14-10-2025`
- **Riparazioni:** `A1 – BLENDING 70-42-00-350-002`
- **Tipo operazione (v1):** `blending`
- **Pagine originali:** `11`
- **File/CSV:** `File: 38960731.pdf · cycle_validation_38960731_1795787958988.csv · testo originale a pagina 63`

#### Segnalazioni v1
1. **Op. 010 · Operazione**
   Error found: Operation states maximum number of blends for one blade is 6, maximum number of blends on trailing edge is 3, maximum number of blends on leading edge is 10. However, manual GEK114120 task 72-56-31-300-804 Figure 902 specifies: maximum cumulative number of blends for one blade on leading edge and trailing edge is four (4 total), maximum on trailing edge is two (2), maximum on leading edge is two (2). The limits stated in operation (6 total, 3 trailing, 10 leading) are incorrect. Source: manual GEK114120, task 72-56-31-300-804, Figure 902.
2. **Op. 030 · Task code**
   Error found: wrong task code reference. The correct reference is 70-42-00-350-002. Source: manual GEK9250, task 70-42-00-350-002
3. **Op. 040 · Operazione**
   Error found: Operation states 'base material: gamma tial. etchant: class i'. Correction: For gamma titanium aluminide alloys, Class I etchant is correct and etching time should be 11-13 minutes per manual specifications. However, the operation does not specify the etching time, which is a critical parameter. Source: manual GEK9250, task 70-24-01-110-034, Table 1.
4. **Op. 040 · Macchina (TM)**
   Error found: machine code 'BA/663' not present among active machines (work_center_usage_cd='TO').
5. **Op. 040 · Scheda**
   Error found: 1) tabNumber 'CPEC521-BR' does not exist in the source documents. The correct tabNumber for local swab etching on gamma TiAl base alloy with class I etchant is 'CPEC522-BR'. 2) task '70-24-00-110-034' contains a typo. The correct task reference in the source is '70-24-01 Class I'. Source: Process sheet documents CPEC522-BR
6. **Op. 050 · Operazione**
   Error found: Operation states 'indications over 0.015 inch (0.38 mm) are non-interpretable and need not to be evaluated'. Correction: Indications LESS THAN 0.015 inch (0.38 mm) are non-interpretable and need not to be evaluated, not 'over'. Source: manual GEK114120, Figure 905.
7. **Op. 050 · Scheda**
   Error found: tabNumber 'SLP-06' is for post emulsified level 4 local remover, but the correct tabNumber for post emulsified level 3 local remover with task '70-32-03-230-002 Class D' is 'SLP-05'. Source: Process sheet documents SLP-05, SLP-06

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A1 | Manual | GEK9250 | — | 70-42-00-350-002 | OK |
| A1 | Manual | GEK114120 | — | 72-56-31-200-801 | OK |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | identification of the blade: this repair is applicable only to the following pn's: 2479M15P01, 2479M15P02. identify and number the defects to be blended with red wax pencil. use the defect report of the repair GXTR-72560011-270-2 RIP.B1. if there isn't an approved dr on this component use the following limits: maximum number of blends for one blade is 6, maximum number of blends on trailing edge is 3, maximum number of blends on leading edge is 10. ref. task 72-56-31-200-801 figure 801 (sheet 3). create a folder in u:\tecpr microscopio named as this ol with the defects pictures. if this repair is combined with others, create a sub-folder and rename it: a1 | ZC/457 | 72-56-31-200-801 | — | Error Operazione |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 030 | blend only the defects identified in op.10. n.b.: do not use abrasives that includes a vitrified bond matrix. requirements: 1) remove the minimum amount of parent material to remove the defect. 2) the length of the blended area should be at least 10 times the depth. 3) spacing between two blending repairs must be at least 1.5x the largest repair semi-length. 4) blended area should maintain approximately the original contour of the blade and the roughness of the adjacent areas. | BA/766 | 70-42-00-350-003 | — | Error Task code |
| 040 | swab etch the blended areas. base material: gamma tial. etchant: class i | BA/663 | — | CPEC521-BR · 70-24-00-110-034 · classe I | Error Operazione / Error Macchina (TM) / Error Scheda |
| 050 | local fpi inspection of the blended areas. acceptability limits: (1) indications over 0.015 inch (0.38 mm) are non-interpretable and need not to be evaluated (2) no interpretable linear indication is permitted, unless specified differently. (3) no through indications are permitted. (4) magnification not to exceed 2x can be used for reference purposes only. (5) minimum spacing between two adjacent indications in airfoil areas, can be no less than 5 times the maximum indication size. note: a linear indication is defined as one having a length of more than 4 times its width. | I1439 | — | SLP-06 · 70-32-03-230-002 · classe D | Error Operazione / Error Scheda |
| 060 | visual inspection of the blended areas with magnification 10x. verify the complete removal of the defects identified in op.10 and requirements of the technical data sheet. | ZC/095 | — | — | OK |
| 070 | preservare componente come da sezione dt preservazione richiamata in testata o.l. | BA/777 | — | — | OK |
| 075 | do a general visual inspection of the part and a check of the related documentation. compilare come da modulo bqp.08.42.06 - "checklist final inspection". | ZC/095 | — | — | OK |


---

### Ciclo 4e64d49a

**GXRC-72560010A190-1 · GENX-1B LPT BLADE STAGE 7**
- **Codice ciclo:** `GXRC-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Validato`
- **Errori v1:** `1 errori v1` (`2 warning`)
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `14-10-2025`
- **Riparazioni:** `A3 – RIMOZ. METALLO IN RILIEVO`
- **Tipo operazione (v1):** `High metal removal`
- **Pagine originali:** `8`
- **File/CSV:** `File: 4e64d49a.pdf · cycle_validation_4e64d49a_1795786971066.csv · testo originale a pagina 71`

#### Segnalazioni v1
1. **Fonte Manual GEK112862 · Fonti**
   Error found: Incorrect task code. The cited task 72-56-32-200-801 refers to LPT Stage 7 blade inspection, which is correct for this MOS cycle (GENX-1B LPT BLADE STAGE 7). The previous feedback incorrectly stated this was for Stage 6. Source: manual GEK112862

#### Warning v1 (2, non conteggiati come errori)
1. **Op. 025 · Task code**
   Warning: task 70-42-00-350-029 is incomplete. The complete reference is LEAP-00-70-42-00-350-029
2. **Op. 030 · Task code**
   Warning: task 70-42-00-350-029 is incomplete. The complete reference is LEAP-00-70-42-00-350-029

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A3 | Manual | GEK9250 | — | 70-42-00-350-029 | OK |
| A3 | Manual | GEK112862 | — | 72-56-32-200-801 | Error |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | identification of the blade: identify the defects from which the high metal has to be removed with red wax pencil. create a folder in u:\tecpr microscopio named as this ol with the defects pictures. if this repair is combined with others create a sub-folder and rename it: a3. if there isn't high metal on the blade's profile surfaces, annul op.25 and 35. | ZC/457 | — | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 025 | manual polishing of the concave and convex profile surfaces, for removing the high metal. use crocus cloth 500 grit | BA/766 | 70-42-00-350-029 | — | Warning Task code |
| 030 | remove the high metal from from the defects identified in op.10. n.b.: do not use abrasives that includes a vitrified bond matrix. | BA/766 | 70-42-00-350-029 | — | Warning Task code |
| 035 | visual inspection of the high metal removal, in op.25. | ZC/095 | — | — | OK |
| 040 | visual inspection. verify that the high metal has been removed from the defects identified in op.10. | ZC/095 | — | — | OK |
| 050 | preservare componente come da sezione dt preservazione richiamata in testata o.l. | BA/777 | — | — | OK |
| 060 | do a general visual inspection of the part and a check of the related documentation. compilare come da modulo bqp.08.42.06 - "checklist final inspection". | ZC/095 | — | — | OK |

---

### Ciclo 5ff17062

**GXRC-72560010A190-1 · GENX-1B LPT BLADE STAGE 7**
- **Codice ciclo:** `GXRC-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Validato`
- **Errori v1:** `5 errori v1` (`1 warning`)
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `11-11-2025`
- **Riparazioni:** `A1 – BLENDING 70-42-00-350-002`
- **Tipo operazione (v1):** `blending`
- **Pagine originali:** `11`
- **File/CSV:** `File: 5ff17062.pdf · cycle_validation_5ff17062_1795787055507.csv · testo originale a pagina 76`

#### Segnalazioni v1
1. **Op. 030 · Operazione**
   Error found: (1) States 'remove the maximum amount of parent material to remove the defect'. Correction: Remove only enough material to repair the defect, not the maximum amount. Blend to approximately 1.25 times the depth of the damage. Source: manual GEK9250, task 70-42-00-350-002. (2) States 'the length of the blended area should be 2 times the depth'. Correction: The length of the blend must be a minimum of 10 times the depth of the blend in all directions. Source: manual GEK9250, GEK112862, task 72-56-32-300-804. (3) States 'use abrasives that includes a vitrified bond matrix only'. Correction: For gamma TiAl material, there is no restriction requiring vitrified bond matrix abrasives. The vitrified bond matrix restriction applies to titanium rotating parts where such abrasives are excluded. Source: manual GEK9250.
2. **Op. 030 · Task code**
   Error found: wrong task code reference. The correct reference is 70-42-00-350-002. Source: manual GEK9250, task 70-42-00-350-002
3. **Op. 040 · Operazione**
   Error found: Etchant class specified as 'Class A' is incorrect for gamma TiAl material. Correction: For gamma titanium aluminide alloys, use Class I etchant. Source: manual GEK112862, task 72-56-32-110-010, GEK9250, task 70-24-00-110-033.
4. **Op. 040 · Scheda**
   Error found: 1) Incorrect task code. The task '70-24-00-110-033' is a general reference but the specific task for CPEC522-BR is '70-24-01 Class I'. 2) Missing class information. The source specifies 'Class I' is required for CPEC522-BR, but the class field is null. The correct scheda should be: tabNumber 'CPEC522-BR', task '70-24-01', class 'I'. Source: Process sheet documents
5. **Op. 050 · Operazione**
   Error found: (1) States 'cracks are acceptable'. Correction: Cracks are not permitted. Linear indications are not permitted. Source: manual GEK112862, Figure 905. (2) States 'interpretable linear indication is permitted, unless specified differently'. Correction: No interpretable linear indication is permitted. A linear indication is defined as one having a length of more than 4 times its width. Source: manual GEK112862, task 72-56-32-230-009, Figure 905. (3) States 'through indications are permitted'. Correction: Through indications are not permitted. Source: manual GEK112862, task 72-56-32-230-009, Figure 905.

#### Warning v1 (1, non conteggiati come errori)
1. **Fonte Manual GEK112862 · Fonti**
   Warning: task 72-56-32-200-801 refers to LPT Stage 7 blade inspection, which is correct for the component being repaired (GENX-1B LPT BLADE STAGE 7). The previous feedback incorrectly flagged this as an error.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A1 | Manual | GEK9250 | — | 70-42-00-350-002 | OK |
| A1 | Manual | GEK112862 | — | 72-56-32-200-801 | Warning |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | identification of the blade: identify and number the defects to be blended with red wax pencil. use the defect report of the repair GXTR-72560010A190-1 RIP.B1. if there isn't an approved DR on this component use the following limits: maximum number of blends for one blade is 4. maximum number of blends on trailing edge is 2, maximum number of blends on leading edge is 2. ref. task 72-56-32-200-801 figure 801 (sheet 3). create a folder in U:\TECPR MICROSCOPIO named as this OL with the defects pictures. if this repair is combined with others, create a sub-folder and rename it: A1 | ZC/457 | 72-56-32-200-801 | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 030 | blend only the defects identified in OP.10. n.b.: use abrasives that includes a vitrified bond matrix only. requirements: 1) remove the maximum amount of parent material to remove the defect. 2) the length of the blended area should be 2 times the depth. 3) spacing between two blending repairs must be at least 1.5X the largest repair semi-length. 4) blended area should maintain approximately the original contour of the blade and the roughness of the adjacent areas. | BA/766 | 70-60-00-350-005 | — | Error Operazione / Error Task code |
| 040 | swab etch the blended areas. base material: gamma tial. etchant: class A | BA/662 | — | CPEC522-BR · 70-24-00-110-033 | Error Operazione / Error Scheda |
| 050 | local FPI inspection of the blended areas. acceptability limits: (1) cracks are acceptable. (2) interpretable linear indication is permitted, unless specified differently. (3) through indications are permitted. (4) magnification not to exceed 4X can be used for reference purposes only. note: a linear indication is defined as one having a length of more than 4 times its width. | I1439 | — | SLP-05 · 70-32-03-230-002 · classe D | Error Operazione |
| 060 | visual inspection of the blended areas with magnification 10X. verify the complete removal of the defects identified in OP.10 and requirements of the technical data sheet. | ZC/095 | — | — | OK |
| 070 | preservare componente come da sezione DT preservazione richiamata in testata O.L. | BA/777 | — | — | OK |
| 075 | do a general visual inspection of the part and a check of the related documentation. compilare come da modulo BQP.08.42.06 - "CHECKLIST FINAL INSPECTION". | ZC/095 | — | — | OK |

---

### Ciclo 737dec71

**GXPR-72560010A190-1 · GENX-1B LPT BLADE STAGE 7**
- **Codice ciclo:** `GXPR-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Validazione interrotta (dati DR)`
- **Errori v1:** `1 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `28-01-2026`
- **Riparazioni:** `A6 – S25/04343-BLENDING DIFETT`
- **Tipo operazione (v1):** `Defects blending`
- **Pagine originali:** `9`
- **File/CSV:** `File: 737dec71.pdf · cycle_validation_737dec71_1795787670475.csv · testo originale a pagina 84`

#### Segnalazioni v1
> **Validazione interrotta.** La v1 non ha valutato le operazioni: la segnalazione sotto è il motivo dell'interruzione.

1. **Fonte DR Case 02251702 · Fonti**
   Error found: both serial number and repair condition missing in MOS cycle. Exiting validation process. Provide these info to correctly validate against DR data.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A6 | DR Case | 02251702 | — | — | Error |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | repair in accordance with dr. identification of the blade. record p/n and s/n of the blade. create a new folder in u:\tecpr microscopio\genx with the pictures of the defects to be blended and name it as the ol. record the max depth of defects to be blended. | ZC/454 | — | — | non valutata |
| 020 | handling of the part to the repair area. | PREC01 | — | — | non valutata |
| 030 | blend the defects indicated in the technical inspection, according to d.r. case #02251702. see photos in the folder:u:\tecpr microscopio\genx. remove a minimum amount of material, ensuring a surface finish after blending equivalent to the adjacent surface finish. blow the part with clean and dry air. | BA/098 | 70-42-00 | — | non valutata |
| 040 | visual check of the repaired areas to verify complete removal of the defect. take photos of repaired areas and save them in the folder named as ol in u:\tecpr microscopio\genx. | ZC/095 | — | — | non valutata |
| 050 | swab etch the blended areas. parent material: tial. | BA/662 | — | CPEC522-BR · 70-24-01-110-034 · classe I | non valutata |
| 060 | local fpi inspection of the blended areas. seviceable limit: indications less than 0.38 mm are not interpretable and need not to be evaluated. linear or through indications are not permitted, unless specified differently. magnification not to exceed 4x can be used for reference purposes only. note: linear indications are indications that are at least four times longer than they are wide. | I1439 | — | SLP-04 · 70-32-02-230-001 · classe D | non valutata |
| 080 | preserve component in accordance with work instruction sheet, referred in headline ol. | BA/777 | — | — | non valutata |
| 090 | do a general visual inspection of the part and a check of related documentation. | ZC/095 | — | — | non valutata |

---

### Ciclo 895167b9

**GXPR-72560010A190-1 · GENX-1B LPT BLADE STAGE 7**
- **Codice ciclo:** `GXPR-72560010A190-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 7`
- **Stato:** `Validazione interrotta (dati DR)`
- **Errori v1:** `1 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `28-01-2026`
- **Riparazioni:** `A6 – S25/04343-BLENDING DIFETT`
- **Tipo operazione (v1):** `blending defects`
- **Pagine originali:** `9`
- **File/CSV:** `File: 895167b9.pdf · cycle_validation_895167b9_1795787787443.csv · testo originale a pagina 90`

#### Segnalazioni v1
> **Validazione interrotta.** La v1 non ha valutato le operazioni: la segnalazione sotto è il motivo dell'interruzione.

1. **Fonte DR Case 02251702 · Fonti**
   Error found: no matching DR data found. Check or provide a correct serial number / repair condition. Exiting validation process.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A6 | DR Case | 02251702 | FGGF0HBK | — | Error |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | repair in accordance with dr. identification of the blade. record p/n and s/n of the blade. create a new folder in u:\tecpr microscopio\genx with the pictures of the defects to be blended and name it as the ol. record the min depth of defects to be blended. | ZC/454 | — | — | non valutata |
| 020 | handling of the part to the repair area. | PREC01 | — | — | non valutata |
| 030 | blend the defects indicated in the technical inspection, according to d.r. case #02251703. see photos in the folder:u:\tecpr microscopio\genx. remove a minimum amount of material, ensuring a surface finish after blending equivalent to the adjacent surface finish.remove till 0.2 inch. blow the part with clean and dry air. | BA/098 | 70-42-00 | — | non valutata |
| 040 | visual check of the repaired areas to verify complete removal of the defect. take photos of repaired areas and save them in the folder named as ol in u:\tecpr microscopio\genx. | ZC/095 | — | — | non valutata |
| 050 | swab etch all areas. parent material: inco718. | BA/662 | — | CPEC525-BR · 70-24-01-110-034 · classe A | non valutata |
| 060 | local fpi inspection of the blended areas. seviceable limit: - indications less than 0.38 mm are not interpretable and need not to be evaluated. - linear or through indications are permitted, unless specified differently. - magnification not to exceed 4x can be used for reference purposes only. note: linear indications are indications that are at least four times longer than they are wide. | I1439 | — | SLP-10 · 70-32-02-230-001 · classe D | non valutata |
| 080 | preserve component in accordance with work instruction sheet, referred in headline ol. | BA/777 | — | — | non valutata |
| 090 | do a general visual inspection of the part and a check of related documentation. | ZC/095 | — | — | non valutata |

---

### Ciclo 8bdb25d5

**GXRC-72560010A100-1 · GENX-1B LPT BLADE STAGE 6**
- **Codice ciclo:** `GXRC-72560010A100-1`
- **Descrizione:** `GENX-1B LPT BLADE STAGE 6`
- **Stato:** `Validato`
- **Errori v1:** `3 errori v1`
- **Progetto:** `GENX-1B/GENX-2B`
- **Tipo ciclo:** `NORMALE · MOS Cycle`
- **Data stampa:** `04-12-2025`
- **Riparazioni:** `A2 – APPL. LUBRIFIC. SECCO`
- **Tipo operazione (v1):** `application of solid film lubricant on the coating of the dovetail pressure surfaces`
- **Pagine originali:** `8`
- **File/CSV:** `File: 8bdb25d5.pdf · cycle_validation_8bdb25d5_1795787250978.csv · testo originale a pagina 96`

#### Segnalazioni v1
1. **Op. 030 · Operazione**
   Error found: (1) Operation states 'apply solid film lubricant on the coating of the dovetail pressure surfaces' but the manual specifies application on 'dovetail side surfaces' after thermal spray coating replacement, not on existing coating. The correct procedure is to apply lubricant after coating replacement per TASK 72-56-32-300-802. (2) Operation mentions specimen p/n 3962922/13 with and without thermal spray coating, but this specimen part number is not referenced in the retrieved manual context for Stage 6 blades. Impossible to verify correctness of specimen requirements. (3) Operation states 'the specimens shall be perform the same operations as the blades' but manual does not specify this requirement for solid film lubricant application. Source: manual GEK112862, task 72-56-32-640-001; manual GEK9250, task 70-43-31-640-801.
2. **Op. 030 · Macchina (TM)**
   Error found: machine code IM0823 not found in TM documentation. Unable to verify suitability for solid film lubricant application operation. Warning: machine IM0823 not present in the documents. Impossible to verify correctness of this operation. Source: Machine tags documentation.
3. **Op. 030 · Scheda**
   Error found: 1) tabNumber 'SV562-BR' does not exist in the provided SP documents. 2) Task '70-43-31' is incomplete - the documents do not contain this task reference for GENX engine. The operation describes application of solid film lubricant, but no matching process sheet is found in the sources. Correction needed: verify the correct tabNumber and complete task code for solid film lubricant application on GENX-1B LPT blade dovetail coating.

#### Fonti
| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| A2 | Manual | GEK9250 | — | 70-43-31-640-801 | OK |
| A2 | Manual | GEK112862 | — | 72-56-31-640-001 | OK |

#### Operazioni
| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
| --- | --- | --- | --- | --- | --- |
| 010 | identification of the part. | ZC/457 | — | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 025 | mask the areas of the blade that are not to be painted. | BA/063 | — | — | OK |
| 030 | apply solid film lubricant on the coating of the dovetail pressure surfaces and specimen p/n 3962922/13 (with thermal spray coating) together with each batch of blades for next testing. apply solid film lubricant on the another specimen p/n 3962922/13 (without thermal spray coating) for the next thickness check. note: the specimens shall be perform the same operations as the blades. | IM0823 | — | SV562-BR · 70-43-31 | Error Operazione / Error Macchina (TM) / Error Scheda |
| 040 | visual inspection of coated area: check to ensure that the coating on the hardware has a uniform, dark gray to dark blue color. check to ensure that the coating is free from defects such as pits, blisters, bubbles or scaling. perform the adhesion test on specimen. press a tape on the coating and remove it in an abrupt stripping motion perpendicular to the surface, and ensure that there is no evidence of scaling, peeling or lifting of the coating. perform lubricant thickness check on specimen p/n 3962922/13 (without thermal spray coating). make sure the thickness is within 13-38 micron. | ZC/491 | 70-43-31-640-803 | — | OK |
| 050 | preserve the component i.a.w. the technical data sheet. | BA/777 | — | — | OK |
| 065 | check of the documentation. note: pay attention during the handling of the blade in order to not damage it or their coatings. protect the blades with protective paper. | ZC/095 | — | — | OK |


---

### Ciclo 8d3c673c

- **Codice ciclo**: `GXRC-72560010A190-1`
- **Descrizione**: `GENX-1B LPT BLADE STAGE 7`
- **Stato**: Validato
- **Errori v1**: 5 errori v1 (10 warning)
- **Progetto**: `GENX-1B/GENX-2B`
- **Tipo ciclo**: `NORMALE · MOS Cycle`
- **Data stampa**: `15-12-2025`
- **Riparazioni**: `A4 - 72-56-32 REPAIR 005`
- **Tipo operazione (v1)**: `blending`
- **Pagine originali**: `14`
- **File/CSV**: `8d3c673c.pdf` · `cycle_validation_8d3c673c_1795787291659.csv` · testo originale a pagina 101

#### Segnalazioni v1

1. **Op. 060 · Operazione**
   Error found: (1) Operation states 'opposing blends are not permitted' but manual specifies 'opposite blends are not permitted'. Correction: Use correct terminology 'opposite blends' instead of 'opposing blends'. Source: GEK112862, page 7. (2) Operation states 'blend dovetail corners to a radius of 0.005-0.060 inch (0.13-1.52 mm)' but manual specifies this applies only when repairing corner defects by blending the corner itself to this radius range. For general dovetail area blending (platform, shank, angel wing, dovetail areas), the length and width must be minimum 10 times the depth, except for dovetail corners. The radius specification 0.005-0.060 inch applies specifically to corner repair, not general dovetail blending. Source: GEK112862, page 7.
2. **Op. 070 · Macchina (TM)**
   Error found: machine code ZC/098 not found in machine tags documentation. The correct machine for dimensional inspection should be ZC/095 or A04606. Source: Machine tags documentation.
3. **Op. 100 · Scheda**
   Error found: 1) tabNumber 'CPEC505-BR' is for nickel-based alloy with chromium content less than 20%, not for gamma TiAl material. For gamma TiAl base material, the correct tabNumber should be 'CPEC522-BR' with task '70-24-01 Class I'. 2) Task '70-25-01-110-034' contains a typo: should be '70-24-01-110-034' not '70-25-01-110-034'. 3) Task '70-24-00-110-033' is correct for etching procedures reference. Correction: use tabNumber 'CPEC522-BR' with task '70-24-01 Class I' for gamma TiAl base material. Sources: Process sheet documents, manual GEK112862.
4. **Op. 110 · Scheda**
   Error found: 1) tabNumber 'SLP-06' is for LEAP engines ('70-32-24-01A-351A-D') and post emulsified level 4 local remover, not for GENX engines. For GENX engine local FPI with class D penetrant, the correct tabNumber should be 'SLP-05' with task '70-32-03-230-002 Class D' or '70-32-03 Class D'. 2) Task '70-32-04-230-002' contains a typo: should be '70-32-03-230-002' (spot-fluorescent-penetrant inspection, not '70-32-04'). Correction: use tabNumber 'SLP-05', task '70-32-03-230-002 Class D'. Sources: Process sheet documents.
5. **Op. 140 · Operazione**
   Error found: Operation references task 72-56-31 which is for stage 6 blades, but this cycle is for stage 7 blades. The correct reference should be task 72-56-32 for stage 7 blade inspection. Source: GEK112862.

#### Warning v1 (10, non conteggiati come errori)

1. **Fonte Manual GEK112862 · Fonti**
   Warning: incomplete task code. The correct reference should be 72-56-32-300-804
2. **Op. 060 · Task code**
   Warning: incomplete task code. The complete reference is 70-42-00-350-002 for blending and removal of high metal procedures. Source: manual GEK112862, task 70-42-00-350-002
3. **Op. 090 · Operazione**
   Warning: Operation references '72-56-32, cleaning 001' as task code cited, which is incomplete. The correct reference should include full task code format 72-56-32-XXX-XXX per manual structure. Source: GEK112862.
4. **Op. 090 · Macchina (TM)**
   Warning: machine IM0739 not present in the documents. Impossible to verify correctness of this operation. Source: Machine tags documentation.
5. **Op. 090 · Task code**
   Warning: incomplete task code. The complete reference is 72-56-32-100-801 (72-56-32, CLEANING 001). Source: manual GEK112862, task 72-56-32-100-801
6. **Op. 110 · Operazione**
   Warning: Operation states 'use class d penetrant' but manual specifies 'Use Class D penetrant' (capitalization). However, this is an acceptable variation per validation rules. Operation states 'perform local fpi inspection' but manual specifies spot-fluorescent-penetrant inspection procedures. Impossible to verify if 'local fpi' is equivalent to spot inspection or full FPI without additional context. Source: GEK112862, TASK 70-32-03-230-002, TASK 70-32-02-230-001.
7. **Op. 130 · Operazione**
   Warning: Operation references '72-56-32, cleaning 001' as task code cited, which is incomplete. The correct reference should include full task code format 72-56-32-XXX-XXX per manual structure. Source: GEK112862.
8. **Op. 130 · Macchina (TM)**
   Warning: machine IM0739 not present in the documents. Impossible to verify correctness of this operation. Source: Machine tags documentation.
9. **Op. 130 · Task code**
   Warning: incomplete task code. The complete reference is 72-56-32-100-801 (72-56-32, CLEANING 001). Source: manual GEK112862, task 72-56-32-100-801
10. **Op. 140 · Task code**
    Warning: incomplete task codes. The first cited reference should be 72-56-32-200-801 (72-56-32, INSPECTION 001) for stage 7 blades. The second reference 72-56-31-200-801 (72-56-31, INSPECTION 001) is for stage 6 blades and should not be cited for stage 7 blade inspection. Source: manual GEK112862, tasks 72-56-32-200-801 and 72-56-31-200-801

#### Fonti

| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
|---|---|---|---|---|---|
| A4 | Manual | GEK112862 | — | 72-56-32 | Warning |

#### Operazioni

| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
|---|---|---|---|---|---|
| 020 | identification of the blade: identify and number the defects to be blended with red wax pencil. record number of defects to be blended. create a folder in u:\tecpr microscopio\genx named as this ol with the defects pictures. if this repair is combined with others, create a sub-folder and rename it: a4 | ZC/457 | — | — | OK |
| 030 | handling of the part to repair area | PREC02 | — | — | OK |
| 060 | caution: all blended area must be marked by a wax pencil to allow to identify the area that must checked in next step. refer the map attached to this router. blend the defects identified in op.10. if a large blend in depth is necessary, use a slow speed power tool. make sure that the surface finish after blending is equivalent to the adjacent surface finish. airfoil surf. concave/convex-no area 'x', 'y': blend the concave and convex side airfoil surfaces. refer to d.t. limits. blend and polish in a longitudinal direction, parallel with the length of the blade. blending is not permitted in area x and area y. opposing blends are not permitted. leading/trailing edge area area 'j', 'k','l','m': blend the leading and trailing edges on area j, area k, area l and area m of the blade. refer to d.t. limits. blend and polish in a longitudinal direction, parallel with the length of the blade. the leading and trailing edge radius of the repaired area must agree with the initial contour. refer to figure 903. airfoil surface concave/convex area 'x', 'y': blend to remove damage on area 'x' and 'y'. refer to d.t. limits. platform, shank, angel wing, dovetail shroud: blend to remove the damage on the platform, shank angel wing, dovetail and shroud areas of the blade. refer to d.t. limits. blend dovetail corners to a radius of 0.005-0.060 inch (0.13-1.52 mm). blending on notch 'r' is not permitted. blending on dovetail side surfaces is not permitted. | BA/766 | 70-42-00 | — | Error Operazione; Warning Task code |
| 070 | do a visual and dimensional check of the repaired areas blended in the previous step. make sure that the surface finish after blending is equivalent to the adjacent surface finish. verify the complete removal of the defects identified in op.10 and requirements of the technical data sheet. | ZC/098 | — | — | Error Macchina (TM) |
| 090 | if necessary, clean the blade. refer to 72-56-32, cleaning 001 | IM0739 | 72-56-32 | PG-128 · 70-21-03 | Warning Operazione; Warning Macchina (TM); Warning Task code |
| 100 | swab etch the blended areas. base material: gamma tial. etchant: class i | BA/662 | — | CPEC505-BR · 70-25-01-110-034; 70-24-00-110-033 · classe I | Error Scheda |
| 110 | perform local fpi inspection of the blended areas. use class d penetrant. refer to technical data sheet for the acceptance limits. | ZC/080 | — | SLP-06 · 70-32-04-230-002 · classe D | Error Scheda; Warning Operazione |
| 130 | if necessary, clean the blade. refer to 72-56-32, cleaning 001 | IM0739 | 72-56-32 | PG-128 · 70-21-03 | Warning Operazione; Warning Macchina (TM); Warning Task code |
| 140 | do a visual inspection of the blade. refer to task 72-56-31, inspection 001. fluorescent penetrant inspection is not required. | ZC/095 | 72-56-32, 72-56-31 | — | Error Operazione; Warning Task code |
| 150 | preserve component in accordance with work instruction sheet preservation referred in headline of o.l. | BA/777 | — | — | OK |
| 160 | do a general visual inspection of the part and a check of related documentation. read as per form bqp.08.42.06 - "checklist final inspection". | ZC/095 | — | — | OK |

---

### Ciclo c5ff3cd6

- **Codice ciclo**: `GXRC-72560010A100-1`
- **Descrizione**: `GENX-1B LPT BLADE STAGE 6`
- **Stato**: Validato
- **Errori v1**: 4 errori v1
- **Progetto**: `GENX-1B/GENX-2B`
- **Tipo ciclo**: `NORMALE · MOS Cycle`
- **Data stampa**: `04-12-2025`
- **Riparazioni**: `A2 - APPL. LUBRIFIC. SECCO`
- **Tipo operazione (v1)**: `Application of solid film lubricant`
- **Pagine originali**: `8`
- **File/CSV**: `c5ff3cd6.pdf` · `cycle_validation_c5ff3cd6_1795788078229.csv` · testo originale a pagina 111

#### Segnalazioni v1

1. **Op. 030 · Operazione**
   Error found: Operation states 'apply solid film lubricant on the coating of the dovetail pressure surfaces' but the correct procedure is to apply solid film lubricant directly to the dovetail pressure surfaces after thermal spray coating has been applied. The thermal spray coating is applied first to the dovetail pressure surfaces, then the solid film lubricant is applied to those coated surfaces. The phrasing 'on the coating of the dovetail pressure surfaces' is technically correct as the lubricant is applied to the already-coated dovetail surfaces. Source: manual GEK112862, task 72-56-31-640-001 and 72-56-32-640-001.
2. **Op. 030 · Macchina (TM)**
   Error found: machine code IM0823 not found in TM documentation. Unable to validate suitability for solid film lubricant application operation. Warning: machine IM0823 not present in the documents. Impossible to verify correctness of this operation. Source: Machine tags documentation.
3. **Op. 030 · Scheda**
   Error found: 1) tabNumber 'GEK9250' is not a valid process sheet code. It appears to be a manual reference instead of a process sheet tabNumber. The correct tabNumber should reference a specific process sheet for solid film lubricant application. 2) task '70-43-31' is incomplete. According to the source documents, the complete task reference should be '70-43-31-640-801' as cited in the cycle sources. Source: GEK9250 manual, task 70-43-31-640-801
4. **Op. 040 · Operazione**
   Error found: Operation states 'make sure the thickness is within 13-58 micron' but the correct thickness range for solid film lubricant C02-065 is 0.0005 to 0.0015 inch (12.7 to 38.1 microns). The maximum thickness should be 38.1 microns, not 58 microns. Source: manual GEK9250, task 70-43-31-640-801.

#### Fonti

| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
|---|---|---|---|---|---|
| A2 | Manual | GEK9250 | — | 70-43-31-640-801 | OK |
| A2 | Manual | GEK112862 | — | 72-56-31-640-001 | OK |

#### Operazioni

| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
|---|---|---|---|---|---|
| 010 | identification of the part. | ZC/457 | — | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 025 | mask the areas of the blade that are not to be painted. | BA/063 | — | — | OK |
| 030 | apply solid film lubricant on the coating of the dovetail pressure surfaces and specimen p/n 3962922/13 (with thermal spray coating) together with each batch of blades for next testing. apply solid film lubricant on the another specimen p/n 3962922/13 (without thermal spray coating) for the next thickness check. note: the specimens shall be perform the same operations as the blades. | IM0823 | — | GEK9250 · 70-43-31 | Error Operazione; Error Macchina (TM); Error Scheda |
| 040 | visual inspection of coated area: check to ensure that the coating on the hardware has a uniform, dark gray to dark blue color. check to ensure that the coating is free from defects such as pits, blisters, bubbles or scaling. perform the adhesion test on specimen. press a tape on the coating and remove it in an abrupt stripping motion perpendicular to the surface, and ensure that there is no evidence of scaling, peeling or lifting of the coating. perform lubricant thickness check on specimen p/n 3962922/13 (without thermal spray coating). make sure the thickness is within 13-58 micron. | ZC/491 | 70-43-31-640-803 | — | Error Operazione |
| 050 | preserve the component i.a.w. the technical data sheet. | BA/777 | — | — | OK |
| 065 | check of the documentation. note: pay attention during the handling of the blade in order to not damage it or their coatings. protect the blades with protective paper. compilare come da modulo bqp.08.42.06 - "checklist final inspection". | ZC/095 | — | — | OK |

---

### Ciclo e9b74c84

- **Codice ciclo**: `GXRC-72560011-270-2`
- **Descrizione**: `GENX-2B LPT BLADE STAGE 6`
- **Stato**: Validato
- **Errori v1**: 3 errori v1 (5 warning)
- **Progetto**: `GENX-1B/GENX-2B`
- **Tipo ciclo**: `NORMALE · MOS Cycle`
- **Data stampa**: `14-10-2025`
- **Riparazioni**: `A3 - RIMOZ.METALLO IN RILIEVO`
- **Tipo operazione (v1)**: `high metal removal`
- **Pagine originali**: `8`
- **File/CSV**: `e9b74c84.pdf` · `cycle_validation_e9b74c84_1795788204224.csv` · testo originale a pagina 116

#### Segnalazioni v1

1. **Op. 025 · Operazione**
   Error found: (1) Operation states 'use crocus cloth 60 grit'. Correction: The manual specifies use of fine abrasive stone, emery cloth, or crocus cloth for high metal removal, but does not specify 60 grit. High metal removal should use fine abrasives. Source: manual GEK9250, task 70-42-00-350-002, paragraph C.(3).(e). (2) Operation states 'manual polishing of the concave and convex profile surfaces'. Correction: High metal removal procedure requires removing only the material projecting above the original surface contour, not polishing entire profile surfaces. Source: manual GEK9250, task 70-42-00-350-002, paragraph C.(3).(e).
2. **Op. 025 · Task code**
   Error found: wrong task code reference. The correct reference is 70-42-00-350-002. Source: manual GEK9250, task 70-42-00-350-002
3. **Op. 040 · Operazione**
   Error found: Operation states 'verify that the high metal has been blended from the defects'. Correction: High metal removal and blending are different procedures. High metal is removed (not blended) by using fine abrasive stone, emery cloth, or crocus cloth to remove only the material projecting above the original surface contour. Blending is a different repair procedure used to remove stress concentrations. Source: manual GEK9250, task 70-42-00-350-002.

#### Warning v1 (5, non conteggiati come errori)

1. **Fonte Manual GEK9250 · Fonti**
   Warning: Task 70-42-00-350-029 refers to 'General Removal of High Metal (No Shot Peening)' procedure. However, for rotating parts like blades, task 70-42-00-350-002 paragraph C.(3).(e) 'High Metal Removal Procedure (Rotating Parts)' should be referenced, which requires FPI and shot peening after high metal removal. Source: manual GEK9250, task 70-42-00-350-002.
2. **Op. 010 · Operazione**
   Warning: Operation states this repair is applicable only to part numbers 2479M15P01, 2479M15P02, but these part numbers are not mentioned in referenced manuals. Impossible to verify correctness of this restriction. Source: manual GEK114120, task 72-56-31-200-801.
3. **Op. 030 · Operazione**
   Warning: Operation states 'do not use abrasives that includes a vitrified bond matrix'. This restriction is specified for blending procedures in manual GEK9250, task 70-42-00-350-002, but not explicitly stated for high metal removal procedures. The high metal removal procedure specifies use of fine abrasive stone, emery cloth, or crocus cloth. Source: manual GEK9250, task 70-42-00-350-002.
4. **Op. 030 · Task code**
   Warning: Task 70-42-00-350-029 refers to 'General Removal of High Metal (No Shot Peening)'. For rotating parts like blades, the complete reference should be 70-42-00-350-002 paragraph C.(3).(e) 'High Metal Removal Procedure (Rotating Parts)'. Source: manual GEK9250, task 70-42-00-350-002.
5. **Op. 050 · Operazione**
   Warning: Operation description is in Italian language ('preservare componente come da sezione dt preservazione richiamata in testata o.l.'). Translation suggests preservation/protection procedure, but specific preservation requirements are not found in referenced manuals. Impossible to verify correctness of this operation. Source: manual GEK114120, task 72-56-31-200-801.

#### Fonti

| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
|---|---|---|---|---|---|
| A3 | Manual | GEK9250 | — | 70-42-00-350-029 | Warning |
| A3 | Manual | GEK114120 | — | 72-56-31-200-801 | OK |

#### Operazioni

| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
|---|---|---|---|---|---|
| 010 | identification of the blade: this repair is applicable only to the following pn's: 2479M15P01, 2479M15P02. identify the defects from which the high metal has to be removed with red wax pencil. create a folder in u:\tecpr microscopio named as this ol with the defects pictures. if this repair is combined with others create a sub-folder and rename it: a3. if there isn't high metal on the blade's profile surfaces, annul op.25 and 35. | ZC/457 | — | — | Warning Operazione |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 025 | manual polishing of the concave and convex profile surfaces, for removing the high metal. use crocus cloth 60 grit. | BA/766 | 70-42-00-350-070 | — | Error Operazione; Error Task code |
| 030 | remove the high metal from from the defects identified in op.10. n.b.: do not use abrasives that includes a vitrified bond matrix. | BA/766 | 70-42-00-350-029 | — | Warning Operazione; Warning Task code |
| 035 | visual inspection of the high metal removal, in op.25. | ZC/095 | — | — | OK |
| 040 | visual inspection. verify that the high metal has been blended from the defects identified in op.10. | ZC/095 | — | — | Error Operazione |
| 050 | preservare componente come da sezione dt preservazione richiamata in testata o.l. | BA/777 | — | — | Warning Operazione |
| 060 | do a general visual inspection of the part and a check of the related documentation. | ZC/095 | — | — | OK |

---

### Ciclo f355dc3c

- **Codice ciclo**: `GXRC-72560010A190-1`
- **Descrizione**: `GENX-1B LPT BLADE STAGE 7`
- **Stato**: Validato
- **Errori v1**: 2 errori v1 (2 warning)
- **Progetto**: `GENX-1B/GENX-2B`
- **Tipo ciclo**: `NORMALE · MOS Cycle`
- **Data stampa**: `11-11-2025`
- **Riparazioni**: `A1 - BLENDING 70-42-00-350-002`
- **Tipo operazione (v1)**: `blending`
- **Pagine originali**: `11`
- **File/CSV**: `f355dc3c.pdf` · `cycle_validation_f355dc3c_1795788379549.csv` · testo originale a pagina 121

#### Segnalazioni v1

1. **Op. 030 · Operazione**
   Error found: (1) Operation states 'do not use abrasives that includes a vitrified bond matrix' without specifying this applies to titanium alloys only. Correction: This restriction applies specifically to titanium rotating parts. For gamma titanium aluminide (TiAl) blades, vitrified bond matrix abrasives are not mentioned as restricted in the manuals. Source: manual GEK9250, task 70-42-00-350-002. (2) Operation states 'spacing between two blending repairs must be at least 1.5x the largest repair semi-length'. Correction: According to manual specifications, defects more than 0.25 inch (6.4 mm) apart shall be blended separately; those 0.25 inch or less apart may be blended together. The 1.5x spacing requirement is not mentioned in the manuals. Source: manual GEK9250, task 70-42-00-350-002.
2. **Op. 030 · Task code**
   Error found: wrong task code reference. The correct reference is 70-42-00-350-002. Source: manual GEK9250, task 70-42-00-350-002

#### Warning v1 (2, non conteggiati come errori)

1. **Op. 040 · Scheda**
   Warning: task 70-24-00-110-033 is incomplete. The complete reference is 70-24-01 Class I. Source: Process sheet documentation.
2. **Op. 050 · Scheda**
   Warning: task 70-32-03-230-002 is incomplete. The complete reference is 70-32-03 Class D. Source: Process sheet documentation.

#### Fonti

| Rip. | Tipo | Riferimento | Serial number | Task | Esito v1 |
|---|---|---|---|---|---|
| A1 | Manual | GEK9250 | — | 70-42-00-350-002 | OK |
| A1 | Manual | GEK112862 | — | 72-56-32-200-801 | OK |

#### Operazioni

| Op. | Descrizione | Macchina | Task code | Scheda | Esito v1 |
|---|---|---|---|---|---|
| 010 | identification of the blade: identify and number the defects to be blended with red wax pencil. use the defect report of the repair GXTR-72560010A190-1 RIP.B1. if there isn't an approved DR on this component use the following limits: maximum number of blends for one blade is 4. maximum number of blends on trailing edge is 2. maximum number of blends on leading edge is 2. ref. task 72-56-32-200-801 figure 801 (sheet 3). create a folder in U:\TECPR MICROSCOPIO named as this OL with the defects pictures. if this repair is combined with others, create a sub-folder and rename it: A1 | ZC/457 | 72-56-32-200-801 | — | OK |
| 020 | handling of the part to the repair area. | PREC01 | — | — | OK |
| 030 | blend only the defects identified in OP.10. n.b.: do not use abrasives that includes a vitrified bond matrix. requirements: 1) remove the minimum amount of parent material to remove the defect. 2) the length of the blended area should be at least 10 times the depth. 3) spacing between two blending repairs must be at least 1.5x the largest repair semi-length. 4) blended area should maintain approximately the original contour of the blade and the roughness of the adjacent areas. | BA/766 | 70-60-00-350-005 | — | Error Operazione; Error Task code |
| 040 | swab etch the blended areas. base material: gamma tial. etchant: class I | BA/662 | — | CPEC522-BR · 70-24-00-110-033 · classe I | Warning Scheda |
| 050 | local FPI inspection of the blended areas. acceptability limits: (1) indications less than 0.015 inch (0.38 mm) are non-interpretable and need not to be evaluated. (2) no interpretable linear indication is permitted, unless specified differently. (3) no through indications are permitted. (4) magnification not to exceed 4x can be used for reference purposes only. note: a linear indication is defined as one having a length of more than 4 times its width. | I1439 | — | SLP-05 · 70-32-03-230-002 · classe D | Warning Scheda |
| 060 | visual inspection of the blended areas with magnification 10x. verify the complete removal of the defects identified in OP.10 and requirements of the technical data sheet. | ZC/095 | — | — | OK |
| 070 | preserve component as per preservation section referenced in OL header. | BA/777 | — | — | OK |
| 075 | do a general visual inspection of the part and a check of the related documentation. complete as per form BQP.08.42.06 - "CHECKLIST FINAL INSPECTION". | ZC/095 | — | — | OK |


---

## Appendice — Testo originale dei cicli

Testo estratto automaticamente dai PDF, pagina per pagina. Impaginazione e grafica possono differire dagli originali; il logo non è riprodotto.

### Testo originale 04ecaabe

**GXRC-72560010A190-1** · [torna ai risultati](#ciclo-04ecaabe) (p. 4)

#### Pagina 1 di 11

```text
 PGM PVRM320                         DATA STAMPA 14-10-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RACCORDATURA DIFETTI SECONDO:                       * *        *                                                  *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
         *        *  GEK 112862 TASK 72-56-32-200-801                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  DEFECTS BLENDING I.A.W.:                           *
         *        *                                                     *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
------------------------------------------------------------------------------ *        *  GEK 112862 TASK 72-56-32-200-801                *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE E NUMERARE I DIFETTI DA RACCORDARE    *
         *        *  CON MATITA A CERA ROSSA.                           *
         *        *                                                     *
         *        *  RIFERIRSI ALLA SCHEDA DIFETTI DELLA RIPARAZIONE    *
         *        *  GXTR-72560010A190-1 RIP.B1                         *
         *        *                                                     *
         *        *  ***************** NOTA BENE ******************     *
         *        *                                                     *
         *        *  SE NON è STATA APPROVATA UNA DR SU QUESTO SN        *
         *        *  RISPETTARE I SEGUENTI LIMITI:                      *
         *        *                                                     *
         *        *  - MASSIMO 4 RACCORDATURE SU TUTTA LA PALA          *
         *        *                                                     *
         *        *  - MASSIMO 2 RACCORDATURE SUL BORDO D'ENTRATA       *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *                                                      * *        *  - MASSIMO 2 RACCORDATURE SUL BORDO D'USCITA     *
         *        *                                                     *
         *        *  VEDI TASK 72-56-32-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  DR:...................................             *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RACCORDARE  *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:...............   *
         *        *                                                     *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINANDOLA COME L'OL ED INSERENDO ALL'INTERNO LE  *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A1               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  IDENTIFY AND NUMBER THE DEFECTS TO BE BLENDED WITH *
         *        *   RED WAX PENCIL. USE THE DEFECT REPORT OF THE      *
         *        *  REPAIR GXTR-72560010A190-1 RIP.B1                  *
         *        *                                                     *
         *        *  ******************** N.B. *********************    *
         *        *                                                     *
         *        *  IF THERE ISN'T AN APPROVED DR ON THIS COMPONENT    *
         *        *  USE THE FOLLOWING LIMITS:                          *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  - MAXIMUM NUMBER OF BLENDS FOR ONE BLADE IS 4       * *        *                                                  *
         *        *  - MAXIMUM NUMBER OF BLENDS ON TRAILING EDGE IS 2   *
         *        *                                                     *
         *        *  - MAXIMUM NUMBER OF BLENDS ON LEADING EDGE IS 2    *
         *        *                                                     *
         *        *  REF. TASK 72-56-32-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO            *
         *        *  NAMED AS THIS OL WITH THE DEFECTS PICTURES. IF     *
         *        *  THIS REPAIR IS COMBINED WITH OTHERS, CREATE A SUB- *
------------------------------------------------------------------------------ *        *  FOLDER AND RENAME IT: A1                        *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 030    *                                                      * *        *                              D.T.    08-08-24  *
AVM751  *        *  RACCORDARE SOLO I DIFETTI IDENTIFICATI IN OP.10     * *        * .                                                *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *         DI INCOLLAGGIO VETRIFICATA.                 *
         *        *                                                     *
         *        *  REQUISITI:                                         *
         *        *                                                     *
         *        *  1) ASPORTARE IL MINIMO MATERIALE NECESSARIO ALLA   *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *     RIMOZIONE DEL DIFETTO.                           * *        *                                                  *
         *        *  2) LA LARGHEZZA DELLA RACCORDATURA DEV'ESSERE PARI *
         *        *     AD ALMENO 10 VOLTE LA PROFONDITA'.              *
         *        *                                                     *
         *        *  3) LA SEPARAZIONE FRA DUE AREE RACCORDATE          *
         *        *     DEV'ESSERE PARI AD ALMENO 1,5 VOLTE LA SEMI-    *
         *        *     LUNGHEZZA MAGGIORE DELLE DUE RACCORDATURE.      *
         *        *                                                     *
         *        *  4)  LE AREE RACCORDATE DEVONO MANTENERE,           *
         *        *      APPROSSIMATIVAMENTE, LA GEOMETRIA E LA         *
         *        *      RUGOSITA DELLE AREE CIRCOSTANTI.               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  BLEND ONLY THE DEFECTS IDENTIFIED IN OP.10         *
         *        *  .                                                  *
         *        *  N.B.: DO NOT USE ABRASIVES THAT INCLUDES A         *
         *        *        VITRIFIED BOND MATRIX.                       *
         *        *                                                     *
         *        *  REQUIREMENTS:                                      *
         *        *                                                     *
         *        *  1) REMOVE THE MINIMUM AMOUNT OF PARENT MATERIAL TO *
         *        *     REMOVE THE DEFECT.                              *
         *        *                                                     *
         *        *  2) THE LENGTH OF THE BLENDED AREA SHOULD BE AT     *
         *        *     LEAST 10 TIMES THE DEPTH.                       *
         *        *                                                     *
         *        *  3) SPACING BETWEEN TWO BLENDING REPAIRS MUST BE AT *
         *        *     LEAST 1,5X THE LARGEST REPAIR SEMI-LENGTH.      *
         *        *                                                     *
         *        *  4) BLENDED AREA SHOULD MAINTAIN APPROXIMATELY      *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *     THE ORIGINAL CONTOUR OF THE BLADE AND THE        * *        *     ROUGHNESS OF THE ADJACENT AREAS.             *
         *        *  * ATTREZZATURA PREVISTA *                          * SP.ORIG. 70-42-00-350-002     SP.FIAT
------------------------------------------------------------------------------ *        *  M8225079        LOCATORE CMM BLADE GENX         *
BA/662  * 040    *                                                      *
AVM751  *        *  ATTACCO CHIMICO A TAMPONE DELLE SUPERFICI           * *        *  RACCORDATE.                                     *
         *        *                                                     *
         *        *  MATERIALE BASE: GAMMA TIAL                         *
         *        *                                                     *
         *        *  ETCHANT: CLASS I                                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  SWAB ETCH THE BLENDED AREAS                        *
         *        *                                                     *
         *        *  BASE MATERIAL: GAMMA TIAL                          *
         *        *                                                     *
SCHEDA : CPEC522-BR SP.ORIG. 70-24-00-110-033     SP.FIAT *        *  ETCHANT: CLASS I                            *
------------------------------------------------------------------------------
I1439   * 050    *                                                      *
AVM758  *        *  ISPEZIONE LOCALE CON LIQUIDI PENTERANTI             * *        *  FLUORESCENTI DELLE AREE RACCORDATE.             *
         *        *                                                     *
         *        *  LIMITI DI ACCETTABILITA':                          *
         *        *                                                     *
         *        *  1) LE INDICAZIONI MINORI DI 0,38 MM NON SONO       *
         *        *     INTERPRETABILI E NON DEVONO ESSERE VALUTATE     *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 050    *  2) NON SONO AMMESSE INDICAZIONI LINEARI             * *        *     INTERPRETABILI, SE NON DIVERSAMENTE          *
         *        *     SPECIFICATO.                                    *
         *        *                                                     *
         *        *  3) NON SONO AMMESSE INDICAZIONI PASSANTI           *
         *        *                                                     *
         *        *  4) POSSONO ESSERE UTILIZZATI INGRANDIMENTI SINO 4X *
         *        *     SOLO COME RIFERIMENTO                           *
         *        *                                                     *
         *        *  NOTA: UN INDICAZIONE VIENE DEFINITA LINEARE SE HA  *
         *        *        LUNGHEZZA PARI AD ALMENO 4 VOLTE LA SUA      *
         *        *        LARGHEZZA                                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *                                                     *
         *        *  ACCEPTABILITY LIMITS:                              *
         *        *                                                     *
         *        *  (1)INDICATIONS LESS THAN 0.015 INCH (0.38 MM) ARE  *
         *        *     NON-INTERPRETABLE AND NEED NOT TO BE EVALUATED. *
         *        *                                                     *
         *        *  (2) NO INTERPRETABLE LINEAR INDICATION IS          *
         *        *      PERMITTED, UNLESS SPECIFIED DIFFERENTLY.       *
         *        *                                                     *
         *        *  (3) NO THROUGH INDICATIONS ARE PERMITTED.          *
         *        *                                                     *
         *        *  (4) MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR *
         *        *       REFERENCE PURPOSES ONLY.                      *
         *        *                                                     *
         *        *  NOTE: A LINEAR INDICATION IS DEFINED AS ONE HAVING *
         *        *        A LENGTH OF MORE THAN 4 TIMES ITS WIDTH.     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 8 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
SCHEDA : SLP-05     SP.ORIG. 70-32-03-230-002 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    08-08-24  *
ZC/095  * 060    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELLE AREE RACCORDATE CON LENTE    * *        *  10X.                                            *
         *        *                                                     *
         *        *  VERIFICARE CHE SIANO STATI COMPLETAMENTE RIMOSSI I *
         *        *  DIFETTI IDENTIFICATI IN OP.10 E CHE SIANO          *
         *        *  RISPETTATI I REQUISITI DEL DETTAGLIO TECNICO.      *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE BLENDED AREAS WITH        *
         *        *  MAGNIFICATION 10X.                                 *
         *        *                                                     *
         *        *  VERIFY THE COMPLETE REMOVAL OF THE DEFECTS         *
         *        *  IDENTIFIED IN OP.10 AND REQUIREMENTS OF THE        *
------------------------------------------------------------------------------ *        *  TECHNICAL DATA SHEET.                           *
BA/777  * 070    *                                                      * *        *                              D.T.    09-07-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 075    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
         *        *  A CHECK OF THE RELATED DOCUMENTATION.              *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 9 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 075    *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST  * *        *  FINAL INSPECTION".                              *
==============================================================================
RIP: A1 OEM: GEK112862                   CHANGE: 40        DEL :31.10.2024
FIRMA CHANGE            [NOME OMESSO]           09-12-2024
FIRMA AUTORE
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           12-12-2024
FIRMA ANALISI LAVORO    [NOME OMESSO]           12-12-2024
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 10 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.  10
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 11 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.  11
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 22f586bb

**GXPR-72560010A190-1** · [torna ai risultati](#ciclo-22f586bb) (p. 6)

#### Pagina 1 di 9

```text
 PGM PVRM320                         DATA STAMPA 28-01-2026 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **

==============================================================================                                                    ciclo PROVA AI
```

#### Pagina 2 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  QUESTA PROCEDURA DI RIPARAZIONE FORNI

[... righe non trascritte: nella foto la pagina 44 del PDF non era ancora caricata del tutto ...]

         *        *  .                                                  *
         *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.            *
         *        *  REGISTRARE P/N E S/N DEL PARTICOLARE.              *
         *        *  .                                                  *
         *        *  P/N:                        S/N:                   *
         *        *     ----------------------      -----------------   *
         *        *  .                                                  *
         *        *  ESEGUIRE MAPPATURA DEI DIFETTI DA RIPARARE.        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/454  * 010    *  CREARE NUOVA CARTELLA U:\TECPR MICROSCOPIO\GENX     * *        *  NOMINANDOLA COME L'O.L. E SALVARE FOTO DELLA    *
         *        *  MAPPATURA.                                         *
         *        *  .                                                  *
         *        *  RIPORTARE DI SEGUITO LA PROFONDITA' MASSIMA DEI    *
         *        *  DIFETTI DA RACCORDARE, INDICATA NELLA SEGNALAZIONE *
         *        *  .                                                  *
         *        *  MAX PROFONDITA' DIFETTO:                           *
         *        *                       ----------------------        *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  REPAIR IN ACCORDANCE WITH DR:                      *
         *        *  .                                                  *
         *        *  IDENTIFICATION OF THE BLADE.                       *
         *        *  RECORD P/N AND S/N OF THE BLADE.                   *
         *        *  .                                                  *
         *        *  CREATE A NEW FOLDER IN U:\TECPR MICROSCOPIO\GENX   *
         *        *  WITH THE PICTURES OF THE DEFECTS TO BE BLENDED     *
         *        *  AND NAME IT AS THE OL.                             *
         *        *  .                                                  *
         *        *  RECORD THE MIN DEPTH OF DEFECTS TO BE BLENDED.     *
------------------------------------------------------------------------------ *        * .                                                *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA                          * *        * .                                                *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  HANDLING OF THE PART TO THE REPAIR AREA.           *
------------------------------------------------------------------------------ *        * .                                                *
         *        *                              D.T.    16-09-25 *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
BA/098  * 030    *                                                      *
AVM751  *        *  ESEGUIRE RACCORDATURA DEI DIFETTI INDICATI IN       * *        *  OP.010, SECONDO D.R. CASE #02251703.            *
         *        *  .                                                  *
         *        *  VEDI FOTO IN CARTELLA: U:\TECPR MICROSCOPIO\GENX   *
         *        *  .                                                  *
         *        *  RIMUOVERE IL MINIMO MATERIALE NECESSARIO PER       *
         *        *  RIMUOVERE IL DIFETTO GARANTENDO UNA FINITURA       *
         *        *  SUPERFICIALE PARI A QUELLA DELLE AREE ADIACENTI    *
         *        *  NON LAVORATE.                                      *
         *        *  .                                                  *
         *        *  ESEGUIRE SOFFIATURA CON ARIA SECCA E PULITA DEL    *
         *        *  PARTICOLARE.                                       *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  BLEND THE DEFECTS INDICATED IN THE TECHNICAL       *
         *        *  INSPECTION, ACCORDING TO D.R. CASE #02251703.      *
         *        *  .                                                  *
         *        *  SEE PHOTOS IN THE FOLDER:U:\TECPR MICROSCOPIO\GENX *
         *        *  .                                                  *
         *        *  REMOVE A MINIMUM AMOUNT OF MATERIAL, ENSURING      *
         *        *  A SURFACE FINISH AFTER BLENDING EQUIVALENT TO      *
         *        *  THE ADJACENT SURFACE FINISH.REMOVE TILL 0.2 INCH
                  * *        *  .
                    BLOW THE PART WITH CLEAN AND DRY AIR.               * *
               *  .                                                     * SP.ORIG. 70-42-00             SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    16-09-25  *
ZC/095  * 040    *                                                      *
AVM75A  *        *  ESEGUIRE CONTROLLO VISIVO DELLE AREE RIPARATE       * *        *  AL FINE DI VERIFICARE LA COMPLETA RIMOZIONE     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 040    *  DEL DIFETTO.                                        * *        *  FOTOGRAFARE LE AREE RIPARATE E SALVARE LE FOTO  *
         *        *  IN CARTELLA NOMINATA COME L'O.L. IN                *
         *        *  U:\TECPR MICROSCOPIO\GENX.                         *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  VISUAL CHECK OF THE REPAIRED AREAS TO VERIFY       *
         *        *  COMPLETE REMOVAL OF THE DEFECT.                    *
         *        *  TAKE PHOTOS OF REPAIRED AREAS AND SAVE THEM IN THE *
         *        *  FOLDER NAMED AS OL IN U:\TECPR MICROSCOPIO\GENX    *
------------------------------------------------------------------------------ *        * .                                                *
BA/662  * 050    *                                                      * *        *                              D.T.    16-09-25  *
AVM751  *        *  ESEGUIRE ATTACCO CHIMICO LOCALE A TAMPONE DELLE     * *        *  SUPERFICI RACCORDATE.                           *
         *        *  .                                                  *
         *        *  MATERIALE BASE: TIAL                               *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  SWAB ETCH ALL AREAS.                        * *
          * .                                                    * *
         *          PARENT MATERIAL: INCO718                          *
SCHEDA : CPEC525-BR SP.ORIG. 70-24-01-110-034 A   SP.FIAT 70-24-00-110-033   *        * .                                                *
------------------------------------------------------------------------------ *        *                              D.T.    16-09-25  *
I1439   * 060    *                                                      *
AVM758  *        *  ESEGUIRE CONTROLLO LOCALE CON LIQUIDI PENETRANTI    * *        *  FLUORESCENTI, CLASSE D, DELLE AREE RACCORDATE.  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 060    *  .                                                   * *        *  LIMITI DI ACCETTABILITA':                       *
         *        *  - INDICAZIONI INFERIORI A 0.38 MM NON SONO         *
         *        *    INTERPRETABILI E NON DEVONO ESSERE VALUTATE.     *
         *        *  .                                                  *
         *        *  - NON SONO AMMESSE INDICAZIONI LINEARI O PASSANTI  *
         *        *    INTERPRETABILI, SALVO DIVERSA INDICAZIONE.       *
         *        *  .                                                  *
         *        *  - LENTE CON INGRANDIMENTO SUPERIORE A 4X PUÒ       *
         *        *    ESSERE UTILIZZATA SOLTANTO COME RIFERIMENTO.     *
         *        *                                                     *
         *        *  NOTA: SI DEFINISCE LINEARE UN'INDICAZIONE CHE      *
         *        *        PRESENTA UNA LUNGHEZZA PARI AD ALMENO        *
         *        *        QUATTRO VOLTE LA SUA LARGHEZZA.              *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *  .                                                  *
         *        *  SEVICEABLE LIMIT:                                  *
         *        *  - INDICATIONS LESS THAN 0.38 MM ARE NOT            *
         *        *    INTERPRETABLE AND NEED NOT TO BE EVALUATED       *
         *        *  .                                                  * *        *  - LINEAR OR THROUGH INDICATIONS ARE PERMITTED,  *
         *        *    UNLESS SPECIFIED DIFFERENTLY.                    *
         *        *  .                                                  *
         *        *  - MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR   *
         *        *    REFERENCE PURPOSES ONLY.                         *
         *        *  .                                                  *
         *        *  NOTE: LINEAR INDICATIONS ARE INDICATIONS THAT      *
         *        *        ARE AT LEAST FOUR TIMES LONGER THAN THEY ARE *
         *        *        WIDE.                                        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 060    *  .                                                   *
SCHEDA : SLP-10     SP.ORIG. 70-32-02-230-001 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    07-04-19  *
BA/777  * 080    *                                                      *
AVM75A  *        *  PRESERVARE IL COMPONENTE COME DA PRESERVAZIONE      * *        *  RICHIAMATA NELL' O.L. PRIMA PAGINA.             *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  PRESERVE COMPONENT IN ACCORDANCE WITH WORK         *
         *        *  INSTRUCTION SHEET, REFERRED IN HEADLINE OL.        *
------------------------------------------------------------------------------ *        * .                                                *
ZC/095  * 090    *                                                      * *        *                              D.T.    27-09-24  *
AVM75A  *        *  ESEGUIRE COLLAUDO FINALE, DOCUMENTALE E             * *        *  VERSAMENTO.                                     *
         *        *  CONSULTARE LA LISTA DI CONTROLLO COME DA MODULO    *
         *        *  BQP.08.42.06 - "CHECKLIST FINAL INSPECTION".       *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND A   *
         *        *  CHECK OF RELATED DOCUMENTATION.                    *
============================================================================== *        * .                                                *
RIP: A6 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]           15/09/2025
FIRMA AUTORE            [NOME OMESSO]           25-09-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           17-09-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           17-09-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 8 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 9 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 298bc28e

**GXRC-72560010A190-1** · [torna ai risultati](#ciclo-298bc28e) (p. 8)

#### Pagina 1 di 8

```text
 PGM PVRM320                         DATA STAMPA 11-11-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RIMOZIONE METALLO IN RILIEVO SECONDO:               * *        *                                                  *
         *        *  GEK9250 SUBTASK 70-42-00-350-035                   *
         *        *  GEK112862 TASK 72-56-32-200-801                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  REMOVAL OF HIGH METAL PROCEDURES I.A.W.:           *
         *        *                                                     *
         *        *  GEK9250 SUBTASK 70-42-00-350-029                   *
------------------------------------------------------------------------------ *        *  GEK112862 TASK 72-56-32-200-801                 *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE I DIFETTI DAI QUALI RIMUOVERE IL      *
         *        *  METALLO IN RILIEVO INDICANDOLI SULLA PALA CON      *
         *        *  MATITA A CERA ROSSA.                               *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RIPARARE:   *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:...............   *
         *        *                                                     *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINADOLA COME L'OL ED INSERENDO ALL'INTERNO LE   *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A3               *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  SE NON è PRESENTE METALLO IN RILIEVO SUL PROFILO    * *        *  DELLA PALA ANNULLARE LE OP.25 E 35.             *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  IDENTIFY THE DEFECTS FROM WHICH THE HIGH METAL HAS *
         *        *  TO BE REMOVED WITH RED WAX PENCIL.                 *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO NAMED AS   *
         *        *  THIS OL WITH THE DEFECTS PICTURES. IF THIS REPAIR  *
         *        *  IS COMBINED WITH OTHERS CREATE A SUB-FOLDER AND    *
         *        *  RENAME IT: A3                                      *
         *        *                                                     *
         *        *  IF THERE ISN'T HIGH METAL ON THE BLADE'S PROFILE   *
------------------------------------------------------------------------------ *        *  SURFACES, ANNUL OP.25 AND 35.                   *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 025    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM751  *        *  LUCIDATURA MANUALE DELLE AREE CONCAVA E CONVESSA    * *        *  DEL PROFILO PALA, AL FINE DI RIMUOVERE IL METALLO *
         *        *  IN RILIEVO.                                        *
         *        *                                                     *
         *        *  UTILIZZARE CARTA ABRASIVA GRANA 500                *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 025    *                                                      * *        *  * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  MANUAL POLISHING OF THE CONCAVE AND CONVEX PROFILE *
         *        *  SURFACES, FOR REMOVING THE HIGH METAL.             *
         *        *                                                     *
         *        *  USE CROCUS CLOTH 500 GRIT                          * SP.ORIG. 70-42-00-350-029     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8225079       LOCATORE CMM BLADE GENX          *
BA/766  * 030    *                                                      *
AVM751  *        *  RIMUOVERE IL METALLO IN RILIEVO DAI DIFETTI         * *        *  INDICATI IN OP.10.                              *
         *        *  .                                                  *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *        DI INCOLLAGGIO VETRIFICATA.                  *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  REMOVE THE HIGH METAL FROM FROM THE DEFECTS        *
         *        *  IDENTIFIED IN OP.10.                               *
         *        *  .                                                  *
         *        *       N.B.: DO NOT USE ABRASIVES THAT INCLUDES A     *
         *        *       VITRIFIED BOND MATRIX.                        * SP.ORIG. 70-42-00-350-029     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8225079       LOCATORE CMM BLADE GENX          *
ZC/095  * 035    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM75A  *        *  COLLAUDO VISIVO DELLE AREE RACCORDATE  * *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
------------------------------------------------------------------------------
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 035    *  EFFETTUATA IN OP.25.                                * *        *                                                  *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE HIGH METAL REMOVAL,       *
------------------------------------------------------------------------------ *        *  IN OP.25.                                       *
ZC/095  * 040    *                                                      *
AVM75A  *        *  CONTROLLO VISIVO.                                   * *        *                                                  *
         *        *  VERIFICARE CHE SIA STATO RIMOSSO IL METALLO IN     *
         *        *  RILIEVO DAI DIFETTI IDENTIFICATI IN OP.10.         *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION                                  *
         *        *                                                     *
         *        *  VERIFY THAT THE HIGH METAL HAS BEEN REMOVED FROM   *
------------------------------------------------------------------------------ *        *  THE DEFECTS IDENTIFIED IN OP.10.                *
BA/777  * 050    *                                                      * *        *                              D.T.    07-04-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 060    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
         *        *  A CHECK OF THE RELATED DOCUMENTATION.              *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 060    *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST  * *        *  FINAL INSPECTION".                              *
==============================================================================
RIP: A3 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]           03/07/2025
FIRMA AUTORE            [NOME OMESSO]           02-10-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           02-10-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           02-10-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 7 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 8 di 8

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 2d724fba

**GXRC-72560010A100-1** · [torna ai risultati](#ciclo-2d724fba) (p. 9)

#### Pagina 1 di 11

```text
 PGM PVRM320                         DATA STAMPA 14-10-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RACCORDATURA DIFETTI SECONDO:                       * *        *                                                  *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
         *        *  GEK 112862 TASK 72-56-31-200-801                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  DEFECTS BLENDING I.A.W.:                           *
         *        *                                                     *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
------------------------------------------------------------------------------ *        *  GEK 112862 TASK 72-56-31-200-801                *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE E NUMERARE I DIFETTI DA RACCORDARE    *
         *        *  CON MATITA A CERA ROSSA.                           *
         *        *                                                     *
         *        *  RIFERIRSI ALLA SCHEDA DIFETTI DELLA RIPARAZIONE    *
         *        *  GXTR-72560010A100-1 RIP.B1                         *
         *        *                                                     *
         *        *  ***************** NOTA BENE ******************     *
         *        *                                                     *
         *        *  SE NON è STATA APPROVATA UNA DR SU QUESTO SN       *
         *        *  RISPETTARE I SEGUENTI LIMITI:                      *
         *        *                                                     *
         *        *  - MASSIMO 4 RACCORDATURE SU TUTTA LA PALA          *
         *        *                                                     *
         *        *  - MASSIMO 2 RACCORDATURE SUL BORDO D'ENTRATA       *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *                                                      * *        *  - MASSIMO 2 RACCORDATURE SUL BORDO D'USCITA     *
         *        *                                                     *
         *        *  VEDI TASK 72-56-31-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  DR:..................................              *
         *        *  .                                                  *
         *        *  SD:..........................................      *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RACCORDARE  *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:................  *
         *        *                                                     *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINANDOLA COME L'OL ED INSERENDO ALL'INTERNO LE  *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A1               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  IDENTIFY AND NUMBER THE DEFECTS TO BE BLENDED WITH *
         *        *   RED WAX PENCIL. USE THE DEFECT REPORT OF THE      *
         *        *  REPAIR GXTR-72560010A100-1 RIP.B1                  *
         *        *                                                     *
         *        *  ********************* N.B. ********************    *
         *        *                                                     *
         *        *  IF THERE ISN'T AN APPROVED DR ON THIS COMPONENT    *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  USE THE FOLLOWING LIMITS:                           * *        *                                                  *
         *        *  - MAXIMUM NUMBER OF BLENDS FOR ONE BLADE IS 4      *
         *        *                                                     *
         *        *  - MAXIMUM NUMBER OF BLENDS ON TRAILING EDGE IS 2   *
         *        *                                                     *
         *        *  - MAXIMUM NUMBER OF BLENDS ON LEADING EDGE IS 2    *
         *        *                                                     *
         *        *  REF. TASK 72-56-31-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO            *
         *        *  NAMED AS THIS OL WITH THE DEFECTS PICTURES. IF     *
         *        *  THIS REPAIR IS COMBINED WITH OTHERS, CREATE A SUB- *
------------------------------------------------------------------------------ *        *  FOLDER AND RENAME IT: A1                        *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 030    *                                                      * *        *                              D.T.    08-08-24  *
AVM751  *        *  RACCORDARE SOLO I DIFETTI IDENTIFICATI IN OP.10     * *        * .                                                *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *        DI INCOLLAGGIO VETRIFICATA.                  *
         *        *                                                     *
         *        *  REQUISITI:                                         *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *                                                      * *        *  1) ASPORTARE IL MINIMO MATERIALE NECESSARIO ALLA *
         *        *      RIMOZIONE DEL DIFETTO.                         *
         *        *                                                     *
         *        *  2) LA LARGHEZZA DELLA RACCORDATURA DEV'ESSERE PARI *
         *        *     AD ALMENO 10 VOLTE LA PROFONDITA'.              *
         *        *                                                     *
         *        *  3) LA SEPARAZIONE FRA DUE AREE RACCORDATE          *
         *        *     DEV'ESSERE PARI AD ALMENO 1,5 VOLTE LA SEMI-    *
         *        *     LUNGHEZZA MAGGIORE DELLE DUE RACCORDATURE.      *
         *        *                                                     *
         *        *  4)  LE AREE RACCORDATE DEVONO MANTENERE,           *
         *        *      APPROSSIMATIVAMENTE, LA GEOMETRIA E LA         *
         *        *      RUGOSITA DELLE AREE CIRCOSTANTI.               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  BLEND ONLY THE DEFECTS IDENTIFIED IN OP.10         *
         *        *  .                                                  *
         *        *  N.B.: DO NOT USE ABRASIVES THAT INCLUDES A         *
         *        *        VITRIFIED BOND MATRIX.                       *
         *        *                                                     *
         *        *  REQUIREMENTS:                                      *
         *        *                                                     *
         *        *  1) REMOVE THE MINIMUM AMOUNT OF PARENT MATERIAL TO *
         *        *     REMOVE THE DEFECT.                              *
         *        *                                                     *
         *        *  2) THE LENGTH OF THE BLENDED AREA SHOULD BE AT     *
         *        *     LEAST 10 TIMES THE DEPTH.                       *
         *        *                                                     *
         *        *  3) SPACING BETWEEN TWO BLENDING REPAIRS MUST BE AT *
         *        *     LEAST 1,5X THE LARGEST REPAIR SEMI-LENGTH.      *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *                                                      * *        *  4) BLENDED AREA SHOULD MAINTAIN APPROXIMATELY   *
         *        *     THE ORIGINAL CONTOUR OF THE BLADE AND THE       *
         *        *     ROUGHNESS OF THE ADJACENT AREAS.                * SP.ORIG. 70-42-00-350-002     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8225078       LOCATORE CMM BLADE GENX          *
BA/662  * 040    *                                                      *
AVM751  *        *  ATTACCO CHIMICO A TAMPONE DELLE SUPERFICI           * *        *  RACCORDATE.                                     *
         *        *                                                     *
         *        *  MATERIALE BASE: GAMMA TIAL                         *
         *        *                                                     *
         *        *  ETCHANT: CLASS I                                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  SWAB ETCH THE BLENDED AREAS                        *
         *        *                                                     *
         *        *  BASE MATERIAL: GAMMA TIAL                          *
         *        *                                                     *
SCHEDA : CPEC522-BR SP.ORIG. 70-24-00-110-033     SP.FIAT *        *  ETCHANT: CLASS I                                *
------------------------------------------------------------------------------
I1439   * 050    *                                                      *
AVM758  *        *  ISPEZIONE LOCALE CON LIQUIDI PENTERANTI             * *        *  FLUORESCENTI DELLE AREE RACCORDATE.             *
         *        *                                                     *
         *        *  LIMITI DI ACCETTABILITA':                          *
         *        *                                                     *
         *        *  1) LE INDICAZIONI MINORI DI 0,38 MM NON SONO       *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 050    *     INTERPRETABILI E NON DEVONO ESSERE VALUTATE      * *        *                                                  *
         *        *  2) NON SONO AMMESSE INDICAZIONI LINEARI            *
         *        *     INTERPRETABILI, SE NON DIVERSAMENTE             *
         *        *     SPECIFICATO.                                    *
         *        *                                                     *
         *        *  3) NON SONO AMMESSE INDICAZIONI PASSANTI           *
         *        *                                                     *
         *        *  4) POSSONO ESSERE UTILIZZATI INGRANDIMENTI SINO 4X *
         *        *     SOLO COME RIFERIMENTO                           *
         *        *                                                     *
         *        *  NOTA: UN INDICAZIONE VIENE DEFINITA LINEARE SE HA  *
         *        *        LUNGHEZZA PARI AD ALMENO 4 VOLTE LA SUA      *
         *        *        LARGHEZZA                                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *                                                     *
         *        *  ACCEPTABILITY LIMITS:                              *
         *        *                                                     *
         *        *  (1)INDICATIONS LESS THAN 0.015 INCH (0.38 MM) ARE  *
         *        *     NON-INTERPRETABLE AND NEED NOT TO BE EVALUATED. *
         *        *                                                     *
         *        *  (2) NO INTERPRETABLE LINEAR INDICATION IS          *
         *        *      PERMITTED, UNLESS SPECIFIED DIFFERENTLY.       *
         *        *                                                     *
         *        *  (3) NO THROUGH INDICATIONS ARE PERMITTED.          *
         *        *                                                     *
         *        *  (4) MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR *
         *        *      REFERENCE PURPOSES ONLY.                       *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 8 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 050    *  NOTE: A LINEAR INDICATION IS DEFINED AS ONE HAVING  * *        *     A LENGTH OF MORE THAN 4 TIMES ITS WIDTH.     *
SCHEDA : SLP-05     SP.ORIG. 70-32-03-230-002 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    08-08-24  *
ZC/095  * 060    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELLE AREE RACCORDATE CON LENTE    * *        *  10X.                                            *
         *        *                                                     *
         *        *  VERIFICARE CHE SIANO STATI COMPLETAMENTE RIMOSSI I *
         *        *  DIFETTI IDENTIFICATI IN OP.10 E CHE SIANO          *
         *        *  RISPETTATI I REQUISITI DEL DETTAGLIO TECNICO.      *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE BLENDED AREAS WITH        *
         *        *  MAGNIFICATION 10X.                                 *
         *        *                                                     *
         *        *  VERIFY THE COMPLETE REMOVAL OF THE DEFECTS         *
         *        *  IDENTIFIED IN OP.10 AND REQUIREMENTS OF THE        *
------------------------------------------------------------------------------ *        *  TECHNICAL DATA SHEET.                           *
BA/777  * 070    *                                                      * *        *                              D.T.    09-07-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 075    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 9 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 075    *  DO A GENERAL VISUAL INSPECTION OF THE PART AND      * *        *  A CHECK OF THE RELATED DOCUMENTATION.           *
         *        *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST *
============================================================================== *        *  FINAL INSPECTION".                              *
RIP: A1 OEM: GEK112862                   CHANGE: 40        DEL :31.10.2024
FIRMA CHANGE            [NOME OMESSO]           06-12-2024
FIRMA AUTORE
FIRMA TECN.GIE PRODOTTO
FIRMA ANALISI LAVORO
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 10 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.  10
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 11 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.  11
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 38960731

**GXRC-72560011-270-2** · [torna ai risultati](#ciclo-38960731) (p. 11)

#### Pagina 1 di 11

```text
 PGM PVRM320                         DATA STAMPA 14-10-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RACCORDATURA DIFETTI SECONDO:                       * *        *                                                  *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
         *        *  GEK 114120 TASK 72-56-31-200-801                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  DEFECTS BLENDING I.A.W.:                           *
         *        *                                                     *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
------------------------------------------------------------------------------ *        *  GEK 114120 TASK 72-56-31-200-801                *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  QUESTA RIPARAZIONE è APPLICABILE SOLO AI SEGUENTI  *
         *        *  PN:                                                *
         *        *                                                     *
         *        *  - 2479M15P01                                       *
         *        *  - 2479M15P02                                       *
         *        *                                                     *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE E NUMERARE I DIFETTI DA RACCORDARE    *
         *        *  CON MATITA A CERA ROSSA.                           *
         *        *                                                     *
         *        *  RIFERIRSI ALLA SCHEDA DIFETTI DELLA RIPARAZIONE    *
         *        *  GXTR-72560011-270-2 RIP.B1                         *
         *        *                                                     *
         *        *  ***************** NOTA BENE ******************     *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  SE NON è STATA APPROVATA UNA DR SU QUESTO SN        * *        *  RISPETTARE I SEGUENTI LIMITI:                   *
         *        *                                                     *
         *        *   - MASSIMO 4 RACCORDATURE SU TUTTA LA PALA         *
         *        *                                                     *
         *        *   - MASSIMO 2 RACCORDATURE SUL BORDO D'ENTRATA      *
         *        *                                                     *
         *        *   - MASSIMO 2 RACCORDATURE SUL BORDO D'USCITA       *
         *        *                                                     *
         *        *  VEDI TASK 72-56-31-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  DR:..................................              *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RACCORDARE  *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:................  *
         *        *                                                     *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINANDOLA COME L'OL ED INSERENDO ALL'INTERNO LE  *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A1               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  THIS REPAIR IS APPLICABLE ONLY TO THE FOLLOWING    *
         *        *  PN'S:                                              *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  - 2479M15P01                                        * *        *  - 2479M15P02                                    *
         *        *                                                     *
         *        *  IDENTIFY AND NUMBER THE DEFECTS TO BE BLENDED WITH *
         *        *   RED WAX PENCIL. USE THE DEFECT REPORT OF THE      *
         *        *  REPAIR GXTR-72560011-270-2 RIP.B1                  *
         *        *                                                     *
         *        *  ********************* N.B. ********************    *
         *        *                                                     *
         *        *  IF THERE ISN'T AN APPROVED DR ON THIS COMPONENT    *
         *        *  USE THE FOLLOWING LIMITS:                          *
         *        *                                                     *
         *        *  - MAXIMUM NUMBER OF BLENDS FOR ONE BLADE IS 6      *
         *        *                                                     *
         *        *  - MAXIMUM NUMBER OF BLENDS ON TRAILING EDGE IS 3   *
        *       * - MAXIMUM NUMBER OF BLENDS ON LEADING EDGE IS 10      * *        *                                                  *
         *        *                                                     *
         *        *  REF. TASK 72-56-31-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO            *
         *        *  NAMED AS THIS OL WITH THE DEFECTS PICTURES. IF     *
         *        *  THIS REPAIR IS COMBINED WITH OTHERS, CREATE A SUB- *
------------------------------------------------------------------------------ *        *  FOLDER AND RENAME IT: A1                        *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
PREC01  * 020    *  HANDLING OF THE PART TO THE REPAIR AREA.            *
------------------------------------------------------------------------------ *        *                              D.T.    08-01-25  *
BA/766  * 030    *                                                      *
AVM751  *        *  RACCORDARE SOLO I DIFETTI IDENTIFICATI IN OP.10     * *        * .                                                *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *        DI INCOLLAGGIO VETRIFICATA.                  *
         *        *                                                     *
         *        *  REQUISITI:                                         *
         *        *                                                     *
         *        *  1) ASPORTARE IL MINIMO MATERIALE NECESSARIO ALLA   *
         *        *     RIMOZIONE DEL DIFETTO.                          *
         *        *                                                     *
         *        *  2) LA LARGHEZZA DELLA RACCORDATURA DEV'ESSERE PARI *
         *        *     AD ALMENO 10 VOLTE LA PROFONDITA'.              *
         *        *                                                     *
         *        *  3) LA SEPARAZIONE FRA DUE AREE RACCORDATE          *
         *        *     DEV'ESSERE PARI AD ALMENO 1,5 VOLTE LA SEMI-    *
         *        *     LUNGHEZZA MAGGIORE DELLE DUE RACCORDATURE.      *
         *        *                                                     *
         *        *  4)  LE AREE RACCORDATE DEVONO MANTENERE,           *
         *        *      APPROSSIMATIVAMENTE, LA GEOMETRIA E LA         *
         *        *      RUGOSITA DELLE AREE CIRCOSTANTI.               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  BLEND ONLY THE DEFECTS IDENTIFIED IN OP.10         *
         *        *  .                                                  *
         *        *  N.B.: DO NOT USE ABRASIVES THAT INCLUDES A         *
         *        *        VITRIFIED BOND MATRIX.                       *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *  REQUIREMENTS:                                       * *        *                                                  *
         *        *  1) REMOVE THE MINIMUM AMOUNT OF PARENT MATERIAL TO *
         *        *     REMOVE THE DEFECT.                              *
         *        *                                                     *
         *        *  2) THE LENGTH OF THE BLENDED AREA SHOULD BE AT     *
         *        *     LEAST 10 TIMES THE DEPTH.                       *
         *        *                                                     *
         *        *  3) SPACING BETWEEN TWO BLENDING REPAIRS MUST BE AT *
         *        *      LEAST 1,5X THE LARGEST REPAIR SEMI-LENGTH.     *
         *        *                                                     *
         *        *  4) BLENDED AREA SHOULD MAINTAIN APPROXIMATELY      *
         *        *     THE ORIGINAL CONTOUR OF THE BLADE AND THE       *
         *        *     ROUGHNESS OF THE ADJACENT AREAS.                * SP.ORIG. 70-42-00-350-003     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
         *        *  M8225077       LOCATORE CMM BLADE GENX             *
------------------------------------------------------------------------------ *        *  M8225081       LOCATORE CMM BLADE GENX          *
BA/663  * 040    *                                                      *
AVM751  *        *  ATTACCO CHIMICO A TAMPONE DELLE SUPERFICI           * *        *  RACCORDATE.                                     *
         *        *                                                     *
         *        *  MATERIALE BASE: GAMMA TIAL                         *
         *        *                                                     *
         *        *  ETCHANT: CLASS I                                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  SWAB ETCH THE BLENDED AREAS                        *
         *        *                                                     *
         *        *  BASE MATERIAL: GAMMA TIAL                          *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/662  * 040    *                                                      * *        *  ETCHANT: CLASS I                                *
SCHEDA : CPEC521-BR SP.ORIG. 70-24-00-110-034 I   SP.FIAT
------------------------------------------------------------------------------
I1439   * 050    *                                                      *
AVM758  *        *  ISPEZIONE LOCALE CON LIQUIDI PENTERANTI             * *        *  FLUORESCENTI DELLE AREE RACCORDATE.             *
         *        *                                                     *
         *        *  LIMITI DI ACCETTABILITA':                          *
         *        *                                                     *
         *        *  1) LE INDICAZIONI MINORI DI 0,38 MM NON SONO       *
         *        *     INTERPRETABILI E NON DEVONO ESSERE VALUTATE     *
         *        *                                                     *
         *        *  2) NON SONO AMMESSE INDICAZIONI LINEARI            *
         *        *     INTERPRETABILI, SE NON DIVERSAMENTE             *
         *        *     SPECIFICATO.                                    *
         *        *                                                     *
         *        *  3) NON SONO AMMESSE INDICAZIONI PASSANTI           *
         *        *                                                     *
         *        *  4) POSSONO ESSERE UTILIZZATI INGRANDIMENTI SINO 4X *
         *        *     SOLO COME RIFERIMENTO                           *
         *        *  .                                                  *
         *        *  5) NELLE AREE DEL PROFILO, LA SEPARAZIONE MINIMA   *
         *        *     FRA DUE INDICAZIONI DEV'ESSERE ALMENO 5 VOLTE   *
         *        *     LA DIMENSIONE MASSIMA DELL'INDICAZIONE MAGGIORE *
         *        *                                                     *
         *        *  NOTA: UN INDICAZIONE VIENE DEFINITA LINEARE SE HA  *
         *        *        LUNGHEZZA PARI AD ALMENO 4 VOLTE LA SUA      *
         *        *        LARGHEZZA                                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 8 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 050    *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.          * *        *                                                  *
         *        *  ACCEPTABILITY LIMITS:                              *
         *        *                                                     * *        *  (1) INDICATIONS over  0.015 INCH (0.38 MM) ARE  *
         *        *      NON-INTERPRETABLE AND NEED NOT TO BE EVALUATED *
         *        *                                                     *
         *        *  (2) NO INTERPRETABLE LINEAR INDICATION IS          *
         *        *      PERMITTED, UNLESS SPECIFIED DIFFERENTLY.       *
         *        *                                                     *
         *        *  (3) NO THROUGH INDICATIONS ARE PERMITTED.          *
         *        *                                                     *
         *        *  (4) MAGNIFICATION NOT TO EXCEED 2X CAN BE USED FOR *
         *        *      REFERENCE PURPOSES ONLY.                       *
         *        *  .                                                  *
         *        *  (5) MINIMUM SPACING BETWEEN TWO ADJACENT           *
         *        *      INDICATIONS IN AIRFOIL AREAS, CAN BE NO LESS   *
         *        *      THAN 5 TIMES THE MAXIMUM INDICATION SIZE.      *
         *        *                                                     *
         *        *  NOTE: A LINEAR INDICATION IS DEFINED AS ONE HAVING *
SCHEDA : SLP-06     SP.ORIG. 70-32-03-230-002 D   SP.FIAT * *        *  A LENGTH OF MORE THAN 4 TIMES ITS WIDTH.        *
------------------------------------------------------------------------------ *        *                              D.T.    08-01-25  *
ZC/095  * 060    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELLE AREE RACCORDATE CON LENTE    * *        *  10X.                                            *
         *        *                                                     *
         *        *  VERIFICARE CHE SIANO STATI COMPLETAMENTE RIMOSSI I *
         *        *  DIFETTI IDENTIFICATI IN OP.10 E CHE SIANO          *
         *        *  RISPETTATI I REQUISITI DEL DETTAGLIO TECNICO.      *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 9 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 060    *  * * * * * * * * * * * * * * * * * * * * * * * * *  * *        *                                                  *
         *        *  VISUAL INSPECTION OF THE BLENDED AREAS WITH        *
         *        *  MAGNIFICATION 10X.                                 *
         *        *                                                     *
         *        *  VERIFY THE COMPLETE REMOVAL OF THE DEFECTS         *
         *        *  IDENTIFIED IN OP.10 AND REQUIREMENTS OF THE        *
------------------------------------------------------------------------------ *        *  TECHNICAL DATA SHEET.                           *
BA/777  * 070    *                                                      * *        *                              D.T.    07-04-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 075    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
         *        *  A CHECK OF THE RELATED DOCUMENTATION.              *
         *        *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST *
============================================================================== *        *  FINAL INSPECTION".                              *
RIP: A1 OEM: GEK114120                   CHANGE: 33        DEL :31.10.2024
FIRMA CHANGE            [NOME OMESSO]           09-01-2025
FIRMA AUTORE
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           06-02-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           06-02-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 10 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.  10
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 11 di 11

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.  11
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 4e64d49a

**GXRC-72560010A190-1** · [torna ai risultati](#ciclo-4e64d49a) (p. 14)

#### Pagina 1 di 8

```text
 PGM PVRM320                         DATA STAMPA 14-10-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RIMOZIONE METALLO IN RILIEVO SECONDO:               * *        *                                                  *
         *        *   GEK9250 SUBTASK 70-42-00-350-029                  *
         *        *   GEK112862 TASK 72-56-32-200-801                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  REMOVAL OF HIGH METAL PROCEDURES I.A.W.:           *
         *        *                                                     *
         *        *  GEK9250 SUBTASK 70-42-00-350-029                   *
------------------------------------------------------------------------------ *        *  GEK112862 TASK 72-56-32-200-801                 *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE I DIFETTI DAI QUALI RIMUOVERE IL      *
         *        *  METALLO IN RILIEVO INDICANDOLI SULLA PALA CON      *
         *        *  MATITA A CERA ROSSA.
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINADOLA COME L'OL ED INSERENDO ALL'INTERNO LE   *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A3               *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  SE NON è PRESENTE METALLO IN RILIEVO SUL PROFILO    * *        *  DELLA PALA ANNULLARE LE OP.25 E 35.             *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  IDENTIFY THE DEFECTS FROM WHICH THE HIGH METAL HAS *
         *        *  TO BE REMOVED WITH RED WAX PENCIL.                 *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO NAMED AS   *
         *        *  THIS OL WITH THE DEFECTS PICTURES. IF THIS REPAIR  *
         *        *  IS COMBINED WITH OTHERS CREATE A SUB-FOLDER AND    *
         *        *  RENAME IT: A3                                      *
         *        *                                                     *
         *        *  IF THERE ISN'T HIGH METAL ON THE BLADE'S PROFILE   *
------------------------------------------------------------------------------ *        *  SURFACES, ANNUL OP.25 AND 35.                   *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 025    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM751  *        *  LUCIDATURA MANUALE DELLE AREE CONCAVA E CONVESSA    * *        *  DEL PROFILO PALA, AL FINE DI RIMUOVERE IL METALLO *
         *        *  IN RILIEVO.                                        *
         *        *                                                     *
         *        *  UTILIZZARE CARTA ABRASIVA GRANA 500                *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 025    *                                                      * *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  MANUAL POLISHING OF THE CONCAVE AND CONVEX PROFILE *
         *        *  SURFACES, FOR REMOVING THE HIGH METAL.             *
         *        *                                                     *
         *        *  USE CROCUS CLOTH 500 GRIT                          * SP.ORIG. 70-42-00-350-029     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8225079       LOCATORE CMM BLADE GENX          *
BA/766  * 030    *                                                      *
AVM751  *        *  RIMUOVERE IL METALLO IN RILIEVO DAI DIFETTI         * *        *  INDICATI IN OP.10.                              *
         *        *  .                                                  *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *        DI INCOLLAGGIO VETRIFICATA.                  *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  REMOVE THE HIGH METAL FROM FROM THE DEFECTS        *
         *        *  IDENTIFIED IN OP.10.                               *
         *        *  .                                                  *
         *        *        N.B.: DO NOT USE ABRASIVES THAT INCLUDES A      *
         *        *         VITRIFIED BOND MATRIX.                      * SP.ORIG. 70-42-00-350-029     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8225079       LOCATORE CMM BLADE GENX          *
ZC/095  * 035    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM75A  *        *  COLLAUDO VISIVO DELLA RIMOZIONE METALLO IN RILIEVO  * *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
------------------------------------------------------------------------------
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 035    *  EFFETTUATA IN OP.25.                                * *        *                                                  *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE HIGH METAL REMOVAL,       *
------------------------------------------------------------------------------ *        *  IN OP.25.                                       *
ZC/095  * 040    *                                                      *
AVM75A  *        *  CONTROLLO VISIVO.                                   * *        *                                                  *
         *        *  VERIFICARE CHE SIA STATO RIMOSSO IL METALLO IN     *
         *        *  RILIEVO DAI DIFETTI IDENTIFICATI IN OP.10.         *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION                                  *
         *        *                                                     *
         *        *  VERIFY THAT THE HIGH METAL HAS BEEN REMOVED FROM   *
------------------------------------------------------------------------------ *        *  THE DEFECTS IDENTIFIED IN OP.10.                *
BA/777  * 050    *                                                      * *        *                              D.T.    07-04-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 060    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
         *        *  A CHECK OF THE RELATED DOCUMENTATION.              *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 060    *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST  * *        *  FINAL INSPECTION".                              *
==============================================================================
RIP: A3 OEM: GEK112862                   CHANGE: 41        DEL :30.04.2025
FIRMA CHANGE            [NOME OMESSO]           03-07-2025
FIRMA AUTORE            [NOME OMESSO]           02-10-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           02-10-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           02-10-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 7 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 8 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ. METALLO IN RILIEVO
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 5ff17062

**GXRC-72560010A190-1** · [torna ai risultati](#ciclo-5ff17062) (p. 16)

#### Pagina 1 di 11

```text
 PGM PVRM320                         DATA STAMPA 11-11-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RACCORDATURA DIFETTI SECONDO:                       * *        *                                                  *
         *        *   GEK 9250 TASK 70-42-00-350-002                    *
         *        *   GEK 112862 TASK 72-56-32-200-801                  *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  DEFECTS BLENDING I.A.W.:                           *
         *        *                                                     *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
------------------------------------------------------------------------------ *        *  GEK 112862 TASK 72-56-32-200-801                *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE E NUMERARE I DIFETTI DA RACCORDARE    *
         *        *  CON MATITA A CERA ROSSA.                           *
         *        *                                                     *
         *        *  RIFERIRSI ALLA SCHEDA DIFETTI DELLA RIPARAZIONE    *
         *        *  GXTR-72560010A190-1 RIP.B1                         *
         *        *                                                     *
         *        *  ***************** NOTA BENE ******************     *
         *        *                                                     *
         *        *  SE NON è STATA APPROVATA UNA DR SU QUESTO SN       *
         *        *  RISPETTARE I SEGUENTI LIMITI:                      *
         *        *                                                     *
         *        *  - MASSIMO 8 RACCORDATURE SU TUTTA LA PALA          *
         *        *                                                     *
         *        *  - MASSIMO 10 RACCORDATURE SUL BORDO D'ENTRATA       *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *                                                      * *        *  - MASSIMO 7 RACCORDATURE SUL BORDO D'USCITA     *
         *        *                                                     *
         *        *  VEDI TASK 72-56-32-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  DR:..................................              *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RACCORDARE  *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:................  *
         *        *                                                     *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINANDOLA COME L'OL ED INSERENDO ALL'INTERNO LE  *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A1               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  IDENTIFY AND NUMBER THE DEFECTS TO BE BLENDED WITH *
         *        *   RED WAX PENCIL. USE THE DEFECT REPORT OF THE      *
         *        *  REPAIR GXTR-72560010A190-1 RIP.B1                  *
         *        *                                                     *
         *        *  ********************* N.B. ********************    *
         *        *                                                     *
         *        *  IF THERE ISN'T AN APPROVED DR ON THIS COMPONENT    *
         *        *  USE THE FOLLOWING LIMITS:                          *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  - MAXIMUM NUMBER OF BLENDS FOR ONE BLADE IS 4       * *        *                                                  *
         *        *   - MAXIMUM NUMBER OF BLENDS ON TRAILING EDGE IS 2  *
         *        *                                                     *
         *        *   - MAXIMUM NUMBER OF BLENDS ON LEADING EDGE IS 2   *
         *        *                                                     *
         *        *  REF. TASK 72-56-32-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO            *
         *        *  NAMED AS THIS OL WITH THE DEFECTS PICTURES. IF     *
         *        *  THIS REPAIR IS COMBINED WITH OTHERS, CREATE A SUB- *
------------------------------------------------------------------------------ *        *  FOLDER AND RENAME IT: A1                        *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 030    *                                                      * *        *                              D.T.    08-08-24  *
AVM751  *        *  RACCORDARE SOLO I DIFETTI IDENTIFICATI IN OP.10     * *        * .                                                *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *        DI INCOLLAGGIO VETRIFICATA.                  *
         *        *                                                     *
         *        *  REQUISITI:                                         *
         *        *                                                     *
         *        *  1) ASPORTARE IL MINIMO MATERIALE NECESSARIO ALLA   *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *      RIMOZIONE DEL DIFETTO.                          * *        *                                                  *
         *        *   2) LA LARGHEZZA DELLA RACCORDATURA DEV'ESSERE PARI *
         *        *      AD ALMENO 30 VOLTE LA PROFONDITA'.             *
         *        *                                                     *
         *        *   3) LA SEPARAZIONE FRA DUE AREE RACCORDATE         *
         *        *      DEV'ESSERE PARI AD ALMENO 0,5 VOLTE LA SEMI-   *
         *        *      LUNGHEZZA MAGGIORE DELLE DUE RACCORDATURE.     *
         *        *                                                     * *        *  4)  LE AREE RACCORDATE DEVONO AVERE              *
*         *      RUGOSITA DELLE AREE CIRCOSTANTI DIFFERENTI.            * *        *      APPROSSIMATIVAMENTE, LA GEOMETRIA E LA      *

         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  BLEND ONLY THE DEFECTS IDENTIFIED IN OP.10         *
         *        *  .                                                  *
         *        *  N.B.: USE ABRASIVES THAT INCLUDES A           * *
          *          VITRIFIED BOND MATRIX ONLY.                       * *
            *                                                          * *
            *  REQUIREMENTS:                                           * *
            *                                                          * *
            *  1) REMOVE THE MAIMUM AMOUNT OF PARENT MATERIAL TO       * *
           *      REMOVE THE DEFECT.                                   * *
           *                                                           * *
           *  2) THE LENGTH OF THE BLENDED AREA SHOULD BE          * *
          *     2 TIMES THE DEPTH.                              * *        *
                                                                * *        *
       3) SPACING BETWEEN TWO BLENDING REPAIRS MUST BE AT       * *        *
          LEAST 1,5X THE LARGEST REPAIR SEMI-LENGTH.            * *        *
                                                                * *        *
       4) BLENDED AREA SHOULD MAINTAIN APPROXIMATELY            * *        *
------------------------------------------------------------------------------ *******  CONTINUA ALLA PAGINA SEGUENTE  ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *      THE ORIGINAL CONTOUR OF THE BLADE AND THE       * *        *      ROUGHNESS OF THE ADJACENT AREAS.            *
         *        *  * ATTREZZATURA PREVISTA *                          * SP.ORIG. 70-60-00-350-005     SP.FIAT
------------------------------------------------------------------------------ *        *  M8225079       LOCATORE CMM BLADE GENX          *
BA/662  * 040    *                                                      *
AVM751  *        *  ATTACCO CHIMICO A TAMPONE DELLE SUPERFICI           * *        *  RACCORDATE.                                     *
         *        *                                                     *
         *        *  MATERIALE BASE: GAMMA TIAL                         *
         *        *                                                     *
         *        *  ETCHANT: CLASS A                                   * *
                  *                                                     * *
                  *  * * * * * * * * * * * * * * * * * * * * * * * * *  * *
                  *                                                     * *
                  *  SWAB ETCH THE BLENDED AREAS                        * *
                  *                                                     * *
                  *  BASE MATERIAL: GAMMA TIAL                          * *
                  *                                                     * *
SCHEDA : CPEC522-BR SP.ORIG. 70-24-00-110-033     SP.FIAT        *  ETCHANT: CLASS A                        *
------------------------------------------------------------------------------
I1439   * 050    *                                                      *
AVM758  *        *  ISPEZIONE LOCALE CON LIQUIDI PENTERANTI             * *        *  FLUORESCENTI DELLE AREE RACCORDATE.             *
         *        *                                                     *
         *        *  LIMITI DI ACCETTABILITA':                          *
         *        *                                                     *
         *        *  1)SONO AMMESSE CRICCHE        *        * *       *
                                                            * *        *
         *******  CONTINUA ALLA PAGINA SEGUENTE  ******     *
------------------------------------------------------------------------------
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/080  * 050    *  2) NON SONO AMMESSE INDICAZIONI LINEARI             * *        *     INTERPRETABILI, SE NON DIVERSAMENTE          *
         *        *      SPECIFICATO.                                   *
         *        *                                                     *
         *        *  3) NON SONO AMMESSE INDICAZIONI PASSANTI           *
         *        *                                                     *
         *        *  4) POSSONO ESSERE UTILIZZATI INGRANDIMENTI SINO 4X *
         *        *     SOLO COME RIFERIMENTO                           *
         *        *                                                     *
         *        *  NOTA: UN INDICAZIONE VIENE DEFINITA LINEARE SE HA  *
         *        *        LUNGHEZZA PARI AD ALMENO 4 VOLTE LA SUA      *
         *        *        LARGHEZZA                                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *                                                     *
         *        *  ACCEPTABILITY LIMITS:                              *
         *        *                                                     *
         *        *  (1)CRACKS ARE ACCEPTABLE
       . * *         *
         * *        (2) INTERPRETABLE LINEAR INDICATION IS          * *
            *        PERMITTED, UNLESS SPECIFIED DIFFERENTLY.       * *
            *                                                       * *
            *       (3) THROUGH INDICATIONS ARE PERMITTED.          * *
            *                                                       * *
            *    (4) MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR * *
            *           REFERENCE PURPOSES ONLY.                    * *
            *                                                       * *
            *    NOTE: A LINEAR INDICATION IS DEFINED AS ONE HAVING * *
            *           A LENGTH OF MORE THAN 4 TIMES ITS WIDTH.    * *
            *    *******  CONTINUA ALLA PAGINA SEGUENTE  ******     *
------------------------------------------------------------------------------
                                                     *** C O N T I N U A ***
```

#### Pagina 8 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
SCHEDA : SLP-05     SP.ORIG. 70-32-03-230-002 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    08-08-24  *
ZC/095  * 060    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELLE AREE RACCORDATE CON LENTE    * *        *  10X.                                            *
         *        *                                                     *
         *        *  VERIFICARE CHE SIANO STATI COMPLETAMENTE RIMOSSI I *
         *        *  DIFETTI IDENTIFICATI IN OP.10 E CHE SIANO          *
         *        *  RISPETTATI I REQUISITI DEL DETTAGLIO TECNICO.      *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE BLENDED AREAS WITH        *
         *        *  MAGNIFICATION 10X.                                 *
         *        *                                                     *
         *        *  VERIFY THE COMPLETE REMOVAL OF THE DEFECTS         *
         *        *  IDENTIFIED IN OP.10 AND REQUIREMENTS OF THE        *
------------------------------------------------------------------------------ *        *  TECHNICAL DATA SHEET.                           *
BA/777  * 070    *                                                      * *        *                              D.T.    09-07-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 075    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
         *        *  A CHECK OF THE RELATED DOCUMENTATION.              *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 9 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 075    *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST  * *        *  FINAL INSPECTION".                              *
==============================================================================
RIP: A1 OEM: GEK112862                   CHANGE: 40           DEL :31/10/2024 FIRMATO DA: [NOME OMESSO]        09/12/2024
FIRMA AUTORE
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           12-12-2024
FIRMA ANALISI LAVORO    [NOME OMESSO]           12-12-2024
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 10 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.  10
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 11 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.  11
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 737dec71

**GXPR-72560010A190-1** · [torna ai risultati](#ciclo-737dec71) (p. 19)

#### Pagina 1 di 9

```text
 PGM PVRM320                         DATA STAMPA 28-01-2026 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  QUESTA PROCEDURA DI RIPARAZIONE FORNISCE LE         * *        *  ISTRUZIONI PER EFFETTUARE LA RACCORDATURA DEI   *
         *        *  DIFETTI RISCONTRATI SULLA SUPERFICIE LATERALE      *
         *        *  DEL DOVETAIL , A FRONTE DELLA SEGNALAZIONE         *
         *        *  DIFETTI S25/04343.                                 *
         *        *  TUTTE LE OPERAZIONI SEGUENTI SONO CONFORMI ALLE    *
         *        *  ISTRUZIONI FORNITE NELLA D.R. CASE #02251702.      *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  THIS REPAIR PROCEDURE PROVIDES INSTRUCTIONS        *
         *        *  TO BLEND DEFECTS FOUND ON THE SIDE SURFACE         *
         *        *  OF THE DOVETAIL, IN ACCORDANCE WITH SA S25/04343.  *
         *        *  ALL THE FOLLOWING OPERATIONS ARE IN COMPLIANCE     *
         *        *  WITH THE INSTRUCTIONS PROVIDED IN                  *
         *        *  D.R. CASE #02251702.                               *
------------------------------------------------------------------------------ *        * .                                                *
ZC/454  * 010    *                                                      *
AVM747  *        *                                                      * *        *  DR:...................................          *
         *        *  .                                                  *
         *        *  SEGNALAZIONE:.........................             *
         *        *  .                                                  *
         *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.            *
         *        *  REGISTRARE P/N E S/N DEL PARTICOLARE.              *
         *        *  .                                                  *
         *        *  P/N:                          S/N:                 *
         *        *       ----------------------     -----------------  *
         *        *  .                                                  *
         *        *  ESEGUIRE MAPPATURA DEI DIFETTI DA RIPARARE.        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/454  * 010    *  CREARE NUOVA CARTELLA U:\TECPR MICROSCOPIO\GENX     * *        *  NOMINANDOLA COME L'O.L. E SALVARE FOTO DELLA    *
         *        *  MAPPATURA.                                         *
         *        *  .                                                  *
         *        *  RIPORTARE DI SEGUITO LA PROFONDITA' MASSIMA DEI    *
         *        *  DIFETTI DA RACCORDARE, INDICATA NELLA SEGNALAZIONE *
         *        *  .                                                  *
         *        *  MAX PROFONDITA' DIFETTO:                           *
         *        *                          ----------------------     *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  REPAIR IN ACCORDANCE WITH DR:                      *
         *        *  .                                                  *
         *        *  IDENTIFICATION OF THE BLADE.                       *
         *        *  RECORD P/N AND S/N OF THE BLADE.                   *
         *        *  .                                                  *
         *        *  CREATE A NEW FOLDER IN U:\TECPR MICROSCOPIO\GENX   *
         *        *  WITH THE PICTURES OF THE DEFECTS TO BE BLENDED     *
         *        *  AND NAME IT AS THE OL.                             *
         *        *  .                                                  *
         *        *  RECORD THE MAX DEPTH OF DEFECTS TO BE BLENDED.     *
------------------------------------------------------------------------------ *        * .                                                *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA                          * *        * .                                                *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  HANDLING OF THE PART TO THE REPAIR AREA.           *
------------------------------------------------------------------------------ *        * .                                                *
         *        *                              D.T.    16-09-25  *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
BA/098  * 030    *                                                      *
AVM751  *        *  ESEGUIRE RACCORDATURA DEI DIFETTI INDICATI IN       * *        *  OP.010, SECONDO D.R. CASE #02251702.            *
         *        *  .                                                  *
         *        *  VEDI FOTO IN CARTELLA: U:\TECPR MICROSCOPIO\GENX   *
         *        *  .                                                  *
         *        *  RIMUOVERE IL MINIMO MATERIALE NECESSARIO PER       *
         *        *  RIMUOVERE IL DIFETTO GARANTENDO UNA FINITURA       *
         *        *  SUPERFICIALE PARI A QUELLA DELLE AREE ADIACENTI    *
         *        *  NON LAVORATE.                                      *
         *        *  .                                                  *
         *        *  ESEGUIRE SOFFIATURA CON ARIA SECCA E PULITA DEL    *
         *        *  PARTICOLARE.                                       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  BLEND THE DEFECTS INDICATED IN THE TECHNICAL       *
         *        *  INSPECTION, ACCORDING TO D.R. CASE #02251702.      *
         *        *  .                                                  *
         *        *  SEE PHOTOS IN THE FOLDER:U:\TECPR MICROSCOPIO\GENX *
         *        *  .                                                  *
         *        *  REMOVE A MINIMUM AMOUNT OF MATERIAL, ENSURING      *
         *        *  A SURFACE FINISH AFTER BLENDING EQUIVALENT TO      *
         *        *  THE ADJACENT SURFACE FINISH.                       *
         *        *  .                                                  *
         *        *  BLOW THE PART WITH CLEAN AND DRY AIR.              *
         *        *  .                                                  * SP.ORIG. 70-42-00             SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    16-09-25  *
ZC/095  * 040    *                                                      *
AVM75A  *        *  ESEGUIRE CONTROLLO VISIVO DELLE AREE RIPARATE       * *        *  AL FINE DI VERIFICARE LA COMPLETA RIMOZIONE     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 040    *  DEL DIFETTO.                                        * *        *  FOTOGRAFARE LE AREE RIPARATE E SALVARE LE FOTO  *
         *        *   IN CARTELLA NOMINATA COME L'O.L. IN               *
         *        *   U:\TECPR MICROSCOPIO\GENX.                        *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  VISUAL CHECK OF THE REPAIRED AREAS TO VERIFY       *
         *        *  COMPLETE REMOVAL OF THE DEFECT.                    *
         *        *  TAKE PHOTOS OF REPAIRED AREAS AND SAVE THEM IN THE *
         *        *  FOLDER NAMED AS OL IN U:\TECPR MICROSCOPIO\GENX    *
------------------------------------------------------------------------------ *        * .                                                *
BA/662  * 050    *                                                      * *        *                              D.T.    16-09-25  *
AVM751  *        *  ESEGUIRE ATTACCO CHIMICO LOCALE A TAMPONE DELLE     * *        *  SUPERFICI RACCORDATE.                           *
         *        *  .                                                  *
         *        *  MATERIALE BASE: TIAL                               *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  SWAB ETCH THE BLENDED AREAS.                       *
         *        *  .                                                  *
         *        *  PARENT MATERIAL: TIAL                              *
SCHEDA : CPEC522-BR SP.ORIG. 70-24-01-110-034 I   SP.FIAT 70-24-00-110-033 *        * .                                                *
------------------------------------------------------------------------------ *        *                              D.T.    16-09-25  *
I1439   * 060    *                                                      *
AVM758  *        *  ESEGUIRE CONTROLLO LOCALE CON LIQUIDI PENETRANTI    * *        *  FLUORESCENTI, CLASSE D, DELLE AREE RACCORDATE.  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 060    *  .                                                   * *        *  LIMITI DI ACCETTABILITA':                       *
         *        *  - INDICAZIONI INFERIORI A 0.38 MM NON SONO         *
         *        *    INTERPRETABILI E NON DEVONO ESSERE VALUTATE.     *
         *        *  .                                                  *
         *        *  - NON SONO AMMESSE INDICAZIONI LINEARI O PASSANTI  *
         *        *    INTERPRETABILI, SALVO DIVERSA INDICAZIONE.       *
         *        *  .                                                  *
         *        *  - LENTE CON INGRANDIMENTO SUPERIORE A 4X PUÒ       *
         *        *    ESSERE UTILIZZATA SOLTANTO COME RIFERIMENTO.     *
         *        *                                                     *
         *        *  NOTA: SI DEFINISCE LINEARE UN'INDICAZIONE CHE      *
         *        *        PRESENTA UNA LUNGHEZZA PARI AD ALMENO        *
         *        *        QUATTRO VOLTE LA SUA LARGHEZZA.              *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *  .                                                  *
         *        *  SEVICEABLE LIMIT:                                  *
         *        *  - INDICATIONS LESS THAN 0.38 MM ARE NOT            *
         *        *    INTERPRETABLE AND NEED NOT TO BE EVALUATED       *
         *        *  .                                                  *
         *        *  - LINEAR OR THROUGH INDICATIONS ARE NOT PERMITTED, *
         *        *    UNLESS SPECIFIED DIFFERENTLY.                    *
         *        *  .                                                  *
         *        *  - MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR   *
         *        *    REFERENCE PURPOSES ONLY.                         *
         *        *  .                                                  *
         *        *  NOTE: LINEAR INDICATIONS ARE INDICATIONS THAT      *
         *        *        ARE AT LEAST FOUR TIMES LONGER THAN THEY ARE *
         *        *        WIDE.                                        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 060    *  .                                                   *
SCHEDA : SLP-04     SP.ORIG. 70-32-02-230-001 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    07-04-19  *
BA/777  * 080    *                                                      *
AVM75A  *        *  PRESERVARE IL COMPONENTE COME DA PRESERVAZIONE      * *        *  RICHIAMATA NELL' O.L. PRIMA PAGINA.             *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  PRESERVE COMPONENT IN ACCORDANCE WITH WORK         *
         *        *  INSTRUCTION SHEET, REFERRED IN HEADLINE OL.        *
------------------------------------------------------------------------------ *        * .                                                *
ZC/095  * 090    *                                                      * *        *                              D.T.    27-09-24  *
AVM75A  *        *  ESEGUIRE COLLAUDO FINALE, DOCUMENTALE E             * *        *  VERSAMENTO.                                     *
         *        *  CONSULTARE LA LISTA DI CONTROLLO COME DA MODULO    *
         *        *  BQP.08.42.06 - "CHECKLIST FINAL INSPECTION".       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND A   *
         *        *  CHECK OF RELATED DOCUMENTATION.                    *
============================================================================== *        * .                                                *
RIP: A6 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]        15/09/2025
FIRMA AUTORE            [NOME OMESSO]           25-09-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           17-09-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           17-09-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 8 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 9 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 895167b9

**GXPR-72560010A190-1** · [torna ai risultati](#ciclo-895167b9) (p. 21)

#### Pagina 1 di 9

```text
 PGM PVRM320                         DATA STAMPA 28-01-2026 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **

==============================================================================                                                               ciclo PROVA AI
```

#### Pagina 2 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  QUESTA PROCEDURA DI RIPARAZIONE FORNISCE LE         * *        *  ISTRUZIONI PER EFFETTUARE LA RACCORDATURA DEI   *
         *        *  DIFETTI RISCONTRATI SULLA SUPERFICIE LATERALE      *
         *        *  DEL DOVETAIL , A FRONTE DELLA SEGNALAZIONE         *
         *        *  DIFETTI S25/04343.                                 *
         *        *  TUTTE LE OPERAZIONI SEGUENTI SONO CONFORMI ALLE    *
         *        *  ISTRUZIONI FORNITE NELLA D.R. CASE #02251702.      *
         *        *                                                     * *
                  *  *************************************************  * *
                  *  .                                                  * *
                  *  THIS REPAIR PROCEDURE PROVIDES INSTRUCTIONS        * *
                  *  TO BLEND DEFECTS FOUND ON THE SIDE SURFACE         * *
                  *  OF THE DOVETAIL, IN ACCORDANCE WITH SA S25/04343.  * *
                  *  ALL THE FOLLOWING OPERATIONS ARE IN COMPLIANCE     * *
                  *  WITH THE INSTRUCTIONS PROVIDED IN                  * *
                  *  D.R. CASE #02251702.                               * *
                  *  APPLY ON S/N FGGF0HBK
------------------------------------------------------------------------------           *
ZC/454  * 010    *                                                      *
AVM747  *        *                                                      * *        *  DR:...................................          *
         *        *  .                                                  *
         *        *  SEGNALAZIONE:.........................             *
         *        *  .                                                  *
         *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.            *
         *        *  REGISTRARE P/N E S/N DEL PARTICOLARE.              *
         *        *  .                                                  *
         *        *  P/N:                          S/N:                 *
         *        *       ----------------------     -----------------  *
         *        *  .                                                  *
         *        *  ESEGUIRE MAPPATURA DEI DIFETTI DA RIPARARE.        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/454  * 010    *  CREARE NUOVA CARTELLA U:\TECPR MICROSCOPIO\GENX     * *        *  NOMINANDOLA COME L'O.L. E SALVARE FOTO DELLA    *
         *        *  MAPPATURA.                                         *
         *        *  .                                                  *
         *        *  RIPORTARE DI SEGUITO LA PROFONDITA' MASSIMA DEI    *
         *        *  DIFETTI DA RACCORDARE, INDICATA NELLA SEGNALAZIONE *
         *        *  .                                                  *
         *        *  MAX PROFONDITA' DIFETTO:                           *
         *        *                          ----------------------     *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  REPAIR IN ACCORDANCE WITH DR:                      *
         *        *  .                                                  *
         *        *  IDENTIFICATION OF THE BLADE.                       *
         *        *  RECORD P/N AND S/N OF THE BLADE.                   *
         *        *  .                                                  *
         *        *  CREATE A NEW FOLDER IN U:\TECPR MICROSCOPIO\GENX   *
         *        *  WITH THE PICTURES OF THE DEFECTS TO BE BLENDED     *
         *        *  AND NAME IT AS THE OL.                             *
         *        *  .                                                  *
         *        *  RECORD THE MIN DEPTH OF DEFECTS TO BE BLENDED.     *
------------------------------------------------------------------------------ *        * .                                                *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA                          * *        * .                                                *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  HANDLING OF THE PART TO THE REPAIR AREA.           *
------------------------------------------------------------------------------ *        * .                                                *
         *        *                              D.T.    16-09-25  *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
BA/098  * 030    *                                                      *
AVM751  *        *  ESEGUIRE RACCORDATURA DEI DIFETTI INDICATI IN       * *        *  OP.010, SECONDO D.R. CASE #02251703.            *
         *        *  .                                                  *
         *        *  VEDI FOTO IN CARTELLA: U:\TECPR MICROSCOPIO\GENX   *
         *        *  .                                                  *
         *        *  RIMUOVERE IL MINIMO MATERIALE NECESSARIO PER       *
         *        *  RIMUOVERE IL DIFETTO GARANTENDO UNA FINITURA       *
         *        *  SUPERFICIALE PARI A QUELLA DELLE AREE ADIACENTI    *
         *        *  NON LAVORATE.                                      *
         *        *  .                                                  *
         *        *  ESEGUIRE SOFFIATURA CON ARIA SECCA E PULITA DEL    *
         *        *  PARTICOLARE.                                       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  BLEND THE DEFECTS INDICATED IN THE TECHNICAL       *
         *        *  INSPECTION, ACCORDING TO D.R. CASE #02251703.      *
         *        *  .                                                  *
         *        *  SEE PHOTOS IN THE FOLDER:U:\TECPR MICROSCOPIO\GENX *
         *        *  .                                                  *
         *        *  REMOVE A MINIMUM AMOUNT OF MATERIAL, ENSURING      *
         *        *  A SURFACE FINISH AFTER BLENDING EQUIVALENT TO      *
         *        *  THE ADJACENT SURFACE FINISH.REMOVE TILL 0.2 INCH
                * *        * .
              BLOW THE PART WITH CLEAN AND DRY AIR.                     * *
                  * .                                                   * SP.ORIG. 70-42-00             SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    16-09-25  *
ZC/095  * 040    *                                                      *
AVM75A  *        *  ESEGUIRE CONTROLLO VISIVO DELLE AREE RIPARATE       * *        *  AL FINE DI VERIFICARE LA COMPLETA RIMOZIONE     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 040    *  DEL DIFETTO.                                        * *        *  FOTOGRAFARE LE AREE RIPARATE E SALVARE LE FOTO  *
         *        *   IN CARTELLA NOMINATA COME L'O.L. IN               *
         *        *   U:\TECPR MICROSCOPIO\GENX.                        *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  VISUAL CHECK OF THE REPAIRED AREAS TO VERIFY       *
         *        *  COMPLETE REMOVAL OF THE DEFECT.                    *
         *        *  TAKE PHOTOS OF REPAIRED AREAS AND SAVE THEM IN THE *
         *        *  FOLDER NAMED AS OL IN U:\TECPR MICROSCOPIO\GENX    *
------------------------------------------------------------------------------ *        * .                                                *
BA/662  * 050    *                                                      * *        *                              D.T.    16-09-25  *
AVM751  *        *  ESEGUIRE ATTACCO CHIMICO LOCALE A TAMPONE DELLE     * *        *  SUPERFICI RACCORDATE.                           *
         *        *  .                                                  *
         *        *  MATERIALE BASE: TIAL                               *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  SWAB ETCH ALL AREAS.                           * *
          * .                                                       * *
         *          PARENT MATERIAL: INCO718                            *
SCHEDA : CPEC525-BR SP.ORIG. 70-24-01-110-034 A   SP.FIAT 70-24-00-110-033   *        * .                                                *
------------------------------------------------------------------------------ *        *                              D.T.    16-09-25  *
I1439   * 060    *                                                      *
AVM758  *        *  ESEGUIRE CONTROLLO LOCALE CON LIQUIDI PENETRANTI    * *        *  FLUORESCENTI, CLASSE D, DELLE AREE RACCORDATE.  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 060    *  .                                                   * *        *  LIMITI DI ACCETTABILITA':                       *
         *        *  - INDICAZIONI INFERIORI A 0.38 MM NON SONO         *
         *        *    INTERPRETABILI E NON DEVONO ESSERE VALUTATE.     *
         *        *  .                                                  *
         *        *  - NON SONO AMMESSE INDICAZIONI LINEARI O PASSANTI  *
         *        *    INTERPRETABILI, SALVO DIVERSA INDICAZIONE.       *
         *        *  .                                                  *
         *        *  - LENTE CON INGRANDIMENTO SUPERIORE A 4X PUÒ       *
         *        *    ESSERE UTILIZZATA SOLTANTO COME RIFERIMENTO.     *
         *        *                                                     *
         *        *  NOTA: SI DEFINISCE LINEARE UN'INDICAZIONE CHE      *
         *        *        PRESENTA UNA LUNGHEZZA PARI AD ALMENO        *
         *        *        QUATTRO VOLTE LA SUA LARGHEZZA.              *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *  .                                                  *
         *        *  SEVICEABLE LIMIT:                                  *
         *        *  - INDICATIONS LESS THAN 0.38 MM ARE NOT            *
         *        *    INTERPRETABLE AND NEED NOT TO BE EVALUATED       *
         *        *  .                                                  * *        *  - LINEAR OR THROUGH INDICATIONS ARE PERMITTED,  *
         *        *    UNLESS SPECIFIED DIFFERENTLY.                    *
         *        *  .                                                  *
         *        *  - MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR   *
         *        *    REFERENCE PURPOSES ONLY.                         *
         *        *  .                                                  *
         *        *  NOTE: LINEAR INDICATIONS ARE INDICATIONS THAT      *
         *        *        ARE AT LEAST FOUR TIMES LONGER THAN THEY ARE *
         *        *        WIDE.                                        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
I1439   * 060    *  .                                                   *
SCHEDA : SLP-10     SP.ORIG. 70-32-02-230-001 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    07-04-19  *
BA/777  * 080    *                                                      *
AVM75A  *        *  PRESERVARE IL COMPONENTE COME DA PRESERVAZIONE      * *        *  RICHIAMATA NELL' O.L. PRIMA PAGINA.             *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  PRESERVE COMPONENT IN ACCORDANCE WITH WORK         *
         *        *  INSTRUCTION SHEET, REFERRED IN HEADLINE OL.        *
------------------------------------------------------------------------------ *        * .                                                *
ZC/095  * 090    *                                                      * *        *                              D.T.    27-09-24  *
AVM75A  *        *  ESEGUIRE COLLAUDO FINALE, DOCUMENTALE E             * *        *  VERSAMENTO.                                     *
         *        *  CONSULTARE LA LISTA DI CONTROLLO COME DA MODULO    *
         *        *  BQP.08.42.06 - "CHECKLIST FINAL INSPECTION".       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND A   *
         *        *  CHECK OF RELATED DOCUMENTATION.                    *
============================================================================== *        * .                                                *
RIP: A6 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]        15/09/2025
FIRMA AUTORE            [NOME OMESSO]           25-09-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           17-09-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           17-09-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 8 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 9 di 9

```text
 PGM PVRM320                          DATA STAMPA 28-01-2026 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXPR-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... UTILIZZAB.                 NOTE.......
RIPARAZIONE : A6                    S25/04343-BLENDING DIFETT
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 8bdb25d5

**GXRC-72560010A100-1** · [torna ai risultati](#ciclo-8bdb25d5) (p. 23)

#### Pagina 1 di 8

```text
 PGM PVRM320                         DATA STAMPA 04-12-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  APPLICAZIONE LUBRIFICANTE SECCO SUL RIPORTO         * *        *  PRESENTE SULLE SUPERFICI DI PRESSIONE DEL       *
         *        *  DOVETAIL, SECONDO:                                 *
         *        *                                                     *
         *        *  GEK9250 TASK 70-43-31-640-801                      *
         *        *                                                     *
         *        *  GEK112862 SUBTASK 72-56-31-640-001                 *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  APPLICATION OF SOLID FILM LUBRICANT ON THE COATING *
         *        *  OF THE DOVETAIL PRESSURE SURFACES, I.A.W:          *
         *        *                                                     *
         *        *  GEK9250 TASK 70-43-31-640-801                      *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  GEK112862 SUBTASK 72-56-31-640-001              *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DEL PARTICOLARE:        * *        *                                                  *
         *        *  P/N .....................  S/N .................  *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  IDENTIFICATION OF THE PART.                     *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        *                                                  *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
PREC01  * 020    *  HANDLING OF THE PART TO THE REPAIR AREA.            *
------------------------------------------------------------------------------ *        *                              D.T.    15-09-23  *
BA/063  * 025    *                                                      *
AVM753  *        *  PROTEGGERE LE AREE DELLA PALA CHE NON DEVONO        * *        *  ESSERE VERNICIATE.                              *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  MASK THE AREAS OF THE BLADE THAT ARE NOT           *
------------------------------------------------------------------------------ *        *  TO BE PAINTED.                                  *
IM0823  * 030    *                                                      * *        *                              D.T.    05-08-25  *
AVM753  *        *  APPLICARE LUBRIFICANTE SECCO SUL RIPORTO PRESENTE   * *        *  SULLE FACCE DI PRESSIONE DEL DOVETAIL E SUL     *
         *        *  PROVINO P/N P3962922/13 (SU CUI È PRESENTE IL      *
         *        *  RIPORTO PLASMA) DI ACCOMPAGNAMENTO DEL             *
         *        *  LOTTO DI PALE, E UTILIZZATO PER LE SUCCESSIVE      *
         *        *  PROVE DI COLLAUDO.                                 *
         *        *  APPLICARE LUBRIFICANTE SECCO SU UN ALTRO PROVINO   *
         *        *  P/N P3962922/13 (SENZA RIPORTO PLASMA) UTILIZZATO  *
         *        *  PER IL SUCCESSIVO CONTROLLO SPESSORE LUBRIFICANTE. *
         *        *  .                                                  *
         *        *  NOTA: I PROVINI DEVONO ESEGUIRE LE STESSE          *
         *        *        OPERAZIONI DELLE PALE.                       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  APPLY SOLID FILM LUBRICANT ON THE COATING OF THE   *
         *        *  DOVETAIL PRESSURE SURFACES AND SPECIMEN            *
         *        *  P/N 3962922/13 (WITH THERMAL SPRAY COATING)        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
IM0823  * 030    *  TOGETHER WITH EACH BATCH OF BLADES FOR NEXT         * *        *  TESTING.                                        *
         *        *  APPLY SOLID FILM LUBRICANT ON THE ANOTHER SPECIMEN *
         *        *  P/N 3962922/13 (WITHOUT THERMAL SPRAY COATING)     *
         *        *  FOR THE NEXT THICKNESS CHECK.                      *
         *        *  .                                                  *
         *        *  NOTE: THE SPECIMENS SHALL BE PERFORM THE SAME      *
         *        *        OPERATIONS AS THE BLADES.                    *
SCHEDA : SV562-BR   SP.ORIG. GEK9250 70-43-31     SP.FIAT *        * .                                                *
------------------------------------------------------------------------------ *        *                              D.T.    05-08-25  *
ZC/491  * 040    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELL'AREA RIVESTITA:               * *        *                                                  *
         *        *  - VERIFICARE CHE IL RIPORTO SIA UNIFORME E CHE     *
         *        *    ABBIA UN COLORE DAL GRIGIO SCURO AL BLU SCURO.   *
         *        *  - LE SUPERFICI RIVESTITE DEVONO ESSERE PRIVE DI    *
         *        *    POROSITA', DISTACCHI, BOLLE, INCROSTAZIONI.      *
         *        *                                                     *
         *        *  EFFETTUARE PROVA DI ADESIONE SUL PROVINO           *
         *        *  P/N P3962922/13 (SU CUI È PRESENTE IL RIPORTO      *
         *        *  PLASMA) DI ACCOMPAGNAMENTO DEL LOTTO.              *
         *        *                                                     *
         *        *  - FAR ADERIRE DEL NASTRO SUL LUBRIFICANTE          *
         *        *    APPLICATO. STRAPPARE IL NASTRO CON UN MOVIMENTO  *
         *        *    BRUSCO IN DIREZIONE PERPENDICOLARE ALLA          *
         *        *    SUPERFICIE RIVESTITA. ASSICURARSI CHE NON VI     *
         *        *    SIANO EVIDENZE DI DISTACCO O PELATURE DEL        *
         *        *    LUBRIFICANTE APPLICATO.                          *
         *        *                                                     *
         *        *  EFFETTUARE CONTROLLO DELLO SPESSORE DEL            *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/491  * 040    *  LUBRIFICANTE SECCO SUL SECONDO PROVINO              * *        *  P/N P3962922/13 (SENZA RIPORTO PLASMA).         *
         *        *  VERIFICARE CHE SIA ENTRO I LIMITI 13-38 MICRON.    *
         *        *  .                                                  *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF COATED AREA:                  *
         *        *                                                     *
         *        *  - CHECK TO ENSURE THAT THE COATING ON THE HARDWARE *
         *        *    HAS A UNIFORM, DARK GRAY TO DARK BLUE COLOR.     *
         *        *  - CHECK TO ENSURE THAT THE COATING IS FREE FROM    *
         *        *    DEFECTS SUCH AS PITS, BLISTERS, BUBBLES OR       *
         *        *    SCALING.                                         *
         *        *                                                     *
         *        *  PERFORM THE ADHESION TEST ON SPECIMEN.             *
         *        *                                                     *
         *        *  - PRESS A TAPE ON THE COATING AND REMOVE IT IN AN  *
         *        *    ABRUPT STRIPPING MOTION PERPENDICULAR TO THE     *
         *        *    SURFACE, AND ENSURE THAT THERE IS NO EVIDENCE OF *
         *        *    SCALING, PEELING OR LIFTING OF THE COATING.      *
         *        *  .                                                  *
         *        *  PERFORM LUBRICANT THICKNESS CHECK ON SPECIMEN      *
         *        *  P/N 3962922/13 (WITHOUT THERMAL SPRAY COATING).    *
         *        *  MAKE SURE THE THICKNESS IS WITHIN 13-38 MICRON.    * SP.ORIG. 70-43-31-640-803     SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    07-04-19  *
BA/777  * 050    *                                                      *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/777  * 050    *                                                      * *        *  PRESERVE THE COMPONENT I.A.W. THE TECHNICAL DATA *
------------------------------------------------------------------------------ *        *  SHEET.                                          *
ZC/095  * 065    *                                                      *
AVM75A  *        *  COLLAUDO VISIVO FINALE E VERSAMENTO.                * *        *                                                  *
         *        *  N.B.: PRESTARE PARTICOLARE ATTENZIONE A NON        *
         *        *        DANNEGGIARE LA PALA ED I RIPORTI ESISTENTI.  *
         *        *        PROTEGGERE LA PALA CON CARTA PALLINATA.      *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  CHECK OF THE DOCUMENTATION.                        *
         *        *                                                     *
         *        *  NOTE: PAY ATTENTION DURING THE HANDLING OF THE     *
         *        *        BLADE IN ORDER TO NOT DAMAGE IT OR THEIR     *
         *        *        COATINGS.                                    *
         *        *        PROTECT THE BLADES WITH PROTECTIVE PAPER.    *
         *        *                                                     *
         *        *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST *
============================================================================== *        *  FINAL INSPECTION".                              *
RIP: A2 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]        02/07/2025
FIRMA AUTORE            [NOME OMESSO]           04-09-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           09-09-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           04-09-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 7 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 8 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale 8d3c673c

**GXRC-72560010A190-1** · [torna ai risultati](#ciclo-8d3c673c) (p. 25)

#### Pagina 1 di 14

```text
 PGM PVRM320                         DATA STAMPA 15-12-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 010    *                                                      *
999999  *        *  QUESTA PROCEDURA FORNISCE LE ISTRUZIONI PER         * *        *  LA RIPARAZIONE DI RACCORDATURA PALE TIAL        *
         *        *  STADIO 7 COME DA REPAIR 005                        *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  THIS REPAIR, PROVIDE ISTRUCTION FOR BLENDING       *
         *        *  PROVIDES INSTRUCTIONS FOR BLENDING OF TIAL BLADE   *
------------------------------------------------------------------------------ *        *  STAGE 7 AS PER REPAIR 005                       *
ZC/457  * 020    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DEL PARTICOLARE         * *        * .                                                *
         *        *  REGISTRARE PN E SN.                                *
         *        *  .                                                  *
         *        *  P/N:                       S/N:                    *
         *        *       --------------------     ---------------------*
         *        *  .                                                  *
         *        *  IDENTIFICARE E NUMERARE I DIFETTI DA RACCORDARE    *
         *        *  CON MATITA A CERA ROSSA.                           *
         *        *  .                                                  *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RACCORDARE  *
         *        *  .                                                  *
         *        *  N° DIFETTI:.............. TIMBRO:..............    *
         *        *  .                                                  *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO\GENX    *
         *        *  NOMINANDOLA COME L'OL ED INSERENDO ALL'INTERNO LE  *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A4               *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 020    *  *************************************************  * *        * .                                                *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *  .                                                  *
         *        *  IDENTIFY AND NUMBER THE DEFECTS TO BE BLENDED WITH *
         *        *  RED WAX PENCIL.                                    *
         *        *  .                                                  *
         *        *  RECORD NUMBER OF DEFECTS TO BE BLENDED.            *
         *        *  .                                                  *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO\GENX       *
         *        *  NAMED AS THIS OL WITH THE DEFECTS PICTURES. IF     *
         *        *  THIS REPAIR IS COMBINED WITH OTHERS, CREATE A SUB- *
------------------------------------------------------------------------------ *        *  FOLDER AND RENAME IT: A4                        *
PREC02  * 030    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA                          * *        * .                                                *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  HANDLING OF THE PART TO REPAIR AREA                *
------------------------------------------------------------------------------ *        * .                                                *
BA/766  * 060    *                                                      * *        *                              D.T.    26-03-25  *
AVM751  *        *  ATTENZIONE: TUTTE LE AREE RACCORDATE DEVONO ESSERE  * *        *          CONTRASSEGNATE CON UNA MATITA A CERA    *
         *        *              PER CONSENTIRE DI IDENTIFICARE L'AREA  *
         *        *              DA ISPEZIONARE NELLA OPERAZIONE 70     *
         *        *              SUCCESSIVA. RIFERIRSI ALLA MAPPA DEI   *
         *        *              DIFETTI ALLEGATA AL PRESENTE CICLO.    *
         *        *  .                                                  *
         *        *  ESEGUIRE RACCORDATURA DEI DIFETTI IDENTIFICATI     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 060    *  IN OP.10.                                           * *        * .                                                *
         *        *  SE NECESSARIA UNA RACCORADATURA PIU' PROFONDA,     *
         *        *  UTILIZZARE UN ELETTROUTENSILE A BASSO NUMERO DI    *
         *        *  GIRI.                                              *
         *        *  .                                                  *
         *        *  ASSICURARSI CHE LA FINITURA SUPERFICIALE DOPO      *
         *        *  RACCORDATURA SIA EQUIVALENTE O MIGLIORE A          *
         *        *  QUELLA DELLE AREE ADIACENTI NON LAVORATE.          *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  * SUP. PROFILO CONCAVO/CONVESSO-NO AREA 'X', 'Y' * *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  RACCORDARE I DIFETTI SULLA SUPERFICIE DEL          *
         *        *  PROFILO CONCAVO E/O CONVESSO. RIFERIRSI AI         *
         *        *  REQUISITI RIPORTATI NEL D.T.                       *
         *        *  .                                                  *
         *        *  RACCORDARE E LUCIDARE IN DIREZIONE LONGITUDINALE   *
         *        *  PARALLELAMENTE ALLA LUNGHEZZA DELLA PALA.          *
         *        *  .                                                  *
         *        *  LA RACCORDATURA NON E' PERMESSA IN AREA 'X' E 'Y'  *
         *        *  .                                                  *
         *        *  RACCORDATURE NELLO STESSO PUNTO SUL LATO OPPOSTO   *
         *        *  NON SONO PERMESSE.                                 *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  * BORDO DI ENTRATA/USCITA AREA 'J','K','L','M'*    *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  SE RICHIESTO, RACCORDARE IL BORDO DI ENTRATA E/O   *
         *        *  IL BORDO DI USCITA IN AREA 'J', 'K','L' E/O 'M'    *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 060    *  DELLA PALA. RIFERIRSI AI REQUISITI RIPORTATI NEL    * *        *  D.T.                                            *
         *        *  .                                                  *
         *        *  RACCORDARE E LUCIDARE IN DIREZIONE LONGITUDINALE   *
         *        *  PARALLELAMENTE ALLA LUNGHEZZA DELLA PALA.          *
         *        *  .                                                  *
         *        *  IL RAGGIO DELL'AREA RIPARATA SUL BORDO DI          *
         *        *  ENTRATA E DI USCITA DEVE ESSERE UGUALE AL          *
         *        *  CONTORNO/PROFILO ORIGINALE. RIFERIRSI AI REQUISITI *
         *        *  RIPORTATI NEL D.T.                                 *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  * SUP. PROFILO CONCAVO/CONVESSO AREA 'X', 'Y' *    *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  RACCORDARE L'AREA 'X' E 'Y' SULLA SUPERFICIE       *
         *        *  CONCAVA E CONVESSA DELLA PALA.                     *
         *        *  RIFERIRSI AI REQUISITI RIPORTATI NEL D.T.          *
         *        *  .                                                  *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  * PLATFORM, SHANK, ANGEL WING, DOVETAIL SHROUD *   *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  RACCORDARE LA PALA PER RIMUOVERE IL DANNO SULLA    *
         *        *  PIATTAFORMA, SHANK, ANGEL WING, L'ATTACCO A CODA   *
         *        *  DI RONDINE E L'AREA SHORUD.                        *
         *        *  RIFERIRSI AI REQUISITI RIPORTATI NEL D.T.          *
         *        *  .                                                  *
         *        *  LA RACCORDATURA SUL NOTCH 'R' NON È PERMESSA.      *
         *        *  .                                                  *
         *        *  LA RACCORDATURA SULLE SUPERFICI LATERALI DEL       *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 060    *  DOVETAIL NON E' PERMESSA.                           * *        * .                                                *
         *        *   RACCORDARE GLI SPIGOLI DEL DOVETAIL CON UN RAGGIO *
         *        *   DI 0.005-0.060 INCH (0.13-1.52 MM).               *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  CAUTION: ALL BLENDED AREA MUST BE MARKED BY A      *
         *        *           WAX PENSIL TO ALLOW TO IDENTY THE AREA    *
         *        *           THAT MUST CHECKED IN NEXT STEP. REFER     *
         *        *           THE MAP ATTACHED TO THIS ROUTER.          *
         *        *  .                                                  *
         *        *  BLEND THE DEFECTS IDENTIFIED IN OP.10              *
         *        *  .                                                  *
         *        *  IF A LARGE BLEND IN DEPTH IS NECESSARY, USE A SLOW *
         *        *  SPEED POWER TOOL.                                  *
         *        *  .                                                  *
         *        *  MAKE SURE THAT THE SURFACE FINISH AFTER BLENDING   *
         *        *  IS EQUIVALENT TO THE ADJACENT SURFACE FINISH.      *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  * AIRFOIL SURF. CONCAVE/CONVEX-NO AREA 'X', 'Y' *  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  BLEND THE CONCAVE AND CONVEX SIDE AIRFOIL          *
         *        *  SURFACES. REFER TO D.T. LIMITS                     *
         *        *  .                                                  *
         *        *  BLEND AND POLISH IN A LONGITUDINAL DIRECTION,      *
         *        *  PARALLEL WITH THE LENGTH OF THE BLADE.             *
         *        *  .                                                  *
         *        *  BLENDING IS NOT PERMITTED IN AREA X AND AREA Y     *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 060    *  OPPOSING BLENDS ARE NOT PERMITTED.                  * *        * .                                                *
         *        *  *************************************************  *
         *        *  * LEADING/TRAILING EDGE AREA AREA 'J','K','L','M'* *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  BLEND THE LEADING AND TRAILING EDGES ON AREA J,    *
         *        *  AREA K,AREA L AND AREA M OF THE BLADE.             *
         *        *  REFER TO D.T. LIMITS.                              *
         *        *  .                                                  *
         *        *  BLEND AND POLISH IN A LONGITUDINAL DIRECTION,      *
         *        *  PARALLEL WITH THE LENGTH OF THE BLADE.             *
         *        *  .                                                  *
         *        *  THE LEADING AND TRAILING EDGE RADIUS OF THE        *
         *        *  REPAIRED AREA MUST AGREE WITH THE INITIAL CONTOUR. *
         *        *  REFER TO FIGURE 903.                               *
         *        *  .                                                  *
         *        *  ************************************************   *
         *        *  * AIRFOIL SURFACE CONCAVE/CONVEX AREA 'X', 'Y' *   *
         *        *  ************************************************   *
         *        *  .                                                  *
         *        *  BLEND TO REMOVE DAMAGE ON AREA 'X' AND 'Y'         *
         *        *  REFER TO D.T. LIMITS.                              *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  * PLATFORM, SHANK, ANGEL WING, DOVETAIL SHROUD *   *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  BLEND TO REMOVE THE DAMAGE ON THE PLATFORM, SHANK  *
         *        *  ANGEL WING, DOVETAIL AND SHROUD AREAS OF THE       *
         *        *  BLADE. REFER TO D.T. LIMITS.                       *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 8 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 060    *  BLEND DOVETAIL CORNERS TO A RADIUS OF 0.005-0.060   * *        *  060 INCH (0.13-1.52 MM).                        *
         *        *  .                                                  *
         *        *  BLENDING ON NOTCH 'R' IS NOT PERMITTED.            *
         *        *  .                                                  *
         *        *  BLENDING ON DOVETAIL SIDE SURFACES IS NOT          *
         *        *  PERMITTED.                                         *
         *        *  .                                                  * SP.ORIG. 70-42-00              SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
         *        *  B1336196       KIT CALIBRI A SFERA                 *
------------------------------------------------------------------------------ *        *  M8225078        LOCATORE CMM BLADE GENX         *
ZC/095  * 070    *                                                      * *        *                              D.T.    26-03-25  *
AVM75A  *        *  ESEGUIRE CONTROLLO VISIVO E DIMENSIONALE DELLE      * *        *  AREE RIPARATE NEL PRECEDENTE STEP, IDENTIFICATE *
         *        *  IN OP.10.                                          *
         *        *  .                                                  *
         *        *  ASSICURARSI CHE LA FINITURA SUPERFICIALE DOPO      *
         *        *  RACCORDATURA SIA EQUIVALENTE O MIGLIORE A          *
         *        *  QUELLA DELLE AREE ADIACENTI NON LAVORATE.          *
         *        *  .                                                  *
         *        *  VERIFICARE CHE SIANO STATI COMPLETAMENTE RIMOSSI I *
         *        *  DIFETTI IDENTIFICATI IN OP.10 E CHE SIANO STATI    *
         *        *  RISPETTATI I REQUISITI DIMENSIONALI DEL D.T.       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  DO A VISUAL AND DIMENSIONAL CHECK OF THE REPAIRED  *
         *        *  AREAS BLENDED IN THE PREVIOUS STEP.                *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 9 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 070    *  MAKE SURE THAT THE SURFACE FINISH AFTER BLENDING    * *        *  IS EQUIVALENT TO THE ADJACENT SURFACE FINISH.   *
         *        *  .                                                  *
         *        *  VERIFY THE COMPLETE REMOVAL OF THE DEFECTS         *
         *        *  IDENTIFIED IN OP.10 AND REQUIREMENTS OF THE        *
         *        *  TECHNICAL DATA SHEET.                              *
         *        *  .                                                  *
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  B1336196       KIT CALIBRI A SFERA              *
IM0739  * 090    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM759  *        *  SE NECESSARIO PULIRE LA PALA. RIFERIMENTO ESM       * *        *  72-56-32, CLEANING 001, SPM 70-21-03            *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  IF NECESSARY, CLEAN THE BLADE. REFER TO 72-56-32,  *
         *        *  CLEANING 001                                       *
SCHEDA : PG-128     SP.ORIG. 70-21-03            SP.FIAT *        * .                                                *
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8224852       CESTELLO X LAVAGGIO              *
BA/662  * 100    *                                                      * *        *                              D.T.    26-03-25  *
AVM751  *        *  ESEGUIRE ATTACCO CHIMICO A TAMPONE DELLE SUPERFICI  * *        *  RACCORDATE.                                     *
         *        *  .                                                  *
         *        *  MATERIALE BASE: GAMMA TIAL                         *
         *        *  .                                                  *
         *        *  ETCHANT: CLASS I                                   *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 10 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.  10
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/662  * 100    *  .                                                   * *        *  *************************************************  *
         *        *  .                                                  *
         *        *  SWAB ETCH THE BLENDED AREAS                        *
         *        *  .                                                  *
         *        *  BASE MATERIAL: GAMMA TIAL                          *
         *        *  .                                                  *
SCHEDA : CPEC505-BR SP.ORIG. 70-25-01-110-034 I   SP.FIAT 70-24-00-110-033 *        *  ETCHANT: CLASS I                                *
------------------------------------------------------------------------------ *        *                              D.T.    26-03-25  *
ZC/080  * 110    *                                                      *
AVM758  *        *  ESEGUIRE CONTROLLO CON LIQUIDI PENETRANTI           * *        *  FLUORESCENTI DELLE AREE RACCORDATE.             *
         *        *  .                                                  *
         *        *  USARE PENETRANTE CLASSE 'D'                        *
         *        *  .                                                  *
         *        *  FARE RIFERIMENTO AI LIMITI DI ACCETTABILITÀ        *
         *        *  RIPORTATI NEL DETTAGLIO TECNICO.                   *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  PERFORM LOCAL FPI INSPECTION OF THE BLENDED AREAS  *
         *        *  .                                                  *
         *        *  USE CLASS D PENETRANT                              *
         *        *  .                                                  *
         *        *  REFER TO TECHNICAL DATA SHEET FOR THE              *
         *        *  ACCEPTANCE LIMITS.                                 *
SCHEDA : SLP-06     SP.ORIG. 70-32-04-230-002 D   SP.FIAT *        * .                                                *
------------------------------------------------------------------------------ *        *  ***** OPERAZIONE EVENTUALE *****                *
                                                     *** C O N T I N U A ***
```

#### Pagina 11 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.  11
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
IM0739  * 130    *                                                      *
AVM759  *        *  SE NECESSARIO PULIRE LA PALA. RIFERIMENTO ESM       * *        *  72-56-32, CLEANING 001, SPM 70-21-03            *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  IF NECESSARY, CLEAN THE BLADE. REFER TO 72-56-32,  *
         *        *  CLEANING 001                                       *
SCHEDA : PG-128     SP.ORIG. 70-21-03            SP.FIAT *        * .                                                *
         *        *  * ATTREZZATURA PREVISTA *                          *
------------------------------------------------------------------------------ *        *  M8224852       CESTELLO X LAVAGGIO              *
ZC/095  * 140    *                                                      *
AVM75A  *        *  ESEGUIRE ISPEZIONE VISIVA FINALE DELLA PALA COME    * *        *  DA TASK 72-56-32 INSPECTION 001.                *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  DO A VISUAL INSPECTION OF THE BLADE. REFER TO      *
         *        *  TASK 72-56-31, INSPECTION 001.                     *
         *        *  .                                                  *
         *        *  FLUORESCENT PENETRANT INSPECTION IS NOT REQUIRED.  *
------------------------------------------------------------------------------ *        * .                                                *
BA/777  * 150    *                                                      * *        *                              D.T.    07-04-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT.           * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  PRESERVE COMPONENT IN ACCORDANCE WITH WORK         *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 12 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.  12
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/777  * 150    *  INSTRUCTION SHEET                                   * *        *  PRESERVATION REFERRED IN HEADLINE OF O.L.       *
------------------------------------------------------------------------------ *        * .                                                *
ZC/095  * 160    *                                                      *
AVM75A  *        *  ESEGUIRE UNA VISUAL INSPECTION GENERALE DELLA       * *        *  PARTE E LA RELATIVA DOCUMENTAZIONE              *
         *        *                                                     *
         *        *  CONSULTARE COME DA MODULO BQP.08.42.06 -           *
         *        *  "CHECKLIST FINAL INSPECTION".                      *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND A   *
         *        *  CHECK OF RELATED DOCUMENTATION.                    *
         *        *  .                                                  *
         *        *  READ AS PER FORM BQP.08.42.06 - "CHECKLIST         *
         *        *  FINAL INSPECTION".                                 *
============================================================================== *        * .                                                *
RIP: A4 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]        25/06/2025
FIRMA AUTORE            [NOME OMESSO]           30-09-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           02-10-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           30-09-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 13 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.  13
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 14 di 14

```text
 PGM PVRM320                          DATA STAMPA 15-12-2025 PAG.  14
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A4                    72-56-32 REPAIR 005
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale c5ff3cd6

**GXRC-72560010A100-1** · [torna ai risultati](#ciclo-c5ff3cd6) (p. 29)

#### Pagina 1 di 8

```text
 PGM PVRM320                         DATA STAMPA 04-12-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  APPLICAZIONE LUBRIFICANTE SECCO SUL RIPORTO         * *        *  PRESENTE SULLE SUPERFICI DI PRESSIONE DEL       *
         *        *  DOVETAIL, SECONDO:                                 *
         *        *                                                     *
         *        *  GEK9250 TASK 70-43-31-640-801                      *
         *        *                                                     *
         *        *  GEK112862 SUBTASK 72-56-31-640-001                 *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  APPLICATION OF SOLID FILM LUBRICANT ON THE COATING *
         *        *  OF THE DOVETAIL PRESSURE SURFACES, I.A.W:          *
         *        *                                                     *
         *        *  GEK9250 TASK 70-43-31-640-801                      *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  GEK112862 SUBTASK 72-56-31-640-001              *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DEL PARTICOLARE:        * *        *                                                  *
         *        *  P/N .....................  S/N .................  *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  IDENTIFICATION OF THE PART.                     *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        *                                                  *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
PREC01  * 020    *  HANDLING OF THE PART TO THE REPAIR AREA.            *
------------------------------------------------------------------------------ *        *                              D.T.    15-09-23  *
BA/063  * 025    *                                                      *
AVM753  *        *  PROTEGGERE LE AREE DELLA PALA CHE NON DEVONO        * *        *  ESSERE VERNICIATE.                              *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  MASK THE AREAS OF THE BLADE THAT ARE NOT           *
------------------------------------------------------------------------------ *        *  TO BE PAINTED.                                  *
IM0823  * 030    *                                                      * *        *                              D.T.    05-08-25  *
AVM753  *        *  APPLICARE LUBRIFICANTE SECCO SUL RIPORTO PRESENTE   * *        *  SULLE FACCE DI PRESSIONE DEL DOVETAIL E SUL     *
         *        *  PROVINO P/N P3962922/13 (SU CUI È PRESENTE IL      *
         *        *  RIPORTO PLASMA) DI ACCOMPAGNAMENTO DEL             *
         *        *  LOTTO DI PALE, E UTILIZZATO PER LE SUCCESSIVE      *
         *        *  PROVE DI COLLAUDO.                                 *
         *        *  APPLICARE LUBRIFICANTE SECCO SU UN ALTRO PROVINO   *
         *        *  P/N P3962922/13 (SENZA RIPORTO PLASMA) UTILIZZATO  *
         *        *  PER IL SUCCESSIVO CONTROLLO SPESSORE LUBRIFICANTE. *
         *        *  .                                                  *
         *        *  NOTA: I PROVINI DEVONO ESEGUIRE LE STESSE          *
         *        *        OPERAZIONI DELLE PALE.                       *
         *        *  .                                                  *
         *        *  *************************************************  *
         *        *  .                                                  *
         *        *  APPLY SOLID FILM LUBRICANT ON THE COATING OF THE   *
         *        *  DOVETAIL PRESSURE SURFACES AND SPECIMEN            *
         *        *  P/N 3962922/13 (WITH THERMAL SPRAY COATING)        *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
IM0823  * 030    *  TOGETHER WITH EACH BATCH OF BLADES FOR NEXT         * *        *  TESTING.                                        *
         *        *  APPLY SOLID FILM LUBRICANT ON THE ANOTHER SPECIMEN *
         *        *  P/N 3962922/13 (WITHOUT THERMAL SPRAY COATING)     *
         *        *  FOR THE NEXT THICKNESS CHECK.                      *
         *        *  .                                                  *
         *        *  NOTE: THE SPECIMENS SHALL BE PERFORM THE SAME      *
         *        *        OPERATIONS AS THE BLADES.                    *
SCHEDA : SV562-BR   SP.ORIG. GEK9250 70-43-31     SP.FIAT *        * .                                                *
------------------------------------------------------------------------------ *        *                              D.T.    05-08-25  *
ZC/491  * 040    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELL'AREA RIVESTITA:               * *        *                                                  *
         *        *  - VERIFICARE CHE IL RIPORTO SIA UNIFORME E CHE     *
         *        *    ABBIA UN COLORE DAL GRIGIO SCURO AL BLU SCURO.   *
         *        *  - LE SUPERFICI RIVESTITE DEVONO ESSERE PRIVE DI    *
         *        *    POROSITA', DISTACCHI, BOLLE, INCROSTAZIONI.      *
         *        *                                                     *
         *        *  EFFETTUARE PROVA DI ADESIONE SUL PROVINO           *
         *        *  P/N P3962922/13 (SU CUI È PRESENTE IL RIPORTO      *
         *        *  PLASMA) DI ACCOMPAGNAMENTO DEL LOTTO.              *
         *        *                                                     *
         *        *  - FAR ADERIRE DEL NASTRO SUL LUBRIFICANTE          *
         *        *    APPLICATO. STRAPPARE IL NASTRO CON UN MOVIMENTO  *
         *        *    BRUSCO IN DIREZIONE PERPENDICOLARE ALLA          *
         *        *    SUPERFICIE RIVESTITA. ASSICURARSI CHE NON VI     *
         *        *    SIANO EVIDENZE DI DISTACCO O PELATURE DEL        *
         *        *    LUBRIFICANTE APPLICATO.                          *
         *        *                                                     *
         *        *  EFFETTUARE CONTROLLO DELLO SPESSORE DEL            *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/491  * 040    *  LUBRIFICANTE SECCO SUL SECONDO PROVINO              * *        *  P/N P3962922/13 (SENZA RIPORTO PLASMA).         *
         *        *  VERIFICARE CHE SIA ENTRO I LIMITI 13-38 MICRON.    *
         *        *  .                                                  *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF COATED AREA:                  *
         *        *                                                     *
         *        *  - CHECK TO ENSURE THAT THE COATING ON THE HARDWARE *
         *        *    HAS A UNIFORM, DARK GRAY TO DARK BLUE COLOR.     *
         *        *  - CHECK TO ENSURE THAT THE COATING IS FREE FROM    *
         *        *    DEFECTS SUCH AS PITS, BLISTERS, BUBBLES OR       *
         *        *    SCALING.                                         *
         *        *                                                     *
         *        *  PERFORM THE ADHESION TEST ON SPECIMEN.             *
         *        *                                                     *
         *        *  - PRESS A TAPE ON THE COATING AND REMOVE IT IN AN  *
         *        *    ABRUPT STRIPPING MOTION PERPENDICULAR TO THE     *
         *        *    SURFACE, AND ENSURE THAT THERE IS NO EVIDENCE OF *
         *        *    SCALING, PEELING OR LIFTING OF THE COATING.      *
         *        *  .                                                  *
         *        *  PERFORM LUBRICANT THICKNESS CHECK ON SPECIMEN      *
         *        *  P/N 3962922/13 (WITHOUT THERMAL SPRAY COATING).    *
         *        *  MAKE SURE THE THICKNESS IS WITHIN 13-38 MICRON.    * SP.ORIG. 70-43-31-640-803     SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    07-04-19  *
BA/777  * 050    *                                                      *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/777  * 050    *                                                      * *        *  PRESERVE THE COMPONENT I.A.W. THE TECHNICAL DATA *
------------------------------------------------------------------------------ *        *  SHEET.                                          *
ZC/095  * 065    *                                                      *
AVM75A  *        *  COLLAUDO VISIVO FINALE E VERSAMENTO.                * *        *                                                  *
         *        *  N.B.: PRESTARE PARTICOLARE ATTENZIONE A NON        *
         *        *        DANNEGGIARE LA PALA ED I RIPORTI ESISTENTI.  *
         *        *        PROTEGGERE LA PALA CON CARTA PALLINATA.      *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  CHECK OF THE DOCUMENTATION.                        *
         *        *                                                     *
         *        *  NOTE: PAY ATTENTION DURING THE HANDLING OF THE     *
         *        *        BLADE IN ORDER TO NOT DAMAGE IT OR THEIR     *
         *        *        COATINGS.                                    *
         *        *        PROTECT THE BLADES WITH PROTECTIVE PAPER.    *
         *        *                                                     *
         *        *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST *
============================================================================== *        *  FINAL INSPECTION".                              *
RIP: A2 OEM: GEK112862                   CHANGE: 41           DEL :30/04/2025 FIRMATO DA: [NOME OMESSO]        02/07/2025
FIRMA AUTORE            [NOME OMESSO]           04-09-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           09-09-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           04-09-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 7 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 8 di 8

```text
 PGM PVRM320                          DATA STAMPA 04-12-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A100-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A2                    APPL. LUBRIFIC. SECCO
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---


### Testo originale e9b74c84

**GXRC-72560011-270-2** · [torna ai risultati](#ciclo-e9b74c84) (p. 31)

#### Pagina 1 di 8

```text
 PGM PVRM320                         DATA STAMPA 14-10-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RIMOZIONE METALLO IN RILIEVO SECONDO:               * *        *                                                  *
         *        *  GEK9250 SUBTASK 70-42-00-350-029                   *
         *        *  GEK114120 TASK 72-56-31-200-801                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  REMOVAL OF HIGH METAL PROCEDURES I.A.W.:           *
         *        *                                                     *
         *        *  GEK9250 SUBTASK 70-42-00-350-029                   *
------------------------------------------------------------------------------ *        *  GEK114120 TASK 72-56-31-200-801                 *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  QUESTA RIPARAZIONE è APPLICABILE SOLO AI SEGUENTI  *
         *        *  PN:                                                *
         *        *                                                     *
         *        *  - 2479M15P01                                       *
         *        *  - 2479M15P02                                       *
         *        *                                                     *
         *        *  P/N ..................... S/N .................    *
         *        *                                                     *
         *        *  IDENTIFICARE I DIFETTI DAI QUALI RIMUOVERE IL      *
         *        *  METALLO IN RILIEVO INDICANDOLI SULLA PALA CON      *
         *        *  MATITA A CERA ROSSA.                               *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RIPARARE:   *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:...............   *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO          * *        *  NOMINADOLA COME L'OL ED INSERENDO ALL'INTERNO LE *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A3               *
         *        *                                                     *
         *        *  SE NON è PRESENTE METALLO IN RILIEVO SUL PROFILO   *
         *        *  DELLA PALA ANNULLARE LE OP.25 E 35.                *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  THIS REPAIR IS APPLICABLE ONLY TO THE FOLLOWING    *
         *        *  PN'S:                                              *
         *        *                                                     *
         *        *  - 2479M15P01                                       *
         *        *  - 2479M15P02                                       *
         *        *                                                     *
         *        *  IDENTIFY THE DEFECTS FROM WHICH THE HIGH METAL HAS *
         *        *  TO BE REMOVED WITH RED WAX PENCIL.                 *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO NAMED AS   *
         *        *  THIS OL WITH THE DEFECTS PICTURES. IF THIS REPAIR  *
         *        *  IS COMBINED WITH OTHERS CREATE A SUB-FOLDER AND    *
         *        *  RENAME IT: A3                                      *
         *        *                                                     *
         *        *  IF THERE ISN'T HIGH METAL ON THE BLADE'S PROFILE   *
------------------------------------------------------------------------------ *        *  SURFACES, ANNUL OP.25 AND 35.                   *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
------------------------------------------------------------------------------
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
PREC01  * 020    *  .                                                   * *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 025    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM751  *        *  LUCIDATURA MANUALE DELLE AREE CONCAVA E CONVESSA    * *        *  DEL PROFILO PALA, AL FINE DI RIMUOVERE IL METALLO *
         *        *  IN RILIEVO.                                        *
         *        *                                                     *
         *        *  UTILIZZARE CARTA ABRASIVA GRANA 500                *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  MANUAL POLISHING OF THE CONCAVE AND CONVEX PROFILE *
         *        *  SURFACES, FOR REMOVING THE HIGH METAL.             *
         *        *                                                     *
         *        *  USE CROCUS CLOTH 60 GRIT                           * SP.ORIG. 70-42-00-350-070     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
         *        *  M8225077       LOCATORE CMM BLADE GENX             *
------------------------------------------------------------------------------ *        *  M8225081       LOCATORE CMM BLADE GENX          *
BA/766  * 030    *                                                      *
AVM751  *        *  RIMUOVERE IL METALLO IN RILIEVO DAI DIFETTI         * *        *  INDICATI IN OP.10.                              *
         *        *  .                                                  *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *        DI INCOLLAGGIO VETRIFICATA.                  *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *                                                      * *        *  REMOVE THE HIGH METAL FROM FROM THE DEFECTS     *
         *        *  IDENTIFIED IN OP.10.                               *
         *        *  .                                                  *
         *        *       N.B.: DO NOT USE ABRASIVES THAT INCLUDES A      *
         *        *        VITRIFIED BOND MATRIX.                       * SP.ORIG. 70-42-00-350-029     SP.FIAT
         *        *  * ATTREZZATURA PREVISTA *                          *
         *        *  M8225077       LOCATORE CMM BLADE GENX             *
------------------------------------------------------------------------------ *        *  M8225081       LOCATORE CMM BLADE GENX          *
ZC/095  * 035    *                                                      * *        *  ***** OPERAZIONE EVENTUALE *****                *
AVM75A  *        *  COLLAUDO VISIVO DELLA RIMOZIONE METALLO IN RILIEVO  * *        *  EFFETTUATA IN OP.25.                            *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE HIGH METAL REMOVAL,       *
------------------------------------------------------------------------------ *        *  IN OP.25.                                       *
ZC/095  * 040    *                                                      *
AVM75A  *        *  CONTROLLO VISIVO.                                   * *        *                                                  *
         *        *  VERIFICARE CHE SIA STATO RIMOSSO IL METALLO IN     *
         *        *  RILIEVO DAI DIFETTI IDENTIFICATI IN OP.10.         *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION                                  *
         *        *                                                     *
         *        *  VERIFY THAT THE HIGH METAL HAS BEEN blended FROM   *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 040    *  THE DEFECTS IDENTIFIED IN OP.10.                    *
------------------------------------------------------------------------------ *        *                              D.T.    07-04-19  *
BA/777  * 050    *                                                      *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------ *        *                              D.T.    27-09-24  *
ZC/095  * 060    *                                                      *
AVM75A  *        *  ESEGUIRE UNA VISUAL INSPECTION GENERALE DELLA       * *        *  PARTE E DELLA RELATIVA DOCUMENTAZIONE           *
         *        *  .                                                  *
         *        *  CONSULTARE COME DA MODULO BQP.08.42.06 -           *
         *        *  "CHECKLIST FINAL INSPECTION".                      *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
============================================================================== *        *  A CHECK OF THE RELATED DOCUMENTATION.           *
RIP: A3 OEM: GEK114120                   CHANGE: 34        DEL :30.04.2025
FIRMA CHANGE            [NOME OMESSO]           06-10-2025
FIRMA AUTORE            [NOME OMESSO]           06-10-2025
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           06-10-2025
FIRMA ANALISI LAVORO    [NOME OMESSO]           06-10-2025
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 7 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
============================================================================== 1  AGGIORNATA CHANGE ED OP.30 E 40                      06-10-2025 [NOME OMESSO]
```

#### Pagina 8 di 8

```text
 PGM PVRM320                          DATA STAMPA 14-10-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560011-270-2       DESCR.CICLO : GENX-2B LPT BLADE STAGE 6
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A3                    RIMOZ.METALLO IN RILIEVO
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---

### Testo originale f355dc3c

**GXRC-72560010A190-1** · [torna ai risultati](#ciclo-f355dc3c) (p. 34)

#### Pagina 1 di 11

```text
 PGM PVRM320                         DATA STAMPA 11-11-2025 PAG.   1 ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
MODIFICHE TESTATA CICLO                         DATA   NOME UTENTE
** NESSUNA DESCRIZIONE O MODIFICA SU TESTATA CICLO **
==============================================================================
```

#### Pagina 2 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   2
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------
------------------------------------------------------------------------------
NOTE    * 005    *                                                      *
999999  *        *  RACCORDATURA DIFETTI SECONDO:                       * *        *                                                  *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
         *        *  GEK 112862 TASK 72-56-32-200-801                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  DEFECTS BLENDING I.A.W.:                           *
         *        *                                                     *
         *        *  GEK 9250 TASK 70-42-00-350-002                     *
------------------------------------------------------------------------------ *        *  GEK 112862 TASK 72-56-32-200-801                *
ZC/457  * 010    *                                                      *
AVM772  *        *  PRELIEVO ED IDENTIFICAZIONE DELLA PALA.             * *        *                                                  *
         *        *  P/N ...................... S/N .................   *
         *        *                                                     *
         *        *  IDENTIFICARE E NUMERARE I DIFETTI DA RACCORDARE    *
         *        *  CON MATITA A CERA ROSSA.                           *
         *        *                                                     *
         *        *  RIFERIRSI ALLA SCHEDA DIFETTI DELLA RIPARAZIONE    *
         *        *  GXTR-72560010A190-1 RIP.B1                         *
         *        *                                                     *
         *        *  ***************** NOTA BENE ******************     *
         *        *                                                     *
         *        *  SE NON è STATA APPROVATA UNA DR SU QUESTO SN        *
         *        *  RISPETTARE I SEGUENTI LIMITI:                      *
         *        *                                                     *
         *        *  - MASSIMO 8 RACCORDATURE SU TUTTA LA PALA          *
         *        *                                                     *
         *        *  - MASSIMO 10 RACCORDATURE SUL BORDO D'ENTRATA      *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 3 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   3
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *                                                      * *        *  - MASSIMO 7 RACCORDATURE SUL BORDO D'USCITA     *
         *        *                                                     *
         *        *  VEDI TASK 72-56-32-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  DR:...................................             *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  RIPORTARE DI SEGUITO N° DEI DIFETTI DA RACCORDARE  *
         *        *                                                     *
         *        *  N° DIFETTI:.............. TIMBRO:...............   *
         *        *                                                     *
         *        *  CREARE UN CARTELLA IN U:\TECPR MICROSCOPIO         *
         *        *  NOMINANDOLA COME L'OL ED INSERENDO ALL'INTERNO LE  *
         *        *  FOTO DEI DIFETTI DA RIPARARE. SE QUESTA            *
         *        *  RIPARAZIONE VIENE LANCIATA IN COMBINATA, CREARE    *
         *        *  UNA SOTTOCARTELLA, RINOMINANDOLA: A1               *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  IDENTIFICATION OF THE BLADE:                       *
         *        *                                                     *
         *        *  IDENTIFY AND NUMBER THE DEFECTS TO BE BLENDED WITH *
         *        *   RED WAX PENCIL. USE THE DEFECT REPORT OF THE      *
         *        *  REPAIR GXTR-72560010A190-1 RIP.B1                  *
         *        *                                                     *
         *        *  ******************** N.B. *********************    *
         *        *                                                     *
         *        *  IF THERE ISN'T AN APPROVED DR ON THIS COMPONENT    *
         *        *  USE THE FOLLOWING LIMITS:                          *
         *        *                                                     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 4 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   4
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/457  * 010    *  - MAXIMUM NUMBER OF BLENDS FOR ONE BLADE IS 4       * *        *                                                  *
         *        *  - MAXIMUM NUMBER OF BLENDS ON TRAILING EDGE IS 2   *
         *        *                                                     *
         *        *  - MAXIMUM NUMBER OF BLENDS ON LEADING EDGE IS 2    *
         *        *                                                     *
         *        *  REF. TASK 72-56-32-200-801 FIGURE 801 (SHEET 3)    *
         *        *                                                     *
         *        *  ************************************************   *
         *        *                                                     *
         *        *  CREATE A FOLDER IN U:\TECPR MICROSCOPIO            *
         *        *  NAMED AS THIS OL WITH THE DEFECTS PICTURES. IF     *
         *        *  THIS REPAIR IS COMBINED WITH OTHERS, CREATE A SUB- *
------------------------------------------------------------------------------ *        *  FOLDER AND RENAME IT: A1                        *
PREC01  * 020    *                                                      *
AVM753  *        *  PRESA IN CARICO DA PERIZIA.                         * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
------------------------------------------------------------------------------ *        *  HANDLING OF THE PART TO THE REPAIR AREA.        *
BA/766  * 030    *                                                      * *        *                              D.T.    08-08-24  *
AVM751  *        *  RACCORDARE SOLO I DIFETTI IDENTIFICATI IN OP.10     * *        * .                                                *
         *        *  N.B.: NON UTILIZZARE UTENSILI ABRASIVI CON MATRICE *
         *        *         DI INCOLLAGGIO VETRIFICATA.                 *
         *        *                                                     *
         *        *  REQUISITI:                                         *
         *        *                                                     *
         *        *  1) ASPORTARE IL MINIMO MATERIALE NECESSARIO ALLA   *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 5 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   5
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *     RIMOZIONE DEL DIFETTO.                           * *        *                                                  *
         *        *  2) LA LARGHEZZA DELLA RACCORDATURA DEV'ESSERE PARI *
         *        *     AD ALMENO 30 VOLTE LA PROFONDITA'.              *
         *        *                                                     *
         *        *  3) LA SEPARAZIONE FRA DUE AREE RACCORDATE          *
         *        *     DEV'ESSERE PARI AD ALMENO 0,5 VOLTE LA SEMI-    *
         *        *     LUNGHEZZA MAGGIORE DELLE DUE RACCORDATURE.      *
         *        *                                                     * *        *  4)  LE AREE RACCORDATE DEVONO AVERE              *
*        *     RUGOSITA DELLE AREE CIRCOSTANTI DIFFERENTI.              * *        *      APPROSSIMATIVAMENTE, LA GEOMETRIA E LA      *

         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  BLEND ONLY THE DEFECTS IDENTIFIED IN OP.10         *
         *        *  .                                                  *
         *        *  N.B.: DO NOT USE ABRASIVES THAT INCLUDES A         *
         *        *        VITRIFIED BOND MATRIX.                       *
         *        *                                                     *
         *        *  REQUIREMENTS:                                      *
         *        *                                                     *
         *        *  1) REMOVE THE MINIMUM AMOUNT OF PARENT MATERIAL TO *
         *        *     REMOVE THE DEFECT.                              *
         *        *                                                     *
         *        *  2) THE LENGTH OF THE BLENDED AREA SHOULD BE AT     *
         *        *     LEAST 10 TIMES THE DEPTH.                       *
         *        *                                                     *
         *        *  3) SPACING BETWEEN TWO BLENDING REPAIRS MUST BE AT *
         *        *     LEAST 1,5X THE LARGEST REPAIR SEMI-LENGTH.      *
         *        *                                                     *
         *        *  4) BLENDED AREA SHOULD MAINTAIN APPROXIMATELY      *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 6 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   6
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
BA/766  * 030    *     THE ORIGINAL CONTOUR OF THE BLADE AND THE        * *        *     ROUGHNESS OF THE ADJACENT AREAS.             *
         *        *  * ATTREZZATURA PREVISTA *                          * SP.ORIG. 70-60-00-350-005     SP.FIAT
------------------------------------------------------------------------------ *        *  M8225079        LOCATORE CMM BLADE GENX         *
BA/662  * 040    *                                                      *
AVM751  *        *  ATTACCO CHIMICO A TAMPONE DELLE SUPERFICI           * *        *  RACCORDATE.                                     *
         *        *                                                     *
         *        *  MATERIALE BASE: GAMMA TIAL                         *
         *        *                                                     *
         *        *  ETCHANT: CLASS A                                   *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  SWAB ETCH THE BLENDED AREAS                        *
         *        *                                                     *
         *        *  BASE MATERIAL: GAMMA TIAL                          *
         *        *                                                     *
SCHEDA : CPEC522-BR SP.ORIG. 70-24-00-110-033     SP.FIAT *        *  ETCHANT: CLASS I                            *
------------------------------------------------------------------------------
I1439   * 050    *                                                      *
AVM758  *        *  ISPEZIONE LOCALE CON LIQUIDI PENTERANTI             * *        *  FLUORESCENTI DELLE AREE RACCORDATE.             *
         *        *                                                     *
         *        *  LIMITI DI ACCETTABILITA':                          *
         *        *                                                     *
         *        *  1)SONO AMMESSE CRICCHE        *       * *        *
                                                   * *                *
       *******  CONTINUA ALLA PAGINA SEGUENTE  ******     *
------------------------------------------------------------------------------
                                                     *** C O N T I N U A ***
```

#### Pagina 7 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   7
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/080  * 050    *  2) NON SONO AMMESSE INDICAZIONI LINEARI             * *        *     INTERPRETABILI, SE NON DIVERSAMENTE          *
         *        *     SPECIFICATO.                                    *
         *        *                                                     *
         *        *  3) NON SONO AMMESSE INDICAZIONI PASSANTI           *
         *        *                                                     *
         *        *  4) POSSONO ESSERE UTILIZZATI INGRANDIMENTI SINO 4X *
         *        *     SOLO COME RIFERIMENTO                           *
         *        *                                                     *
         *        *  NOTA: UN INDICAZIONE VIENE DEFINITA LINEARE SE HA  *
         *        *        LUNGHEZZA PARI AD ALMENO 4 VOLTE LA SUA      *
         *        *        LARGHEZZA                                    *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  LOCAL FPI INSPECTION OF THE BLENDED AREAS.         *
         *        *                                                     *
         *        *  ACCEPTABILITY LIMITS:                              *
         *        *                                                     *
         *        *  (1)INDICATIONS LESS THAN 0.015 INCH (0.38 MM) ARE  *
         *        *     NON-INTERPRETABLE AND NEED NOT TO BE EVALUATED. *
         *        *                                                     *
         *        *  (2) NO INTERPRETABLE LINEAR INDICATION IS          *
         *        *      PERMITTED, UNLESS SPECIFIED DIFFERENTLY.       *
         *        *                                                     *
         *        *  (3) NO THROUGH INDICATIONS ARE PERMITTED.          *
         *        *                                                     *
         *        *  (4) MAGNIFICATION NOT TO EXCEED 4X CAN BE USED FOR *
         *        *       REFERENCE PURPOSES ONLY.                      *
         *        *                                                     *
         *        *  NOTE: A LINEAR INDICATION IS DEFINED AS ONE HAVING *
         *        *        A LENGTH OF MORE THAN 4 TIMES ITS WIDTH.     *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 8 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   8
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
SCHEDA : SLP-05     SP.ORIG. 70-32-03-230-002 D   SP.FIAT
------------------------------------------------------------------------------ *        *                              D.T.    08-08-24  *
ZC/095  * 060    *                                                      *
AVM75A  *        *  ISPEZIONE VISIVA DELLE AREE RACCORDATE CON LENTE    * *        *  10X.                                            *
         *        *                                                     *
         *        *  VERIFICARE CHE SIANO STATI COMPLETAMENTE RIMOSSI I *
         *        *  DIFETTI IDENTIFICATI IN OP.10 E CHE SIANO          *
         *        *  RISPETTATI I REQUISITI DEL DETTAGLIO TECNICO.      *
         *        *                                                     *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *                                                     *
         *        *  VISUAL INSPECTION OF THE BLENDED AREAS WITH        *
         *        *  MAGNIFICATION 10X.                                 *
         *        *                                                     *
         *        *  VERIFY THE COMPLETE REMOVAL OF THE DEFECTS         *
         *        *  IDENTIFIED IN OP.10 AND REQUIREMENTS OF THE        *
------------------------------------------------------------------------------ *        *  TECHNICAL DATA SHEET.                           *
BA/777  * 070    *                                                      * *        *                              D.T.    09-07-19  *
AVM75A  *        *  PRESERVARE COMPONENTE COME DA SEZIONE DT            * *        *  PRESERVAZIONE RICHIAMATA IN TESTATA O.L.        *
------------------------------------------------------------------------------
ZC/095  * 075    *                                                      *
AVM75A  *        *  COLLAUDO FINALE, DOCUMENTALE E VERSAMENTO.          * *        * .                                                *
         *        *  * * * * * * * * * * * * * * * * * * * * * * * * *  *
         *        *  .                                                  *
         *        *  DO A GENERAL VISUAL INSPECTION OF THE PART AND     *
         *        *  A CHECK OF THE RELATED DOCUMENTATION.              *
------------------------------------------------------------------------------ *        *  ******* CONTINUA ALLA PAGINA SEGUENTE ******     *
                                                     *** C O N T I N U A ***
```

#### Pagina 9 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.   9
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================

==============================================================================
TARGA   * NUM.   *   DESCRIZIONE  OPERAZIONE                            *
C.RESP. * OPER   *                                                      * PRE *        *                                                  *
------------------------------------------------------------------------------ *        *  ***  CONTINUAZIONE DALLA PAGINA PRECEDENTE  ***  *
ZC/095  * 075    *  COMPILARE COME DA MODULO BQP.08.42.06 - "CHECKLIST  * *        *  FINAL INSPECTION".                              *
==============================================================================
RIP: A1 OEM: GEK112862                   CHANGE: 40        DEL :31/10/2024 FIRMATO DA: [NOME OMESSO]        09/12/2024
FIRMA AUTORE
FIRMA TECN.GIE PRODOTTO [NOME OMESSO]           12-12-2024
FIRMA ANALISI LAVORO    [NOME OMESSO]           12-12-2024
FIRMA LABORATORIO
FIRMA QUALITA'
```

#### Pagina 10 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.  10
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
MODIFICHE DELLA RIPARAZIONE N.MOD. MODIFICA                                 DATA       INSERITA DA
==============================================================================
```

#### Pagina 11 di 11

```text
 PGM PVRM320                          DATA STAMPA 11-11-2025 PAG.  11
  ** C I C L O    D I   L A V O R A Z I O N E **    *** SENZA TEMPI ***
CICLO :   GXRC-72560010A190-1       DESCR.CICLO : GENX-1B LPT BLADE STAGE 7
TIPO CICLO : NORMALE                PROGETTO...   GENX-1B/GENX-2B
DISEGNO..                           TIPO CICLO.   R
STATO... AGG.ALTR.UT.               NOTE.......
RIPARAZIONE : A1                    BLENDING 70-42-00-350-002
==============================================================================
STORICO DELLE VALIDAZIONI
VERSIONE COD.VALIDAZ.               DATA VALID UTENTE
------------------------------------------------------------------------------
```

---
