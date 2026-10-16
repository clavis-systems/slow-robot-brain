# Legge 1 della freschezza: risultato finale (14/10/2026, 22:55)

L'analisi è quella congelata (`analisi_legge1.py`, sha256 f0bddd4d…), con la previsione congelata il 14/10 alle 09:24
(commit 3a96427, tag `legge1-congelata`).

## Dati

| File | Fase (versione Kaggle) | Righe | sha256 |
|---|---|---|---|
| `dati/b_1.jsonl` | B (v5) | 150 | de8ccd6d51ad7258… |
| `dati/b_2.jsonl` | B-bis (v6) | 150 | 197919dd81f140e2… |
| `dati/c_1.jsonl` | C1: ritardo 0 e 16, K = 8 (v7) | 400 | 9e01f980e7318bdd… |
| `dati/c_2.jsonl` | C2: controllo, ritardo 0 con K = 16 (v8, 2 h 36 min) | 200 | 7c5c58f20275d0af7886d02cde697c41aac1bfdc75d78976c600ce84e7390d23 |

Nel log della v8 le impronte di `analisi_legge1.py`, `kaggle_esegui.sh` e `CONGELAMENTO_LEGGE1.md` coincidono con
quelle congelate.

## Risultato

- **Verdetto: H1 non sostenuta.** ρ = 0,370, p unilaterale esatto = 0,1478 (n = 10).
- **Sensibilità:** ρ = 0,285, p = 0,2135.
- **Calo totale da ritardo 0 a ritardo 16:** 27,5 punti percentuali, quindi la prova è informativa.
- **Controllo negativo (ritardo 0, K = 16):** ρ(T̂, R_K16) = −0,12 su 10 abilità. Senza ritardo, T̂ non prevede
  l'effetto di K, come atteso: il controllo non segnala correlazioni spurie. Successi con K = 16: 147/200.
- **Meccanismo, solo esplorativo:** −0,75 per il cambio di piano e −0,50 per lo scarto d'attesa. Dipende in gran
  parte dalla durata degli episodi: con i primi 3 arrivi i valori sono −0,19 e −0,32. Vedi
  `revisioni/verifica_indipendente_legge1_verdetto.md`.
- **Verifica indipendente del verdetto:** confermato (Claude nuovo, 14/10). Codex lo ricontrollerà quando torna
  disponibile, dal 10/11.
