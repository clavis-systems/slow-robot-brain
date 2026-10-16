"""Rapporto finale della Legge 1: verdetto, tabella e grafici, scritto PRIMA dei dati della fase C.

  python rapporto_legge1.py CARTELLA_USCITA --c c_1.jsonl [--c c_2.jsonl] --b b.jsonl [--b b2.jsonl] [--lingua en]

I file della fase C si danno nell'ordine di esecuzione delle sessioni (premessa, "Unione dei file della fase C").

Scrive in CARTELLA_USCITA:
- risultato.json: l'uscita completa di analisi_legge1.test (p esatto);
- rapporto.md: verdetto, tabella per abilità, confronti, controlli;
- classifica.png: classifica prevista contro classifica osservata;
- tolleranza.png: tolleranza prevista T̂ contro robustezza R;
- successi.png: successi con ritardo 0 e 16 per abilità;
- mano.png: controllo descrittivo della fase B, distanza mano-oggetto alla prima chiusura secondo la spinta.
"""

import argparse
import json
import os
import statistics
import sys
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")
import matplotlib.ticker  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

import analisi_legge1 as A  # noqa: E402
from congela_legge1 import NOMI  # noqa: E402

NOMI_EN = dict(zip(A.ABILITA, (
    "open the middle drawer", "bowl on the stove", "wine on the cabinet", "top drawer + bowl inside",
    "bowl on the cabinet", "push the plate", "cream cheese in the bowl", "turn on the stove (knob)",
    "bowl on the plate", "wine on the rack")))
TESTI = {
    "it": {"prev": "Prevista (T̂ = M / v)", "oss": "Osservata (R)", "fragile": "1 = crolla per prima",
           "titolo_cl": "Quali abilità crollano per prime col cervello lento", "tol": "Tolleranza prevista T̂ (passi)",
           "rob": "Robustezza R = (k16 + ½) / (k0 + ½)", "cens": "censurata (M ≥ ultima spinta)",
           "titolo_tol": "Previsione contro misura", "succ": "Successo su 20 episodi", "d0": "ritardo 0",
           "d16": "ritardo 16", "titolo_succ": "Successi senza e con ritardo (in alto le più fragili previste)",
           "spinta": "Spinta (cm)", "dist": "distanza mano-oggetto alla prima chiusura (cm)",
           "rif": "se si fidasse solo del corpo", "titolo_mano": "Controllo descrittivo della fase B",
           "non_valida": "prova non valida", "verdetti": {}},
    "en": {"prev": "Predicted (T̂ = M / v)", "oss": "Observed (R)", "fragile": "1 = breaks first",
           "titolo_cl": "Which skills break first when the robot brain lags", "tol": "Predicted tolerance T̂ (steps)",
           "rob": "Robustness R = (k16 + ½) / (k0 + ½)", "cens": "censored (M ≥ last offset)",
           "titolo_tol": "Prediction vs measurement", "succ": "Success out of 20 episodes", "d0": "delay 0",
           "d16": "delay 16", "titolo_succ": "Success without and with delay (predicted most fragile on top)",
           "spinta": "Offset (cm)", "dist": "hand-object distance at first grasp (cm)",
           "rif": "if it trusted only its body sense", "titolo_mano": "Descriptive check of phase B",
           "non_valida": "test not valid",
           "verdetti": {"H1 sostenuta": "H1 supported", "H1 non sostenuta": "H1 not supported",
                        "non concludente": "inconclusive", "prova non informativa": "test not informative"}},
}
BLU, ARANCIO, GRIGIO = "#2a78d6", "#eb6834", "#b7b6b0"
SUPERFICIE, TESTO, TESTO2, GRIGLIA = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"


def _stile():
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "axes.edgecolor": GRIGLIA, "axes.labelcolor": TESTO2, "xtick.color": TESTO2, "ytick.color": TESTO2,
        "text.color": TESTO, "axes.grid": True, "grid.color": GRIGLIA, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 12,
        "axes.titleweight": "bold", "lines.linewidth": 2, "lines.solid_capstyle": "round"})


def _titolo_esito(r, t):
    if not r["valido"]:
        return t["non_valida"]
    return f"{t['verdetti'].get(r['verdetto'], r['verdetto'])}: ρ = {r['rho']:.2f}, p = {r['p_unilaterale']:.4f} (sens. p = {r['p_sensibilita']:.4f})"


def grafico_classifica(righe, r, t, nomi, percorso):
    prev = A.ranghi([x["tolleranza"] for x in righe])
    oss = A.ranghi([x["robustezza_f"] for x in righe])
    n = len(righe)
    fig, ax = plt.subplots(figsize=(8, 0.42 * n + 1.8))
    for x, p, o in zip(righe, prev, oss):
        ax.plot([0, 1], [p, o], color=BLU, marker="o", markersize=7, markeredgecolor=SUPERFICIE, markeredgewidth=2)
        ax.text(-0.04, p, f"{nomi[x['task']]}  {p:g}", ha="right", va="center", color=TESTO, fontsize=9)
        ax.text(1.04, o, f"{o:g}  {nomi[x['task']]}", ha="left", va="center", color=TESTO, fontsize=9)
    ax.set_xlim(-0.9, 1.9)
    ax.set_ylim(n + 0.6, 0.4)
    ax.set_xticks([0, 1], [t["prev"], t["oss"]])
    ax.set_yticks([])
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.set_title(f"{t['titolo_cl']}\n{_titolo_esito(r, t)}", loc="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.text(0.99, 0.01, t["fragile"], ha="right", va="bottom", color=TESTO2, fontsize=8)
    fig.savefig(percorso, dpi=150)
    plt.close(fig)


def grafico_tolleranza(righe, r, t, nomi, percorso):
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    tol = [x["tolleranza"] for x in righe]
    basso, alto = min(tol) / 1.25, max(tol) * 1.25
    for x in righe:
        pieno = not x["censurato"]
        ax.plot(x["tolleranza"], x["robustezza_f"], "o", markersize=8, color=BLU,
                markerfacecolor=BLU if pieno else SUPERFICIE, markeredgewidth=2)
        a_sinistra = x["tolleranza"] > max(tol) / 1.6  # le etichette vicine al bordo destro vanno a sinistra
        ax.annotate(nomi[x["task"]], (x["tolleranza"], x["robustezza_f"]), xytext=(-6 if a_sinistra else 6, 4),
                    textcoords="offset points", fontsize=8, color=TESTO2, ha="right" if a_sinistra else "left")
    pad = 12
    if any(x["censurato"] for x in righe):
        ax.plot([], [], "o", color=BLU, markerfacecolor=SUPERFICIE, markeredgewidth=2, label=t["cens"])
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0))
        pad = 28
    ax.set_xscale("log")
    ax.set_xlim(basso, alto)
    tacche = [v for v in (1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100, 150, 200, 300) if basso <= v <= alto]
    ax.set_xticks(tacche, [f"{v:g}" for v in tacche])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel(t["tol"])
    ax.set_ylabel(t["rob"])
    ax.set_title(f"{t['titolo_tol']}\n{_titolo_esito(r, t)}", loc="left", pad=pad)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150)
    plt.close(fig)


def grafico_successi(righe, t, nomi, percorso):
    ordinate = sorted(righe, key=lambda x: x["tolleranza"])  # in alto le più fragili previste
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(ordinate) + 1.6))
    for i, x in enumerate(ordinate):
        ax.plot([x["k16"], x["k0"]], [i, i], color=GRIGIO, linewidth=2, zorder=1)
        ax.plot(x["k0"], i, "o", color=BLU, markersize=8, markeredgecolor=SUPERFICIE, markeredgewidth=2, zorder=2)
        ax.plot(x["k16"], i, "o", color=ARANCIO, markersize=8, markeredgecolor=SUPERFICIE, markeredgewidth=2, zorder=2)
    ax.set_yticks(range(len(ordinate)), [nomi[x["task"]] for x in ordinate])
    ax.set_ylim(len(ordinate) - 0.4, -0.6)
    ax.set_xlim(-0.5, A.EP_C + 0.5)
    ax.set_xticks(range(0, A.EP_C + 1, 5))
    ax.grid(axis="y", visible=False)  # la linea grigia di ogni abilità non deve sovrapporsi alla griglia
    ax.set_xlabel(t["succ"])
    ax.plot([], [], "o", color=BLU, label=t["d0"])
    ax.plot([], [], "o", color=ARANCIO, label=t["d16"])
    ax.legend(frameon=False, loc="lower left", ncol=2, bbox_to_anchor=(0, 1.0))
    fig.suptitle(t["titolo_succ"], x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150)
    plt.close(fig)


def grafico_mano(righe_b, t, nomi, percorso):
    """Mediana della distanza mano-oggetto alla prima chiusura per spinta, solo per le abilità con un oggetto."""
    b = A.righe_fase_b(righe_b)
    serie = {}
    for task in A.ABILITA:
        punti = []
        for cm in A.SPINTE + A.SPINTE_ESTESE:
            d = [r["dist_mano_oggetto"] * 100 for r in b if r["task"] == task and float(r["spinta_cm"]) == cm
                 and r.get("dist_mano_oggetto") is not None]
            if d:
                punti.append((cm, statistics.median(d)))
        if len(punti) >= 2:
            serie[task] = punti
    if not serie:
        return False
    col = min(4, len(serie))
    righe_g = (len(serie) + col - 1) // col
    fig, assi = plt.subplots(righe_g, col, figsize=(3.2 * col, 2.8 * righe_g + 0.8), squeeze=False, sharex=True,
                             sharey=True)
    massimo = max(cm for p in serie.values() for cm, _ in p)
    for ax, (task, punti) in zip(assi.flat, serie.items()):
        ax.plot([0, massimo], [0, massimo], color=GRIGIO, linewidth=1.5, label=t["rif"])
        ax.plot(*zip(*punti), color=BLU, marker="o", markersize=6, markeredgecolor=SUPERFICIE, markeredgewidth=1.5)
        ax.set_title(nomi[task], fontsize=9, loc="left")
    for ax in list(assi.flat)[len(serie):]:
        ax.set_visible(False)
    for ax in assi[-1]:
        ax.set_xlabel(t["spinta"])
    for ax in assi[:, 0]:
        ax.set_ylabel("cm")
    assi.flat[0].legend(frameon=False, fontsize=7, loc="upper left")
    fig.suptitle(f"{t['titolo_mano']}: {t['dist']}", x=0.01, ha="left", fontweight="bold", fontsize=11)
    fig.tight_layout()
    fig.savefig(percorso, dpi=150)
    plt.close(fig)
    return True


def testo_rapporto(r, righe, nomi):
    out = ["# Legge 1 della freschezza: risultato della prova decisiva", ""]
    if not r["valido"]:
        out += ["**Prova non valida.**", "", f"- Escluse: {', '.join(nomi[t] for t in r['escluse']) or 'nessuna'}",
                f"- Problemi: {'; '.join(r['problemi']) or 'nessuno'}"]
        return "\n".join(out) + "\n"
    ic = r["ic95_bootstrap"]
    out += [f"**Verdetto: {r['verdetto']}.**", "",
            f"- ρ di Spearman = {r['rho']:.3f}, p unilaterale esatto = {r['p_unilaterale']:.4f} (n = {r['n']}).",
            f"- Sensibilità (censurate con T̂ = +∞, cioè tra le più robuste, come nel codice congelato): "
            f"ρ = {r['rho_sensibilita']:.3f}, p = {r['p_sensibilita']:.4f}.",
            f"- Intervallo bootstrap al 95% di ρ (descrittivo): da {ic[0]:.2f} a {ic[1]:.2f}.",
            f"- Calo totale del successo da ritardo 0 a ritardo 16: {r['calo_totale'] * 100:.1f} punti percentuali.",
            f"- Escluse: {', '.join(nomi[t] for t in r['escluse']) or 'nessuna'}; righe doppie scartate: "
            f"{r['doppioni_c_scartati']}.", "",
            "| Abilità | Posto previsto | T̂ (passi) | k0 | k16 | R | Posto osservato | Fallimenti a 16 per tempo scaduto |",
            "|---|---|---|---|---|---|---|---|"]
    prev = A.ranghi([x["tolleranza"] for x in righe])
    oss = A.ranghi([x["robustezza_f"] for x in righe])
    for x, p, o in sorted(zip(righe, prev, oss), key=lambda z: z[1]):
        out.append(f"| {nomi[x['task']]}{' (censurata)' if x['censurato'] else ''} | {p:g} | {x['tolleranza']:.1f} | "
                   f"{x['k0']} | {x['k16']} | {x['robustezza_f']:.2f} | {o:g} | "
                   f"{round(x['tempo_scaduto_16'] * A.EP_C)} su {A.EP_C - x['k16']} |")
    c = r["confronti"]
    fmt = lambda v: "non disponibile" if v is None else f"{v:.2f}"  # noqa: E731
    k16 = "non disponibile (fase C2 non ancora eseguita)" if c["controllo_negativo_K16"] is None \
        else fmt(c["controllo_negativo_K16"])
    out += ["", "## Confronti (non cambiano il verdetto)", "",
            f"- Solo margine M: ρ = {fmt(c['solo_margine'])}; solo 1/v: ρ = {fmt(c['solo_1_su_velocita'])}.",
            f"- Solo successo di base in B: ρ = {fmt(c['solo_successo_base_b'])}; T̂ a parità di successo di base: "
            f"ρ parziale = {fmt(c['tolleranza_a_parita_di_successo_base'])}.",
            f"- Passi dei successi a 0 cm (compiti lunghi): ρ = {fmt(c['passi_dei_successi_a_0cm'])}.",
            f"- Controllo negativo, ritardo 0 con K = 16: ρ(T̂, R_K16) = {k16} su {c['n_controllo']} abilità.", "",
            "## Meccanismo (solo esplorativo)", "",
            f"- Scarto nell'attesa (ritardo 16, primi 6 arrivi): ρ con R = "
            f"{fmt(r['meccanismo_esplorativo']['scarto_attesa_16'])}.",
            f"- Cambio di piano (ritardo 16, primi 6 arrivi): ρ con R = "
            f"{fmt(r['meccanismo_esplorativo']['cambio_piano_16'])}.",
            "- Attenzione: queste misure dipendono dalla durata degli episodi. Un episodio riuscito finisce presto e "
            "spesso ha meno di 6 arrivi, uno fallito arriva a 300 passi e li ha tutti. Non sono una prova della "
            "Legge 2.", "",
            "## Avvisi sui dati", ""] + ([f"- {a}" for a in r["avvisi"]] or ["- nessuno"])
    return "\n".join(out) + "\n"


def rapporto(cartella, percorsi_c, percorsi_b, lingua="it"):
    _stile()
    os.makedirs(cartella, exist_ok=True)
    righe_b, righe_c = A.leggi(*percorsi_b), A.leggi(*percorsi_c)
    r = A.test(righe_b, righe_c)
    with open(os.path.join(cartella, "risultato.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1, ensure_ascii=False, default=str)
    nomi, t = (NOMI_EN, TESTI["en"]) if lingua == "en" else (NOMI, TESTI["it"])
    righe = [{**x, "robustezza_f": float(Fraction(x["robustezza"]))} for x in r.get("righe", [])]
    if righe:
        grafico_classifica(righe, r, t, nomi, os.path.join(cartella, "classifica.png"))
        grafico_tolleranza(righe, r, t, nomi, os.path.join(cartella, "tolleranza.png"))
        grafico_successi(righe, t, nomi, os.path.join(cartella, "successi.png"))
    grafico_mano(righe_b, t, nomi, os.path.join(cartella, "mano.png"))
    with open(os.path.join(cartella, "rapporto.md"), "w", encoding="utf-8") as f:
        f.write(testo_rapporto(r, righe, NOMI))
    return r


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = argparse.ArgumentParser()
    a.add_argument("cartella")
    a.add_argument("--c", action="append", required=True, help="file della fase C, nell'ordine di esecuzione")
    a.add_argument("--b", action="append", required=True, help="file della fase B (e B2)")
    a.add_argument("--lingua", default="it", choices=("it", "en"))
    arg = a.parse_args()
    esito = rapporto(arg.cartella, arg.c, arg.b, arg.lingua)
    print(esito.get("verdetto", "prova non valida"))
