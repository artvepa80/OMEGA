from __future__ import annotations
import math, random
from typing import Dict


class UCB1Policy:
    """Política UCB1 simple para selección de configuraciones.

    Mantiene contadores y valores promedio por brazo y aplica el puntaje
    UCB clásico: value + sqrt(2 * ln(t) / n).
    """

    def __init__(self):
        self.counts: Dict[str, int] = {}   # sig -> plays
        self.values: Dict[str, float] = {} # sig -> avg reward
        self.t: int = 0

    def select(self, arms: Dict[str, float]) -> str:
        # arms: sig -> latest observed reward in [0, 1]
        self.t += 1
        for a, r in arms.items():
            if a not in self.counts:
                self.counts[a] = 0
                self.values[a] = 0.0
        # play each untried arm once
        for a in arms:
            if self.counts[a] == 0:
                self.counts[a] += 1
                self.values[a] = arms[a]
                return a
        # UCB
        ucb_scores = {
            a: self.values[a] + math.sqrt(2 * math.log(max(self.t, 2)) / self.counts[a])
            for a in arms
        }
        chosen = max(ucb_scores, key=ucb_scores.get)
        # update avg with current reward
        r = float(arms[chosen])
        n = self.counts[chosen] + 1
        self.values[chosen] = (self.values[chosen] * self.counts[chosen] + r) / n
        self.counts[chosen] = n
        return chosen


class ThompsonSamplingPolicy:
    """Política Thompson Sampling con priors Beta para recompensas en [0, 1].

    Interpreta la recompensa continua como evidencia en una distribución
    Beta, actualizando alpha con reward y beta con (1 - reward).
    """

    def __init__(self):
        self.alpha: Dict[str, float] = {}  # éxitos
        self.beta: Dict[str, float] = {}   # fracasos

    def select(self, arms: Dict[str, float]) -> str:
        # Inicializar priors
        for a, r in arms.items():
            if a not in self.alpha:
                self.alpha[a] = 1.0
                self.beta[a] = 1.0
        # Samplear de Beta(alpha, beta)
        samples = {a: random.betavariate(self.alpha[a], self.beta[a]) for a in arms}
        chosen = max(samples, key=samples.get)
        # Actualizar posterior con la recompensa observada del brazo elegido
        r = float(arms[chosen])
        self.alpha[chosen] += max(0.0, min(1.0, r))
        self.beta[chosen] += max(0.0, min(1.0, 1.0 - r))
        return chosen
