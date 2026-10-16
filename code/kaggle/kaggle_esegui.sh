#!/usr/bin/env bash
# Kaggle (due GPU T4): Legge 1 della freschezza (premessa PREMESSA_LEGGE1.md, versione 3).
#   FASE=B   margine e velocità: spinte 0-16 cm, scene 15-19, 10 abilità
#   FASE=B2  estensione per le censurate: spinte 24 e 32 cm, abilità in COMPITI_G0 / COMPITI_G1 (es. '[1]' '[7]')
#   FASE=C   prova decisiva, scene 25-44: ritardo 0 e 16 con K=8, poi il controllo ritardo 0 con K=16
#   FASE=C1  solo ritardo 0 e 16;  FASE=C2  solo il controllo
#   FASE=R   ripresa di una condizione di C (R_RITARDO, R_K) per le abilità COMPITI_G0 / COMPITI_G1;
#            le righe già presenti si ripetono e l'analisi tiene la prima.
set -uo pipefail
INIZIO=$(date +%s); BUDGET=${BUDGET:-30000}
REV_MODELLO=${REV_MODELLO:-6721902bc4d61e50a3bfdb11dfb4cb626f05d102}  # smolvla_libero, la revisione della fase B
N_COPIE=$(find /kaggle/input -name organo_tatto.py | wc -l)
[ "$N_COPIE" = 1 ] || { echo "STOP: $N_COPIE copie del codice in /kaggle/input"; exit 1; }
CODICE=$(dirname "$(find /kaggle/input -name organo_tatto.py)")
W=/kaggle/working; R=/tmp/robotica; mkdir -p "$R" "$W/out"
[ -z "$(ls -A "$W/out")" ] || { echo "STOP: $W/out non è vuota (usare una versione salvata nuova)"; exit 1; }
echo "codice in $CODICE"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; python3 --version
echo "hash del codice (SHA-256, fine riga LF):"
for f in "$CODICE"/*; do printf '%s  %s\n' "$(tr -d '\r' < "$f" | sha256sum | cut -d' ' -f1)" "$(basename "$f")"; done
# Versioni della fase B (vincoli.txt = il suo pip freeze): torch e torchvision esatti dall'indice di PyTorch, il resto
# vincolato nell'installazione da PyPI (i pacchetti di torch restano fuori: vengono dall'altro indice).
FASE=${FASE:-B}
TORCH_REQ=("torch==2.11.*" "torchvision==0.26.*"); VINCOLI=()
[ "$FASE" = B ] || [ -f "$CODICE/vincoli.txt" ] || { echo "STOP: manca vincoli.txt (versioni della fase B)"; exit 1; }
if [ -f "$CODICE/vincoli.txt" ]; then
  T=$(grep -iE '^torch==' "$CODICE/vincoli.txt"); TV=$(grep -iE '^torchvision==' "$CODICE/vincoli.txt")
  [ -n "$T" ] && [ -n "$TV" ] || { echo "STOP: vincoli.txt senza torch o torchvision"; exit 1; }
  TORCH_REQ=("$T" "$TV")
  grep -viE '^((torch|torchvision|torchaudio|triton)==|nvidia-)' "$CODICE/vincoli.txt" | grep -E '^[A-Za-z0-9_.-]+==' \
    > "$R/vincoli_pypi.txt"
  VINCOLI=(-c "$R/vincoli_pypi.txt")
  echo "versioni fissate da vincoli.txt: ${TORCH_REQ[*]} e $(wc -l < "$R/vincoli_pypi.txt") pacchetti da PyPI"
fi
# Fase B-bis (completamento, premessa "Deviazioni"): servono le liste delle abilità, i vincoli e i dati B precedenti,
# e le abilità da misurare non devono essere già nei b_*.jsonl.
PREC=("$CODICE"/b_*.jsonl); [ -e "${PREC[0]}" ] || PREC=()
if [ "$FASE" = B ] && [ -n "${COMPITI_G0:-}${COMPITI_G1:-}${PREC[*]}" ]; then
  [ -n "${COMPITI_G0:-}" ] && [ -n "${COMPITI_G1:-}" ] && [ -f "$CODICE/vincoli.txt" ] && [ ${#PREC[@]} -gt 0 ] \
    || { echo "STOP: B-bis senza COMPITI_G0, COMPITI_G1, vincoli.txt o b_*.jsonl"; exit 1; }
  python3 - "$COMPITI_G0" "$COMPITI_G1" "${PREC[@]}" <<'EOF' || { echo "STOP: abilità della B-bis già misurate"; exit 1; }
import json, sys
nuove = json.loads(sys.argv[1]) + json.loads(sys.argv[2])
ordine = ["open the middle drawer of the cabinet", "put the bowl on the stove", "put the wine bottle on top of the cabinet",
          "open the top drawer and put the bowl inside", "put the bowl on top of the cabinet",
          "push the plate to the front of the stove", "put the cream cheese in the bowl", "turn on the stove",
          "put the bowl on the plate", "put the wine bottle on the rack"]
gia = {json.loads(r)["task"] for f in sys.argv[3:] for r in open(f) if r.strip()}
doppie = [i for i in nuove if ordine[i] in gia]
print("B-bis: abilità", nuove, "- già misurate nei file precedenti:", sorted(ordine.index(t) for t in gia))
sys.exit(1 if doppie or len(set(nuove)) != len(nuove) else 0)
EOF
  echo "B-bis: GPU0 $COMPITI_G0, GPU1 $COMPITI_G1"
fi
cd "$R"
echo "[1] uv e Python 3.12"; pip install -q uv && uv python install 3.12 -q && uv venv -q -p 3.12 .venv || exit 1
PY="$R/.venv/bin/python"
echo "[2] torch"; uv pip install -q -p "$PY" "${TORCH_REQ[@]}" --index-url https://download.pytorch.org/whl/cu128 || exit 1
echo "[3] lerobot"; export CMAKE_POLICY_VERSION_MINIMUM=3.5 PATH="$R/.venv/bin:$PATH"
uv pip install -q -p "$PY" ${VINCOLI[@]+"${VINCOLI[@]}"} cmake \
  && uv pip install -q -p "$PY" ${VINCOLI[@]+"${VINCOLI[@]}"} "lerobot[smolvla,libero]==0.6.1" || exit 1
# Kaggle impone MPLBACKEND=matplotlib_inline (assente nel nostro ambiente); LIBERO al primo avvio fa una domanda.
export MPLBACKEND=Agg
LIB=$("$PY" -c "import importlib.util,os;print(os.path.dirname(importlib.util.find_spec('libero').origin))")/libero
mkdir -p ~/.libero && printf 'assets: %s/./assets
bddl_files: %s/./bddl_files
benchmark_root: %s
datasets: %s/../datasets
init_states: %s/./init_files
' "$LIB" "$LIB" "$LIB" "$LIB" "$LIB" > ~/.libero/config.yaml
echo "[4] modello, revisione $REV_MODELLO"
"$R/.venv/bin/hf" download HuggingFaceVLA/smolvla_libero --revision "$REV_MODELLO" --local-dir "$R/smolvla_libero" \
  > /dev/null || exit 1
"$PY" -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available(),torch.cuda.get_device_name(0))"
prova_gl() { MUJOCO_GL=$1 "$PY" -c "import mujoco;m=mujoco.MjModel.from_xml_string('<mujoco/>');mujoco.Renderer(m).render();print('$1 ok')"; }
if prova_gl egl; then GL=egl; else
  echo "[5] librerie grafiche"; apt-get -qq update && apt-get -qq install -y libegl1 libgl1 libosmesa6 > /dev/null
  if prova_gl egl; then GL=egl; elif prova_gl osmesa; then GL=osmesa; else echo "STOP: nessun rendering"; exit 1; fi
fi
echo "rendering: $GL; preparazione in $(( $(date +%s) - INIZIO )) s"
[ "$GL" = egl ] || { echo "STOP: rendering $GL diverso dalla fase B (egl)"; exit 1; }
corri() {  # NOME FILE_OUT N_EPISODI [COMPITI_GPU0] [COMPITI_GPU1]  + variabili d'ambiente per organo_tatto
  # Due processi in parallelo, uno per ciascuna delle due T4: metà delle abilità ciascuno, file separati, poi uniti.
  RESTA=$(( BUDGET - ($(date +%s) - INIZIO) )); [ $RESTA -lt 1200 ] && { echo "$1 saltata: tempo finito"; return; }
  s=$(date +%s)
  local T0=${4:-[0,1,2,3,4]} T1=${5:-[5,6,7,8,9]}
  for G in 0 1; do
    local T=$T0; [ $G = 1 ] && T=$T1
    [ "$T" = "-" ] && continue
    # Con CUDA_VISIBLE_DEVICES=1 EGL vedeva una sola scheda e la seconda T4 falliva ("between 0 and 0", fase B del
    # 13/10). Entrambe visibili con la nostra per prima: torch usa cuda:0 = GPU G. L'indice EGL 0 esiste sempre e
    # passa il controllo di robosuite ("0" è in "G,1-G"); quale scheda fisica disegna dipende dall'ordine del driver.
    CUDA_VISIBLE_DEVICES=$G,$((1 - G)) MUJOCO_EGL_DEVICE_ID=0 MUJOCO_GL=$GL OUT="$W/out/$1_g$G.jsonl" timeout $RESTA \
      "$PY" "$CODICE/organo_tatto.py" --policy.path="$R/smolvla_libero" --env.type=libero --env.task=libero_goal \
      --env.task_ids="$T" --eval.batch_size=1 --eval.n_episodes=$3 --eval.use_async_envs=false --policy.device=cuda \
      --output_dir="$R/out/$1_g$G" < /dev/null > "$W/out/$1_g$G.log" 2>&1 &
  done
  wait
  cat "$W/out/$1"_g*.jsonl >> "$W/out/$2" 2>/dev/null
  echo "$1: $(cat "$W/out/$1"_g*.jsonl 2>/dev/null | wc -l) episodi in $(( $(date +%s)-s )) s" \
    "(per GPU: $(for f in "$W/out/$1"_g*.jsonl; do [ -e "$f" ] && printf '%s ' "$(wc -l < "$f")"; done))"
  for f in "$W/out/$1"_g*.log; do tail -c 600 "$f" | tr '\r' '\n' | grep -iE "error|traceback" | tail -2; done
}
"$PY" -m pip freeze > "$W/out/pip_freeze.txt" 2>/dev/null || uv pip freeze -p "$PY" > "$W/out/pip_freeze.txt"
# Prova di fumo: 1 episodio per GPU, scena 49 (riservata); si ferma subito se una delle due GPU non produce risultati.
ORGANO=spinta SPINTA_CM=2 N_DIREZIONI=5 PERTURBA=0 RITARDO=16 LENTO_K=8 STATO_BASE=49 corri fumo fumo.jsonl 1 '[7]' '[0]'
[ "$(grep -c '"hash_stato"' "$W/out/fumo.jsonl" 2>/dev/null)" -ge 2 ] 2>/dev/null || {
  echo "STOP: la prova di fumo non ha prodotto una riga per GPU"; tail -c 1500 "$W/out"/fumo_g*.log; exit 1; }
# Revisioni dei modelli scaricati dalla cache (il processore del VLM si scarica senza revisione fissata).
for f in ~/.cache/huggingface/hub/models--*/refs/main; do [ -e "$f" ] && echo "revisione $(basename "$(dirname "$(dirname "$f")")"): $(cat "$f")"; done
case "$FASE" in
  B)  # Margine e velocità, scene 15-19, 5 direzioni equidistanti, spinte 0-16 cm (abilità: COMPITI_G0 / COMPITI_G1).
    for CM in 0 2 4 8 12 16; do
      ORGANO=spinta SPINTA_CM=$CM N_DIREZIONI=5 PERTURBA=0 RITARDO=0 LENTO_K=8 STATO_BASE=15 \
        corri "b_spinta_$CM" b.jsonl 5 "${COMPITI_G0:-[0,1,2,3,4]}" "${COMPITI_G1:-[5,6,7,8,9]}"
    done
    # Regola della fase B2 (premessa): se almeno 3 abilità sono censurate a 16 cm, contando i dati B delle sessioni
    # precedenti (b_*.jsonl nel dataset), si misurano subito 24 e 32 cm per quelle sole, metà per GPU.
    PREC=("$CODICE"/b_*.jsonl); [ -e "${PREC[0]}" ] || PREC=()
    CENS=$("$PY" "$CODICE/analisi_legge1.py" censurate ${PREC[@]+"${PREC[@]}"} "$W/out/b.jsonl")
    if [ -n "$CENS" ]; then
      IFS=, read -ra L <<< "$CENS"; H=$(( (${#L[@]} + 1) / 2 ))
      C0=$(IFS=,; echo "${L[*]:0:H}"); C1=$(IFS=,; echo "${L[*]:H}")
      echo "fase B2 per le censurate: [$C0] e [${C1:--}]"
      for CM in 24 32; do
        ORGANO=spinta SPINTA_CM=$CM N_DIREZIONI=5 PERTURBA=0 RITARDO=0 LENTO_K=8 STATO_BASE=15 \
          corri "b2_spinta_$CM" b2.jsonl 5 "[$C0]" "$([ -n "$C1" ] && echo "[$C1]" || echo -)"
      done
    fi
    B2=(); [ -s "$W/out/b2.jsonl" ] && B2=("$W/out/b2.jsonl")
    "$PY" "$CODICE/analisi_legge1.py" previsione ${PREC[@]+"${PREC[@]}"} "$W/out/b.jsonl" ${B2[@]+"${B2[@]}"} ;;
  B2)  # Solo per le censurate a 16 cm (regola della premessa), stesse scene e direzioni.
    for CM in 24 32; do
      ORGANO=spinta SPINTA_CM=$CM N_DIREZIONI=5 PERTURBA=0 RITARDO=0 LENTO_K=8 STATO_BASE=15 \
        corri "b2_spinta_$CM" b2.jsonl 5 "${COMPITI_G0:--}" "${COMPITI_G1:--}"
    done ;;
  C|C1|C2)  # Prova decisiva, solo dopo il congelamento. Prima le due condizioni dell'ipotesi, poi il controllo.
    if [ "$FASE" != C2 ]; then
      ORGANO=nessuno PERTURBA=0 RITARDO=0 LENTO_K=8 STATO_BASE=25 corri c_d0 c.jsonl 20
      ORGANO=nessuno PERTURBA=0 RITARDO=16 LENTO_K=8 STATO_BASE=25 corri c_d16 c.jsonl 20
    fi
    if [ "$FASE" != C1 ]; then
      ORGANO=nessuno PERTURBA=0 RITARDO=0 LENTO_K=16 STATO_BASE=25 corri c_k16 c.jsonl 20
    fi
    "$PY" "$CODICE/riassunto.py" "$W/out" "c_*_g*.jsonl" ;;
  R)
    ORGANO=nessuno PERTURBA=0 RITARDO=$R_RITARDO LENTO_K=$R_K STATO_BASE=25 \
      corri "c_ripresa_d${R_RITARDO}_k${R_K}" c.jsonl 20 "${COMPITI_G0:--}" "${COMPITI_G1:--}" ;;
  *) echo "STOP: FASE sconosciuta: $FASE"; exit 1 ;;
esac
echo "FINITO in $(( $(date +%s) - INIZIO )) s"
