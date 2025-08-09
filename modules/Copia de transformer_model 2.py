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
from modules import transformer_data_utils  # Importación para características temporales reales

# Configuración centralizada de logging
def configurar_logger(logger=None):
    """Configura el logger de manera centralizada"""
    if logger is None:
        logger = logging.getLogger('transformer_model')
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    return logger

def cargar_modelo_transformer(model_path="model/transformer_model.pt"):
    """Carga un modelo Transformer pre-entrenado con manejo de dispositivo"""
    logger = configurar_logger()
    try:
        # Determinar dispositivo primero para carga consistente
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        model = LotteryTransformer(num_numbers=40, d_model=128, nhead=4, num_layers=3, dropout=0.1)
        model = model.to(device)  # Mover a dispositivo antes de cargar
        
        if os.path.exists(model_path):
            # Cargar con mapeo de dispositivo para evitar conflictos
            state_dict = torch.load(model_path, map_location=device)
            
            # Carga tolerante a cambios en la estructura del modelo
            model.load_state_dict(state_dict, strict=False)
            logger.info(f"✅ Modelo Transformer cargado desde {model_path} en {device}")
            logger.debug(f"Modelo: {repr(model)}")
            
            # Verificar versión del modelo si está disponible en el state_dict
            if 'version' in state_dict:
                model_version = state_dict['version']
                logger.info(f"ℹ️ Versión del modelo: {model_version}")
            else:
                logger.warning("⚠️ Versión del modelo no encontrada en el archivo")
            
            return model
        else:
            logger.warning(f"⚠️ Modelo no encontrado en {model_path}, devolviendo modelo sin entrenar")
            logger.debug(f"Modelo: {repr(model)}")
            return model
    except Exception as e:
        logger.error(f"🚨 Error cargando modelo Transformer: {str(e)}")
        return None

def preprocess_data(historial_df, seq_length=10, num_numbers=6):
    """
    Preprocesa los datos históricos para asegurar dimensiones correctas.
    Mejorado con manejo de NaN e integración de características temporales reales.
    """
    logger = configurar_logger()
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

    # 1. Manejo de valores faltantes: reemplazar NaN con la moda (valor más frecuente)
    historial_df = historial_df.copy()
    for col in columnas_bolillas:
        # Calcular la moda (valor más frecuente) para la columna
        mode_val = historial_df[col].mode()
        if not mode_val.empty:
            fill_value = mode_val.iloc[0]
        else:
            fill_value = 1  # Valor predeterminado si no hay moda
            
        # Reemplazar NaN con la moda
        historial_df[col] = historial_df[col].fillna(fill_value)
    
    # Convertir a enteros después del reemplazo
    historial = historial_df[columnas_bolillas].astype(int).values
    
    if historial.shape[1] != num_numbers:
        raise ValueError(f"🚨 Cada sorteo debe contener {num_numbers} números, se encontraron {historial.shape[1]}")
    
    # Asegurar que los datos estén en el rango válido (1-40)
    if not ((historial >= 1) & (historial <= 40)).all():
        # Identificar valores inválidos para mejor diagnóstico
        invalid_mask = (historial < 1) | (historial > 40)
        invalid_count = np.sum(invalid_mask)
        invalid_values = historial[invalid_mask]
        
        if invalid_count > 0:
            logger.warning(f"🚨 {invalid_count} valores inválidos detectados. Ejemplos: {invalid_values[:5]}")
        
        # Filtrar filas con valores inválidos en lugar de fallar completamente
        valid_rows = np.all((historial >= 1) & (historial <= 40), axis=1)
        historial = historial[valid_rows]
        
        if len(historial) == 0:
            raise ValueError("🚨 No quedan datos válidos después de filtrar valores fuera de rango")
    
    # 2. Generar características temporales avanzadas
    try:
        # Usar el módulo transformer_data_utils para generar características temporales reales
        temporal_features = transformer_data_utils.generar_caracteristicas_temporales(historial_df)
        logger.debug("✅ Características temporales avanzadas generadas")
    except Exception as e:
        logger.warning(f"⚠️ Error generando características temporales: {str(e)}")
        # Fallback a características temporales básicas
        temporal_features = np.zeros((len(historial), 3))
    
    # Crear secuencias de longitud seq_length
    sequences = []
    temporal_sequences = []
    
    if len(historial) < seq_length:
        # Rellenar con el primer sorteo si hay menos de seq_length sorteos
        num_padding = seq_length - len(historial)
        padding = np.tile(historial[0], (num_padding, 1))
        historial = np.vstack([padding, historial])
        
        # Rellenar características temporales con ceros
        temporal_padding = np.zeros((num_padding, temporal_features.shape[1]))
        temporal_features = np.vstack([temporal_padding, temporal_features])
    
    for i in range(len(historial) - seq_length + 1):
        seq = historial[i:i + seq_length]
        temp_seq = temporal_features[i:i + seq_length]
        
        if seq.shape == (seq_length, num_numbers):
            sequences.append(seq)
            temporal_sequences.append(temp_seq)
    
    logger.debug(f"Preprocesamiento completado: {len(sequences)} secuencias generadas")
    return sequences, temporal_sequences

def generar_combinaciones_transformer(historial_df: pd.DataFrame, cantidad: int = 100, perfil_svi: str = 'moderado', logger=None):
    """
    Genera combinaciones usando el modelo LotteryTransformer.
    Optimizado con salidas tempranas y manejo mejorado de errores.
    """
    # 1. Configurar logger centralizado
    logger = configurar_logger(logger)
    log_func = logger.info
    
    # 2. Salida temprana para datos de entrada inválidos
    if historial_df is None or historial_df.empty:
        log_func("❌ Historial vacío o nulo, generando combinaciones aleatorias.")
        return [{
            "combination": sorted(random.sample(range(1, 41), 6)), 
            "score": 0.5, 
            "source": "transformer_fallback", 
            "metrics": {}
        } for _ in range(cantidad)]

    # 3. Inicializar modelo con manejo de dispositivo integrado
    model = cargar_modelo_transformer()
    if model is None:
        log_func("❌ No se pudo cargar el modelo Transformer, usando combinaciones aleatorias.")
        return [{
            "combination": sorted(random.sample(range(1, 41), 6)), 
            "score": 0.5, 
            "source": "transformer_fallback", 
            "metrics": {}
        } for _ in range(cantidad)]
    
    # 4. Preparar datos con manejo robusto de errores
    try:
        sequences, temporal_sequences = preprocess_data(historial_df)
    except ValueError as e:
        log_func(f"❌ Error en preprocesamiento: {str(e)}")
        return [{
            "combination": sorted(random.sample(range(1, 41), 6)), 
            "score": 0.5, 
            "source": "transformer_fallback", 
            "metrics": {}
        } for _ in range(cantidad)]
    
    # Salida temprana si no hay secuencias válidas
    if not sequences:
        log_func("❌ No se pudieron generar secuencias válidas")
        return [{
            "combination": sorted(random.sample(range(1, 41), 6)), 
            "score": 0.5, 
            "source": "transformer_fallback", 
            "metrics": {}
        } for _ in range(cantidad)]
    
    # 5. Preparar historial para filtrado
    bolilla_cols = [col for col in historial_df.columns if "Bolilla" in col or col in ["1", "2", "3", "4", "5", "6"]]
    if not bolilla_cols:
        bolilla_cols = historial_df.columns[:6]  # Fallback a primeras 6 columnas
        
    historial = historial_df[bolilla_cols].values.tolist()
    historial_set = {tuple(sorted(map(int, c))) for c in historial}  # Conversión robusta a int

    # 6. Inicializar filtro estratégico con relajación opcional
    filtro = FiltroEstrategico()
    filtro_original = None  # Para almacenar configuración original
    try:
        filtro.cargar_historial(historial)
        filtro_original = filtro.configurar_modo_estricto(True)  # Guardar configuración original
    except Exception as e:
        log_func(f"⚠️ Error al cargar historial en filtro: {str(e)}")

    # 7. Generar combinaciones con dispositivo del modelo
    device = next(model.parameters()).device
    combinaciones = []
    max_attempts = cantidad * 5
    attempt = 0
    rejection_count = 0  # Contador de rechazos
    log_func(f"🚀 Iniciando generación de {cantidad} combinaciones (máx {max_attempts} intentos)")

    while len(combinaciones) < cantidad and attempt < max_attempts:
        attempt += 1

        # Usar la última secuencia disponible o generar dummy
        seq_idx = -1 if sequences else 0
        input_data = sequences[seq_idx] if sequences else np.array([[1, 2, 3, 4, 5, 6]] * 10)
        temporal_data = temporal_sequences[seq_idx] if temporal_sequences else np.zeros((10, 3))

        try:
            # Preparar tensores con autocorrección de dimensiones
            numbers = torch.tensor(input_data, dtype=torch.long).to(device)
            temporal = torch.tensor(temporal_data, dtype=torch.float).to(device)

            # Autocorrección si input malformado
            if numbers.shape != (10, 6):
                if numbers.numel() == 0:  # Tensor vacío
                    numbers = torch.randint(1, 41, (1, 10, 6)).to(device)
                    temporal = torch.zeros((1, 10, 3), dtype=torch.float).to(device)
                elif numbers.ndim == 1 and numbers.shape[0] == 6:
                    numbers = numbers.unsqueeze(0).repeat(10, 1)
                    temporal = torch.zeros((1, 10, 3), dtype=torch.float).to(device)
                else:
                    # Redimensionar a (batch, seq, nums)
                    if numbers.ndim == 2:
                        numbers = numbers.unsqueeze(0)
                    if numbers.shape[1] < 10 or numbers.shape[2] < 6:
                        numbers = torch.randint(1, 41, (1, 10, 6)).to(device)
                        temporal = torch.zeros((1, 10, 3), dtype=torch.float).to(device)
            
            # Asegurar dimensión de batch
            if numbers.dim() == 2:
                numbers = numbers.unsqueeze(0)
            if temporal.dim() == 2:
                temporal = temporal.unsqueeze(0)
            
            # Ajustar tensores auxiliares
            seq_len = numbers.shape[1]
            positions = torch.arange(0, seq_len, dtype=torch.long).unsqueeze(0).to(device)

            # Validación de dimensiones antes de predicción
            if numbers.shape[0] < 1 or numbers.shape[1] < 1:
                logger.debug(f"⚠️ Input shape inválido: {numbers.shape}, skipping")
                continue

            # Predicción con manejo robusto de dimensiones
            with torch.no_grad():
                num_logits, _ = model(numbers, temporal, positions)
                
                # Aplanar logits y tomar primeros 40 elementos
                flat_logits = num_logits.view(-1)
                
                if flat_logits.size(0) < 40:
                    probs = np.ones(40) / 40
                    logger.debug(f"⚠️ [TRANSFORMER] No hay suficientes logits ({flat_logits.size(0)}), usando uniforme")
                else:
                    logits_1d = flat_logits[:40]
                    probs = torch.softmax(logits_1d, dim=0).cpu().numpy()

                # Generar combinación mediante muestreo
                combo = []
                used = set()
                for _ in range(6):
                    valid_indices = [i for i in range(1, 41) if i not in used]
                    if not valid_indices:
                        break
                    
                    # Obtener probabilidades para números válidos
                    valid_probs = probs[np.array(valid_indices) - 1]
                    valid_probs_sum = valid_probs.sum()
                    
                    # Normalizar o usar uniforme si suma es cero
                    if valid_probs_sum > 1e-8:
                        valid_probs /= valid_probs_sum
                    else:
                        valid_probs = np.ones(len(valid_indices)) / len(valid_indices)
                    
                    num = np.random.choice(valid_indices, p=valid_probs)
                    combo.append(int(num))
                    used.add(num)

                combo = sorted(combo)

        except Exception as e:
            logger.debug(f"⚠️ Error en la predicción del Transformer: {str(e)}")
            continue

        # Validar combinación generada
        combo_tuple = tuple(combo)
        if len(combo) != 6:
            logger.debug(f"Combinación descartada por longitud incorrecta: {combo}")
            rejection_count += 1
            continue
            
        # Comprobar si la combinación está en el historial
        if combo_tuple in historial_set:
            logger.debug(f"Combinación descartada por estar en historial: {combo}")
            rejection_count += 1
            continue
            
        # Aplicar filtros estratégicos
        try:
            if not filtro.aplicar_filtros(combo):
                logger.debug(f"Combinación descartada por filtros: {combo}")
                rejection_count += 1
                continue
        except Exception as e:
            logger.debug(f"⚠️ Error en filtro estratégico: {str(e)}")
            rejection_count += 1
            continue

        # Calcular score (manejo de errores en indexación)
        try:
            score = probs[np.array(combo) - 1].mean().item()
        except:
            score = 0.5  # Fallback si hay error en cálculo de score

        combinaciones.append({
            "combination": combo,
            "score": round(score, 4),
            "source": "transformer_deep",
            "metrics": {"transformer_score": score}
        })
        logger.debug(f"[TRANSFORMER] Combinación generada: {combo} - Score: {score:.4f}")

        # Relajar filtro si la tasa de rechazo es demasiado alta (>50%)
        rejection_rate = rejection_count / attempt
        if rejection_rate > 0.5 and filtro_original is not None:
            logger.warning(f"⚠️ Alta tasa de rechazo ({rejection_rate*100:.1f}%), relajando filtros")
            filtro.configurar_modo_estricto(False)

    # 8. Respaldo inteligente si no se generaron suficientes
    if len(combinaciones) < cantidad:
        needed = cantidad - len(combinaciones)
        log_func(f"🔁 [TRANSFORMER] Generando respaldo para {needed} combinaciones")
        
        # Restaurar configuración original del filtro
        if filtro_original is not None:
            filtro.configurar_modo_estricto(filtro_original)
        
        for _ in range(needed):
            # Generar combinación aleatoria válida
            while True:
                combo = sorted(random.sample(range(1, 41), 6))
                combo_tuple = tuple(combo)
                
                # Saltar combinaciones en historial o que fallen filtros
                if combo_tuple in historial_set:
                    continue
                try:
                    if not filtro.aplicar_filtros(combo):
                        continue
                except:
                    continue
                    
                combinaciones.append({
                    "combination": combo,
                    "score": 0.5,
                    "source": "transformer_fallback",
                    "metrics": {}
                })
                logger.debug(f"[TRANSFORMER] Respaldo generado: {combo}")
                break

    # 9. Scoring avanzado con manejo de errores
    if combinaciones:
        try:
            combinaciones_scored = score_combinations(
                combinations=combinaciones,
                historial=historial_df,
                perfil_svi=perfil_svi,
                logger=logger,
                sequential=True  # Usar procesamiento secuencial para evitar problemas de pickling
            )
            for i, scored in enumerate(combinaciones_scored):
                try:
                    # Mantener el score original si hay error en el scoring dinámico
                    new_score = max(combinaciones[i]["score"], scored.get("score", 0))
                    combinaciones[i]["score"] = round(new_score, 4)
                    
                    # Solo agregar métrica si el scoring fue exitoso
                    if "score" in scored:
                        combinaciones[i]["metrics"]["dynamic_score"] = scored["score"]
                except Exception as e:
                    logger.debug(f"⚠️ Error en scoring para combinación {i}: {str(e)} - Manteniendo score original")
        except Exception as e:
            log_func(f"⚠️ [TRANSFORMER] Error en scoring avanzado: {str(e)} - Se mantienen scores originales")

    log_func(f"✅ [TRANSFORMER] Generadas {len(combinaciones)}/{cantidad} combinaciones")
    return combinaciones[:cantidad]