import json
import os
import tempfile
import unittest

import analisi_legge1 as A
import rapporto_legge1 as RP
import test_analisi_legge1 as TA


def scrivi(cartella, nome, righe):
    p = os.path.join(cartella, nome)
    with open(p, "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(r) + "\n" for r in righe))
    return p


class TestRapporto(unittest.TestCase):
    def test_piu_file_c_nell_ordine_di_esecuzione(self):
        b, c = TA.TestTest()._scenario(True, k_ctrl=18)
        for r in b:
            r["dist_mano_oggetto"] = round((r["spinta_cm"] * 0.8 + 1) / 100, 4)
        sessione1 = [r for r in c if r["lento_k"] == 8]
        sessione2 = [r for r in c if r["lento_k"] == 16]
        ripresa = [{**r, "successo": not r["successo"]} for r in sessione1[:20]]  # doppie: conta la sessione 1
        with tempfile.TemporaryDirectory() as d:
            pb = scrivi(d, "b.jsonl", b)
            pc = [scrivi(d, "c_1.jsonl", sessione1), scrivi(d, "c_2.jsonl", sessione2), scrivi(d, "c_r1.jsonl", ripresa)]
            r = RP.rapporto(os.path.join(d, "it"), pc, [pb])
            r_en = RP.rapporto(os.path.join(d, "en"), pc, [pb], "en")
            uscite = sorted(os.listdir(os.path.join(d, "it")))
            testo = open(os.path.join(d, "it", "rapporto.md"), encoding="utf-8").read()
        self.assertEqual(r["verdetto"], "H1 sostenuta")
        self.assertEqual(r["doppioni_c_scartati"], 20)
        self.assertEqual(r["confronti"]["n_controllo"], 10)
        self.assertEqual(r_en["verdetto"], r["verdetto"])
        self.assertEqual(uscite, ["classifica.png", "mano.png", "rapporto.md", "risultato.json", "successi.png",
                                  "tolleranza.png"])
        self.assertIn("**Verdetto: H1 sostenuta.**", testo)

    def test_prova_non_valida_senza_grafici_di_c(self):
        b, c = TA.TestTest()._scenario(True)
        c = [r for r in c if r["task"] not in A.ABILITA[:4]]
        with tempfile.TemporaryDirectory() as d:
            r = RP.rapporto(d, [scrivi(d, "c_1.jsonl", c)], [scrivi(d, "b.jsonl", b)])
            uscite = sorted(os.listdir(d))
            testo = open(os.path.join(d, "rapporto.md"), encoding="utf-8").read()
        self.assertFalse(r["valido"])
        self.assertNotIn("classifica.png", uscite)
        self.assertIn("**Prova non valida.**", testo)


if __name__ == "__main__":
    unittest.main()
