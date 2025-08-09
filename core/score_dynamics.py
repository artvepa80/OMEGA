# Sistema de puntuación adaptativa# score_dynamics.py – Sistema de puntuación adaptativa para OMEGA PRO AI

import numpy as np

def score_combination(combination, memory):
    """
    Calcula un puntaje para una combinación dada usando criterios adaptativos.
    """

    score = 0
    history = memory.get_full_history()

    # 1. Suma total ideal (entre 105 y 145)
    total = sum(combination)
    if 105 <= total <= 145:
        score += 1.5
    else:
        score -= 0.5

    # 2. Saltos entre números
    jumps = [abs(combination[i+1] - combination[i]) for i in range(len(combination)-1)]
    jump_sum = sum(jumps)
    if 25 <= jump_sum <= 35:
        score += 1.0
    else:
        score -= 0.5

    # 3. Balance pares/impares
    evens = len([n for n in combination if n % 2 == 0])
    if 2 <= evens <= 4:
        score += 1.2
    else:
        score -= 0.4

    # 4. Penalizar combinaciones repetidas
    if any(set(combination) == set(row) for row in history.values.tolist()):
        score -= 3.0

    # 5. Penalizar combinaciones con más de 2 números del último sorteo
    latest = memory.get_latest_draw()
    repeated = len(set(combination) & set(latest))
    if repeated > 2:
        score -= 1.5

    return score
