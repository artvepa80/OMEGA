def score_combinations(combinations, historial, config=None):
    scored = []

    try:
        for idx, combo_data in enumerate(combinations):
            if not isinstance(combo_data, dict):
                print(f"❌ [Score] Entrada {idx} no es un dict:", combo_data)
                continue
            if "combination" not in combo_data:
                print(f"❌ [Score] Falta clave 'combination' en entrada {idx}:", combo_data)
                continue

            combo = combo_data["combination"]
            if not isinstance(combo, (list, tuple)):
                print(f"❌ [Score] Formato inválido de combinación en entrada {idx}:", combo)
                continue
            if any(not isinstance(x, int) for x in combo):
                print(f"❌ [Score] Elementos no enteros en entrada {idx}:", combo)
                continue
            if len(combo) != 6:
                print(f"❌ [Score] Longitud distinta de 6 en entrada {idx}:", combo)
                continue

            source = combo_data.get("source", "desconocido")
            score = 0
            bonus = 0

            # 🎯 1. Suma total entre 105 y 145
            total = sum(combo)
            if 105 <= total <= 145:
                score += 1

            # 🎯 2. Pares entre 2 y 4
            pares = sum(1 for n in combo if n % 2 == 0)
            if 2 <= pares <= 4:
                score += 1

            # 🎯 3. Saltos entre 25 y 35
            saltos = sum(abs(combo[i] - combo[i - 1]) for i in range(1, len(combo)))
            if 25 <= saltos <= 35:
                score += 1

            # 🎯 4. Repetidos con sorteo anterior (máx 2)
            ultimos = historial.iloc[-1].dropna().astype(int).tolist()
            repetidos = len(set(combo) & set(ultimos))
            if repetidos <= 2:
                score += 1

            # ⚡ BONUS: Presencia de extremos bajos (1–5)
            extremos_bajos = sum(1 for n in combo if n in [1, 2, 3, 4, 5])
            if extremos_bajos >= 2:
                bonus += 0.25  # puedes subir a 0.5 si quieres enfatizarlo más

            scored.append({
                "combination": combo,
                "score": round((score / 4.0) + bonus, 3),
                "source": source
            })

        return scored

    except Exception as e:
        print("❌ [Score] Error inesperado:", e)
        return -1