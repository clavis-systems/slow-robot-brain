# Revisione indipendente 1 della premessa Legge 1 (13/10/2026)

Revisore: un altro Claude (opus) in un contesto nuovo, in sola lettura. Sostituisce Codex, bloccato fino al 10/11.
Verdetto: **NON PRONTA**. Sintesi fedele; il testo completo è nella trascrizione della sessione.

## Problemi bloccanti

- **B1. Validità dell'analisi.**
  - Un'abilità a cui manca un livello viene scartata in silenzio.
  - La soglia fissa ρ ≥ 0,56 vale solo con n = 10.
  - Mancano i controlli su episodi, scene, organo e K.
  - R calcolato in virgola mobile rompe i pareggi.
  - Correzione: lista fissa delle abilità, controlli di completezza, frazioni esatte, decisione con il p di
    permutazione.
- **B2. Censura a 8 cm** incoerente con la fase B2 e con il pilota (fornello 3/3 a 6 cm).
  - Correzione: spinte fino a 16 cm decise prima di vedere B, più un'analisi di sensibilità con le censurate in
    cima. Se i due verdetti differiscono: "non concludente".
- **B3. La spinta non è il ritardo.**
  - Le immagini restano fresche.
  - Nel cervello lento l'errore non viene da v·D ma dal salto tra un piano e l'altro.
  - Indizio: con ritardo 24, 14/40, nonostante T̂ di circa 7–11 passi.
  - Correzione: misurare il meccanismo (lo spostamento davvero ottenuto e lo scarto al cambio di piano) e presentare H1
    come previsione di una classifica.
- **B4. Poca potenza e spiegazione alternativa** ("sono le abilità difficili").
  - Correzione: una simulazione di potenza; almeno 20 episodi per condizione in C; R stabilizzato; confronti con M da
    solo, 1/v, successo di base e ρ parziale.

## Suggerimenti

- **S1:** velocità vicino al contatto, solo negli episodi riusciti, nel piano xy.
- **S2:** stesse direzioni equidistanti per tutte le abilità; M stimato con una curva monotona.
- **S3:**
  - hash dello stato iniziale;
  - un controllo sulle scene oltre il limite;
  - `pip freeze`;
  - ricaricare la cartella dei file per Kaggle.
- **S4:** correggere il dato "ritardo 24 parziale" (è 14/40); hash e regole nel commit di congelamento.
- **S5:** il controllo ritardo 0 con K = 16, perché con ritardo 16 il cervello ripensa ogni 16 passi.
- **S6:** citare l'inferenza asincrona di SmolVLA e il real-time chunking; verificare le citazioni del 2026.

## Cosa è stato fatto (13/10)

Tutto quanto sopra tranne:
- la misura dello "spostamento davvero ottenuto" della mano in B, rimandata;
- la variante con più ritardi (S5 facoltativo), non fatta.

Riferimenti: `analisi_legge1.py` (8 test), `cervello_lento.py` (misure del meccanismo, 7 test), `organo_tatto.py`,
`potenza_legge1.py`, `kaggle/kaggle_esegui.sh`, `PREMESSA_LEGGE1.md` versione 2.
