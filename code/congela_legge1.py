"""Congelamento della previsione della Legge 1 (PREMESSA_LEGGE1.md, sezione "Al congelamento").

  python congela_legge1.py --b b.jsonl [--b b2.jsonl] [--codice-b CARTELLA] [--comando-c FILE] [altri file da fissare]

Controlla i dati della fase B, stampa la classifica prevista con analisi_legge1.previsione (senza cambiare nulla
dell'analisi), la classifica di sensibilità e gli hash dei file da fissare prima della fase C. Gli hash del codice
sono calcolati con fine riga LF, cioè sul contenuto eseguito su Kaggle. Esce con codice 1 se i dati hanno problemi.
"""

import argparse
import collections
import hashlib
import os
import sys

import analisi_legge1 as A

NOMI = {  # nomi brevi in italiano, solo per leggere la classifica
    "open the middle drawer of the cabinet": "apri il cassetto centrale",
    "put the bowl on the stove": "ciotola sul fornello",
    "put the wine bottle on top of the cabinet": "vino sopra il mobile",
    "open the top drawer and put the bowl inside": "cassetto in alto e ciotola dentro",
    "put the bowl on top of the cabinet": "ciotola sopra il mobile",
    "push the plate to the front of the stove": "spingi il piatto",
    "put the cream cheese in the bowl": "formaggio nella ciotola",
    "turn on the stove": "accendi il fornello (manopola)",
    "put the bowl on the plate": "ciotola sul piatto",
    "put the wine bottle on the rack": "vino sulla rastrelliera",
}
CODICE = ("analisi_legge1.py", "kaggle/kaggle_esegui.sh", "organo_tatto.py", "cervello_lento.py", "riassunto.py",
          "congela_legge1.py")


def sha256(percorso, lf=False):
    dati = open(percorso, "rb").read()
    return hashlib.sha256(dati.replace(b"\r\n", b"\n") if lf else dati).hexdigest()


def controlli(righe):
    """Problemi nei dati di B: righe fuori protocollo, celle mancanti o ripetute, scene ed episodi non allineati,
    stati iniziali incoerenti, estensione B2 mancante quando la regola la richiede."""
    problemi = []
    fuori = [r for r in righe if not (r.get("organo") == "spinta" and r.get("ritardo") == 0 and r.get("lento_k") == A.K
                                      and r.get("n_direzioni") == 5 and not r.get("perturba"))]
    if fuori:
        problemi.append(f"{len(fuori)} righe fuori protocollo")
    sconosciute = sorted({r["task"] for r in righe} - set(A.ABILITA))
    if sconosciute:
        problemi.append(f"abilità sconosciute: {sconosciute}")
    celle = collections.Counter((r["task"], float(r["spinta_cm"]), r["stato_iniziale"]) for r in righe)
    for (task, cm, s), n in sorted(celle.items()):
        if n > 1:
            problemi.append(f"ripetuta {n} volte: {task} | spinta {cm} | scena {s}")
    estese = {r["task"] for r in righe if float(r["spinta_cm"]) in A.SPINTE_ESTESE}
    for task in A.ABILITA:
        for cm in A.SPINTE + (A.SPINTE_ESTESE if task in estese else ()):
            for s in A.SCENE_B:
                if not celle[(task, cm, s)]:
                    problemi.append(f"manca: {task} | spinta {cm} | scena {s}")
    # Direzione della spinta = scena % 5. Le righe della fase B in corso non la scrivono: lì la direzione veniva
    # dall'episodio, quindi scena 15 + i deve essere l'episodio i.
    if any(r.get("direzione") is None and r.get("ep") != r["stato_iniziale"] - A.SCENE_B[0] for r in righe):
        problemi.append("episodio e scena non allineati (la direzione della spinta non sarebbe quella prevista)")
    if any(r.get("direzione") is not None and r["direzione"] != r["stato_iniziale"] % 5 for r in righe):
        problemi.append("direzione della spinta diversa da scena % 5")
    # La spinta cambia solo ciò che il cervello sente: la stessa scena parte dallo stesso stato fisico a ogni spinta,
    # e scene diverse partono da stati diversi.
    stati = collections.defaultdict(set)
    for r in righe:
        stati[(r["task"], r["stato_iniziale"])].add(r.get("hash_stato"))
    diverse = sorted(k for k, h in stati.items() if len(h) > 1 or None in h)
    if diverse:
        problemi.append(f"{len(diverse)} scene con stato iniziale diverso o mancante tra le spinte: {diverse[:3]}")
    for task in A.ABILITA:
        unici = [next(iter(h)) for (t, s), h in stati.items() if t == task and len(h) == 1 and None not in h]
        if len(set(unici)) < len(unici):
            problemi.append(f"{task}: scene diverse con lo stesso stato iniziale")
    cens = A.censurate_a_16(righe)
    if len(cens) >= A.MIN_CENSURATE and not set(cens) <= estese:
        problemi.append(f"{len(cens)} abilità censurate a 16 cm: la premessa richiede la fase B2 (24 e 32 cm) per "
                        f"{sorted(NOMI[t] for t in set(cens) - estese)} prima del congelamento")
    return problemi


def classifica(prev):
    """Dalla più fragile (tolleranza T̂ più piccola: crolla prima) alla più robusta; poi le escluse."""
    valide = sorted((t for t in A.ABILITA if prev[t] and prev[t]["tolleranza_passi"] is not None),
                    key=lambda t: prev[t]["tolleranza_passi"])
    return valide, [t for t in A.ABILITA if t not in valide]


def rapporto(percorsi_b, altri=(), codice_b=None, comando_c=None):
    righe = A.leggi(*percorsi_b)
    problemi = controlli(righe)
    prev = A.previsione(righe)
    valide, escluse = classifica(prev)
    nomi_b = ", ".join(f"`{os.path.basename(p)}`" for p in percorsi_b)
    out = ["# Congelamento della previsione della Legge 1", "",
           f"Dati della fase B: {nomi_b}, {len(righe)} episodi.", "", "## Controlli dei dati", ""]
    out += [f"- PROBLEMA: {p}" for p in problemi] or ["- nessun problema: tutte le celle abilità × spinta × scena "
                                                     "(15-19) presenti una volta, ogni scena con lo stesso stato "
                                                     "iniziale a tutte le spinte, scene diverse con stati diversi"]
    out += ["", "## Classifica prevista (T̂ = M / v, dalla più fragile alla più robusta)", "",
            "| Posto | Abilità | M (cm) | v (mm/passo) | T̂ (passi) | Successo a 0 cm | Successi per spinta |",
            "|---|---|---|---|---|---|---|"]
    for i, t in enumerate(valide, 1):
        p = prev[t]
        m = f"≥ {p['margine_cm']:.2f} (censurata)" if p["censurato"] else f"{p['margine_cm']:.2f}"
        succ = " / ".join(f"{cm:g}: {round(f * A.EP_B)}" for cm, f in zip(p["spinte"], p["frazioni"]))
        out.append(f"| {i} | {NOMI[t]} | {m} | {p['vel_m_passo'] * 1000:.2f} | {p['tolleranza_passi']:.2f} | "
                   f"{p['successo_base_b']:.0%} | {succ} |")
    for t in escluse:
        motivo = "dati incompleti" if prev[t] is None else "mai riuscita a 0 cm, o velocità non misurabile"
        out.append(f"| esclusa | {NOMI[t]} | | | | | {motivo} |")
    censurate = [NOMI[t] for t in valide if prev[t]["censurato"]]
    out += ["", "Analisi di sensibilità: " + (f"le censurate ({', '.join(censurate)}) vanno tutte a pari merito in "
                                               "cima alla classifica, le altre restano nell'ordine sopra."
                                               if censurate else "nessuna abilità censurata, coincide con la principale.")]
    if comando_c:
        out += ["", "## Comando esatto della fase C (cella del notebook Kaggle)", "", "```",
                open(comando_c, encoding="utf-8").read().rstrip(), "```"]
    out += ["", "## Hash SHA-256", "", "| File | SHA-256 |", "|---|---|"]
    out += [f"| `{os.path.basename(f)}` | `{sha256(f)}` |" for f in list(percorsi_b) + list(altri)]
    qui = os.path.dirname(os.path.abspath(__file__))
    out += [f"| `{f}` (fine riga LF, per la fase C) | `{sha256(os.path.join(qui, f), lf=True)}` |" for f in CODICE]
    if codice_b:
        out += [f"| `{f}` (fine riga LF, eseguito nella fase B) | `{sha256(os.path.join(codice_b, f), lf=True)}` |"
                for f in sorted(os.listdir(codice_b)) if os.path.isfile(os.path.join(codice_b, f))]
    return "\n".join(out) + "\n", problemi


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = argparse.ArgumentParser()
    a.add_argument("--b", action="append", required=True, help="file della fase B (e B2), nell'ordine")
    a.add_argument("--codice-b", help="cartella con le copie del codice eseguito nella fase B")
    a.add_argument("--comando-c", help="file con la cella esatta del notebook per la fase C")
    a.add_argument("altri", nargs="*", help="altri file da fissare (curve di sviluppo, pip_freeze.txt)")
    arg = a.parse_args()
    testo, problemi = rapporto(arg.b, arg.altri, arg.codice_b, arg.comando_c)
    print(testo, end="")
    sys.exit(1 if problemi else 0)
