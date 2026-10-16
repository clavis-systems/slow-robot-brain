import unittest

import numpy as np

from cervello_lento import CervelloLento


class Orologio:
    """Il 'cervello' finto restituisce un piano che dice per quale istante è stata pensata ogni azione."""

    def __init__(self):
        self.t = 0

    def pensa(self, _oss):
        return np.array([[(self.t, self.t + i) for i in range(50)]])  # (1, 50, 2): (visto al tempo, per il tempo)


def esegui(d, k, passi=60):
    o = Orologio()
    c = CervelloLento(o.pensa, d, k)
    righe = []
    for t in range(passi):
        o.t = t
        visto, per = c(None)[0]
        righe.append((t, int(visto), int(per)))
    return c, righe


class TestCervelloLento(unittest.TestCase):
    def test_ogni_azione_e_per_il_suo_istante(self):
        for d in (0, 1, 3, 10):
            for k in (1, 5, 10):
                _, righe = esegui(d, k)
                for t, visto, per in righe:
                    self.assertEqual(per, t, (d, k, t))

    def test_eta_dell_osservazione(self):
        for d in (1, 4, 8, 16, 24):
            for k in (1, 8):
                _, righe = esegui(d, k, passi=200)
                eta = [t - visto for t, visto, _ in righe if t >= d]  # dopo l'arrivo del secondo piano
                self.assertEqual(min(eta), d, (d, k))
                self.assertEqual(max(eta), d + max(k, d) - 1, (d, k))

    def test_un_pensiero_alla_volta(self):
        c, _ = esegui(16, 8, passi=160)
        self.assertEqual(c.pensieri, 11)  # t=0, t=8, poi ogni max(K, D)=16 passi fino a 152

    def test_senza_ritardo_e_normale(self):
        c, righe = esegui(0, 5, passi=50)
        self.assertEqual(c.pensieri, 10)
        self.assertTrue(all(t - visto < 5 for t, visto, _ in righe))

    def test_ritardo_troppo_grande(self):
        with self.assertRaises(RuntimeError):
            esegui(30, 8, passi=100)  # servirebbero 60 azioni per piano, ne ha 50

    def test_misure_del_meccanismo(self):
        # Il cervello finto ha piani che differiscono solo per "quando sono stati visti": ogni arrivo ha un cambio > 0.
        c, _ = esegui(3, 5, passi=60)
        self.assertEqual(len(c.cambi_piano), c.pensieri - 1)
        self.assertEqual(len(c.scarti_attesa), c.pensieri - 1)
        self.assertTrue(all(x > 0 for x in c.cambi_piano + c.scarti_attesa))
        c0, _ = esegui(0, 5, passi=60)
        self.assertEqual(c0.scarti_attesa, [])  # senza ritardo non c'è attesa
        self.assertEqual(len(c0.cambi_piano), c0.pensieri - 1)
        self.assertAlmostEqual(c0.cambi_piano[0], 25.0)  # 5 azioni, ognuna vista 5 passi prima nel piano vecchio

    def test_reset(self):
        c, _ = esegui(3, 5)
        c.reset()
        self.assertEqual((c.coda, c.in_arrivo, c.pensieri), ([], None, 0))


if __name__ == "__main__":
    unittest.main()
