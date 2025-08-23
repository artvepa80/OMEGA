import numpy as np
from collections import Counter

def apply_strategic_filters(combinations, data, previous_results, modo_ataque=False):
    """
    Filtro dinámico adaptativo para OMEGA PRO AI.
    Si `modo_ataque=True`, se relajan restricciones para aprovechar sesgos del RNG.
    """

    last_draw = data.values[-1].tolist()
    historical_set = {tuple(sorted(row)) for row in data.values.tolist()}
    previous_recent = {tuple(sorted(r)) for r in previous_results[-30:]}

    def suma_total(comb):
        return sum(comb)

    def suma_saltos(comb):
        return sum(abs(b - a) for a, b in zip(comb[:-1], comb[1:]))

    def cantidad_pares(comb):
        return sum(1 for x in comb if x % 2 == 0)

    def repetidos_ult_sorteo(comb):
        return len(set(comb) & set(last_draw))

    def es_valida(comb):
        s = suma_total(comb)
        saltos = suma_saltos(comb)
        pares = cantidad_pares(comb)
        rep_last = repetidos_ult_sorteo(comb)

        if modo_ataque:
            return (
                95 <= s <= 155 and
                20 <= saltos <= 40 and
                1 <= pares <= 5 and
                rep_last <= 3
            )
        else:
            return (
                105 <= s <= 145 and
                25 <= saltos <= 35 and
                2 <= pares <= 4 and
                rep_last <= 2
            )

    def es_repetida_exacta(comb):
        return tuple(sorted(comb)) in previous_recent or tuple(sorted(comb)) in historical_set

    def frecuencia_individual_excesiva(comb):
        flat = data.values.flatten()
        freq = Counter(flat)
        umbral = 190 if modo_ataque else 170
        return any(freq[num] > umbral for num in comb)

    final = []
    descartadas = {
        "repetidas": 0,
        "invalidas": 0,
        "frecuencia_excesiva": 0,
        "mal_formateadas": 0
    }

    for item in combinations:
        raw = item.get("combination", [])

        try:
            if any(isinstance(x, list) for x in raw):
                raw = [int(i) for sub in raw for i in (sub if isinstance(sub, list) else [sub])]
            else:
                raw = [int(x) for x in raw]

            if len(raw) != 6 or any(not isinstance(x, int) for x in raw):
                raise ValueError("Formato incorrecto")

        except Exception:
            descartadas["mal_formateadas"] += 1
            continue

        if es_repetida_exacta(raw):
            descartadas["repetidas"] += 1
            continue
        if not es_valida(raw):
            descartadas["invalidas"] += 1
            continue
        if frecuencia_individual_excesiva(raw):
            descartadas["frecuencia_excesiva"] += 1
            continue

        item["combination"] = raw
        final.append(item)

    print("📊 Descartadas por motivo:")
    for k, v in descartadas.items():
        print(f"   - {k}: {v}")

    return final
