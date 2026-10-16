# Premessa: Legge 1 della freschezza su LIBERO-goal (versione 3, NON ancora congelata)

- **Versione 1:** 12/10/2026.
- **Versione 2:** 13/10/2026, dopo la revisione indipendente 1 (`revisioni/revisione_claude_legge1_1.md`).
- **Versione 3:** 13/10/2026 sera, dopo la revisione indipendente 2 (`revisioni/revisione_claude_legge1_2.md`, "pronto
  con correzioni minori"). È scritta mentre la fase B della versione 2 girava su Kaggle e **prima di vederne i dati**.
  La fase B non cambia; la v3 aggiunge le regole per i casi limite e fissa il cervello e la prova finale.

## Domanda

Si può prevedere, prima di provarlo, quali abilità di un robot soffrono di più quando il suo cervello (SmolVLA) diventa
lento? Bastano due misure prese a parte: il margine di precisione dell'abilità e la velocità della mano vicino alla
fine del gesto.

## Ipotesi principale (H1) e verdetto

- **Previsione:** T̂ = M / v.
- **Misura:** R = (k16 + ½) / (k0 + ½), dove k0 e k16 sono i successi su 20 episodi con ritardo 0 e con ritardo 16.
- **Ipotesi:** Spearman ρ(T̂, R) > 0.
- **p unilaterale esatto:** si contano tutte le n! permutazioni di R (n ≤ 10). Analisi principale e di sensibilità
  usano le stesse permutazioni, quindi danno lo stesso p quando non ci sono abilità censurate.
- **Regola di decisione:**
  1. Se dal ritardo 0 al ritardo 16 il successo totale (sulle abilità incluse) cala meno di 10 punti percentuali, la
     prova è **non informativa**: il ritardo non fa abbastanza danni da fare una classifica.
  2. Altrimenti H1 è **sostenuta** se p ≤ 0,05 sia nell'analisi principale sia in quella di sensibilità; **non
     sostenuta** se non lo è in nessuna delle due; **non concludente** se lo è in una sola.
- La legge è presentata come **previsione di una classifica**. Sul meccanismo non si conclude nulla: le sue misure
  sono solo esplorative (sotto).

## Fase B: margine e velocità (scene 15–19, mai usate)

- **Episodi:** spinta 0, 2, 4, 8, 12 e 16 cm, 5 episodi per spinta e per abilità, su 10 abilità.
- **Spinta:** il cervello vede la mano spostata nel piano xy. Le 5 direzioni equidistanti sono le stesse per tutte le
  abilità; la direzione è scena % 5 (nella fase B in corso coincide con il numero dell'episodio). Il cervello è
  fresco: ritardo 0, K = 8.
- **M:** si stima una curva non crescente (isotonica) del successo in funzione della spinta. M è la prima spinta in cui
  la curva scende a metà del valore a 0 cm, interpolata. Se non scende entro l'ultima spinta, l'abilità è "censurata"
  e M è uguale all'ultima spinta.
- **Fase B2, regola fissata prima dei dati:**
  - Se almeno 3 abilità sono censurate a 16 cm, prima del congelamento si misurano per quelle sole le spinte 24 e 32 cm
    (5 episodi, scene 15–19, stesso protocollo).
  - M si ricalcola sulla griglia 0–32 cm. Resta censurata (M = 32) solo un'abilità che non scende a metà neanche a
    32 cm.
  - Con meno di 3 censurate non si estende.
- **v:** mediana, sugli episodi riusciti a spinta 0, della velocità xy della mano nei 32 passi prima del primo
  successo: è la parte finale del gesto, non esattamente il contatto.
- **Esclusioni in B:** è esclusa un'abilità con dati incompleti, senza successi a spinta 0 (M non misurabile) o senza
  velocità misurabile.
- **Controlli di completezza:** esattamente 5 episodi, con scene distinte 15–19, per ogni spinta e abilità, dopo aver
  filtrato per organo, ritardo, K e direzioni.
- **Righe doppie** (stessa abilità, condizione e scena), in B come in C: conta la prima nell'ordine dei file; le altre
  si contano e si riportano.

## Fase C: prova decisiva (scene 25–44, mai usate)

- **Condizioni:** 20 episodi per abilità in ciascuna di tre condizioni:
  - ritardo 0 con K = 8;
  - ritardo 16 con K = 8;
  - controllo: ritardo 0 con K = 16.
- **Il controllo:** con ritardo 16 il cervello ripensa ogni 16 passi. Il controllo separa "piano vecchio" da "si
  ripensa meno spesso". Non entra in H1: serve come controllo negativo (sotto).
- **Esclusioni:**
  - un'abilità è esclusa se i dati di B o di C sono incompleti, oppure se k0 = 0;
  - con più di 3 escluse la prova non è valida e lo si riporta;
  - le esclusioni si contano su una lista fissa di 10 abilità (codice `ABILITA`).
- **Validità delle scene:**
  - se due scene diverse della stessa abilità partono dallo stesso stato iniziale (la scena non è stata impostata), la
    prova non è valida;
  - uno stato iniziale diverso tra le condizioni nella stessa scena si riporta come avviso.
- **Tempo e sessioni, regola fissata ora:**
  - Dal log della fase B si ricava s̄ = secondi del blocco ÷ 25, media dei 6 blocchi. Ogni blocco ha 25 episodi per
    processo; il log conta insieme i 50 episodi delle due GPU, ma i processi girano in parallelo.
  - Se 300 · s̄ · 1,1 + 900 ≤ 38.000 s, la fase C gira in una sola sessione con BUDGET = 40.000 s. Prima girano le due
    condizioni dell'ipotesi, poi il controllo.
  - Altrimenti si divide: C1 (ritardo 0 e 16, BUDGET = 40.000 s), poi C2 (controllo) in una seconda sessione.
- **Corse interrotte:** le abilità incomplete si ripetono con FASE=R (tutta la condizione per quelle abilità). Le righe
  doppie si scartano tenendo la prima, e si riporta tutto.
- **Unione dei file della fase C, regola fissata ora:**
  - ogni sessione dà un file con il proprio nome: `c_1.jsonl` (C o C1), `c_2.jsonl` (C2), `c_r1.jsonl`, `c_r2.jsonl`…
    (riprese);
  - l'analisi li legge nell'ordine in cui sono state eseguite le sessioni (numero di versione del notebook), così una
    riga ripetuta conta sempre quella della corsa originale;
  - l'hash di ciascun file si riporta con i risultati.
- **Stesso cervello e stesse librerie della fase B:**
  - il modello è fissato alla revisione `6721902bc4d61e50a3bfdb11dfb4cb626f05d102`. È quella usata in B: su Hugging
    Face non cambia dal 17/09/2025;
  - le librerie sono vincolate al `pip_freeze.txt` della fase B (file `vincoli.txt` nel dataset);
  - il log di Kaggle stampa gli hash del codice;
  - ogni differenza tra il pip freeze di B e quello di C si riporta.

## Analisi (codice `analisi_legge1.py`, 18 test in `test_analisi_legge1.py`)

- **Principale:** ρ di Spearman con ranghi medi per i pareggi, R con frazioni esatte, p unilaterale esatto. Si riporta
  anche un intervallo bootstrap al 95% (descrittivo, 10.000 campioni, seme 12102026).
- **Sensibilità:** le abilità censurate stanno tutte a pari merito in cima alla classifica di T̂.
- **Confronti, riportati senza cambiare il verdetto:**
  - ρ di M da solo;
  - ρ di 1/v da solo;
  - ρ del solo successo di base in B;
  - ρ parziale di T̂ a parità di successo di base. Risponde all'obiezione "sono solo le abilità difficili";
  - ρ tra i passi medi dei successi a 0 cm in B e R. Risponde all'obiezione "sono solo i compiti lunghi, che col
    ritardo arrivano al limite dei 300 passi". Per lo stesso motivo si riporta, per abilità, la quota di fallimenti per
    tempo scaduto con ritardo 16;
  - **controllo negativo:** ρ(T̂, R_K16), con R_K16 = (k_K16 + ½) / (k0 + ½). Se T̂ prevede R_K16 quanto R, la legge
    parla più di "ripensare meno spesso" che di "piano vecchio".
- **Meccanismo (solo esplorativo, nessuna conclusione):**
  - per ogni episodio con ritardo 16 si prendono i primi 6 arrivi di piano: scarto tra le azioni eseguite nell'attesa
    e quelle che il piano nuovo dava per fatte, e cambio tra piano vecchio e nuovo;
  - si fa la media per episodio, poi per abilità, e si calcola ρ con R;
  - solo i primi 6 arrivi, perché gli episodi falliti durano di più e hanno più arrivi (l'esito non deve entrare
    nella misura);
  - i valori sono somme sulle azioni confrontate, in numero fisso dentro la condizione, quindi i ranghi non cambiano.

## Potenza (simulazione `potenza_legge1.py`, 500 simulazioni, seme 1)

Il modello è semplice e dichiarato nel file. Usa la regola di decisione vera: fase B2, esclusioni, calo minimo e doppia
soglia. Il p è stimato con 2.000 permutazioni, mentre nella prova vera è esatto.

- **Legge vera del tutto:** potenza circa 0,52.
- **Legge vera in parte** (forza 0,7): potenza circa 0,35.
- In media 1,7 abilità risultano censurate a 16 cm, e la fase B2 scatta nel 25% delle simulazioni.
- La stima della v2 (0,60 e 0,41) era troppo ottimista: non applicava la doppia soglia né la censura (revisione 2).

**Anche se la legge è vera, c'è circa una probabilità su due di non vederla**: un risultato nullo non la smentisce.

## Cosa è già stato visto

- **Curve di sviluppo, scene 0–3:** ritardo 0 29/40, ritardo 8 24/40, ritardo 24 14/40. Sono solo totali: per abilità
  non sono state guardate, e non lo saranno prima di C.
- **Pilota, scene 4–6, compiti 0, 5 e 7:** spinte 0/3/6 cm, sotto.

  | Abilità | 0 cm | 3 cm | 6 cm |
  |---|---|---|---|
  | Cassetto | 3/3 | 3/3 | 1/3 |
  | Piatto | 3/3 | 3/3 | 2/3 |
  | Fornello | 3/3 | 3/3 | 3/3 |

- **Fase B vecchia, scene 10–14, su Kaggle:** è un pilota, non ancora guardato.
- **Durante la scrittura della v3** nessuno ha visto dati della fase B in corso.

## Previsioni delle persone

Le previsioni a parole in `PREVISIONI.md` sono di Emanuele ("per prima crolla la manopola del fornello") e di Claude
(stesso ordine). Si riportano come confronto descrittivo con la classifica della legge e non entrano in H1.

## Lavori precedenti (prima passata)

- **Persone:** MacKenzie e Ware 1993; Ware e Balakrishnan 1994 (il ritardo moltiplica la difficoltà dei bersagli
  piccoli).
- **Telechirurgia** (3GPP TR 22.826) e **velocità e separazione** nei robot collaborativi.
- **Esecuzione asincrona e real-time chunking:** Black e altri 2025; inferenza asincrona di SmolVLA.
- **"When Delay Meets Distribution Shift"** (NeurIPS 2026): conta la copertura del piano. Nel nostro cervello lento la
  copertura è garantita: D + max(K, D) ≤ 50, altrimenti il programma si ferma.
- **Self-Adaptive VLA** 2609.30092.
- **Cervelli che si appoggiano allo stato del robot** (2509.18644; ReViP 2601.16667): rende plausibile che M misuri
  anche quanto il cervello si fida della posizione "sentita" della mano.

## Limiti dichiarati

- Simulazione, un solo cervello, una sola famiglia di scene, 10 abilità.
- La spinta falsa solo la posizione sentita: le immagini restano fresche. Il ritardo invece invecchia tutto, quindi M
  può misurare anche "quanto il cervello si fida dello stato".
- Lo spostamento davvero ottenuto della mano non è misurato direttamente. La distanza mano-oggetto alla prima chiusura
  (`dist_mano_oggetto`, già registrata in B, solo per le abilità con un oggetto da prendere) serve da controllo
  descrittivo.
- Il revisore indipendente è un altro Claude in un contesto nuovo, non Codex, che è bloccato fino al 10/11: è meno
  indipendente.

## Al congelamento (commit prima della fase C)

**Fatto il 14/10/2026 alle 09:24:** `CONGELAMENTO_LEGGE1.md` (controlli senza problemi, classifica, hash, cella
della fase C), classifica copiata in `PREVISIONI.md`, commit con il tag `legge1-congelata`. Per la regola dei tempi
la fase C si divide in C1 e C2 (s̄ = 116,0 s).

- L'uscita di `congela_legge1.py`, in `CONGELAMENTO_LEGGE1.md`:
  - controlli dei dati;
  - classifica di T̂ e classifica di sensibilità;
  - hash di `b.jsonl` (e `b2.jsonl`), dei file `c_d*.jsonl` di sviluppo e del `pip_freeze.txt` di B;
  - hash del codice per la fase C e del codice eseguito nella fase B;
  - la cella esatta del notebook per la fase C (FASE, BUDGET, revisione del modello).
- La classifica copiata in `PREVISIONI.md`.
- **Prova esterna della data:**
  - l'hash di `CONGELAMENTO_LEGGE1.md` è stampato dalla cella della fase C;
  - il file sta nella versione del dataset usata da C;
  - Kaggle conserva le versioni con la loro data. La prova vale solo se la fase C gira come versione salvata del
    notebook ("Save & Run All", che conserva log e data), non in una sessione interattiva;
  - notebook e dataset si rendono pubblici insieme ai risultati.
- **Comando dell'analisi finale:** `python analisi_legge1.py test --c c_1.jsonl [--c c_2.jsonl …] --b b.jsonl
  [--b b2.jsonl]`; per il rapporto con i grafici, `python rapporto_legge1.py CARTELLA` con le stesse opzioni.

## Deviazioni

Ogni cambiamento dopo il congelamento va scritto qui, con data e motivo.

**13/10/2026, 21:35 — fase B incompleta, prima del congelamento.**
- **Cosa è successo:** la fase B (Kaggle, versione 5 del notebook, 16:49–20:51) ha prodotto dati solo dalla prima
  GPU, cioè per le abilità 0–4. Il processo della seconda GPU (abilità 5–9) si è fermato in ogni blocco con
  "MUJOCO_EGL_DEVICE_ID must be an integer between 0 and 0": con `CUDA_VISIBLE_DEVICES=1` il sistema grafico vede
  una sola scheda. La prova di fumo di allora accettava una sola riga (punto S8 della revisione 2, già corretto
  nella v3).
- **Cosa è stato visto:** la stampa finale della fase B per le abilità 0–4 (margine, velocità, tolleranza, successo
  a 0 cm, censura) e i conteggi e i tempi dei blocchi nel log. Per le abilità 5–9 non esistono dati. Nessun dato della
  fase C esiste.
- **Correzione:** le due GPU restano entrambe visibili, con la propria per prima (`CUDA_VISIBLE_DEVICES=G,1-G`), e
  il rendering usa l'indice EGL 0, che esiste sempre. Lo script si ferma se:
  - la prova di fumo non dà una riga per GPU;
  - il rendering non è EGL come nella fase B;
  - mancano gli ingressi della B-bis, o le sue abilità sono già nei dati precedenti;
  - la cartella di uscita non è vuota.
- **Revisioni dei modelli:** il log stampa le revisioni scaricate. Il processore del VLM (SmolVLM2-500M, revisione
  `7b375e1b…`, invariata dall'08/04/2025) si scarica senza revisione fissata: la revisione stampata si riporta con i
  risultati.
- **Completamento (fase B-bis), stesso protocollo:**
  - abilità 5–9, spinte 0–16 cm, scene 15–19, 5 direzioni, ritardo 0, K = 8;
  - stesso modello (revisione fissata) e librerie vincolate al `pip_freeze.txt` della fase B;
  - la regola della fase B2 si applica automaticamente a fine sessione, contando anche i dati delle abilità 0–4.
- **File:** `b_1.jsonl` = la fase B della versione 5 (abilità 0–4), `b_2.jsonl` = la B-bis, `b2.jsonl` =
  l'eventuale fase B2. L'analisi li legge in quest'ordine.
- **Tempi, regola fissata ora:** s̄ = secondi del blocco ÷ 15, media dei 6 blocchi `b_spinta` della B-bis, esclusi
  i blocchi B2. Nella B-bis il processo più carico fa 15 episodi per blocco (3 abilità × 5), e i due processi girano
  in parallelo come nella fase C. I blocchi della versione 5 avevano un solo processo attivo (circa 95 s per
  episodio) e non si usano per s̄.

**Codice cambiato dalla v3, prima del congelamento.** Nessuna di queste modifiche tocca la fase B in corso, che usa il
codice della v2 (dataset Kaggle versione 3, commit a524aa1); i suoi hash entrano nel congelamento.
- `organo_tatto.py`: la direzione della spinta si ricava dalla scena (identica per le scene 15–19); si salvano i primi
  12 valori del meccanismo per episodio.
- `kaggle_esegui.sh`:
  - revisione del modello e hash del codice nel log;
  - versioni delle librerie vincolate;
  - prova di fumo su entrambe le GPU;
  - fasi B2, C1, C2 e R.
- `analisi_legge1.py`:
  - p esatto;
  - righe doppie;
  - fase B2;
  - controlli e confronti della fase C;
  - meccanismo esplorativo;
  - più file della fase C, letti nell'ordine di esecuzione.
- `rapporto_legge1.py` (nuovo): verdetto, tabella e grafici decisi prima dei dati della fase C. Sono la classifica
  prevista contro quella osservata, T̂ contro R, i successi con e senza ritardo, e il controllo descrittivo della mano.

### 14/10/2026, 16:36: solo il testo del rapporto (dopo il congelamento)

- **Cosa è cambiato.** In `rapporto_legge1.py` (commit 0a93a5f) sono cambiate solo le parole del rapporto leggibile,
  come chiesto dalla verifica indipendente:
  - la descrizione della sensibilità;
  - i "punti percentuali";
  - una colonna sui fallimenti per tempo scaduto;
  - un avviso sul meccanismo;
  - la frase "C2 non ancora eseguita".
- **Cosa non è cambiato.** `analisi_legge1.py`, che dà il verdetto, è identico a quello congelato (sha256 f0bddd4d…).
- Questa nota è stata aggiunta il 16/10, su segnalazione del controllo indipendente del resoconto pubblico.
