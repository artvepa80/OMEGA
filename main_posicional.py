# main_posicional.py

from core.predictor import OmegaPredictor

omega = OmegaPredictor()
omega.set_positional_analysis(True)
resultados = omega.run_all_models()

print("\n=== Resultados del modelo OMEGA PRO AI v10.2 con LSTM Posicional ===")
for idx, r in enumerate(resultados, 1):
    print(f"{idx}. {r['combination']} - Modelo: {r['source']}")