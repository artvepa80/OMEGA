# rules_filter.py – Filtro estratégico para OMEGA PRO AI

import numpy as np

def suma_total_ok(combination, min_sum=105, max_sum=145):
    total = sum(combination)
    return min_sum <= total <= max_sum

def suma_saltos_ok(combination, min_jump=25, max_jump=35):
    jumps = [abs(b - a) for a, b in zip(combination, combination[1:])]
    return min_jump <= sum(jumps) <= max_jump

def balance_pares_ok(combination, min_pares=2, max_pares=4):
    num_pares = sum(1 for num in combination if num % 2 == 0)
    return min_pares <= num_pares <= max_pares

def no_repetida_exacta(combination, historical_set):
    return tuple(combination) not in historical_set

def aplicar_filtros(combination, historical_combinations_set):
    return (
        suma_total_ok(combination)
        and suma_saltos_ok(combination)
        and balance_pares_ok(combination)
        and no_repetida_exacta(combination, historical_combinations_set)
    )