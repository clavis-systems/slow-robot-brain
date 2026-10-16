# Congelamento della previsione della Legge 1

Dati della fase B: `b_1.jsonl`, `b_2.jsonl`, 300 episodi.

## Controlli dei dati

- nessun problema: tutte le celle abilità × spinta × scena (15-19) presenti una volta, ogni scena con lo stesso stato iniziale a tutte le spinte, scene diverse con stati diversi

## Classifica prevista (T̂ = M / v, dalla più fragile alla più robusta)

| Posto | Abilità | M (cm) | v (mm/passo) | T̂ (passi) | Successo a 0 cm | Successi per spinta |
|---|---|---|---|---|---|---|
| 1 | cassetto in alto e ciotola dentro | 1.00 | 8.26 | 1.21 | 20% | 0: 1 / 2: 0 / 4: 0 / 8: 0 / 12: 0 / 16: 0 |
| 2 | ciotola sul piatto | 2.00 | 5.70 | 3.51 | 100% | 0: 5 / 2: 2 / 4: 3 / 8: 1 / 12: 1 / 16: 0 |
| 3 | ciotola sul fornello | 5.00 | 7.68 | 6.51 | 100% | 0: 5 / 2: 5 / 4: 3 / 8: 1 / 12: 1 / 16: 1 |
| 4 | formaggio nella ciotola | 2.75 | 4.06 | 6.77 | 100% | 0: 5 / 2: 4 / 4: 0 / 8: 0 / 12: 0 / 16: 0 |
| 5 | ciotola sopra il mobile | 7.00 | 7.59 | 9.22 | 100% | 0: 5 / 2: 5 / 4: 4 / 8: 2 / 12: 0 / 16: 0 |
| 6 | spingi il piatto | 8.33 | 4.89 | 17.04 | 60% | 0: 3 / 2: 4 / 4: 4 / 8: 2 / 12: 0 / 16: 0 |
| 7 | vino sopra il mobile | 10.93 | 6.10 | 17.91 | 80% | 0: 4 / 2: 4 / 4: 5 / 8: 4 / 12: 1 / 16: 2 |
| 8 | apri il cassetto centrale | 12.00 | 5.68 | 21.11 | 80% | 0: 4 / 2: 4 / 4: 4 / 8: 3 / 12: 2 / 16: 2 |
| 9 | vino sulla rastrelliera | ≥ 16.00 (censurata) | 6.69 | 23.92 | 20% | 0: 1 / 2: 2 / 4: 0 / 8: 2 / 12: 0 / 16: 2 |
| 10 | accendi il fornello (manopola) | 14.00 | 0.68 | 205.88 | 100% | 0: 5 / 2: 3 / 4: 5 / 8: 5 / 12: 3 / 16: 2 |

Analisi di sensibilità: le censurate (vino sulla rastrelliera) vanno tutte a pari merito in cima alla classifica, le altre restano nell'ordine sopra.

## Comando esatto della fase C (cella del notebook Kaggle)

```
%%bash
export MPLBACKEND=Agg FASE=C1 BUDGET=40000
bash "$(find /kaggle/input -name kaggle_esegui.sh)" 2>&1 | tee /kaggle/working/esecuzione.log
```

## Hash SHA-256

| File | SHA-256 |
|---|---|
| `b_1.jsonl` | `de8ccd6d51ad7258217a57da99f2e125b51f0893683d7d2baee1d760220ab401` |
| `b_2.jsonl` | `197919dd81f140e2d71ce556347e86079c538d247d38a0ef40d105d2a077d3c6` |
| `c_d0.jsonl` | `c6bfde2d2b95d59c6bdd2c0073893ba514f03d34f54c9f6a16b23078f3993945` |
| `c_d8.jsonl` | `c4747a426858fcc983284d1702af65ee11cc45c4236ee75fb1a6f41f2fdd9514` |
| `c_d24.jsonl` | `fe1ca92a8a6af4db93cafb04bb13efd28bbdbdd9ab96b7cc28c17a465941ab45` |
| `pip_freeze_fase_b.txt` | `db78729ba9d128e44b0531be09e2785c71486e7b8c037acaa0e930dcf9fa7104` |
| `analisi_legge1.py` (fine riga LF, per la fase C) | `f0bddd4d190cb46fbc4b7ac9458a097fc28e190282c8ae849b0746a7045ced4d` |
| `kaggle/kaggle_esegui.sh` (fine riga LF, per la fase C) | `e848594ed259d2a3ee0d7ff9170f52ad2149f7c61488b8a38804cb3934370bce` |
| `organo_tatto.py` (fine riga LF, per la fase C) | `fcd5c56f52424ac83d09ac92845c651ee2c6202702e06508766237395fbea0ee` |
| `cervello_lento.py` (fine riga LF, per la fase C) | `3aa3cf3453d24e421448082621aac73617cff6e8253b1fb76bf8780b6b067875` |
| `riassunto.py` (fine riga LF, per la fase C) | `db489246c6c19dc5daffbc4753938860acba4db8f6291251e79e394a4f09cd13` |
| `congela_legge1.py` (fine riga LF, per la fase C) | `8c794fdaa31c9192d2bac2d161ba0284640e29c5c540b2978ffaccb63caaee86` |
| `analisi_legge1.py` (fine riga LF, eseguito nella fase B) | `1219ba32bdf9aa9db1cef854d4edb4a30b092b7e67a2250e1ab40da084f9c96a` |
| `cervello_lento.py` (fine riga LF, eseguito nella fase B) | `3aa3cf3453d24e421448082621aac73617cff6e8253b1fb76bf8780b6b067875` |
| `kaggle_esegui.sh` (fine riga LF, eseguito nella fase B) | `648a11c2d87a4b759e3ce145ad57501949d9001625d44eb1a1a677db25cd9a33` |
| `organo_tatto.py` (fine riga LF, eseguito nella fase B) | `3d5a2dde3d262092b70290a7a0d6dc03e597c36f03e57d54cec2fd265f6bd405` |
| `riassunto.py` (fine riga LF, eseguito nella fase B) | `db489246c6c19dc5daffbc4753938860acba4db8f6291251e79e394a4f09cd13` |
| `riassunto_b.py` (fine riga LF, eseguito nella fase B) | `d4141c2f4acc5be05d6d9b6e837c4a0e249e59bd066f983950f46078258012c8` |

## Note

- **Codice eseguito nella fase B:** la versione 5 del notebook (abilità 0–4) ha usato il codice della v2 (commit
  a524aa1, hash "eseguito nella fase B" qui sopra). La versione 6, cioè la B-bis (abilità 5–9), ha usato lo stesso
  codice della fase C: gli hash stampati nel suo log Kaggle coincidono con quelli "per la fase C".
- **Revisioni dei modelli** stampate dalla B-bis: smolvla_libero `6721902bc4d61e50a3bfdb11dfb4cb626f05d102`, processore
  SmolVLM2-500M `7b375e1b73b11138ff12fe22c8f2822d8fe03467`.
- **Regola dei tempi della fase C:** s̄ = media dei 6 blocchi della B-bis ÷ 15 = 116,0 s per episodio;
  300 · s̄ · 1,1 + 900 = 39.184 s > 38.000 s, quindi la fase C si divide. Prima C1 (ritardo 0 e 16, cella qui sopra,
  file `c_1.jsonl`), poi C2 (controllo K = 16, stessa cella con `FASE=C2`, file `c_2.jsonl`).
- **Fase B2:** non serve, c'è una sola abilità censurata (ne servono almeno 3).
- **Previsioni delle persone** (descrittive, fuori da H1): Emanuele aveva previsto che la manopola del fornello
  crollasse per prima; la legge la mette ultima, cioè la più robusta.
