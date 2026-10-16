import hashlib
import json
import os
import tempfile
import unittest

import analisi_legge1 as A
import congela_legge1 as C


def righe_b(task, successi_per_spinta, vel=0.004, spinte=A.SPINTE):
    """Come la fase B vera: una riga per episodio, scena 15 + ep, stesso stato iniziale a tutte le spinte."""
    out = []
    for cm, k in zip(spinte, successi_per_spinta):
        for i, s in enumerate(A.SCENE_B):
            out.append({"task": task, "organo": "spinta", "perturba": False, "ritardo": 0, "lento_k": 8,
                        "n_direzioni": 5, "spinta_cm": cm, "ep": i, "stato_iniziale": s, "direzione": s % 5,
                        "hash_stato": f"{task}|{s}", "successo": i < k, "vel_finale_xy": vel, "passi": 120})
    return out


def dati_completi():
    """Stessa curva di successo per tutte, velocità crescente: T̂ decresce lungo ABILITA."""
    righe = []
    for j, task in enumerate(A.ABILITA):
        righe += righe_b(task, [5, 5, 4, 2, 1, 0], vel=0.002 + 0.0005 * j)
    return righe


def scrivi(cartella, nome, righe):
    p = os.path.join(cartella, nome)
    with open(p, "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(r) + "\n" for r in righe))
    return p


class TestCongela(unittest.TestCase):
    def test_dati_completi_nessun_problema_e_classifica_in_ordine(self):
        righe = dati_completi()
        self.assertEqual(C.controlli(righe), [])
        valide, escluse = C.classifica(A.previsione(righe))
        self.assertEqual((valide, escluse), (list(reversed(A.ABILITA)), []))

    def test_cella_mancante_e_ripetuta(self):
        righe = dati_completi()
        tolta = righe.pop(7)
        righe.append(dict(righe[0]))
        problemi = C.controlli(righe)
        self.assertTrue(any(p.startswith("manca:") and f"scena {tolta['stato_iniziale']}" in p for p in problemi))
        self.assertTrue(any(p.startswith("ripetuta 2 volte") for p in problemi))

    def test_stato_iniziale_diverso_tra_le_spinte(self):
        righe = dati_completi()
        righe[12]["hash_stato"] = "diverso"
        self.assertTrue(any("stato iniziale diverso" in p for p in C.controlli(righe)))

    def test_scene_diverse_con_lo_stesso_stato(self):
        righe = [{**r, "hash_stato": "uguale"} if r["task"] == A.ABILITA[3] else r for r in dati_completi()]
        self.assertTrue(any("scene diverse con lo stesso stato" in p for p in C.controlli(righe)))

    def test_episodio_scena_e_direzione_non_allineati(self):
        righe = dati_completi()
        del righe[3]["direzione"]  # riga come quelle della fase B in corso: vale il controllo sull'episodio
        righe[3]["ep"] = 0
        righe[4]["direzione"] = 0
        righe[5]["ep"] = 0  # con la direzione scritta, l'episodio non conta (riprese parziali)
        self.assertEqual(sum("non allineati" in p for p in C.controlli([righe[5]])), 0)
        problemi = C.controlli(righe)
        self.assertTrue(any("non allineati" in p for p in problemi))
        self.assertTrue(any("direzione" in p for p in problemi))

    def test_tre_censurate_richiedono_la_fase_b2(self):
        righe = []
        for j, task in enumerate(A.ABILITA):
            righe += righe_b(task, [5] * 6 if j < 3 else [5, 5, 4, 2, 1, 0])
        self.assertTrue(any("fase B2" in p for p in C.controlli(righe)))
        for task in A.ABILITA[:3]:
            righe += righe_b(task, [3, 1], spinte=A.SPINTE_ESTESE)
        self.assertEqual(C.controlli(righe), [])
        self.assertTrue(A.previsione(righe)[A.ABILITA[0]]["griglia_estesa"])

    def test_rapporto_con_hash_comando_e_esclusa(self):
        righe = [r for r in dati_completi() if not (r["task"] == A.ABILITA[2] and r["spinta_cm"] == 16.0)]
        with tempfile.TemporaryDirectory() as d:
            p = scrivi(d, "b.jsonl", righe)
            comando = os.path.join(d, "cella_c.txt")
            with open(comando, "w", encoding="utf-8") as f:
                f.write("export FASE=C BUDGET=40000\n")
            vecchio = os.path.join(d, "codice_b")
            os.mkdir(vecchio)
            with open(os.path.join(vecchio, "organo_tatto.py"), "wb") as f:
                f.write(b"x = 1\r\n")
            testo, problemi = C.rapporto([p], [], vecchio, comando)
            atteso = C.sha256(p)
        self.assertTrue(problemi)
        self.assertIn("| esclusa | vino sopra il mobile |", testo)
        self.assertIn(f"| `b.jsonl` | `{atteso}` |", testo)
        self.assertIn("`analisi_legge1.py` (fine riga LF, per la fase C)", testo)
        self.assertIn("export FASE=C BUDGET=40000", testo)
        lf = hashlib.sha256(b"x = 1\n").hexdigest()
        self.assertIn(f"| `organo_tatto.py` (fine riga LF, eseguito nella fase B) | `{lf}` |", testo)
        self.assertIn("nessuna abilità censurata", testo)


if __name__ == "__main__":
    unittest.main()
