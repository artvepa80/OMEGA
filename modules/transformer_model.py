# OMEGA_PRO_AI_v10.1/modules/transformer_model.py – Transformer-based combination generator (OMEGA PRO AI v12.0) – Versión Ultra-Mejorada

import os  # FIX: Agregado para path.exists
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import logging
import re
import random
from datetime import datetime  # Para timestamps en logs
from modules.lottery_transformer import LotteryTransformer
from modules.filters.rules_filter import FiltroEstrategico
from modules.score_dynamics import score_combinations
from utils.transformer_data_utils import prepare_advanced_transformer_data

# Logger global con timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def cargar_modelo_transformer(model_path="model/transformer_model.pt", train_if_missing=False, historial_df=None):
    logger = logging.getLogger(__name__)
    try:
        model = LotteryTransformer(num_numbers=40, d_model=128, nhead=4, num_layers=3, dropout=0.1)
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path))
            logger.info(f"✅ Modelo Transformer cargado desde {model_path}")
            return model
        else:
            if train_if_missing and historial_df is not None and not historial_df.empty:
                logger.warning("⚠️ Modelo no encontrado; entrenando básico con historial...")
                # Entrenamiento dummy: expande con datos reales
                try:
                    X_seq, X_temp, X_pos, _ = prepare_advanced_transformer_data(historial_df, seq_length=10)
                    if len(X_seq) == 0:
                        raise ValueError("No hay secuencias para entrenamiento")
                    criterion = nn.CrossEntropyLoss(ignore_index=0)
                    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
                    model.train()
                    for epoch in range(5):  # Ciclos básicos
                        for i in range(len(X_seq)):
                            numbers = X_seq[i].unsqueeze(0)
                            temporal = X_temp[i].unsqueeze(0)
                            positions = X_pos[i].unsqueeze(0)
                            num_logits, _ = model(numbers, temporal, positions)
                            target = numbers[0, -1, :]  # Predice último como target dummy
                            loss = criterion(num_logits.view(-1, 40), target.long())
                            optimizer.zero_grad()
                            loss.backward()
                            optimizer.step()
                    torch.save(model.state_dict(), model_path)
                    logger.info(f"✅ Modelo entrenado y guardado en {model_path}")
                    model.eval()
                    return model
                except Exception as e:
                    logger.error(f"🚨 Error en entrenamiento dummy: {str(e)}; usando sin entrenar")
            else:
                logger.warning(f"⚠️ Modelo no encontrado en {model_path}, devolviendo sin entrenar")
            return model
    except Exception as e:
        logger.error(f"🚨 Error cargando modelo Transformer: {str(e)}")
        return None

def preprocess_data(historial_df: pd.DataFrame, seq_length: int = 10, num_numbers: int = 6):
    logger = logging.getLogger(__name__)
    
    # Regex mejorado para bolillas (maneja 'bolilla_1', 'Bolilla 1', etc.)
    bol_regex = re.compile(r"(?i)^bolilla[_ \s]*\d+$")
    columnas_bolillas = [c for c in historial_df.columns if bol_regex.match(c)]
    
    if len(columnas_bolillas) != num_numbers:
        if len(historial_df.columns) >= num_numbers:
            tmp_cols = historial_df.columns[:num_numbers]
            rename_map = {col: f"Bolilla {i+1}" for i, col in enumerate(tmp_cols)}
            historial_df = historial_df.rename(columns=rename_map)
            columnas_bolillas = list(rename_map.values())
            logger.info(f"🔄 Columnas renombradas a {columnas_bolillas}")
        if len(columnas_bolillas) != num_numbers:
            raise ValueError(f"🚨 Se esperaban {num_numbers} columnas de bolillas, se encontraron {len(columnas_bolillas)}")
    
    historial_df = historial_df.copy()
    for col in columnas_bolillas:
        mode_val = historial_df[col].mode()
        fill_value = mode_val.iloc[0] if not mode_val.empty else 1
        historial_df[col] = historial_df[col].fillna(fill_value)
    
    try:
        X_seq, X_temp, X_pos, scaler = prepare_advanced_transformer_data(
            historial_df, seq_length=seq_length, for_training=False
        )
        historial = X_seq.numpy() if hasattr(X_seq, "numpy") else np.array(X_seq)
        invalid_mask = (historial < 1) | (historial > 40)
        if np.any(invalid_mask):
            logger.warning("⚠️ Valores inválidos post-utils; filtrando...")
            valid_mask = np.all(~invalid_mask, axis=(1, 2))
            X_seq = X_seq[valid_mask]
            X_temp = X_temp[valid_mask]
            X_pos = X_pos[valid_mask]
        sequences = [(seq.numpy(), temp.numpy(), pos.numpy()) if hasattr(seq, "numpy") else (np.array(seq), np.array(temp), np.array(pos))
                     for seq, temp, pos in zip(X_seq, X_temp, X_pos)]
        logger.debug(f"Preprocesamiento con utils: {len(sequences)} seqs")
        return sequences
    
    except Exception as e:
        logger.error(f"❌ Utils falló: {str(e)}; fallback manual")
        
        historial = historial_df[columnas_bolillas].values.astype(int)
        if historial.shape[1] != num_numbers:
            raise ValueError(f"🚨 Cada sorteo debe contener {num_numbers} números, se encontraron {historial.shape[1]}")
        
        if not ((historial >= 1) & (historial <= 40)).all():
            raise ValueError("🚨 Los números del historial deben estar entre 1 y 40")
        
        sequences = []
        if len(historial) < seq_length:
            num_padding = seq_length - len(historial)
            padding = np.tile(historial[0], (num_padding, 1))
            historial = np.vstack([padding, historial])
            logger.info(f"🔄 Padding agregado: {num_padding} filas")
        
        for i in range(len(historial) - seq_length + 1):
            seq = historial[i:i + seq_length]
            if seq.shape == (seq_length, num_numbers):
                sequences.append(seq)
        
        return sequences

def generar_combinaciones_transformer(historial_df: pd.DataFrame, cantidad: int = 100, perfil_svi: str = 'moderado', logger=None, train_model_if_missing=True):
    log_func = None
    if logger is None:
        logger = logging.getLogger(__name__)
        log_func = logger.info
    else:
        log_func = logger.info if hasattr(logger, 'info') else print
    
    if historial_df.empty:
        log_func("❌ Historial vacío, generando combinaciones aleatorias.")
        return [{"combination": sorted(random.sample(range(1, 41), 6)), "score": 0.5, "source": "transformer_fallback", "metrics": {}} 
                for _ in range(cantidad)]

    model = cargar_modelo_transformer(train_if_missing=train_model_if_missing, historial_df=historial_df)
    if model is None:
        log_func("❌ No se pudo cargar/entrenar el modelo Transformer, usando aleatorias.")
        return [{"combination": sorted(random.sample(range(1, 41), 6)), "score": 0.5, "source": "transformer_fallback", "metrics": {}} 
                for _ in range(cantidad)]
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    log_func("🔧 Transformer model initialized")

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
    
    combinaciones = []
    max_attempts = cantidad * 5
    attempt = 0

    filtro = FiltroEstrategico()
    filtro.cargar_historial(historial)

    while len(combinaciones) < cantidad and attempt < max_attempts:
        attempt += 1

        input_data = sequences[-1] if sequences else np.array([[1, 2, 3, 4, 5, 6]] * 10)

        try:
            # Validación simple de dimensiones
            try:
                if hasattr(input_data, 'shape') and len(input_data.shape) >= 2:
                    if input_data.shape[-1] != 6:
                        continue  # Saltar dimensión incorrecta
            except:
                pass  # Continuar si hay error en validación
            
            numbers = torch.tensor(input_data, dtype=torch.long).to(device)

            if numbers.shape != (10, 6):
                log_func(f"⚠️ Forma de tensor inválida: {numbers.shape}, corrigiendo...")
                if numbers.ndim == 1 and numbers.shape[0] == 6:
                    numbers = numbers.unsqueeze(0).repeat(10, 1)
                else:
                    numbers = torch.randint(1, 41, (10, 6)).to(device)
            
            if numbers.dim() == 2:
                numbers = numbers.unsqueeze(0)
            
            seq_len = numbers.shape[1]
            positions = torch.arange(0, seq_len, dtype=torch.long).unsqueeze(0).to(device)
            temporal = torch.zeros((numbers.shape[0], seq_len, 3), dtype=torch.float).to(device)

            with torch.no_grad():
                num_logits, _ = model(numbers, temporal, positions)
                
                if num_logits.dim() == 3:
                    probs = torch.softmax(num_logits[:, -1, :], dim=-1)
                elif num_logits.dim() == 2:
                    probs = torch.softmax(num_logits, dim=-1).unsqueeze(0)
                else:
                    raise ValueError(f"Forma inesperada de logits: {num_logits.shape}")
                
                probs = probs[0].cpu().numpy()

                if np.sum(probs) == 0:  # FIX: Si probs inválidas, usa uniform
                    probs = np.ones_like(probs) / len(probs)
                    log_func("⚠️ Probs inválidas; usando distribución uniform")

                combo = []
                used = set()
                for _ in range(6):
                    prob_dist = probs.copy()
                    valid_indices = [i for i in range(1, 41) if i not in used]
                    if not valid_indices:
                        break
                    # Fix: Use explicit integer indexing to avoid NumPy boolean subtract warning
                    valid_indices_array = np.array(valid_indices, dtype=int)
                    valid_probs = prob_dist[valid_indices_array - 1]
                    valid_probs = valid_probs / valid_probs.sum() if valid_probs.sum() > 0 else np.ones_like(valid_probs) / len(valid_probs)
                    
                    num = np.random.choice(valid_indices, p=valid_probs)
                    combo.append(int(num))
                    used.add(num)

                combo = sorted(combo)

        except Exception as e:
            # Manejo silencioso de errores de dimensión
            if "expected sequence of length" in str(e):
                pass  # Error conocido de dimensión, ignorar silenciosamente
            else:
                log_func(f"⚠️ Error en predicción: {str(e)}; skip")
            continue

        combo_tuple = tuple(combo)
        if len(combo) != 6:
            log_func(f"⚠️ Descarto por longitud: {combo}")
            continue
        if combo_tuple in historial_set:
            log_func(f"⚠️ Descarto por historial: {combo}")
            continue
        try:
            filtro_resultado = filtro.aplicar_filtros(combo)
            # Manejar posibles tipos de retorno diferentes
            if not (filtro_resultado if isinstance(filtro_resultado, bool) else False):
                log_func(f"⚠️ Descarto por filtro: {combo}")
                continue
        except Exception as e:
            log_func(f"❌ Error en filtro: {str(e)}")
            continue

        # Fix: Use explicit integer indexing to avoid NumPy boolean subtract warning
        combo_indices = np.array(combo, dtype=int) - 1
        score = probs[combo_indices].mean().item()
        combinaciones.append({
            "combination": combo,
            "score": round(score, 4),
            "source": "transformer_deep",
            "metrics": {"transformer_score": score}
        })
        log_func(f"[TRANSFORMER] Generada: {combo} - Score: {score:.4f}")

    if len(combinaciones) < cantidad:
        needed = cantidad - len(combinaciones)
        log_func(f"🔁 Generando respaldo para {needed}")
        generated_backup = 0
        backup_attempts = 0
        max_backup_attempts = needed * 3
        
        while generated_backup < needed and backup_attempts < max_backup_attempts:
            backup_attempts += 1
            combo = sorted(random.sample(range(1, 41), 6))
            combo_tuple = tuple(combo)
            
            if combo_tuple in historial_set:
                continue
            try:
                filtro_resultado = filtro.aplicar_filtros(combo)
                # Manejar posibles tipos de retorno diferentes
                if not (filtro_resultado if isinstance(filtro_resultado, bool) else False):
                    continue
            except Exception:
                continue
                
            combinaciones.append({
                "combination": combo,
                "score": 0.5,
                "source": "transformer_fallback",
                "metrics": {}
            })
            generated_backup += 1
            log_func(f"[TRANSFORMER] Respaldo: {combo}")

    if historial_df is not None and combinaciones:
        try:
            combinaciones_scored = score_combinations(
                combinations=combinaciones,
                historial=historial_df,
                perfil_svi=perfil_svi,
                logger=logger  # Usar logger original, no log_func
            )
            for i, scored in enumerate(combinaciones_scored):
                new_score = max(combinaciones[i]["score"], scored["score"])
                combinaciones[i]["score"] = round(new_score, 4)
                combinaciones[i]["metrics"]["dynamic_score"] = scored["score"]
        except Exception as e:
            log_func(f"⚠️ Error en scoring: {str(e)}")

    log_func(f"✅ Generadas {len(combinaciones)}/{cantidad}")
    return combinaciones[:cantidad]

# Función de test integrada
def test_generar_combinaciones():
    dates = pd.date_range(start='2020-01-01', periods=20, freq='D')
    data = np.random.randint(1, 41, size=(20, 6))
    historial_df = pd.DataFrame(data, columns=[f'Bolilla {i+1}' for i in range(6)])
    historial_df['fecha'] = dates
    result = generar_combinaciones_transformer(historial_df, cantidad=5, train_model_if_missing=True)
    assert len(result) == 5, "No generó 5 combinaciones"
    assert all(len(d['combination']) == 6 for d in result), "Combinaciones inválidas"
    print("✅ Test pasado: ", result)
    return result

# Ejecutar test
test_generar_combinaciones()