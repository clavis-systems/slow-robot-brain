# Revisione indipendente 2 della premessa Legge 1 (13/10/2026, 18:18-18:41)

Revisore: un altro Claude (opus) in un contesto nuovo, in sola lettura, senza dati di B o di C. Sostituisce Codex,
bloccato fino al 10/11. Fatta mentre la fase B girava su Kaggle, prima di vederne i dati.
Verdetto: **PRONTO CON CORREZIONI MINORI.** B1-B4 vanno corretti prima del congelamento; nessuno richiede di rifare
la fase B. Sintesi fedele del rapporto.

## Cosa funziona già

- I comandi di FASE=C producono le righe che `test()` cerca (organo "nessuno", ritardo 0 e 16, lento_k 8, scene
  25-44, 20 episodi); le righe del controllo K=16 sono scartate correttamente.
- Spearman con ranghi medi, R con frazioni esatte, p unilaterale per permutazione, sensibilità e regola del verdetto
  fanno quello che dice il testo. cambio_piano e scarto_attesa confrontano le azioni giuste nel tempo. 20 test OK.

## Bloccanti

- **B1. Tempo della fase C** (kaggle_esegui.sh:5, 34, 63-65): 300 episodi per processo, circa 31.500 s a 105 s
  l'uno, più della BUDGET di 30.000 s. Il controllo K=16 verrebbe tagliato; un taglio colpisce sempre le ultime
  abilità di ogni lista (esclusioni non casuali). Correzione: secondi per episodio dai log di B; C divisa in due
  sessioni oppure BUDGET circa 40.000 se basta; comando per riprendere le coppie mancanti; regola sui duplicati
  (oggi una riga doppia esclude l'abilità, analisi:33-35).
- **B2. Confronto sul meccanismo non definito** (PREMESSA:21-22, 59-62): non dice condizione, statistica, criterio.
  Solo medie per episodio (organo_tatto.py:234-237); gli episodi falliti hanno più arrivi di piano, quindi il legame
  scarto-R può venire dall'esito; cervello_lento.py:38 somma su K azioni (con K=16 raddoppia). Correzione: definire
  la regola oppure dichiarare il meccanismo solo esplorativo.
- **B3. Nessuna regola se B è poco informativa** (PREMESSA:18-20, 28-31): con molte abilità censurate l'analisi
  principale misura solo 1/v; decidere ora una regola o un'estensione (24 e 32 cm solo per le censurate).
  potenza_legge1.py:36 non applica la doppia soglia: con circa 5 censurate la potenza scende a 0,36 (legge vera) e
  0,33 (vera in parte).
- **B4. Stesso sistema in B e in C, prova per chi legge da fuori** (kaggle_esegui.sh:6, 12-14, 24): modello scaricato
  senza revisione, librerie non fissate, nessuna traccia su Kaggle del codice eseguito, nessuna data verificabile
  del congelamento. Correzione: `--revision`, confronto con pip_freeze di B, hash del codice stampati all'avvio,
  data verificabile del congelamento prima di C.

## Suggeriti

- **S1** (analisi:153-157): p principale e di sensibilità con permutazioni diverse; caso trovato con pareggi:
  ρ = 0,555, p = 0,0492 contro 0,0500, verdetto "non concludente" per caso. Usare le stesse permutazioni o il p esatto.
- **S2**: per C mancano i controlli di congela (stesso hash_stato tra condizioni nella stessa scena, hash diversi tra
  scene).
- **S3** (organo_tatto.py:102): la direzione della spinta dipende dall'episodio, non dalla scena; usare
  `stato_iniziale % N_DIREZIONI` (uguale per la B in corso) e scriverla nella riga.
- **S4** (congela_legge1.py): mancano il comando di C e dell'analisi, l'hash di pip_freeze, la classifica di
  sensibilità, gli hash del codice di B se il codice cambia, il controllo "hash diversi tra scene"; copiare la
  classifica in PREVISIONI.md.
- **S5**: spiegazione alternativa dei compiti lunghi (limite dei 300 passi con il ritardo): aggiungere ρ(passi dei
  successi a 0 cm, R), quota di fallimenti per tempo scaduto, ρ(T̂, R con K=16) come controllo negativo.
- **S6** (testi): esclusione per M o v non misurabili; numero di simulazioni e seme della potenza (0,55/0,43 con 300,
  0,57/0,37 con 1000); previsioni secondarie di PREVISIONI.md; "spostamento davvero ottenuto" tra i limiti
  (dist_mano_oggetto come controllo descrittivo).
- **S7**: test per "non concludente", censurate, k0 = 0, duplicati.
- **S8**: la prova di fumo passa con una sola GPU (richiedere 2 righe); `fumo.log` non esiste (sono fumo_g0/g1.log);
  riassunto.py mescola le tre condizioni; import inutile in analisi.

## Verifica della prima revisione

| Punto | Stato | Motivo |
|---|---|---|
| B1 | risolto | lista fissa, controlli, frazioni esatte, p per permutazione (resta S2) |
| B2 | risolto | spinte fino a 16 cm, sensibilità, "non concludente" (manca B3) |
| B3 | in parte | classifica e misure del piano ci sono; "spostamento ottenuto" rinviato; confronto non definito |
| B4 | in parte | 20 episodi, R stabilizzato, confronti ci sono; la potenza ignora doppia soglia e censura |
| S1 | risolto | piano xy, solo successi; "32 passi prima del successo" non è "al contatto": va detto |
| S2 | risolto | direzioni fisse, curva isotonica (vedi S3) |
| S3 | in parte | hash dello stato, limite delle scene e pip freeze ci sono; nessuna prova del codice eseguito su Kaggle |
| S4 | in parte | 14/40 corretto nella premessa (PREVISIONI.md dice ancora "parziale"); congela non dà il comando di C |
| S5 | in parte | il controllo K=16 c'è ma sarebbe tagliato (B1); cambio_piano non confrontabile tra K diversi |
| S6 | in parte | citazioni presenti; quelle del 2026 non verificabili dal revisore |
