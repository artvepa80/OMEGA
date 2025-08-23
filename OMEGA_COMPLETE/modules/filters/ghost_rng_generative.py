# OMEGA_PRO_AI_v10.2/modules/filters/ghost_rng_generative.py

import os
import csv
import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import secrets
import logging
from sklearn.preprocessing import MinMaxScaler
from torch import nn, optim, utils
from utils.viabilidad import cargar_viabilidad, calcular_svi
from utils.logger import log_error, log_info
from typing import List, Dict, Any, Tuple, Optional
import sys
import traceback
from datetime import datetime
# ──────────────────────────────────────────────────────────────
# Import del validador – soporta ambas ubicaciones (legacy/new)
# ──────────────────────────────────────────────────────────────
try:
    # Nueva ubicación (>= v10.x)
    from utils.validation import validate_combination
except ImportError:                 # Soporte a versiones viejas
    from core.validation import validate_combination  # fallback legacy

# Configuración de logger
logger = logging.getLogger("ghost_rng_generative")

# Global cache for the autoencoder model
_global_autoencoder_cache = {}

# 1. FUNCIONES HEREDADAS
def calculate_similarity(historial: List[List[int]], draws: List[Tuple[int, ...]]) -> float:
    historial_set = set(tuple(sorted(h)) for h in historial)
    draws_set = set(draws)
    matches = historial_set.intersection(draws_set)
    return len(matches) / max(len(draws_set), 1)

def fft_entropy_spectrum(draws: List[Tuple[int, ...]]) -> float:
    freq_map = {i: 0 for i in range(1, 41)}
    for draw in draws:
        for num in draw:
            freq_map[num] += 1
    freq_vector = np.array(list(freq_map.values()))
    freq_vector = freq_vector / np.sum(freq_vector)
    entropy = -np.sum(freq_vector * np.log2(freq_vector + 1e-12))
    return entropy

# 2. AUTOENCODER CON RUIDO APRENDIDO
class LotteryAutoencoder(nn.Module):
    def __init__(self, input_dim=6):  # Fixed to match single draw (6 numbers)
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 12),
            nn.ReLU(),
            nn.Linear(12, 8),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 12),
            nn.ReLU(),
            nn.Linear(12, input_dim),
            nn.Sigmoid()
        )
        self.noise_scale = nn.Parameter(torch.tensor(0.1))

    def forward(self, x, regimen='A'):
        if x.dim() > 2:
            x = x.view(x.size(0), -1)
        encoded = self.encoder(x)
        if regimen == 'C':
            encoded = encoded + self.noise_scale * torch.randn_like(encoded)
        decoded = self.decoder(encoded)
        return decoded

# 3. ENTRENAMIENTO CON VALIDACIÓN CRUZADA Y BATCH PROCESSING
def entrenar_autoencoder(model, data, window_size=6, epochs=8, patience=3, batch_size=32):
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    train_size = int(0.8 * len(data))
    train_data = data[:train_size]
    val_data = data[train_size:]
    
    train_tensor = torch.tensor(train_data, dtype=torch.float32)
    val_tensor = torch.tensor(val_data, dtype=torch.float32)
    
    if train_tensor.dim() < 2:
        train_tensor = train_tensor.unsqueeze(0)
    if val_tensor.dim() < 2:
        val_tensor = val_tensor.unsqueeze(0)
    
    train_dataset = utils.data.TensorDataset(train_tensor)
    train_loader = utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    best_loss = float('inf')
    patience_counter = 0
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        model.train()
        epoch_losses = []
        for batch in train_loader:
            inputs = batch[0]
            if inputs.dim() > 2:
                inputs = inputs.view(inputs.size(0), -1)
            optimizer.zero_grad()
            outputs = model(inputs, regimen='A')
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())
        
        train_loss = np.mean(epoch_losses)
        train_losses.append(train_loss)
        
        model.eval()
        with torch.no_grad():
            val_inputs = val_tensor
            if val_inputs.dim() > 2:
                val_inputs = val_inputs.view(val_inputs.size(0), -1)
            val_outputs = model(val_inputs, regimen='A')
            val_loss = criterion(val_outputs, val_inputs).item()
            val_losses.append(val_loss)
        
        if val_loss < best_loss:
            best_loss = val_loss
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                log_info(f"🏁 Early stopping en época {epoch + 1}")
                break
        
        log_info(f"Época {epoch+1}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
    
    metrics_df = pd.DataFrame({
        "epoch": range(1, len(train_losses) + 1),
        "train_loss": train_losses,
        "val_loss": val_losses
    })
    log_dir = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)
    metrics_df.to_csv(f"{log_dir}/autoencoder_metrics.csv", index=False)
    
    log_info(f"🏁 Entrenamiento completado | Mejor Val Loss: {best_loss:.4f}")
    return model

def cargar_o_entrenar_autoencoder(historial_numeros, training_mode=True, window_size=6):
    log_dir = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs("models", exist_ok=True)
    global_model_path = "models/autoencoder_global.pt"
    cache_key = f"{global_model_path}_{window_size}"
    
    if cache_key in _global_autoencoder_cache and not training_mode:
        log_info("✅ Retrieved autoencoder from cache")
        return _global_autoencoder_cache[cache_key]
    
    if not training_mode and os.path.exists(global_model_path):
        model = LotteryAutoencoder(input_dim=window_size)
        try:
            model.load_state_dict(torch.load(global_model_path))
            model = torch.quantization.quantize_dynamic(
                model, {nn.Linear}, dtype=torch.qint8
            )
            model.eval()
            log_info("✅ Modelo global cargado y cuantizado")
            _global_autoencoder_cache[cache_key] = model
            return model
        except Exception as e:
            log_info(f"⚠️ Error loading model: {str(e)}, training new model")
    
    if len(historial_numeros) < window_size:
        log_error(f"🚨 Insufficient data for window_size={window_size}, using default")
        return LotteryAutoencoder(input_dim=window_size)
    
    model = LotteryAutoencoder(input_dim=window_size)
    model = entrenar_autoencoder(model, historial_numeros, window_size)
    try:
        torch.save(model.state_dict(), global_model_path)
        log_info("🎯 Modelo global entrenado y guardado")
    except Exception as e:
        log_info(f"⚠️ Error saving model: {str(e)}")
    _global_autoencoder_cache[cache_key] = model
    return model

# 4. GENERACIÓN DETERMINISTA DE COMBINACIONES
def generar_combinacion_determinista(g, scaler, max_numbers=40):
    unscaled = scaler.inverse_transform([g])[0]
    probs = np.clip(unscaled, 0, None)
    probs = probs / np.sum(probs)
    
    indices = np.argsort(probs)[::-1][:6]
    numbers = [i + 1 for i in indices]
    
    if len(set(numbers)) < 6:
        remaining = list(set(range(1, max_numbers + 1)) - set(numbers))
        additional = min(6 - len(set(numbers)), len(remaining))
        numbers = sorted(set(numbers).union(random.sample(remaining, additional)))
    
    return tuple(sorted(numbers))

# 5. EVALUACIÓN DE ACIERTOS
def evaluar_aciertos(combinaciones: List[Dict[str, Any]], sorteos_reales: List[List[int]]) -> float:
    if not combinaciones or not sorteos_reales:
        return 0.0
    
    sorteos_set = set(tuple(sorted(s)) for s in sorteos_reales)
    combinaciones_set = set(tuple(sorted(c['draw'])) for c in combinaciones)
    aciertos = len(sorteos_set.intersection(combinaciones_set))
    return aciertos / max(len(combinaciones_set), 1)

# 6. DETECCIÓN DE ARTEFACTOS FFT
def detect_fft_artifacts(draws, model, regimen):
    return 0.5, None

# 7. REGISTRO DE COMBINACIONES
def registrar_combinaciones(combinaciones):
    log_dir = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)
    log_info(f"📝 Registered {len(combinaciones)} combinations")
    with open(f"{log_dir}/valid_combinations.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["Seed", "Draw", "SVI", "Composite_Score"])
        for comb in combinaciones:
            writer.writerow([comb["seed"], comb["draw"], comb["svi"], comb["composite_score"]])

# 8. VISUALIZACIÓN DE COMBINACIONES
def generar_visualizacion_combinada(combinaciones, output_path):
    plt.figure(figsize=(10, 6))
    for i, comb in enumerate(combinaciones):
        plt.plot(range(1, 7), comb["draw"], marker="o", label=f"Seed {comb['seed']}")
    plt.title("Generated Combinations")
    plt.xlabel("Position")
    plt.ylabel("Number")
    plt.legend()
    plt.savefig(output_path)
    plt.close()
    log_info(f"📊 Saved visualization to {output_path}")

# 9. FUNCIONES AUXILIARES MEJORADAS
def generate_valid_combination() -> List[int]:
    """Genera una combinación aleatoria válida que pasa los filtros estructurales"""
    rng = secrets.SystemRandom()
    for _ in range(100):  # Intentar hasta 100 veces
        comb = tuple(sorted(rng.sample(range(1, 41), 6)))
        if validate_combination(comb):
            return list(comb)
    # Fallback a combinación válida conocida
    return [1, 7, 13, 19, 25, 31]

def penalizar_triviales(comb: Tuple[int, ...]) -> float:
    """Penaliza combinaciones triviales con puntaje negativo"""
    triviales = {
        (1, 2, 3, 4, 5, 6),
        (2, 4, 6, 8, 10, 12),
        (5, 10, 15, 20, 25, 30),
        (10, 20, 30, 40, 1, 11)
    }
    return -999.0 if comb in triviales else 0.0

def passes_structural_filters(comb: Tuple[int, ...]) -> bool:
    """Verifica reglas básicas de estructura"""
    nums = sorted(comb)
    saltos = [b - a for a, b in zip(nums, nums[1:])]
    pares = sum(1 for n in nums if n % 2 == 0)
    variedad_decenas = len(set(n // 10 for n in nums))
    
    return all([
        2 <= pares <= 4,
        3 <= variedad_decenas <= 5,
        all(1 <= s <= 15 for s in saltos)
    ])

# 10. FUNCIÓN PRINCIPAL MEJORADA
def get_seeds(
    historial_csv_path: str = "data/historial_kabala_github.csv", 
    historial_df: Optional[pd.DataFrame] = None,  # FIX: Added optional historial_df param for compatibility
    sorteos_reales_path: str = None, 
    perfil_svi: str = 'default', 
    max_seeds: int = 5, 
    training_mode: bool = True
) -> List[Dict[str, Any]]:
    try:
        # Enhanced startup logging
        log_info(f"🚀 Starting get_seeds with parameters:")
        log_info(f"  - historial_csv_path: {historial_csv_path}")
        log_info(f"  - historial_df provided: {'Yes' if historial_df is not None else 'No'}")
        log_info(f"  - perfil_svi: {perfil_svi}")
        log_info(f"  - max_seeds: {max_seeds}")
        log_info(f"  - training_mode: {training_mode}")
        
        from modules.filters.rules_filter import FiltroEstrategico
        
        if historial_df is None:  # If no DF provided, load from path
            if not os.path.exists(historial_csv_path):
                log_error(f"🚨 CSV file not found: {historial_csv_path}")
                return [{
                    "seed": "fallback",
                    "composite_score": 0.5,
                    "draw": generate_valid_combination(),
                    "svi": 0.5,
                    "ghost_ok": True
                }]

            file_size = os.path.getsize(historial_csv_path) / (1024 * 1024)
            chunk_size = 1000 if file_size > 10 else None
            log_info(f"📂 Loading CSV: {historial_csv_path} (size: {file_size:.2f} MB)")

            original_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(3000)
            log_info(f"🔧 Set recursion limit to 3000 (original: {original_limit})")

            # Define expected columns - detectar automáticamente
            try:
                df_sample = pd.read_csv(historial_csv_path, nrows=1)
                bolilla_cols = [col for col in df_sample.columns if 'bolilla' in col.lower()]
                
                if len(bolilla_cols) >= 6:
                    expected_cols = bolilla_cols[:6]  # Usar las primeras 6 encontradas
                    log_info(f"📊 Columnas detectadas: {expected_cols}")
                else:
                    # Fallback
                    expected_cols = [f'Bolilla {i}' for i in range(1, 7)]
                    log_warning("⚠️ Usando columnas por defecto")
            except Exception as e:
                expected_cols = [f'Bolilla {i}' for i in range(1, 7)]
                log_error(f"❌ Error detectando columnas: {e}")
            historial = []
            if chunk_size:
                log_info(f"📦 Processing CSV in chunks of {chunk_size} rows")
                for chunk in pd.read_csv(historial_csv_path, chunksize=chunk_size, usecols=expected_cols):
                    try:
                        chunk_data = chunk.dropna().astype(int)
                        if not all(chunk_data[col].between(1, 40).all() for col in expected_cols):
                            log_info(f"⚠️ Skipping chunk with out-of-range values")
                            continue
                        historial.extend(chunk_data[expected_cols].values.tolist())
                    except Exception as e:
                        log_info(f"⚠️ Error processing chunk: {str(e)}")
                        continue
            else:
                df = pd.read_csv(historial_csv_path, usecols=expected_cols)
                df = df.dropna().astype(int)
                if not all(df[col].between(1, 40).all() for col in expected_cols):
                    log_error("🚨 Some numbers in Bolilla columns are outside range [1, 40]")
                    return [{
                        "seed": "fallback",
                        "composite_score": 0.5,
                        "draw": generate_valid_combination(),
                        "svi": 0.5,
                        "ghost_ok": True
                    }]
                historial = df[expected_cols].values.tolist()

            if not historial:
                log_error("🚨 No valid data after loading CSV")
                return [{
                    "seed": "fallback",
                    "composite_score": 0.5,
                    "draw": generate_valid_combination(),
                    "svi": 0.5,
                    "ghost_ok": True
                }]
        else:  # Use provided DF
            log_info("📂 Using provided historial_df")
            expected_cols = [f'Bolilla {i}' for i in range(1, 7)]
            if not all(col in historial_df.columns for col in expected_cols):
                log_error("🚨 Provided DF missing expected columns")
                return [{
                    "seed": "fallback",
                    "composite_score": 0.5,
                    "draw": generate_valid_combination(),
                    "svi": 0.5,
                    "ghost_ok": True
                }]
            historial_df = historial_df[expected_cols].dropna().astype(int)
            historial = historial_df.values.tolist()

        valid_historial = []
        for row in historial[-2000:]:
            if validate_combination(row):
                valid_historial.append(row)
            else:
                log_info(f"⚠️ Invalid row skipped: {row}")
        
        if not valid_historial:
            log_error("🚨 No valid rows after validation")
            return [{
                "seed": "fallback",
                "composite_score": 0.5,
                "draw": generate_valid_combination(),
                "svi": 0.5,
                "ghost_ok": True
            }]
        
        historial = valid_historial
        log_info(f"📊 Loaded {len(historial)} valid historical draws")

        scaler = MinMaxScaler()
        historial_scaled = scaler.fit_transform(historial)
        
        filtro = FiltroEstrategico()
        try:
            filtro.cargar_historial(historial)
        except Exception as e:
            log_error(f"❌ Error al cargar historial en FiltroEstrategico: {str(e)}")
            return [{
                "seed": "fallback",
                "composite_score": 0.5,
                "draw": generate_valid_combination(),
                "svi": 0.5,
                "ghost_ok": True
            }]
        
        regimen = 'C' if fft_entropy_spectrum(historial[-12:]) > 0.8 else 'A'
        window_size = 6  # Fixed to match single draw
        log_info(f"⚙️ Regime: {regimen}, Window size: {window_size}")

        if len(historial) < window_size:
            log_error(f"🚨 Insufficient historical data ({len(historial)} rows) for window_size={window_size}")
            return [{
                "seed": "fallback",
                "composite_score": 0.5,
                "draw": generate_valid_combination(),
                "svi": 0.5,
                "ghost_ok": True
            }]

        model = cargar_o_entrenar_autoencoder(
            historial_scaled, 
            training_mode, 
            window_size
        )
        
        # Verificar si el modelo está disponible
        if model is None:
            log_error("❌ Generative model not loaded, using fallback")
            return [{
                "seed": "fallback",
                "composite_score": 0.5,
                "draw": generate_valid_combination(),
                "svi": 0.5,
                "ghost_ok": True
            }]
        
        combinaciones_validas = []
        log_dir = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(log_dir, exist_ok=True)
        rechazos_path = f"{log_dir}/combinaciones_fallidas.csv"
        
        if os.path.exists(rechazos_path):
            os.rename(rechazos_path, f"{rechazos_path}.backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
        
        with open(rechazos_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Draw', 'Motivo', 'SVI', 'Timestamp'])
            
            # Map perfil_svi to valid values
            perfil_svi_map = {
                "default": "moderado",
                "conservative": "conservador",
                "aggressive": "agresivo"
            }
            perfil_filtro = perfil_svi_map.get(perfil_svi, "moderado")
            log_info(f"🔄 Mapped perfil_svi: {perfil_svi} -> {perfil_filtro}")
            
            # Adjust filter threshold based on perfil
            umbral_map = {
                "moderado": 0.85,
                "conservador": 0.9,
                "agresivo": 0.75
            }
            umbral = umbral_map.get(perfil_filtro, 0.85)
            log_info(f"🧪 Using filter threshold: {umbral} for perfil {perfil_filtro}")

            # Usar semilla criptográfica segura
            base_seed = secrets.randbits(32)
            for i in range(max_seeds * 4):  # Increased for more attempts
                seed = base_seed + i
                torch.manual_seed(seed)
                
                with torch.no_grad():
                    input_data = torch.tensor(historial_scaled[-1:], dtype=torch.float32)  # Use last draw
                    if input_data.dim() > 2:
                        input_data = input_data.view(1, -1)
                    
                    try:
                        generated = model(input_data, regimen=regimen).numpy()
                    except Exception as e:
                        log_error(f"❌ Error during model inference: {str(e)}")
                        continue
                    
                    for g in generated:
                        if g.ndim > 1:
                            g = g.flatten()
                        
                        draw = generar_combinacion_determinista(g, scaler)
                        
                        # Validación estructural adicional
                        if not validate_combination(draw) or not passes_structural_filters(draw):
                            writer.writerow([list(draw), "Combinación inválida", 0.0, pd.Timestamp.now()])
                            log_info(f"⚠️ Invalid draw skipped: {draw}")
                            continue
                        
                        # Rechazar combinaciones triviales
                        if penalizar_triviales(draw) < -900:
                            writer.writerow([list(draw), "Combinación trivial", 0.0, pd.Timestamp.now()])
                            log_info(f"🚫 Rejected trivial combination: {draw}")
                            continue
                        
                        try:
                            score_filtro, razones = filtro.aplicar_filtros(draw, return_score=True, return_reasons=True)
                            if score_filtro < umbral:
                                writer.writerow([list(draw), razones, score_filtro, pd.Timestamp.now()])
                                log_info(f"🧹 Rejected draw: {draw}, Score: {score_filtro:.4f}, Reasons: {razones}")
                                continue
                        except Exception as e:
                            log_error(f"❌ Error al aplicar filtros: {str(e)}")
                            continue
                        
                        similarity_score = calculate_similarity(historial, [draw])
                        fft_score, _ = detect_fft_artifacts([draw], model, regimen)
                        entropy_score = fft_entropy_spectrum([draw])
                        low_num_score = sum(1 for n in draw if n <= 5) / 6
                        
                        composite_score = (
                            0.3 * similarity_score +
                            0.3 * (1.0 / (1.0 + abs(fft_score))) +
                            0.2 * (1.0 / (1.0 + abs(entropy_score))) +
                            (0.3 if regimen == 'C' else 0.2) * low_num_score +
                            penalizar_triviales(draw)  # Penalización adicional
                        )
                        
                        try:
                            svi = calcular_svi(str(list(draw)), perfil_filtro, True, composite_score)
                        except Exception as e:
                            log_error(f"❌ Error calculating SVI: {str(e)}")
                            svi = 0.5
                        
                        combinaciones_validas.append({
                            "seed": f"gen_{seed}_{regimen}",
                            "draw": list(draw),
                            "svi": svi,
                            "composite_score": composite_score,
                            "low_num_score": low_num_score,
                            "ghost_ok": True  # Added for compatibility with predictor.py
                        })
                        
                        if len(combinaciones_validas) >= max_seeds * 4:
                            break
                
                if len(combinaciones_validas) >= max_seeds * 4:
                    break
        
        # Filtrado final para asegurar calidad
        combinaciones_filtradas = [
            c for c in combinaciones_validas 
            if passes_structural_filters(tuple(c['draw']))
        ]
        
        if not combinaciones_filtradas:
            log_error("🚨 No valid combinations after final filtering, using fallback")
            return [{
                "seed": "fallback",
                "composite_score": 0.5,
                "draw": generate_valid_combination(),
                "svi": 0.5,
                "ghost_ok": True
            }]

        registrar_combinaciones(combinaciones_filtradas)
        combinaciones_validas = sorted(
            combinaciones_filtradas, 
            key=lambda x: x['svi'], 
            reverse=True
        )[:max_seeds]
        generar_visualizacion_combinada(combinaciones_validas, f"{log_dir}/ghost_rng_analysis.png")
        
        if sorteos_reales_path and os.path.exists(sorteos_reales_path):
            log_info(f"📊 Evaluating against real draws: {sorteos_reales_path}")
            try:
                sorteos_df = pd.read_csv(sorteos_reales_path, usecols=expected_cols)
                sorteos_reales = sorteos_df[expected_cols].dropna().astype(int).values.tolist()
                
                tasa_aciertos = evaluar_aciertos(combinaciones_validas, sorteos_reales)
                log_info(f"🏆 Tasa de aciertos: {tasa_aciertos:.2%}")
                
                aciertos_path = f"{log_dir}/aciertos.csv"
                if os.path.exists(aciertos_path):
                    os.rename(aciertos_path, f"{aciertos_path}.backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
                
                registro = {
                    "timestamp": pd.Timestamp.now(),
                    "tasa_aciertos": tasa_aciertos,
                    "num_combinaciones": len(combinaciones_validas),
                    "perfil_svi": perfil_filtro,
                    "regimen": regimen
                }
                
                pd.DataFrame([registro]).to_csv(aciertos_path, index=False)
            except Exception as e:
                log_error(f"❌ Error evaluating real draws: {str(e)}")
        
        log_info(f"✅ get_seeds completed successfully")
        log_info(f"  - Generated {len(combinaciones_validas)} valid combinations")
        return combinaciones_validas
    
    except RecursionError as re:
        log_error(f"🚨 Recursion depth exceeded in get_seeds: {str(re)}")
        traceback.print_exc()
        return [{
            "seed": "fallback",
            "composite_score": 0.5,
            "draw": generate_valid_combination(),
            "svi": 0.5,
            "ghost_ok": True
        }]
    except pd.errors.ParserError as pe:
        log_error(f"🚨 CSV parsing error: {str(pe)}")
        traceback.print_exc()
        return [{
            "seed": "fallback",
            "composite_score": 0.5,
            "draw": generate_valid_combination(),
            "svi": 0.5,
            "ghost_ok": True
        }]
    except Exception as e:
        log_error(f"🚨 Critical error in get_seeds: {str(e)}")
        traceback.print_exc()
        return [{
            "seed": "fallback",
            "composite_score": 0.5,
            "draw": generate_valid_combination(),
            "svi": 0.5,
            "ghost_ok": True
        }]
    finally:
        if 'original_limit' in locals():
            sys.setrecursionlimit(original_limit)
            log_info(f"🔧 Restored recursion limit to {original_limit}")

# 11. ALIAS FOR COMPATIBILITY
def simulate_ghost_rng(
    historial_csv_path: str = "data/historial_kabala_github.csv",
    historial_df: Optional[pd.DataFrame] = None,  # FIX: Added for compatibility
    perfil_svi: str = 'default',
    max_seeds: int = 5,
    training_mode: bool = True
) -> List[Dict[str, Any]]:
    """
    Alias for get_seeds to maintain compatibility with inverse_mining_engine.py.

    Args:
        historial_csv_path (str): Path to historical lottery data CSV.
        historial_df (Optional[pd.DataFrame]): Optional DataFrame for historical data.
        perfil_svi (str): SVI profile (e.g., 'default', 'conservative', 'aggressive').
        max_seeds (int): Maximum number of seeds to generate.
        training_mode (bool): Whether to train a new model or load existing.

    Returns:
        List[Dict]: List of dictionaries with 'seed', 'composite_score', 'draw', 'svi', and 'ghost_ok' keys.
    """
    return get_seeds(
        historial_csv_path=historial_csv_path,
        historial_df=historial_df,
        sorteos_reales_path=None,
        perfil_svi=perfil_svi,
        max_seeds=max_seeds,
        training_mode=training_mode
    )