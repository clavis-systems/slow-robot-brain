"""Cervello lento: simula un robot che continua a muoversi mentre il cervello pensa.

Ritardo D = passi che il cervello impiega a pensare; K = ogni quanti passi, al massimo, inizia un pensiero.
- Il primo piano arriva subito (il robot parte da fermo).
- Un pensiero parte con l'osservazione di ADESSO, se nessun altro pensiero è in corso e sono passati almeno K passi
  dall'inizio del pensiero precedente. Il cervello pensa una cosa alla volta.
- Il piano arriva D passi dopo e sostituisce quello vecchio; le sue prime D azioni sono già nel passato e si scartano.
- A regime ogni azione viene da un'osservazione vecchia da D a D + max(K, D) - 1 passi.
Con D = 0 equivale all'esecuzione normale di K azioni per pensiero.

Misure del meccanismo (prime 3 componenti dell'azione, la posizione), a ogni arrivo di un piano:
- cambio_piano: quanto il piano nuovo differisce da quello vecchio sulle prossime K azioni (Legge 2: valore dello
  sguardo);
- scarto_attesa: quanto le azioni eseguite durante l'attesa differiscono da quelle che il piano nuovo dava per fatte.
"""


def _distanza(a, b):
    d = (a - b)[..., :3]
    return float((d * d).sum()) ** 0.5


class CervelloLento:
    def __init__(self, pensa, ritardo, k):
        if ritardo < 0 or k < 1:
            raise ValueError("ritardo >= 0 e k >= 1")
        self.pensa, self.d, self.k = pensa, ritardo, k
        self.reset()

    def reset(self):
        self.coda, self.in_arrivo, self.attesa, self.dall_inizio, self.pensieri = [], None, 0, None, 0
        self.eseguite_in_attesa, self.cambi_piano, self.scarti_attesa = [], [], []

    def _arriva(self, piano):
        nuove = [piano[:, i] for i in range(self.d, piano.shape[1])]
        sovrapposte = min(self.k, len(self.coda), len(nuove))
        if sovrapposte:
            self.cambi_piano.append(sum(_distanza(self.coda[i], nuove[i]) for i in range(sovrapposte)))
        if self.eseguite_in_attesa:
            self.scarti_attesa.append(
                sum(_distanza(a, piano[:, i]) for i, a in enumerate(self.eseguite_in_attesa[: self.d])))
        self.coda, self.eseguite_in_attesa = nuove, []

    def __call__(self, osservazione):
        if self.in_arrivo is not None and self.attesa == 0:
            piano, self.in_arrivo = self.in_arrivo, None
            self._arriva(piano)
        if self.in_arrivo is None and (self.dall_inizio is None or self.dall_inizio >= self.k):
            piano = self.pensa(osservazione)
            self.pensieri += 1
            self.dall_inizio = 0
            if self.d == 0 and self.coda:
                self._arriva(piano)  # senza ritardo il piano nuovo sostituisce subito il vecchio
            elif self.d == 0 or not self.coda:
                self.coda = [piano[:, i] for i in range(piano.shape[1])]
            else:
                self.in_arrivo, self.attesa = piano, self.d
        if not self.coda:
            raise RuntimeError("piano finito prima del successivo: ritardo troppo grande per la lunghezza del piano")
        azione = self.coda.pop(0)
        if self.in_arrivo is not None:
            self.attesa -= 1
            self.eseguite_in_attesa.append(azione)
        self.dall_inizio += 1
        return azione
