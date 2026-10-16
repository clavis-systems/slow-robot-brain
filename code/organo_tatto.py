"""Organo del tatto a distanza per un robot simulato (LIBERO + SmolVLA).

Il cervello (SmolVLA) guarda la scena, poi esegue N mosse alla cieca. Questo script
avvolge `lerobot-eval` e, a ogni mossa, puo':
  - spostare l'oggetto da prendere mentre il braccio si avvicina (PERTURBA=1);
  - far riaprire gli occhi al cervello quando un organo suona l'allarme:
      ORGANO=tof      sensori laser a tempo di volo, uno per dito, puntati in avanti;
      ORGANO=altezza  nessun sensore: la mano e' a meno di H_ALT dal piano dell'oggetto;
      ORGANO=dove     sposta il movimento a memoria di quanto si e' spostato l'oggetto (rilevatore ideale).
Scrive una riga JSON per episodio in OUT.

Uso (dentro WSL, nell'ambiente ~/robotica/.venv):
  ORGANO=tof PERTURBA=1 OUT=r.jsonl python organo_tatto.py --policy.path=... (argomenti di lerobot-eval)
"""

import hashlib
import json
import os
import zlib

import mujoco
import numpy as np

import lerobot.scripts.lerobot_eval as E
from cervello_lento import CervelloLento

ORGANO = os.environ.get("ORGANO", "nessuno")
PERTURBA = os.environ.get("PERTURBA", "0") == "1"
D_TOF = float(os.environ.get("D_TOF", "0.06"))  # metri: allarme se un raggio vede qualcosa piu' vicino
H_ALT = float(os.environ.get("H_ALT", "0.12"))  # metri sopra il centro iniziale dell'oggetto
DIST_SPOSTA = float(os.environ.get("DIST_SPOSTA", "0.06"))
PORTATA_TOF = 0.30
OUT = os.environ.get("OUT", "organo_tatto.jsonl")
RITARDO = int(os.environ.get("RITARDO", "-1"))  # passi che il cervello impiega a pensare; -1 = esecuzione normale
LENTO_K = int(os.environ.get("LENTO_K", "8"))  # ogni quanti passi, al massimo, inizia un pensiero
MAX_PASSO_DOVE = float(os.environ.get("MAX_PASSO_DOVE", "0.01"))  # metri di correzione al massimo per passo
STATO_BASE = int(os.environ.get("STATO_BASE", "-1"))  # >= 0: l'episodio n usa la scena iniziale STATO_BASE + n
SPINTA_CM = float(os.environ.get("SPINTA_CM", "0"))  # ORGANO=spinta: il cervello vede la mano spostata di tanti cm
N_DIREZIONI = int(os.environ.get("N_DIREZIONI", "5"))  # direzioni equidistanti della spinta, una per episodio
PASSI_FINALI = 32  # velocità "vicino al contatto": i passi prima del primo successo
ARRIVI_SALVATI = 12  # misure del meccanismo salvate per episodio


def _nome_con(m, tipo, *pezzi):
    n = {mujoco.mjtObj.mjOBJ_BODY: m.nbody, mujoco.mjtObj.mjOBJ_SITE: m.nsite}[tipo]
    for pezzo in pezzi:
        for i in range(n):
            nome = mujoco.mj_id2name(m, tipo, i) or ""
            if pezzo in nome:
                yield i, nome
                break


class Gancio:
    """Avvolge l'ambiente vettoriale (batch 1, sincrono) e agisce dopo ogni mossa."""

    def __init__(self, venv, policy, contatore):
        self.venv, self.policy, self.contatore = venv, policy, contatore

    def __getattr__(self, nome):
        return getattr(self.venv, nome)

    def reset(self, **kw):
        e = self.venv.envs[0]
        self.task = getattr(e, "task_description", None) or getattr(e, "task", "?")
        self.ep = contatore_episodi.setdefault(self.task, 0)
        contatore_episodi[self.task] += 1
        if STATO_BASE >= 0:
            if STATO_BASE + self.ep >= len(e._init_states):  # LeRobot ricomincerebbe da 0 senza avvisare
                raise RuntimeError(f"scena {STATO_BASE + self.ep} oltre le {len(e._init_states)} disponibili")
            e.init_state_id = STATO_BASE + self.ep  # scene separate per sviluppo e per test
        self.stato_iniziale = getattr(e, "init_state_id", None)
        out = self.venv.reset(**kw)
        rs = self.venv.envs[0]._env.env
        self.rs, self.m, self.d = rs, rs.sim.model._model, rs.sim.data._data
        self.sito = next(_nome_con(self.m, mujoco.mjtObj.mjOBJ_SITE, "grip_site"))[0]
        self.dita = [i for i, _ in _nome_con(self.m, mujoco.mjtObj.mjOBJ_BODY, "finger_joint1_tip", "finger_joint2_tip")]
        if len(self.dita) < 2:
            self.dita = [i for i, _ in _nome_con(self.m, mujoco.mjtObj.mjOBJ_BODY, "leftfinger", "rightfinger")]
        # In LIBERO-goal il primo "oggetto di interesse" può essere una regione (es. un cassetto): niente giunto.
        self.oggetto = next((o for o in rs.obj_of_interest if o in rs.objects_dict), None)
        self.giunto = rs.objects_dict[self.oggetto].joints[-1] if self.oggetto else None
        self.z0 = float(rs.sim.data.get_joint_qpos(self.giunto)[2]) if self.giunto else None
        # Organo del dove: dove stava l'oggetto all'inizio (il posto "imparato a memoria") e spostamento già applicato.
        self.p0 = rs.sim.data.get_joint_qpos(self.giunto)[:2].copy() if self.giunto else None
        try:
            ctrl = rs.robots[0].controller
            self.metri_per_unita = (np.asarray(ctrl.output_max)[:3] / np.asarray(ctrl.input_max)[:3]).astype(float)
        except (AttributeError, TypeError, IndexError):
            self.metri_per_unita = None  # controllore sconosciuto: l'organo del dove resta spento
        self.offset, self.offset_max, self.passi_chiusa = np.zeros(2), 0.0, 0
        self.prima_chiusa = None  # (distanza mano-oggetto, distanza mano-posto iniziale) alla prima chiusura
        rng = np.random.default_rng(zlib.crc32(f"{self.task}|{self.ep}".encode()))
        self.angolo = float(rng.uniform(0, 2 * np.pi))
        self.spostato, self.passi, self.allarmi, self.tof_min = False, 0, 0, PORTATA_TOF
        self.mano_prec, self.velocita, self.velocita_xy, self.primo_successo = None, [], [], None
        self.hash_stato = hashlib.sha1(np.round(rs.sim.data.qpos, 6).tobytes()).hexdigest()[:12]
        self.direzione = None
        self.contatore[0] = 0
        if ORGANO == "spinta":
            # Misura del margine: il cervello crede che la mano sia spostata di SPINTA_CM, quindi la porta davvero
            # SPINTA_CM più in là del punto a cui mira. Le direzioni sono le stesse per tutte le abilità:
            # N_DIREZIONI angoli equidistanti, scelti dalla scena (così una scena ripetuta ha la stessa direzione).
            self.direzione = (self.stato_iniziale if self.stato_iniziale is not None else self.ep) % N_DIREZIONI
            ang = 2 * np.pi * self.direzione / N_DIREZIONI
            self.offset = SPINTA_CM / 100 * np.array([np.cos(ang), np.sin(ang)])
            out[0]["robot_state"]["eef"]["pos"][0, :2] -= self.offset
        return out

    def _direzione(self):
        z = self.d.site_xmat[self.sito].reshape(3, 3)[:, 2].copy()
        return z if z[2] <= 0 else -z  # verso le punte: all'inizio la pinza guarda in basso

    def _tof(self):
        v = self._direzione()
        gid = np.zeros(1, dtype=np.int32)
        gruppi = np.array([1, 0, 0, 0, 0, 0], dtype=np.uint8)  # solo geometrie di collisione
        migliore = PORTATA_TOF
        for b in self.dita:
            p = self.d.xpos[b] + v * 0.005
            dist = mujoco.mj_ray(self.m, self.d, p, v, gruppi, 1, b, gid)
            if 0 <= dist < migliore:
                migliore = dist
        return migliore

    def _dove(self, azione):
        """Sposta il movimento imparato a memoria di quanto si è spostato l'oggetto, solo durante l'avvicinamento.

        Rilevatore ideale: la posizione vera dell'oggetto (in simulazione). Dopo la presa (pinza chiusa per 3 passi)
        lo spostamento torna a zero, perché il cestino non si è mosso.
        """
        azione = np.array(azione, dtype=float, copy=True)
        chiusa = azione[0, 6] > 0
        self.passi_chiusa = self.passi_chiusa + 1 if chiusa else 0
        delta = self.rs.sim.data.get_joint_qpos(self.giunto)[:2] - self.p0
        obiettivo = np.zeros(2) if self.passi_chiusa >= 3 else delta
        c = np.clip(obiettivo - self.offset, -MAX_PASSO_DOVE, MAX_PASSO_DOVE)
        azione[0, :2] += c / self.metri_per_unita[:2]
        self.offset += c
        self.offset_max = max(self.offset_max, float(np.hypot(*self.offset)))
        return azione

    def step(self, azione):
        if ORGANO == "dove" and self.giunto is not None and self.metri_per_unita is not None:
            azione = self._dove(azione)
        out = self.venv.step(azione)
        self.passi += 1
        mano = self.d.site_xpos[self.sito]
        q = self.rs.sim.data.get_joint_qpos(self.giunto).copy() if self.giunto else None
        if PERTURBA and q is not None and not self.spostato and np.hypot(*(mano[:2] - q[:2])) < 0.10:
            q[0] += DIST_SPOSTA * np.cos(self.angolo)
            q[1] += DIST_SPOSTA * np.sin(self.angolo)
            self.rs.sim.data.set_joint_qpos(self.giunto, q)
            self.rs.sim.data.set_joint_qvel(self.giunto, np.zeros(6))
            mujoco.mj_forward(self.m, self.d)
            self.spostato = True
        q_ora = self.rs.sim.data.get_joint_qpos(self.giunto)[:2].copy() if self.giunto else None
        chiusa = np.asarray(azione)[0, 6] > 0
        if self.prima_chiusa is None and q_ora is not None and chiusa:
            self.prima_chiusa = (round(float(np.hypot(*(mano[:2] - q_ora))), 4),
                                 round(float(np.hypot(*(mano[:2] - self.p0))), 4))
        if ORGANO == "dove_stato" and q_ora is not None:
            # Il cervello ragiona nel mondo "imparato a memoria": gli diciamo che la mano è spostata al contrario di
            # quanto si è spostato l'oggetto, e il suo stesso anello di controllo porta la mano sull'oggetto vero.
            self.passi_chiusa = self.passi_chiusa + 1 if chiusa else 0
            obiettivo = np.zeros(2) if self.passi_chiusa >= 3 else q_ora - self.p0
            self.offset += np.clip(obiettivo - self.offset, -MAX_PASSO_DOVE, MAX_PASSO_DOVE)
            self.offset_max = max(self.offset_max, float(np.hypot(*self.offset)))
            out[0]["robot_state"]["eef"]["pos"][0, :2] -= self.offset
        if ORGANO == "spinta":
            out[0]["robot_state"]["eef"]["pos"][0, :2] -= self.offset
        if self.mano_prec is not None:
            self.velocita.append(float(np.linalg.norm(mano - self.mano_prec)))
            self.velocita_xy.append(float(np.linalg.norm(mano[:2] - self.mano_prec[:2])))
        self.mano_prec = np.array(mano, copy=True)
        if self.primo_successo is None and float(np.asarray(out[1]).ravel()[0]) > 0:
            self.primo_successo = len(self.velocita_xy)
        tof = self._tof()
        self.tof_min = min(self.tof_min, tof)
        allarme = (ORGANO == "tof" and tof < D_TOF) or (ORGANO == "altezza" and self.z0 is not None and mano[2] - self.z0 < H_ALT)
        if allarme:
            self.allarmi += 1
            self.policy._queues["action"].clear()  # occhi aperti: alla prossima mossa il cervello riguarda
        return out


contatore_episodi = {}
_rollout_originale = E.rollout


def _rendi_lento(policy):
    """RITARDO >= 0: il robot continua a muoversi mentre il cervello pensa (vedi cervello_lento.py)."""
    if RITARDO < 0 or hasattr(policy, "_lento"):
        return
    import torch

    def pensa(batch):
        with torch.no_grad():
            return policy.predict_action_chunk(batch)

    policy._lento = CervelloLento(pensa, RITARDO, LENTO_K)
    reset_originale = policy.reset

    def reset_lento(*aa, **kk):
        reset_originale(*aa, **kk)
        policy._lento.reset()

    policy.reset = reset_lento
    policy.select_action = lambda batch, *aa, **kk: policy._lento(batch)


def rollout_con_organo(env, policy, *a, **k):
    _rendi_lento(policy)
    contatore = [0]
    if not hasattr(policy, "_chiamate_avvolte"):
        originale = policy._get_action_chunk

        def contato(*aa, **kk):
            policy._contatore[0] += 1
            return originale(*aa, **kk)

        policy._get_action_chunk = contato
        policy._chiamate_avvolte = True
    policy._contatore = contatore
    g = Gancio(env, policy, contatore)
    ret = _rollout_originale(g, policy, *a, **k)
    riga = {
        "organo": ORGANO, "perturba": PERTURBA, "n_action_steps": policy.config.n_action_steps,
        "ritardo": RITARDO, "lento_k": LENTO_K if RITARDO >= 0 else None,
        "task": g.task, "ep": g.ep, "successo": bool(ret["success"].any()),
        "chiamate_cervello": contatore[0], "passi": g.passi, "spostato": g.spostato,
        "allarmi": g.allarmi, "tof_min": round(g.tof_min, 4), "offset_max": round(g.offset_max, 4),
        "stato_iniziale": g.stato_iniziale, "hash_stato": g.hash_stato,
        "spinta_cm": SPINTA_CM if ORGANO == "spinta" else 0.0, "n_direzioni": N_DIREZIONI if ORGANO == "spinta" else None,
        "direzione": g.direzione,
        "vel_finale_xy": (round(float(np.median(g.velocita_xy[max(0, g.primo_successo - PASSI_FINALI):g.primo_successo])), 5)
                          if g.primo_successo else None),
        "cambio_piano_medio": (round(float(np.mean(policy._lento.cambi_piano)), 4)
                               if getattr(policy, "_lento", None) and policy._lento.cambi_piano else None),
        "scarto_attesa_medio": (round(float(np.mean(policy._lento.scarti_attesa)), 4)
                                if getattr(policy, "_lento", None) and policy._lento.scarti_attesa else None),
        # Meccanismo (esplorativo): i primi ARRIVI_SALVATI valori, uno per arrivo di piano.
        "cambi_piano": ([round(float(v), 5) for v in policy._lento.cambi_piano[:ARRIVI_SALVATI]]
                        if getattr(policy, "_lento", None) else None),
        "scarti_attesa": ([round(float(v), 5) for v in policy._lento.scarti_attesa[:ARRIVI_SALVATI]]
                          if getattr(policy, "_lento", None) else None),
        "vel_mediana": round(float(np.median(g.velocita)), 5) if g.velocita else None,
        "vel_media": round(float(np.mean(g.velocita)), 5) if g.velocita else None,
        "dist_mano_oggetto": g.prima_chiusa[0] if g.prima_chiusa else None,
        "dist_mano_p0": g.prima_chiusa[1] if g.prima_chiusa else None,
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(riga) + "\n")
    return ret


if __name__ == "__main__":
    E.rollout = rollout_con_organo
    E.main()
