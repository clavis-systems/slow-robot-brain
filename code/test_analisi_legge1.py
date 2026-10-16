import itertools
import random
import unittest
from fractions import Fraction

import analisi_legge1 as A


def righe_b(task, successi_per_spinta, vel=0.004, spinte=A.SPINTE):
    """successi_per_spinta: quanti successi su 5 per ciascuna spinta."""
    out = []
    for cm, k in zip(spinte, successi_per_spinta):
        for i, s in enumerate(A.SCENE_B):
            out.append({"task": task, "organo": "spinta", "ritardo": 0, "lento_k": 8, "n_direzioni": 5,
                        "spinta_cm": cm, "stato_iniziale": s, "successo": i < k, "vel_finale_xy": vel, "passi": 120})
    return out


def righe_c(task, k0, k16, k_ctrl=None):
    out = []
    condizioni = [(0, 8, k0), (16, 8, k16)] + ([(0, 16, k_ctrl)] if k_ctrl is not None else [])
    for d, kk, k in condizioni:
        for i, s in enumerate(A.SCENE_C):
            out.append({"task": task, "organo": "nessuno", "ritardo": d, "lento_k": kk, "stato_iniziale": s,
                        "hash_stato": f"{task[:6]}-{s}", "successo": i < k, "passi": 150 if i < k else 300,
                        "scarti_attesa": [0.01 * (j + 1) for j in range(8)] if d == 16 else None,
                        "cambi_piano": [0.02] * 8})
    return out


class TestMargine(unittest.TestCase):
    def test_isotonica(self):
        self.assertEqual(A.isotonica_decrescente([1, 0.6, 0.8, 0.2, 0, 0]), [1, 0.7, 0.7, 0.2, 0, 0])

    def test_interpolazione_e_censura(self):
        m, cens = A.margine([1, 1, 1, 0.2, 0, 0])  # metà (0.5) tra 4 e 8 cm sui valori isotonici
        self.assertFalse(cens)
        self.assertAlmostEqual(m, 4 + (1 - 0.5) / (1 - 0.2) * 4)
        self.assertEqual(A.margine([1] * 6), (16.0, True))
        self.assertEqual(A.margine([0] * 6), (None, False))

    def test_griglia_estesa_per_le_censurate(self):
        b = []
        for task in A.ABILITA[:3]:  # tre censurate a 16 cm: si usa la fase B2
            b += righe_b(task, [5] * 6) + righe_b(task, [2, 0], spinte=A.SPINTE_ESTESE)
        for task in A.ABILITA[3:]:
            b += righe_b(task, [5, 5, 4, 2, 0, 0])
        p = A.previsione(b)[A.ABILITA[0]]
        self.assertTrue(p["griglia_estesa"])
        self.assertFalse(p["censurato"])
        self.assertAlmostEqual(p["margine_cm"], 16 + (1 - 0.5) / (1 - 0.4) * 8)
        self.assertFalse(A.previsione(b)[A.ABILITA[5]]["griglia_estesa"])

    def test_meno_di_tre_censurate_nessuna_estensione(self):
        b = righe_b(A.ABILITA[0], [5] * 6) + righe_b(A.ABILITA[0], [0, 0], spinte=A.SPINTE_ESTESE)
        for task in A.ABILITA[1:]:
            b += righe_b(task, [5, 5, 4, 2, 0, 0])
        p = A.previsione(b)[A.ABILITA[0]]
        self.assertEqual((p["margine_cm"], p["censurato"], p["griglia_estesa"]), (16.0, True, False))


class TestDati(unittest.TestCase):
    def test_dati_incompleti_esclusi(self):
        b = righe_b(A.ABILITA[0], [5, 5, 5, 2, 0, 0])
        b.pop()  # manca un episodio
        self.assertIsNone(A.previsione(b)[A.ABILITA[0]])

    def test_doppioni_tiene_il_primo(self):
        b = righe_b(A.ABILITA[0], [5, 5, 5, 2, 0, 0])
        b.append({**b[-1], "successo": True})  # ripetuta (per esempio da una ripresa): conta la prima
        p = A.previsione(b)[A.ABILITA[0]]
        self.assertIsNotNone(p)
        self.assertEqual(p["frazioni"][-1], 0.0)

    def test_pareggi_esatti(self):
        self.assertEqual(A.ranghi([Fraction(1, 3), Fraction(2, 6), Fraction(1, 2)]), [1.5, 1.5, 3.0])


class TestP(unittest.TestCase):
    def test_p_esatto_come_la_forza_bruta(self):
        rnd = random.Random(3)
        for _ in range(8):
            x = [rnd.choice([1, 2, 3, 4, 5]) for _ in range(6)]
            y = [rnd.choice([1, 2, 3, 3, 4]) for _ in range(6)]
            r0 = A.spearman(x, y)
            forza_bruta = sum(A.spearman(x, list(p)) >= r0 - 1e-12 for p in itertools.permutations(y)) / 720
            self.assertAlmostEqual(A.p_esatto(x, y), forza_bruta, places=12)

    def test_p_esatto_casi_limite(self):
        self.assertAlmostEqual(A.p_esatto(list(range(7)), list(range(7))), 1 / 5040)
        self.assertEqual(A.p_esatto([1] * 7, list(range(7))), 1.0)


class TestTest(unittest.TestCase):
    def _scenario(self, legge_vera, k_ctrl=None):
        b, c = [], []
        for i, task in enumerate(A.ABILITA):
            caduta = min(5, 1 + i // 2)  # margine che cresce con i
            succ = [5] * caduta + [0] * (6 - caduta)
            b += righe_b(task, succ)
            k16 = (2 + 2 * i) if legge_vera else (20 - 2 * i)
            c += righe_c(task, 20, k16, k_ctrl)
        return b, c

    def test_legge_vera_passa(self):
        r = A.test(*self._scenario(True), n_boot=300)
        self.assertTrue(r["valido"])
        self.assertEqual(r["verdetto"], "H1 sostenuta")
        self.assertGreater(r["rho"], 0.8)
        self.assertEqual(r["p_unilaterale"], r["p_sensibilita"])  # nessuna censurata: stesso p, stesso verdetto

    def test_legge_falsa_non_passa(self):
        r = A.test(*self._scenario(False), n_boot=300)
        self.assertEqual(r["verdetto"], "H1 non sostenuta")

    def test_troppe_escluse(self):
        b, c = self._scenario(True)
        c = [r for r in c if r["task"] not in A.ABILITA[:4]]  # 4 abilità senza prova decisiva
        self.assertFalse(A.test(b, c, n_boot=10)["valido"])

    def test_k0_zero_esclusa(self):
        b, c = self._scenario(True)
        c = [r for r in c if r["task"] != A.ABILITA[9]] + righe_c(A.ABILITA[9], 0, 0)
        r = A.test(b, c, n_boot=10)
        self.assertIn(A.ABILITA[9], r["escluse"])

    def test_filtro_condizioni_e_controllo_negativo(self):
        r = A.test(*self._scenario(True, k_ctrl=18), n_boot=100)
        self.assertTrue(r["valido"])
        self.assertEqual(r["confronti"]["n_controllo"], 10)
        self.assertIsNotNone(r["confronti"]["controllo_negativo_K16"])
        self.assertIsNotNone(r["meccanismo_esplorativo"]["scarto_attesa_16"])

    def test_prova_non_informativa(self):
        b, c = self._scenario(True)
        c = [{**r, "successo": True} for r in c]  # il ritardo non toglie nulla
        self.assertEqual(A.test(b, c, n_boot=10)["verdetto"], "prova non informativa")

    def test_non_concludente(self):
        # Tre censurate con velocità alta (tolleranza bassa) e robustezza bassa: la legge regge nell'analisi
        # principale, ma non se le censurate vanno in cima (sensibilità).
        b, c = [], []
        for i, task in enumerate(A.ABILITA):
            if i < 3:
                b += righe_b(task, [5] * 6, vel=0.02)
                c += righe_c(task, 20, 2 + i)
            else:
                caduta = min(5, i - 1)
                b += righe_b(task, [5] * caduta + [0] * (6 - caduta), vel=0.004)
                c += righe_c(task, 20, 6 + 2 * i)
        r = A.test(b, c, n_boot=10)
        self.assertLessEqual(r["p_unilaterale"], A.ALFA)
        self.assertGreater(r["p_sensibilita"], A.ALFA)
        self.assertEqual(r["verdetto"], "non concludente")

    def test_scene_non_distinte_invalidano(self):
        b, c = self._scenario(True)
        c = [{**r, "hash_stato": "stesso"} if r["task"] == A.ABILITA[0] else r for r in c]
        r = A.test(b, c, n_boot=10)
        self.assertFalse(r["valido"])
        self.assertTrue(r["problemi"])

    def test_doppioni_in_c(self):
        b, c = self._scenario(True)
        c += [{**r, "successo": not r["successo"]} for r in c[:5]]  # ripetute con esito diverso: conta la prima
        r = A.test(b, c, n_boot=10)
        self.assertEqual(r["doppioni_c_scartati"], 5)
        self.assertEqual(r["verdetto"], "H1 sostenuta")


if __name__ == "__main__":
    unittest.main()
