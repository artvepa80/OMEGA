# test_run.py – Ejecución directa de OMEGA PRO AI v12.0

from core.predictor import HybridOmegaPredictor

def main():
    # Paso 1: Crear instancia del predictor
    predictor = HybridOmegaPredictor(cantidad_final=5)

    # Paso 2 (opcional): Activar exportación automática
    predictor.set_auto_export(True)

    # Paso 3: Ejecutar el pipeline completo
    combinaciones_finales = predictor.run_all_models()

    # Paso 4: Mostrar resultados en consola
    print("\n🎯 Combinaciones Finales Generadas:\n")
    for i, combo in enumerate(combinaciones_finales, start=1):
        print(f"#{i}: {combo['combination']} | Score: {combo['score']:.3f} | SVI: {combo['svi_score']:.2f} | Fuente: {combo['source']}")

if __name__ == "__main__":
    main()