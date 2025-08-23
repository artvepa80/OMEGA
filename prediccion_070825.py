#!/usr/bin/env python3
# PREDICCIÓN OFICIAL OMEGA PRO AI V2.0 PARA 07/08/2025
"""
🎯 PREDICCIÓN OFICIAL PARA HOY: 07/08/2025
Sistema optimizado con resultado real del 05/08/2025 incluido
"""

import os
import sys
import logging
import json
import multiprocessing
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configurar multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
from utils.validation import clean_historial_df

# Módulos optimizados V2
from modules.omega_200_analyzer import Omega200Analyzer
from modules.neural_enhancer import NeuralEnhancer
from modules.ensemble_calibrator import EnsembleCalibrator

# Sistema principal
from core.predictor import HybridOmegaPredictor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/prediccion_070825_{datetime.now().strftime("%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PrediccionOficial070825:
    """Predicción oficial OMEGA para el 07/08/2025"""
    
    def __init__(self):
        self.fecha_objetivo = "07/08/2025"
        self.data_path = "data/historial_kabala_github_fixed.csv"
        self.historial_df = None
        
        # Configuración V2.0 optimizada
        self.config_v2 = {
            'neural_enhanced_weight': 0.45,  # Incrementado por éxito en análisis
            'focus_high_numbers': True,
            'boost_number_14': True,
            'boost_recent_winners': True,  # 31, 34, 39, 40, 29
            'min_high_numbers': 2,  # Mínimo 2 números altos (30-40)
            'max_combinations': 8,
            'confidence_threshold': 0.85
        }
        
        # Números del resultado 05/08/2025 para análisis
        self.ultimo_resultado = [14, 39, 34, 40, 31, 29]
        self.numeros_altos_exitosos = [39, 34, 40, 31]  # 30-40
        self.numero_bajo_exitoso = 14  # Único bajo que salió
        
        logger.info(f"🎯 Predicción oficial inicializada para {self.fecha_objetivo}")
        logger.info(f"📊 Análisis basado en resultado 05/08/2025: {self.ultimo_resultado}")
    
    def verificar_datos_actualizados(self) -> bool:
        """Verifica que los datos incluyan el resultado del 05/08/2025"""
        try:
            df = pd.read_csv(self.data_path)
            
            # Verificar última entrada
            if len(df) > 0:
                ultima_fila = df.iloc[-1]
                numeros_ultima = [int(ultima_fila[f'bolilla_{i}']) for i in range(1, 7)]
                
                if sorted(numeros_ultima) == sorted(self.ultimo_resultado):
                    logger.info(f"✅ Datos actualizados confirmados - Último resultado: {numeros_ultima}")
                    return True
                else:
                    logger.warning(f"⚠️ Último resultado en DB: {numeros_ultima}")
                    logger.warning(f"⚠️ Esperado: {self.ultimo_resultado}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verificando datos: {e}")
            return False
    
    def cargar_datos_optimizados(self) -> bool:
        """Carga y prepara datos con último resultado incluido"""
        try:
            # Verificar datos actualizados
            if not self.verificar_datos_actualizados():
                logger.error("❌ Datos no actualizados - no se puede proceder")
                return False
            
            # Cargar datos
            raw_df = pd.read_csv(self.data_path)
            logger.info(f"📊 Datos cargados: {len(raw_df)} registros")
            
            # Limpiar y validar
            self.historial_df = clean_historial_df(raw_df)
            
            if self.historial_df.empty:
                logger.error("❌ Error procesando datos históricos")
                return False
            
            # Verificar último resultado en datos limpios
            ultima_combinacion = self.historial_df.iloc[-1].values.tolist()
            logger.info(f"🔍 Última combinación procesada: {ultima_combinacion}")
            
            logger.info(f"✅ Datos preparados: {len(self.historial_df)} registros limpios")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            return False
    
    def ejecutar_analisis_200_optimizado(self) -> Dict[str, Any]:
        """Análisis de últimos 200 sorteos con optimizaciones V2"""
        try:
            logger.info("🔍 Ejecutando análisis 200 optimizado V2...")
            
            analyzer = Omega200Analyzer(self.historial_df)
            
            # Obtener insights optimizados
            insights = analyzer.get_prediction_insights()
            
            # Generar combinaciones con enfoque en números altos
            combinaciones = analyzer.generate_optimized_combinations(8)
            
            # Aplicar filtros adicionales V2
            combinaciones_filtradas = []
            for combo in combinaciones:
                numeros_altos = sum(1 for n in combo if n >= 30)
                tiene_14 = 14 in combo
                tiene_exitoso = any(n in self.numeros_altos_exitosos for n in combo)
                
                # Criterios V2
                if numeros_altos >= self.config_v2['min_high_numbers'] or tiene_14 or tiene_exitoso:
                    combinaciones_filtradas.append({
                        'combination': combo,
                        'high_numbers_count': numeros_altos,
                        'has_14': tiene_14,
                        'has_recent_winner': tiene_exitoso,
                        'score': 0.8 + (numeros_altos * 0.05) + (0.1 if tiene_14 else 0)
                    })
            
            logger.info(f"✅ Análisis 200 V2: {len(combinaciones_filtradas)} combinaciones filtradas")
            logger.info(f"🎯 Confianza: {insights.get('confidence_score', 0):.1%}")
            
            return {
                'success': True,
                'insights': insights,
                'combinations': combinaciones_filtradas,
                'total_analyzed': len(combinaciones),
                'filtered_count': len(combinaciones_filtradas)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis 200 V2: {e}")
            return {'success': False, 'error': str(e)}
    
    def ejecutar_neural_enhanced_v2(self) -> Dict[str, Any]:
        """Neural Enhanced V2 con boost para números exitosos"""
        try:
            logger.info("🧠 Ejecutando Neural Enhanced V2 para 07/08/2025...")
            
            enhancer = NeuralEnhancer()
            
            # Entrenar con énfasis en último resultado
            logger.info("📚 Entrenando modelo con datos actualizados...")
            enhancer.train_enhanced_model(
                self.historial_df,
                epochs=60,  # Más épocas para mejor aprendizaje
                learning_rate=0.002,  # Learning rate más bajo para precisión
                focus_recent=True
            )
            
            # Generar predicciones con boost V2
            predictions = enhancer.predict_combinations(
                self.historial_df,
                num_combinations=6,
                focus_high_numbers=True
            )
            
            # Aplicar boost adicional para números exitosos del 05/08
            for pred in predictions:
                combo = pred['combination']
                boost_score = 0
                
                # Boost por números altos exitosos
                for num in combo:
                    if num in self.numeros_altos_exitosos:
                        boost_score += 0.15
                    elif num == 14:  # Boost especial para 14
                        boost_score += 0.20
                    elif num == 29:  # Último número exitoso
                        boost_score += 0.10
                
                # Aplicar boost
                pred['score'] = min(pred.get('score', 0.5) + boost_score, 1.0)
                pred['neural_boost'] = boost_score
                pred['high_numbers_count'] = sum(1 for n in combo if n >= 30)
                pred['has_recent_winners'] = any(n in self.ultimo_resultado for n in combo)
            
            # Ordenar por score
            predictions.sort(key=lambda x: x['score'], reverse=True)
            
            training_summary = enhancer.get_training_summary()
            
            logger.info(f"✅ Neural Enhanced V2 completado: {len(predictions)} predicciones")
            logger.info(f"🎯 Modelo entrenado en {training_summary.get('total_epochs', 0)} épocas")
            
            return {
                'success': True,
                'predictions': predictions,
                'training_summary': training_summary
            }
            
        except Exception as e:
            logger.error(f"❌ Error en Neural Enhanced V2: {e}")
            return {'success': False, 'error': str(e)}
    
    def integrar_predicciones_v2(self, analisis_200: Dict, neural_v2: Dict) -> List[Dict[str, Any]]:
        """Integra todas las predicciones con pesos V2 optimizados"""
        try:
            logger.info("🔀 Integrando predicciones V2 para 07/08/2025...")
            
            todas_combinaciones = []
            
            # 1. Neural Enhanced V2 (PESO 45%)
            if neural_v2.get('success'):
                for pred in neural_v2['predictions']:
                    todas_combinaciones.append({
                        'combination': pred['combination'],
                        'source': 'neural_enhanced_v2',
                        'score': pred['score'] * 1.45,  # Peso 45%
                        'confidence': pred.get('confidence', 0.8),
                        'neural_boost': pred.get('neural_boost', 0),
                        'high_numbers_count': pred.get('high_numbers_count', 0),
                        'has_recent_winners': pred.get('has_recent_winners', False),
                        'priority': 1
                    })
            
            # 2. Análisis 200 V2 (PESO 25%)
            if analisis_200.get('success'):
                for combo_data in analisis_200['combinations']:
                    todas_combinaciones.append({
                        'combination': combo_data['combination'],
                        'source': '200_analyzer_v2',
                        'score': combo_data['score'] * 1.25,  # Peso 25%
                        'confidence': 0.7,
                        'high_numbers_count': combo_data.get('high_numbers_count', 0),
                        'has_14': combo_data.get('has_14', False),
                        'has_recent_winner': combo_data.get('has_recent_winner', False),
                        'priority': 2
                    })
            
            # 3. Eliminar duplicados manteniendo mejor score
            combinaciones_unicas = {}
            for combo_data in todas_combinaciones:
                combo_tuple = tuple(sorted(combo_data['combination']))
                
                if combo_tuple not in combinaciones_unicas:
                    combinaciones_unicas[combo_tuple] = combo_data
                else:
                    if combo_data['score'] > combinaciones_unicas[combo_tuple]['score']:
                        combinaciones_unicas[combo_tuple] = combo_data
            
            # 4. Ordenar y seleccionar top combinaciones
            combinaciones_finales = list(combinaciones_unicas.values())
            combinaciones_finales.sort(key=lambda x: (-x['score'], x['priority']))
            
            # 5. Tomar top 8 para predicción oficial
            top_combinaciones = combinaciones_finales[:8]
            
            logger.info(f"✅ Integración V2 completada: {len(top_combinaciones)} combinaciones finales")
            
            # Estadísticas
            neural_count = sum(1 for c in top_combinaciones if 'neural' in c['source'])
            analyzer_count = sum(1 for c in top_combinaciones if '200' in c['source'])
            
            logger.info(f"🧠 Neural Enhanced: {neural_count}/{len(top_combinaciones)}")
            logger.info(f"📊 Analizador 200: {analyzer_count}/{len(top_combinaciones)}")
            
            return top_combinaciones
            
        except Exception as e:
            logger.error(f"❌ Error integrando predicciones V2: {e}")
            return []
    
    def guardar_prediccion_oficial(self, combinaciones_finales: List[Dict]):
        """Guarda la predicción oficial para el 07/08/2025"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Crear directorio de predicciones
            pred_dir = Path("predictions/070825")
            pred_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar CSV con predicción oficial
            csv_data = []
            for i, combo_data in enumerate(combinaciones_finales):
                row = {
                    'ranking': i + 1,
                    'fecha_prediccion': '07/08/2025',
                    'combination': '-'.join(f"{n:02d}" for n in combo_data['combination']),
                    'source': combo_data['source'],
                    'score': round(combo_data['score'], 3),
                    'confidence': round(combo_data['confidence'], 3),
                    'high_numbers_count': combo_data.get('high_numbers_count', 0),
                    'has_recent_winners': combo_data.get('has_recent_winners', False),
                    'neural_boost': combo_data.get('neural_boost', 0),
                    'priority': combo_data['priority']
                }
                csv_data.append(row)
            
            csv_path = pred_dir / f"prediccion_oficial_070825_{timestamp}.csv"
            pd.DataFrame(csv_data).to_csv(csv_path, index=False)
            
            # Guardar resumen JSON
            resumen_completo = {
                'fecha_prediccion': '07/08/2025',
                'fecha_generacion': datetime.now().isoformat(),
                'version_sistema': 'OMEGA PRO AI V2.0',
                'basado_en_resultado': '05/08/2025: 14-39-34-40-31-29',
                'optimizaciones_aplicadas': [
                    'Neural Enhanced weight 45%',
                    'Boost números altos (30-40)',
                    'Boost especial número 14',
                    'Boost números exitosos recientes',
                    'Análisis 200 optimizado'
                ],
                'combinaciones_oficiales': combinaciones_finales,
                'configuracion_v2': self.config_v2,
                'estadisticas': {
                    'total_combinaciones': len(combinaciones_finales),
                    'promedio_numeros_altos': sum(c.get('high_numbers_count', 0) for c in combinaciones_finales) / len(combinaciones_finales),
                    'combinaciones_con_ganadores_recientes': sum(1 for c in combinaciones_finales if c.get('has_recent_winners', False))
                }
            }
            
            json_path = pred_dir / f"prediccion_oficial_070825_resumen_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(resumen_completo, f, indent=2, default=str)
            
            logger.info(f"💾 Predicción oficial guardada:")
            logger.info(f"   📊 CSV: {csv_path}")
            logger.info(f"   📋 JSON: {json_path}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando predicción oficial: {e}")
    
    def mostrar_prediccion_oficial(self, combinaciones_finales: List[Dict]):
        """Muestra la predicción oficial para el 07/08/2025"""
        try:
            print("\n" + "="*90)
            print("🎯 PREDICCIÓN OFICIAL OMEGA PRO AI V2.0 - 07/08/2025 🎯")
            print("="*90)
            
            print(f"\n📊 SISTEMA OPTIMIZADO:")
            print(f"   • 🧠 Neural Enhanced V2: {self.config_v2['neural_enhanced_weight']:.0%} peso")
            print(f"   • 🎯 Análisis basado en resultado 05/08/2025: {self.ultimo_resultado}")
            print(f"   • 🔥 Boost números altos exitosos: {self.numeros_altos_exitosos}")
            print(f"   • ⭐ Boost especial número 14: ACTIVADO")
            print(f"   • 📈 Datos actualizados hasta: 05/08/2025")
            
            print(f"\n🏆 TOP {len(combinaciones_finales)} COMBINACIONES OFICIALES:")
            print("-" * 90)
            
            for i, combo_data in enumerate(combinaciones_finales):
                combo_str = " - ".join(f"{n:02d}" for n in combo_data['combination'])
                
                # Emojis por fuente
                source_emoji = {
                    'neural_enhanced_v2': '🧠',
                    '200_analyzer_v2': '📊',
                    'ensemble_v2': '🎭',
                    'hybrid': '🚀'
                }.get(combo_data['source'], '🎲')
                
                # Características destacadas
                high_count = combo_data.get('high_numbers_count', 0)
                has_winners = combo_data.get('has_recent_winners', False)
                neural_boost = combo_data.get('neural_boost', 0)
                
                # Indicadores especiales
                indicators = []
                if high_count >= 3:
                    indicators.append("🔥")
                if has_winners:
                    indicators.append("⭐")
                if neural_boost > 0.2:
                    indicators.append("🚀")
                
                indicators_str = " ".join(indicators) if indicators else ""
                
                print(f"  {i+1:2d}. {source_emoji} {combo_str} | "
                      f"Score: {combo_data['score']:.3f} | "
                      f"Altos: {high_count}/6 | "
                      f"Conf: {combo_data['confidence']:.2f} {indicators_str}")
            
            # Estadísticas finales
            total_neural = sum(1 for c in combinaciones_finales if 'neural' in c['source'])
            total_200 = sum(1 for c in combinaciones_finales if '200' in c['source'])
            promedio_altos = sum(c.get('high_numbers_count', 0) for c in combinaciones_finales) / len(combinaciones_finales)
            con_ganadores = sum(1 for c in combinaciones_finales if c.get('has_recent_winners', False))
            
            print(f"\n📈 ESTADÍSTICAS DE LA PREDICCIÓN:")
            print("-" * 50)
            print(f"🧠 Predicciones Neural Enhanced: {total_neural}/{len(combinaciones_finales)}")
            print(f"📊 Predicciones Analizador 200: {total_200}/{len(combinaciones_finales)}")
            print(f"🎯 Promedio números altos (30-40): {promedio_altos:.1f}/6")
            print(f"⭐ Con números del 05/08/2025: {con_ganadores}/{len(combinaciones_finales)}")
            
            # Números más frecuentes en la predicción
            todos_numeros = []
            for combo_data in combinaciones_finales:
                todos_numeros.extend(combo_data['combination'])
            
            from collections import Counter
            frecuencias = Counter(todos_numeros)
            top_numeros = frecuencias.most_common(10)
            
            print(f"\n🔥 NÚMEROS MÁS FRECUENTES EN PREDICCIÓN:")
            print("-" * 50)
            numeros_str = " | ".join([f"{num:02d}({freq}x)" for num, freq in top_numeros])
            print(f"   {numeros_str}")
            
            print("\n" + "="*90)
            print("🍀 ¡BUENA SUERTE CON LA PREDICCIÓN OFICIAL V2.0! 🍀")
            print("🎯 Objetivo: Superar los 2 aciertos del análisis anterior")
            print("="*90)
            
        except Exception as e:
            logger.error(f"❌ Error mostrando predicción oficial: {e}")
    
    def ejecutar_prediccion_completa(self) -> Dict[str, Any]:
        """Ejecuta la predicción completa para el 07/08/2025"""
        try:
            logger.info("🎯 Iniciando predicción oficial para 07/08/2025...")
            
            # 1. Cargar datos actualizados
            if not self.cargar_datos_optimizados():
                return {'success': False, 'error': 'Error cargando datos'}
            
            # 2. Ejecutar análisis 200 V2
            analisis_200 = self.ejecutar_analisis_200_optimizado()
            
            # 3. Ejecutar Neural Enhanced V2
            neural_v2 = self.ejecutar_neural_enhanced_v2()
            
            # 4. Integrar predicciones
            combinaciones_finales = self.integrar_predicciones_v2(analisis_200, neural_v2)
            
            if not combinaciones_finales:
                logger.error("❌ No se generaron combinaciones finales")
                return {'success': False, 'error': 'No hay combinaciones'}
            
            # 5. Guardar predicción oficial
            self.guardar_prediccion_oficial(combinaciones_finales)
            
            # 6. Mostrar predicción oficial
            self.mostrar_prediccion_oficial(combinaciones_finales)
            
            logger.info("🎉 Predicción oficial 07/08/2025 completada exitosamente!")
            
            return {
                'success': True,
                'fecha': '07/08/2025',
                'combinaciones_oficiales': combinaciones_finales,
                'analisis_200': analisis_200,
                'neural_v2': neural_v2,
                'total_combinaciones': len(combinaciones_finales)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción completa: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Función principal"""
    try:
        print("🎯 Generando predicción oficial OMEGA PRO AI V2.0 para 07/08/2025...")
        
        # Crear instancia de predicción
        prediccion = PrediccionOficial070825()
        
        # Ejecutar predicción completa
        resultado = prediccion.ejecutar_prediccion_completa()
        
        if resultado.get('success'):
            print(f"\n🎉 ¡PREDICCIÓN OFICIAL GENERADA EXITOSAMENTE!")
            print(f"📅 Fecha objetivo: {resultado['fecha']}")
            print(f"🎯 Combinaciones oficiales: {resultado['total_combinaciones']}")
        else:
            print(f"\n❌ Error generando predicción: {resultado.get('error')}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Predicción interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        logger.error(f"Error crítico en main: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
