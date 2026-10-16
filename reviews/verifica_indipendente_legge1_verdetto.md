# Verifica indipendente del verdetto della Legge 1 (14/10/2026, circa 16:30)

**Chi:** un altro Claude (opus) in un contesto nuovo. Ha rifatto tutti i calcoli da zero partendo solo da
`PREMESSA_LEGGE1.md` (v3), `CONGELAMENTO_LEGGE1.md` e dai dati grezzi (`dati/b_1.jsonl`, `dati/b_2.jsonl`,
`dati/c_1.jsonl`), e ha aperto il nostro codice solo alla fine. È meno indipendente di Codex, bloccato fino al 10/11.

**Esito: CONFERMATO, nessuna discrepanza.**
- Le impronte dei dati e di `analisi_legge1.py` coincidono con quelle congelate.
- Nessuna riga doppia, nessuna esclusione, nessun avviso.
- Tutti i numeri coincidono:

| Grandezza | Ricalcolo | Rapporto |
|---|---|---|
| ρ principale | 0,3697 | 0,370 |
| p esatto | 536445/3628800 = 0,1478 | 0,1478 |
| ρ sensibilità | 0,2848 | 0,285 |
| p sensibilità | 774897/3628800 = 0,2135 | 0,2135 |
| Calo totale | (136 − 81)/200 = 27,5 punti | 27,5 |
| Verdetto | H1 non sostenuta | H1 non sostenuta |
| Meccanismo: cambio piano / scarto d'attesa | −0,7455 / −0,503 | −0,75 / −0,50 |

## Note da riportare con il risultato

1. **Analisi di sensibilità.**
   - Il codice congelato mette le abilità censurate a T̂ = +∞, cioè tra le più robuste. È la lettura coerente con la
     premessa ("in cima alla classifica di T̂"), perché per una censurata M ≥ 16 è solo un minimo.
   - Il file del congelamento però dice "in cima alla classifica" subito dopo una tabella ordinata dalla più fragile,
     e si potrebbe leggere al contrario. Con quella lettura la sensibilità darebbe ρ = 0,588 e p = 0,0403, e il
     verdetto sarebbe "non concludente".
   - Vale il codice congelato, con il suo hash, fissato prima della fase C.
2. **Il meccanismo dipende dalla durata degli episodi.**
   - Con il ritardo 16 gli episodi riusciti hanno spesso solo 3–5 arrivi di piano, quelli falliti sempre 12.
   - Usando i primi 3 arrivi, che hanno tutti gli episodi, i valori scendono: −0,19 per il cambio di piano, −0,32 per
     lo scarto d'attesa.
   - Il −0,75 viene in gran parte dalla durata, quindi non è un segnale forte della Legge 2. Resta esplorativo.
3. **Tempo scaduto.** Con il ritardo 16 tutti i fallimenti di tutte e 10 le abilità finiscono a 300 passi. La quota
   per abilità è in `risultato.json`, ma non nel rapporto leggibile.
4. **Dettagli.**
   - Il 27,5 sono punti percentuali.
   - Il controllo K = 16 manca perché la fase C2 non era ancora stata eseguita.
