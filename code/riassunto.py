"""Riassume i file out/n_*.jsonl dell'organo del tatto: successi, chiamate al cervello, allarmi."""

import glob
import json
import os
import sys

cartella = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/robotica/out")
schema = sys.argv[2] if len(sys.argv) > 2 else "n_*.jsonl"
for f in sorted(glob.glob(os.path.join(cartella, schema))):
    righe = [json.loads(r) for r in open(f) if r.strip()]
    if not righe:
        continue
    n = len(righe)
    ok = sum(r["successo"] for r in righe)
    chiamate = sum(r["chiamate_cervello"] for r in righe) / n
    allarmi = sum(r["allarmi"] for r in righe) / n
    spostati = sum(r["spostato"] for r in righe)
    print(f"{os.path.basename(f):22s} successi {ok:2d}/{n:2d}  cervello {chiamate:5.1f}/ep  allarmi {allarmi:5.1f}/ep  spostati {spostati}")
