"""Simulazione di potenza (solo CPU) per la prova della Legge 1, premessa v3: se la legge è vera, quante volte la regola
di decisione la trova?

Modello volutamente semplice e dichiarato:
- 10 abilità; margine vero M uniforme tra 2 e 20 cm (così alcune risultano censurate a 16 cm), velocità v tra 4 e 9
  mm/passo, successo di base s0 tra 0,5 e 0,95.
- Successo con la spinta x: s0 / (1 + exp((x - M) / 1.5)).
- Successo con ritardo 16: s0 * exp(-16 / (c * T)). T è la tolleranza "effettiva"; c è tarato perché, con la legge
  vera del tutto, in media resti il 65% del successo (curve di sviluppo: 72,5% a ritardo 0, circa 48% a ritardo 16
  interpolando).
- Forza della legge f: T = T_vera^f * U(5, 25)^(1-f). Con f = 1 la legge è vera del tutto.
- Si usa analisi_legge1.test, cioè la regola vera: fase B2 per le censurate se sono almeno 3, esclusioni, calo minimo
  del 10%, p ≤ 0,05 sia nella principale sia nella sensibilità. Qui il p si stima con 2.000 permutazioni comuni alle
  due analisi (nella prova vera è esatto).
Uso: python potenza_legge1.py [simulazioni=500] [seme=1]
"""

import collections
import math
import random
import sys

import analisi_legge1 as A


def tara_c(forza=1.0, resta=0.65, n=20000):
    rnd = random.Random(0)
    tol = [((rnd.uniform(2, 20) / 100) / rnd.uniform(0.004, 0.009)) for _ in range(n)]
    basso, alto = 0.01, 100.0
    for _ in range(60):
        c = (basso + alto) / 2
        media = sum(math.exp(-16 / (c * t)) for t in tol) / n
        basso, alto = (c, alto) if media < resta else (basso, c)
    return (basso + alto) / 2


def simula(rnd, forza, c):
    b, cc = [], []
    for task in A.ABILITA:
        m, v, s0 = rnd.uniform(2, 20), rnd.uniform(0.004, 0.009), rnd.uniform(0.5, 0.95)
        tol = ((m / 100) / v) ** forza * rnd.uniform(5, 25) ** (1 - forza)
        s16 = s0 * math.exp(-16 / (c * tol))
        for cm in A.SPINTE + A.SPINTE_ESTESE:  # le righe di B2 contano solo se la regola lo prevede
            p = s0 / (1 + math.exp((cm - m) / 1.5))
            b += [{"task": task, "organo": "spinta", "ritardo": 0, "lento_k": A.K, "n_direzioni": 5, "spinta_cm": cm,
                   "stato_iniziale": s, "successo": rnd.random() < p, "vel_finale_xy": v, "passi": 120}
                  for s in A.SCENE_B]
        for d, p in ((0, s0), (A.RITARDO_TEST, s16)):
            cc += [{"task": task, "organo": "nessuno", "ritardo": d, "lento_k": A.K, "stato_iniziale": s,
                    "hash_stato": f"{task}|{s}", "successo": rnd.random() < p} for s in A.SCENE_C]
    r = A.test(b, cc, seme=rnd.randrange(10 ** 9), n_boot=1, esatto=False, n_perm=2000)
    return r["verdetto"] if r["valido"] else "non valida", len(A.censurate_a_16(b))


if __name__ == "__main__":
    n_sim = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seme = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    c = tara_c()
    print(f"simulazioni {n_sim}, seme {seme}, c = {c:.3f}")
    for forza in (1.0, 0.7):
        rnd = random.Random(seme)
        esiti = [simula(rnd, forza, c) for _ in range(n_sim)]
        verdetti = collections.Counter(v for v, _ in esiti)
        cens = sum(n for _, n in esiti) / n_sim
        b2 = sum(n >= A.MIN_CENSURATE for _, n in esiti) / n_sim
        print(f"forza {forza:.1f}: potenza {verdetti['H1 sostenuta'] / n_sim:.2f}  "
              f"(censurate a 16 cm in media {cens:.1f}, fase B2 nel {b2:.0%}; verdetti {dict(verdetti)})")
