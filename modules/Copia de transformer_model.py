# OMEGA_PRO_AI_v10.1/modules/transformer_model.py – Transformer-based combination generator (OMEGA PRO AI v12.0) – Versión Corregida

import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import logging
import re
import random
from modules.lottery_transformer import LotteryTransformer
from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations

def cargar_modelo_transformer(model_path="model/transformer_model.pt"):
    """Carga un modelo Transformer pre-entrenado"""
    try:
        model = LotteryTransformer(num_numbers=40, d_model=128, nhead=4, num_layers=3, dropout=0.1)
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path))
            logging.getLogger(__name__).info(f"✅ Modelo Transformer cargado desde {model_path}")
            return model
        else:
            logging.getLogger(__name__).warning(f"⚠️ Modelo no encontrado en {model_path}, devolviendo modelo sin entrenar")
            return model
    except Exception as e:
        logging.getLogger(__name__).error(f"🚨 Error cargando modelo Transformer: {str(e)}")
        return None

def preprocess_data(historial_df, seq_length=10, num_numbers=6):
    """
    Preprocesa los datos históricos para asegurar dimensiones correctas.
    
    Args:
        historial_df (pd.DataFrame): Datos históricos de lotería
        seq_length (int): Longitud de la secuencia de sorteos esperada
        num_numbers (int): Número de bolillas por sorteo
    
    Returns:
        list: Lista de secuencias válidas
    """
    # Detect columns case-insensitively (accept 'bolilla_1', 'Bolilla 1', 'bolilla1', etc.)
    bol_regex = re.compile(r"^bolilla[_\s]*\d+$", re.I)
    columnas_bolillas = [c for c in historial_df.columns if bol_regex.match(c)]

    if len(columnas_bolillas) != num_numbers:
        # Fallback: intenta renombrar primeros num_numbers campos si sólo recibimos dummy sin nombres correctos
        if len(historial_df.columns) >= num_numbers:
            tmp_cols = historial_df.columns[:num_numbers]
            rename_map = {col: f"Bolilla {i+1}" for i, col in enumerate(tmp_cols)}
            historial_df = historial_df.rename(columns=rename_map)
            columnas_bolillas = list(rename_map.values())
        if len(columnas_bolillas) != num_numbers:
            raise ValueError(f"🚨 Se esperaban {num_numbers} columnas de bolillas, se encontraron {len(columnas_bolillas)}")

    historial = historial_df[columnas_bolillas].values.astype(int)
    if historial.shape[1] != num_numbers:
        raise ValueError(f"🚨 Cada sorteo debe contener {num_numbers} números, se encontraron {historial.shape[1]}")
    
    # Asegurar que los datos estén en el rango válido (1-40)
    if not ((historial >= 1) & (historial <= 40)).all():
        raise ValueError("🚨 Los números del historial deben estar entre 1 y 40")
    
    # Crear secuencias de longitud seq_length
    sequences = []
    if len(historial) < seq_length:
        # Rellenar con el primer sorteo si hay menos de seq_length sorteos
        num_padding = seq_length - len(historial)
        padding = np.tile(historial[0], (num_padding, 1))
        historial = np.vstack([padding, historial])
    
    for i in range(len(historial) - seq_length + 1):
        seq = historial[i:i + seq_length]
        if seq.shape == (seq_length, num_numbers):
            sequences.append(seq)
    
    return sequences

def generar_combinaciones_transformer(historial_df: pd.DataFrame, cantidad: int = 100, perfil_svi: str = 'moderado', logger=None):
    """
    Genera combinaciones usando el modelo LotteryTransformer.
    
    Args:
        historial_df (pd.DataFrame): Historical lottery data
        cantidad (int): Number of combinations to generate
        perfil_svi (str): SVI profile ('moderado', 'conservador', 'agresivo')
        logger: Logger instance or callable
    
    Returns:
        list: List of dictionaries with combinations and scores
    """
    # 1. Configurar logger
    log_func = None
    if logger is None:
        logger = logging.getLogger(__name__)
        logger.propagate = False
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
        log_func = logger.info
    elif hasattr(logger, 'info') and callable(logger.info):
        log_func = logger.info
    else:
        log_func = logger if callable(logger) else print
    
    # 2. Validar datos de entrada
    if historial_df.empty:
        log_func("❌ Historial vacío, generando combinaciones aleatorias.")
        return [{"combination": sorted(random.sample(range(1, 41), 6)), "score": 0.5, "source": "transformer_fallback", "metrics": {}} 
                for _ in range(cantidad)]

    # 3. Inicializar modelo
    model = cargar_modelo_transformer()
    if model is None:
        log_func("❌ No se pudo cargar el modelo Transformer, usando combinaciones aleatorias.")
        return [{"combination": sorted(random.sample(range(1, 41), 6)), "score": 0.5, "source": "transformer_fallback", "metrics": {}} 
                for _ in range(cantidad)]
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    log_func("🔧 Transformer model initialized")

    # 4. Preparar datos
    try:
        sequences = preprocess_data(historial_df)
    except ValueError as e:
        log_func(f"❌ Error en preprocesamiento: {str(e)}")
        return [{"combination": sorted(random.sample(range(1, 41), 6)), "score": 0.5, "source": "transformer_fallback", "metrics": {}} 
                for _ in range(cantidad)]
    
    if not sequences:
        log_func("❌ No se pudieron generar secuencias válidas")
        return [{"combination": sorted(random.sample(range(1, 41), 6)), "score": 0.5, "source": "transformer_fallback", "metrics": {}} 
                for _ in range(cantidad)]
    
    historial = historial_df[[col for col in historial_df.columns if "Bolilla" in col or col in ["1", "2", "3", "4", "5", "6"]]].values.tolist()
    historial_set = {tuple(sorted(c)) for c in historial}
    
    # 5. Generar combinaciones
    combinaciones = []
    max_attempts = cantidad * 5
    attempt = 0

    filtro = FiltroEstrategico()
    filtro.cargar_historial(historial)

    while len(combinaciones) < cantidad and attempt < max_attempts:
        attempt += 1

        # Usar la última secuencia disponible o generar dummy
        input_data = sequences[-1] if sequences else np.array([[1, 2, 3, 4, 5, 6]] * 10)

        try:
            # Preparar tensores con autocorrección de dimensiones
            numbers = torch.tensor(input_data, dtype=torch.long).to(device)

            # Autocorrección si input malformado
            if numbers.shape != (10, 6):
                log_func(f"⚠️ Forma de tensor inválida: {numbers.shape}, se esperaba (10, 6). Corrigiendo...")
                if numbers.ndim == 1 and numbers.shape[0] == 6:
                    numbers = numbers.unsqueeze(0).repeat(10, 1)
                else:
                    numbers = torch.randint(1, 41, (10, 6)).to(device)
            
            # CORRECCIÓN: Añadir dimensión de batch (1, 10, 6)
            if numbers.dim() == 2:
                numbers = numbers.unsqueeze(0)
            
            # CORRECCIÓN: Ajustar tensores auxiliares
            seq_len = numbers.shape[1]  # 10
            positions = torch.arange(0, seq_len, dtype=torch.long).unsqueeze(0).to(device)  # (1, 10)
            temporal = torch.zeros((numbers.shape[0], seq_len, 3), dtype=torch.float).to(device)  # (1, 10, 3)

            # CHEQUEO NUEVO: Validar dimensiones antes de predicción
            if numbers.shape[0] < 1 or numbers.shape[1] < 1:
                log_func(f"⚠️ Input shape inválido: {numbers.shape}, skipping")
                continue

            # PREDICCIÓN CON MANEJO ROBUSTO DE DIMENSIONES
            with torch.no_grad():
                num_logits, _ = model(numbers, temporal, positions)
                
                # FIX: Aplanar logits y tomar primeros 40 elementos
                flat_logits = num_logits.view(-1)   # Convierte a 1D
                
                if flat_logits.size(0) < 40:
                    # No hay suficientes logits, usar distribución uniforme
                    probs = np.ones(40) / 40
                    log_func(f"⚠️ [TRANSFORMER] No hay suficientes logits ({flat_logits.size(0)}), usando uniforme")
                else:
                    # Tomar los primeros 40 logits
                    logits_1d = flat_logits[:40]
                    probs = torch.softmax(logits_1d, dim=0).cpu().numpy()

                combo = []
                used = set()
                for _ in range(6):
                    prob_dist = probs.copy()
                    valid_indices = [i for i in range(1, 41) if i not in used]
                    if not valid_indices:
                        break
                    valid_probs = prob_dist[np.array(valid_indices) - 1]
                    valid_probs = valid_probs / valid_probs.sum() if valid_probs.sum() > 0 else np.ones_like(valid_probs) / len(valid_probs)
                    
                    num = np.random.choice(valid_indices, p=valid_probs)
                    combo.append(int(num))
                    used.add(num)

                combo = sorted(combo)

        except Exception as e:
            log_func(f"⚠️ Error en la predicción del Transformer: {str(e)}")
            continue

        # Validar combinación generada
        combo_tuple = tuple(combo)
        if len(combo) != 6:
            log_func(f"⚠️ [TRANSFORMER] Combinación descartada por longitud: {combo}")
            continue
        if combo_tuple in historial_set:
            log_func(f"⚠️ [TRANSFORMER] Combinación descartada por estar en el historial: {combo}")
            continue
        if not filtro.aplicar_filtros(combo):
            log_func(f"⚠️ [TRANSFORMER] Combinación descartada por el filtro: {combo}")
            continue

        # Calcular score
        score = probs[np.array(combo) - 1].mean().item()
        combinaciones.append({
            "combination": combo,
            "score": round(score, 4),
            "source": "transformer_deep",
            "metrics": {"transformer_score": score}
        })
        log_func(f"[TRANSFORMER] Combinación generada: {combo} - Score: {score:.4f}")

    # 6. Respaldo inteligente si no se generaron suficientes
    if len(combinaciones) < cantidad:
        needed = cantidad - len(combinaciones)
        log_func(f"🔁 [TRANSFORMER] Generando respaldo para {needed} combinaciones")
        generated_backup = 0
        backup_attempts = 0
        max_backup_attempts = needed * 3
        
        while generated_backup < needed and backup_attempts < max_backup_attempts:
            backup_attempts += 1
            combo = sorted(random.sample(range(1, 41), 6))
            combo_tuple = tuple(combo)
            
            if combo_tuple in historial_set:
                continue
            if not filtro.aplicar_filtros(combo):
                continue
                
            combinaciones.append({
                "combination": combo,
                "score": 0.5,
                "source": "transformer_fallback",
                "metrics": {}
            })
            generated_backup += 1
            log_func(f"[TRANSFORMER] Respaldo generado: {combo}")

    # 7. Scoring avanzado
    if historial_df is not None and combinaciones:
        try:
            combinaciones_scored = score_combinations(
                combinations=combinaciones,
                historial=historial_df,
                perfil_svi=perfil_svi,
                logger=log_func
            )
            for i, scored in enumerate(combinaciones_scored):
                new_score = max(combinaciones[i]["score"], scored["score"])
                combinaciones[i]["score"] = round(new_score, 4)
                combinaciones[i]["metrics"]["dynamic_score"] = scored["score"]
        except Exception as e:
            log_func(f"⚠️ [TRANSFORMER] Error en scoring avanzado: {str(e)}")

    log_func(f"✅ [TRANSFORMER] Generadas {len(combinaciones)}/{cantidad} combinaciones")
    return combinaciones[:cantidad]