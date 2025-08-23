import streamlit as st
import pandas as pd
import json
import joblib
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

# Paths
ARTIFACT_DIR = Path("/mnt/data/models")  # Asegúrate de actualizar si es necesario
latest_run = sorted(ARTIFACT_DIR.glob("*"), reverse=True)[0]
report_path = latest_run / "full_results.json"
model_path = latest_run / f"best_model_{latest_run.name.split('_')[-1]}.pkl"
log_path = latest_run / "jackpot_profiler.log"
feature_plot_path = Path("/mnt/data/feature_importances.png")  # O úsalo dinámicamente si lo guardas por timestamp

# Layout
st.set_page_config(layout="wide")
st.title("🎯 Jackpot Profiler Dashboard")
st.markdown(f"📁 Mostrando resultados de: `{latest_run.name}`")

# === SECCIÓN 1: LOG DE EJECUCIÓN ===
with st.expander("📜 Log de Ejecución"):
    if log_path.exists():
        log_content = log_path.read_text()
        st.text_area("Log completo", log_content, height=300)
    else:
        st.warning("Log no encontrado")

# === SECCIÓN 2: IMPORTANCIA DE CARACTERÍSTICAS ===
st.subheader("📊 Importancia de Características")
if feature_plot_path.exists():
    st.image(str(feature_plot_path), caption="Gráfico de Importancia de Características")
else:
    st.warning("Gráfico de características no encontrado")

# === SECCIÓN 3: REPORTE DE CLASIFICACIÓN ===
st.subheader("📈 Resultados por Modelo")
if report_path.exists():
    with open(report_path) as f:
        results = json.load(f)
    
    for model_name, data in results.items():
        st.markdown(f"### 🤖 {model_name}")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("F1 Score", f"{data['f1_score']:.4f}")
        
        with col2:
            st.json(data['report'], expanded=False)
else:
    st.error("No se encontró el archivo de resultados")

# === SECCIÓN 4: PRUEBA DE PREDICCIÓN ===
st.subheader("🔍 Prueba con Combinación Manual")

if model_path.exists():
    model = joblib.load(model_path)
    input_combo = st.text_input("Introduce una combinación de 6 números separados por comas (ej: 5,12,23,34,35,40)")

    if st.button("Evaluar"):
        try:
            nums = [int(x.strip()) for x in input_combo.split(",")]
            if len(nums) != 6:
                st.error("Debes ingresar exactamente 6 números")
            else:
                # Generar features temporalmente
                def extract_temp_features(combo):
                    arr = np.array(combo)
                    sorted_arr = np.sort(arr)
                    stats = [np.sum(arr), np.mean(arr), np.std(arr),
                             np.min(arr), np.max(arr), np.ptp(arr)]
                    decade_bins = (arr - 1) // 10
                    decades = [np.sum(decade_bins == i) for i in range(4)]
                    entropy_decades = -np.sum((np.bincount(decade_bins, minlength=4) / 6) * 
                                              np.log2(np.bincount(decade_bins, minlength=4) / 6 + 1e-10))
                    normalized = sorted_arr - np.mean(sorted_arr)
                    fft = np.abs(np.fft.rfft(normalized)[:3])
                    diffs = np.diff(sorted_arr)
                    entropy_diffs = -np.sum((np.bincount(diffs) / len(diffs)) *
                                            np.log2(np.bincount(diffs) / len(diffs) + 1e-10))
                    diff_features = [np.max(diffs), np.mean(diffs), entropy_diffs]
                    return np.array([stats + decades + [entropy_decades] + fft.tolist() + diff_features])
                
                X_temp = extract_temp_features(nums)
                proba = model.predict_proba(X_temp)[0]
                label = model.predict(X_temp)[0]
                
                st.success(f"✅ Clase Predicha: `{label}`")
                st.write("📊 Probabilidades por clase:")
                for idx, p in enumerate(proba):
                    st.write(f"Clase {idx}: **{p:.4f}**")
        except Exception as e:
            st.error(f"Error al procesar combinación: {str(e)}")
else:
    st.warning("Modelo no encontrado para evaluación manual")

# Footer
st.markdown("---")
st.caption("Creado por OMEGA PRO AI · Streamlit Dashboard · 2025")
