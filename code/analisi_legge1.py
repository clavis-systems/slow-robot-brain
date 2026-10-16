"""Analisi della Legge 1 della freschezza (premessa: PREMESSA_LEGGE1.md, versione 3).

  python analisi_legge1.py previsione b.jsonl [b2.jsonl]                  -> classifica prevista (fase B)
  python analisi_legge1.py test --c c_1.jsonl [--c c_2.jsonl] --b b.jsonl -> verifica sulla prova decisiva (fase C)

I file della fase C si danno nell'ordine di esecuzione delle sessioni. Le righe ripetute (stessa abilità, condizione e
scena) si scartano tenendo la prima nell'ordine dei file.
"""

import argparse
import collections
import itertools
import json
import random
import statistics
import sys
from fractions import Fraction

import numpy as np

ABILITA = (
    "open the middle drawer of the cabinet", "put the bowl on the stove", "put the wine bottle on top of the cabinet",
    "open the top drawer and put the bowl inside", "put the bowl on top of the cabinet",
    "push the plate to the front of the stove", "put the cream cheese in the bowl", "turn on the stove",
    "put the bowl on the plate", "put the wine bottle on the rack",
)
SPINTE = (0.0, 2.0, 4.0, 8.0, 12.0, 16.0)
SPINTE_ESTESE = (24.0, 32.0)  # fase B2: solo per le censurate a 16 cm, se le censurate sono almeno MIN_CENSURATE
MIN_CENSURATE = 3
SCENE_B, EP_B = range(15, 20), 5
SCENE_C, EP_C = range(25, 45), 20
K = 8
RITARDO_TEST = 16
K_CONTROLLO = 16
PASSI_MAX = 300  # libero_goal: un episodio che arriva a 300 passi è finito per tempo scaduto
ALFA = 0.05
MAX_ESCLUSE = 3
CALO_MINIMO = Fraction(1, 10)  # sotto 10 punti di calo totale con il ritardo la prova non è informativa
ARRIVI_MECCANISMO = 6  # meccanismo (esplorativo): primi 6 arrivi di piano, prima che conti l'esito


def leggi(*percorsi):
    return [json.loads(r) for p in percorsi for r in open(p, encoding="utf-8") if r.strip()]


def senza_doppioni(righe, chiave):
    """Tiene la prima riga per ogni chiave; ritorna (righe tenute, righe scartate)."""
    viste, tenute, doppie = set(), [], []
    for r in righe:
        k = chiave(r)
        (doppie if k in viste else tenute).append(r)
        viste.add(k)
    return tenute, doppie


def chiave_b(r):
    return (r["task"], r.get("organo"), r.get("ritardo"), r.get("lento_k"), r.get("n_direzioni"), float(r["spinta_cm"]),
            r["stato_iniziale"])


def chiave_c(r):
    return r["task"], r.get("organo"), r.get("ritardo"), r.get("lento_k"), r["stato_iniziale"]


def _completo(righe, scene, n):
    stati = [r["stato_iniziale"] for r in righe]
    return len(righe) == n and sorted(stati) == list(scene)


def isotonica_decrescente(y):
    """Pool-adjacent-violators: la successione non crescente più vicina a y (pesi uguali)."""
    blocchi = []  # [somma, quanti]
    for v in y:
        blocchi.append([v, 1])
        while len(blocchi) > 1 and blocchi[-2][0] / blocchi[-2][1] < blocchi[-1][0] / blocchi[-1][1]:
            s, n = blocchi.pop()
            blocchi[-1][0] += s
            blocchi[-1][1] += n
    out = []
    for s, n in blocchi:
        out += [s / n] * n
    return out


def margine(frazioni, spinte=SPINTE):
    """frazioni: successo per ciascuna spinta. Prima spinta in cui la curva isotonica scende a metà di quella a 0 cm,
    interpolata. Ritorna (margine_cm, censurato) oppure (None, False) se a 0 cm non riesce mai."""
    f = isotonica_decrescente(frazioni)
    if f[0] == 0:
        return None, False
    soglia = f[0] / 2
    for i in range(1, len(spinte)):
        if f[i] <= soglia:
            a, b = f[i - 1], f[i]
            frazione = (a - soglia) / (a - b) if a != b else 1.0
            return spinte[i - 1] + frazione * (spinte[i] - spinte[i - 1]), False
    return spinte[-1], True


def righe_fase_b(righe):
    b = [r for r in righe if r.get("organo") == "spinta" and r.get("ritardo") == 0 and r.get("lento_k") == K
         and r.get("n_direzioni") == 5]
    return senza_doppioni(b, chiave_b)[0]


def _frazioni(b, task, spinte):
    """Successo per spinta, oppure None se manca qualche episodio; e gli episodi per spinta."""
    per_spinta = {cm: [r for r in b if r["task"] == task and float(r["spinta_cm"]) == cm] for cm in spinte}
    if not all(_completo(per_spinta[cm], SCENE_B, EP_B) for cm in spinte):
        return None, per_spinta
    return [sum(r["successo"] for r in per_spinta[cm]) / EP_B for cm in spinte], per_spinta


def censurate_a_16(righe_b):
    """Abilità complete sulla griglia base che non scendono a metà entro 16 cm."""
    b = righe_fase_b(righe_b)
    out = []
    for task in ABILITA:
        fr, _ = _frazioni(b, task, SPINTE)
        if fr is not None and margine(fr)[1]:
            out.append(task)
    return out


def previsione(righe_b):
    """Per ogni abilità: margine, velocità vicino al contatto, tolleranza prevista; None se i dati sono incompleti.
    Se almeno MIN_CENSURATE abilità sono censurate a 16 cm, per quelle il margine si calcola sulla griglia estesa
    (24 e 32 cm), quando i dati della fase B2 sono completi."""
    b = righe_fase_b(righe_b)
    cens16 = censurate_a_16(righe_b)
    estendi = set(cens16) if len(cens16) >= MIN_CENSURATE else set()
    out = {}
    for task in ABILITA:
        fr, per_spinta = _frazioni(b, task, SPINTE)
        if fr is None:
            out[task] = None
            continue
        spinte = SPINTE
        m, cens = margine(fr)
        estesa = False
        if task in estendi:
            fr_e, _ = _frazioni(b, task, SPINTE_ESTESE)
            if fr_e is not None:
                fr, spinte, estesa = fr + fr_e, SPINTE + SPINTE_ESTESE, True
                m, cens = margine(fr, spinte)
        riusciti = [r for r in per_spinta[0.0] if r["successo"]]
        vel = [r["vel_finale_xy"] for r in riusciti if r.get("vel_finale_xy")]
        v = statistics.median(vel) if vel else None
        passi = [r["passi"] for r in riusciti if r.get("passi")]
        tol = (m / 100) / v if (m is not None and v) else None
        out[task] = {"margine_cm": m, "censurato": cens, "griglia_estesa": estesa, "vel_m_passo": v,
                     "tolleranza_passi": tol, "successo_base_b": fr[0], "frazioni": fr, "spinte": spinte,
                     "passi_successi_0cm": statistics.mean(passi) if passi else None}
    return out


def ranghi(valori):
    ordine = sorted(range(len(valori)), key=lambda i: valori[i])
    r = [0.0] * len(valori)
    i = 0
    while i < len(ordine):
        j = i
        while j + 1 < len(ordine) and valori[ordine[j + 1]] == valori[ordine[i]]:
            j += 1
        for k in range(i, j + 1):
            r[ordine[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def _pearson(x, y):
    mx, my = statistics.mean(x), statistics.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den if den else 0.0


def spearman(x, y):
    return _pearson(ranghi(x), ranghi(y))


def spearman_parziale(x, y, z):
    rxy, rxz, ryz = spearman(x, y), spearman(x, z), spearman(y, z)
    den = ((1 - rxz ** 2) * (1 - ryz ** 2)) ** 0.5
    return (rxy - rxz * ryz) / den if den else 0.0


_PERMUTAZIONI = {}


def _tutte_le_permutazioni(n):
    if n not in _PERMUTAZIONI:
        piatte = np.fromiter(itertools.chain.from_iterable(itertools.permutations(range(n))), dtype=np.int8)
        _PERMUTAZIONI[n] = piatte.reshape(-1, n)
    return _PERMUTAZIONI[n]


def p_esatto(x, y):
    """p unilaterale esatto: quota delle n! permutazioni di y con ρ di Spearman ≥ quello osservato.
    A ranghi fissati ρ cresce con Σ rx·ry, quindi basta contare su quella somma (ranghi raddoppiati: interi)."""
    rx = np.array([round(2 * r) for r in ranghi(x)], dtype=np.int32)
    ry = np.array([round(2 * r) for r in ranghi(y)], dtype=np.int32)
    if len(set(rx.tolist())) == 1 or len(set(ry.tolist())) == 1:
        return 1.0  # ρ = 0 per ogni permutazione
    perm, oss, conta = _tutte_le_permutazioni(len(x)), int(rx @ ry), 0
    for i in range(0, len(perm), 400000):  # a blocchi, per non occupare troppa memoria
        conta += int(np.count_nonzero(ry[perm[i:i + 400000]] @ rx >= oss))
    return conta / len(perm)


def p_montecarlo(xs, y, rnd, n_perm):
    """Solo per prove veloci: le STESSE permutazioni casuali di y per ogni x in xs."""
    rho = [spearman(x, y) for x in xs]
    conta = [0] * len(xs)
    for _ in range(n_perm):
        yp = rnd.sample(y, len(y))
        for i, x in enumerate(xs):
            conta[i] += spearman(x, yp) >= rho[i]
    return [(c + 1) / (n_perm + 1) for c in conta]


def _conta(righe_c, task, ritardo, k):
    return [r for r in righe_c if r["task"] == task and r.get("ritardo") == ritardo and r.get("lento_k") == k]


def controlli_c(righe_c):
    """Gravi: scene diverse con lo stesso stato iniziale (la scena non è stata impostata). Avvisi: stato diverso tra le
    condizioni nella stessa scena, o stato mancante."""
    stati = collections.defaultdict(set)
    for r in righe_c:
        stati[(r["task"], r["stato_iniziale"])].add(r.get("hash_stato"))
    avvisi = [f"{t} scena {s}: stato iniziale diverso o mancante tra le condizioni"
              for (t, s), h in sorted(stati.items()) if len(h) > 1 or None in h]
    gravi = []
    for task in ABILITA:
        unici = [next(iter(h)) for (t, s), h in stati.items() if t == task and len(h) == 1 and None not in h]
        if len(set(unici)) < len(unici):
            gravi.append(f"{task}: scene diverse con lo stesso stato iniziale")
    return gravi, avvisi


def _media_arrivi(righe, campo):
    """Media per abilità dei primi ARRIVI_MECCANISMO valori per episodio (None se mancano)."""
    valori = [statistics.mean(r[campo][:ARRIVI_MECCANISMO]) for r in righe if r.get(campo)]
    return statistics.mean(valori) if valori else None


def _rho_dove_c_e(xs, y):
    coppie = [(a, b) for a, b in zip(xs, y) if a is not None]
    return spearman(*zip(*coppie)) if len(coppie) >= 3 else None


def test(righe_b, righe_c, seme=12102026, n_boot=10000, esatto=True, n_perm=100000):
    prev = previsione(righe_b)
    c, doppie_c = senza_doppioni([r for r in righe_c if r.get("organo") == "nessuno"], chiave_c)
    gravi, avvisi = controlli_c(c)
    righe, escluse = [], []
    for task in ABILITA:
        p = prev[task]
        c0, c16 = _conta(c, task, 0, K), _conta(c, task, RITARDO_TEST, K)
        if p is None or p["tolleranza_passi"] is None or not _completo(c0, SCENE_C, EP_C) \
                or not _completo(c16, SCENE_C, EP_C):
            escluse.append(task)
            continue
        k0, k16 = sum(r["successo"] for r in c0), sum(r["successo"] for r in c16)
        if k0 == 0:
            escluse.append(task)
            continue
        ck = _conta(c, task, 0, K_CONTROLLO)
        k_ctrl = sum(r["successo"] for r in ck) if _completo(ck, SCENE_C, EP_C) else None
        falliti16 = [r for r in c16 if not r["successo"]]
        righe.append({
            "task": task, "tolleranza": p["tolleranza_passi"], "censurato": p["censurato"],
            "margine_cm": p["margine_cm"], "vel": p["vel_m_passo"], "base_b": p["successo_base_b"],
            "passi_b": p["passi_successi_0cm"], "k0": k0, "k16": k16, "k_controllo": k_ctrl,
            "robustezza": (Fraction(k16) + Fraction(1, 2)) / (Fraction(k0) + Fraction(1, 2)),
            "tempo_scaduto_16": sum(r.get("passi", 0) >= PASSI_MAX for r in falliti16) / EP_C,
            "scarto_attesa_16": _media_arrivi(c16, "scarti_attesa"),
            "cambio_piano_16": _media_arrivi(c16, "cambi_piano"),
        })
    base = {"escluse": escluse, "doppioni_c_scartati": len(doppie_c), "problemi": gravi, "avvisi": avvisi}
    if len(escluse) > MAX_ESCLUSE or gravi:
        return {"valido": False, **base}
    x = [r["tolleranza"] for r in righe]
    y = [r["robustezza"] for r in righe]
    # Sensibilità: le abilità censurate tutte a pari merito in cima alla classifica.
    x_sens = [float("inf") if r["censurato"] else r["tolleranza"] for r in righe]
    if esatto:
        p, p_s = p_esatto(x, y), p_esatto(x_sens, y)
    else:
        p, p_s = p_montecarlo([x, x_sens], y, random.Random(seme), n_perm)
    rho, rho_s = spearman(x, y), spearman(x_sens, y)
    calo = Fraction(sum(r["k0"] - r["k16"] for r in righe), EP_C * len(righe))
    h1, h1_s = p <= ALFA, p_s <= ALFA
    if calo < CALO_MINIMO:
        verdetto = "prova non informativa"
    else:
        verdetto = ("H1 sostenuta" if h1 and h1_s else "H1 non sostenuta" if not h1 and not h1_s
                    else "non concludente")
    rnd = random.Random(seme)
    boot = sorted(spearman([x[i] for i in idx], [y[i] for i in idx])
                  for idx in ([rnd.randrange(len(righe)) for _ in righe] for _ in range(n_boot)))
    ctrl = [r for r in righe if r["k_controllo"] is not None]
    return {
        "valido": True, **base, "n": len(righe), "p_esatto": esatto,
        "rho": rho, "p_unilaterale": p, "ic95_bootstrap": (boot[int(0.025 * n_boot)], boot[int(0.975 * n_boot) - 1]),
        "rho_sensibilita": rho_s, "p_sensibilita": p_s, "calo_totale": float(calo), "verdetto": verdetto,
        "confronti": {
            "solo_margine": spearman([r["margine_cm"] for r in righe], y),
            "solo_1_su_velocita": spearman([1 / r["vel"] for r in righe], y),
            "solo_successo_base_b": spearman([r["base_b"] for r in righe], y),
            "tolleranza_a_parita_di_successo_base": spearman_parziale(x, y, [r["base_b"] for r in righe]),
            "passi_dei_successi_a_0cm": _rho_dove_c_e([r["passi_b"] for r in righe], y),
            "controllo_negativo_K16": (spearman([r["tolleranza"] for r in ctrl],
                                                [(Fraction(r["k_controllo"]) + Fraction(1, 2)) /
                                                 (Fraction(r["k0"]) + Fraction(1, 2)) for r in ctrl])
                                       if len(ctrl) >= 3 else None),
            "n_controllo": len(ctrl),
        },
        "meccanismo_esplorativo": {
            "scarto_attesa_16": _rho_dove_c_e([r["scarto_attesa_16"] for r in righe], y),
            "cambio_piano_16": _rho_dove_c_e([r["cambio_piano_16"] for r in righe], y),
        },
        "righe": [{**r, "robustezza": str(r["robustezza"])} for r in righe],
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.argv[1] == "previsione":
        righe_b = leggi(*sys.argv[2:])
        cens = censurate_a_16(righe_b)
        prev = previsione(righe_b)
        if len(cens) >= MIN_CENSURATE:
            manca = [t for t in cens if not prev[t]["griglia_estesa"]]
            print(f"{len(cens)} abilità censurate a 16 cm: fase B2 completa per {len(cens) - len(manca)}, "
                  f"mancante per {len(manca)}" + (" (da fare prima del congelamento)" if manca else ""))
        ordinate = sorted(prev.items(), key=lambda kv: (kv[1] is None or kv[1]["tolleranza_passi"] is None,
                                                       (kv[1] or {}).get("tolleranza_passi") or 0))
        for task, p in ordinate:
            if p is None:
                print(f"{task[:46]:46s} DATI INCOMPLETI")
            else:
                print(f"{task[:46]:46s} margine {p['margine_cm']} cm{' (>=, censurato)' if p['censurato'] else ''}"
                      f"  vel {p['vel_m_passo']}  tolleranza {p['tolleranza_passi']}  base {p['successo_base_b']}")
    elif sys.argv[1] == "censurate":
        # Per la regola della fase B2: numeri delle abilità censurate a 16 cm, solo se sono almeno MIN_CENSURATE.
        cens = censurate_a_16(leggi(*sys.argv[2:]))
        print(",".join(str(ABILITA.index(t)) for t in cens) if len(cens) >= MIN_CENSURATE else "")
    else:
        a = argparse.ArgumentParser(prog="analisi_legge1.py test")
        a.add_argument("--c", action="append", required=True, help="file della fase C, nell'ordine di esecuzione")
        a.add_argument("--b", action="append", required=True, help="file della fase B (e B2)")
        arg = a.parse_args(sys.argv[2:])
        print(json.dumps(test(leggi(*arg.b), leggi(*arg.c)), indent=1, ensure_ascii=False, default=str))
