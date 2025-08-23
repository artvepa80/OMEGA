# OMEGA Evaluation Harness

Un framework de evaluación determinista para modelos de predicción de lotería que permite realizar backtesting sistemático con ventanas rodantes y métricas comprensivas.

## 🚀 Características

- **Backtesting con ventanas rodantes** con protección anti-leakage
- **Métricas comprensivas**: hit rates, diversidad, cobertura, puntuación compuesta
- **Reportes HTML interactivos** con gráficos y análisis
- **Reproducibilidad completa** con seeds y manifiestos de entorno
- **Integración nativa con modelos OMEGA** (pipeline, agéntico, híbrido)

## 📦 Instalación

El harness está incluido en OMEGA_PRO_AI_v10.1. No requiere dependencias adicionales.

```bash
cd /path/to/OMEGA_PRO_AI_v10.1
```

## 🔧 Uso Básico

### Comando Principal

```bash
python -m tools.eval_harness.cli backtest \
  --data data/historial_kabala_github_fixed.csv \
  --models consensus,omega_pipeline,omega_hybrid \
  --windows rolling_200 \
  --top_n 10 \
  --seed 42 \
  --out results/accuracy_analysis/run_test
```

### Parámetros

- `--data`: Archivo CSV con datos históricos
- `--models`: Lista de modelos separados por comas
- `--windows`: Configuración de ventanas (ej: `rolling_200`)
- `--top_n`: Número de predicciones por modelo
- `--seed`: Semilla para reproducibilidad
- `--out`: Directorio base de salida

### Modelos Disponibles

#### Modelos Dummy (para testing)
- `consensus`: Predictor consenso básico
- `transformer_deep`: Simulador transformer
- `lstm_v2`: Simulador LSTM
- `genetico`: Simulador genético
- `montecarlo`: Simulador Monte Carlo
- `apriori`: Simulador Apriori

#### Modelos OMEGA Reales
- `omega_pipeline`: Sistema Pipeline v10.1 robusto
- `omega_hybrid`: Sistema híbrido completo
- `omega_agentic`: Sistema agéntico V4.0
- `omega_production`: Wrapper para omega_production_v4.py
- `omega_main`: Wrapper para main.py

## 📊 Salidas Generadas

Cada run genera un directorio timestamped con:

```
results/accuracy_analysis/run_test/run_YYYYMMDD_HHMMSS/
├── args.json                    # Argumentos del run
├── env_manifest.json           # Versiones y entorno
├── backtest_results.csv        # Resultados detallados por ventana
├── summary.csv                 # Resumen por modelo
├── report.html                 # Reporte interactivo
└── plots/
    ├── compound_over_time.png  # Evolución de puntuación compuesta
    └── hit_rates.png           # Tasas de acierto por modelo
```

## 🎯 Ejemplos de Uso

### 1. Evaluación Rápida (desarrollo)
```bash
python -m tools.eval_harness.cli backtest \
  --data data/historial_kabala_github_fixed.csv \
  --models consensus,omega_pipeline \
  --windows rolling_50 \
  --top_n 5 \
  --seed 42 \
  --out results/dev_test
```

### 2. Comparación Completa OMEGA
```bash
python -m tools.eval_harness.cli backtest \
  --data data/historial_kabala_github_fixed.csv \
  --models omega_pipeline,omega_agentic,omega_hybrid \
  --windows rolling_200 \
  --top_n 10 \
  --seed 42 \
  --out results/omega_comparison
```

### 3. Benchmarking Exhaustivo
```bash
python -m tools.eval_harness.cli backtest \
  --data data/historial_kabala_github_fixed.csv \
  --models consensus,transformer_deep,lstm_v2,genetico,omega_pipeline,omega_hybrid \
  --windows rolling_500 \
  --top_n 15 \
  --seed 42 \
  --out results/full_benchmark
```

## 📈 Métricas Incluidas

### Hit Rates
- `hit6`: Predicción top-1 con 6+ aciertos (jackpot)
- `hit5`: Predicción top-1 con 5+ aciertos
- `hit4`: Predicción top-1 con 4+ aciertos

### Análisis de Conjunto
- `best`: Mejor número de aciertos en top-N predicciones
- `diversity`: Diversidad entre predicciones (1 - Jaccard medio)
- `coverage`: Cobertura del espacio de números (1-40)

### Puntuación Compuesta
Sistema de puntos ponderado configurable:
- Hit6: 30% peso (100 puntos)
- Hit5: 25% peso (50 puntos)
- Hit4: 20% peso (10 puntos)
- Best: 15% peso (normalizado)
- Diversity: 10% peso

## 🔒 Protecciones Anti-Leakage

- **Validación temporal**: Test siempre posterior al entrenamiento
- **Índices únicos**: Sin solapamiento entre conjuntos
- **Orden estricto**: Respeta cronología de datos
- **Validación de columnas**: Coherencia entre train/test

## 🔧 Extensión de Modelos

Para agregar un nuevo modelo:

1. **Crear wrapper en `omega_wrappers.py`:**
```python
def mi_modelo_wrapper(train_df: pd.DataFrame, top_n: int) -> List[List[int]]:
    # Tu lógica aquí
    predictions = mi_modelo_predict(train_df, top_n)
    return predictions
```

2. **Registrar en `OMEGA_MODEL_REGISTRY`:**
```python
OMEGA_MODEL_REGISTRY = {
    "mi_modelo": mi_modelo_wrapper,
    # ... otros modelos
}
```

3. **Usar en evaluación:**
```bash
python -m tools.eval_harness.cli backtest \
  --models mi_modelo,omega_pipeline \
  # ... otros parámetros
```

## 🐛 Solución de Problemas

### Error: "Model not found"
Verifica que el modelo esté en `MODEL_REGISTRY` en `backtest.py`.

### Error: "Data file not found"
Verifica la ruta del archivo CSV y que tenga el formato correcto.

### Error: "Leakage detected"
Los datos no están ordenados temporalmente. Asegúrate que hay una columna `fecha` válida.

### Performance lento
- Reduce `--windows` (ej: `rolling_100` en lugar de `rolling_500`)
- Reduce `--top_n`
- Usa menos modelos en la comparación

## 📚 Referencias

- Framework inspirado en prácticas de ML reproducible
- Métricas adaptadas para problemas de lotería multi-clase
- Integración específica con arquitectura OMEGA

---

**Nota**: Este harness está optimizado para el ecosistema OMEGA. Para uso general, modifica los wrappers según tus necesidades.
