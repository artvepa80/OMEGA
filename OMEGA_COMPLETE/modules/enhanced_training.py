# OMEGA_PRO_AI_v10.1/modules/enhanced_training.py - Sistema de Entrenamiento Mejorado
"""
Sistema de entrenamiento optimizado para OMEGA PRO AI
- Analiza últimos 200 sorteos para máxima precisión
- Implementa validación cruzada temporal
- Entrena múltiples modelos en paralelo
- Genera métricas de evaluación avanzadas
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import joblib
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from collections import defaultdict
import json

# Imports internos
from modules.lstm_predictor_v2 import LSTMPredictorV2
from modules.ensemble_trainer import EnsembleTrainer, EnsembleStrategy
from modules.advanced_neural_networks import OmegaAdvancedNetwork
from modules.profiling.jackpot_profiler import JackpotProfiler
from utils.validation import validate_combination

logger = logging.getLogger(__name__)

class EnhancedTrainingSystem:
    """Sistema de entrenamiento mejorado para OMEGA PRO AI"""
    
    def __init__(self, 
                 data_path: str = "data/historial_kabala_github_fixed.csv",
                 lookback_periods: int = 200,
                 validation_splits: int = 5):
        
        self.data_path = Path(data_path)
        self.lookback_periods = lookback_periods
        self.validation_splits = validation_splits
        
        # Componentes del sistema
        self.lstm_predictor = None
        self.ensemble_trainer = None
        self.neural_network = None
        self.jackpot_profiler = None
        
        # Métricas y resultados
        self.training_metrics = {}
        self.validation_results = {}
        self.model_performances = {}
        
        # Configuración
        self.config = {
            'training_ratio': 0.8,
            'sequence_length': 20,
            'prediction_horizon': 1,
            'min_accuracy_threshold': 0.15,  # 15% de aciertos mínimo
            'models_to_train': ['lstm', 'ensemble', 'neural_network', 'jackpot']
        }
        
        logger.info(f"🎯 Sistema de entrenamiento inicializado: {lookback_periods} sorteos, {validation_splits} validaciones")

    def load_and_prepare_data(self) -> pd.DataFrame:
        """Carga y prepara los datos de entrenamiento"""
        logger.info("📊 Cargando datos históricos...")
        
        # Cargar datos completos
        df = pd.read_csv(self.data_path)
        
        # Tomar solo los últimos N sorteos para entrenamiento optimizado
        df_recent = df.tail(self.lookback_periods).copy()
        
        # Preparar columnas de bolillas
        ball_columns = [f'Bolilla {i}' for i in range(1, 7)]
        
        # Verificar que existen las columnas
        missing_cols = [col for col in ball_columns if col not in df_recent.columns]
        if missing_cols:
            logger.warning(f"⚠️ Columnas faltantes: {missing_cols}")
            # Buscar columnas alternativas
            alt_columns = [col for col in df_recent.columns if 'bolilla' in col.lower()]
            if len(alt_columns) >= 6:
                ball_columns = alt_columns[:6]
                logger.info(f"✅ Usando columnas alternativas: {ball_columns}")
        
        # Extraer combinaciones
        combinations = []
        dates = []
        
        for idx, row in df_recent.iterrows():
            try:
                # Extraer números de las bolillas
                combo = [int(row[col]) for col in ball_columns]
                
                # Validar combinación
                if validate_combination(combo):
                    combinations.append(combo)
                    
                    # Manejar fecha
                    if 'fecha' in row:
                        try:
                            date = pd.to_datetime(row['fecha'])
                        except:
                            date = datetime.now() - timedelta(days=len(combinations))
                    else:
                        date = datetime.now() - timedelta(days=len(combinations))
                    
                    dates.append(date)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"⚠️ Error procesando fila {idx}: {e}")
                continue
        
        # Crear DataFrame final
        processed_df = pd.DataFrame({
            'fecha': dates,
            'combination': combinations
        })
        
        logger.info(f"✅ Datos preparados: {len(processed_df)} sorteos válidos de los últimos {self.lookback_periods}")
        
        return processed_df

    def create_time_series_splits(self, data: pd.DataFrame) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Crea divisiones temporales para validación cruzada"""
        logger.info("⏰ Creando divisiones temporales...")
        
        # Usar TimeSeriesSplit para respetar orden temporal
        tss = TimeSeriesSplit(n_splits=self.validation_splits)
        
        indices = np.arange(len(data))
        splits = list(tss.split(indices))
        
        logger.info(f"✅ {len(splits)} divisiones temporales creadas")
        
        return splits

    def train_lstm_model(self, data: pd.DataFrame, splits: List[Tuple[np.ndarray, np.ndarray]]) -> Dict[str, Any]:
        """Entrena y evalúa el modelo LSTM v2"""
        logger.info("🧠 Entrenando modelo LSTM v2...")
        
        results = {
            'model_type': 'LSTM_v2',
            'fold_results': [],
            'average_metrics': {},
            'best_fold': None,
            'training_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Inicializar LSTM
            self.lstm_predictor = LSTMPredictorV2(
                sequence_length=self.config['sequence_length'],
                hidden_size=256,
                num_layers=3,
                dropout=0.3
            )
            
            fold_metrics = []
            
            for fold_idx, (train_idx, val_idx) in enumerate(splits):
                logger.info(f"🔄 LSTM Fold {fold_idx + 1}/{len(splits)}")
                
                # Dividir datos
                train_data = data.iloc[train_idx]['combination'].tolist()
                val_data = data.iloc[val_idx]['combination'].tolist()
                
                # Entrenar
                training_result = self.lstm_predictor.train(
                    sequences=train_data,
                    epochs=50,
                    batch_size=32
                )
                
                # Evaluar
                predictions = self.lstm_predictor.predict(train_data[-self.config['sequence_length']:], len(val_data))
                
                # Calcular métricas
                fold_result = self._evaluate_predictions(
                    predictions=[p['combination'] for p in predictions],
                    actual=val_data,
                    fold=fold_idx
                )
                
                fold_metrics.append(fold_result)
                results['fold_results'].append(fold_result)
            
            # Promediar métricas
            results['average_metrics'] = self._average_metrics(fold_metrics)
            results['best_fold'] = max(fold_metrics, key=lambda x: x['accuracy'])
            
        except Exception as e:
            logger.error(f"❌ Error entrenando LSTM: {e}")
            results['error'] = str(e)
        
        finally:
            results['training_time'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ LSTM entrenado en {results['training_time']:.2f}s")
        return results

    def train_ensemble_model(self, data: pd.DataFrame, splits: List[Tuple[np.ndarray, np.ndarray]]) -> Dict[str, Any]:
        """Entrena y evalúa el modelo de ensemble"""
        logger.info("🎭 Entrenando modelo Ensemble...")
        
        results = {
            'model_type': 'Ensemble',
            'fold_results': [],
            'average_metrics': {},
            'best_fold': None,
            'training_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Inicializar Ensemble
            self.ensemble_trainer = EnsembleTrainer(
                strategy=EnsembleStrategy.STACKING,
                cv_folds=3,
                normalization_method='standard'
            )
            
            fold_metrics = []
            
            for fold_idx, (train_idx, val_idx) in enumerate(splits):
                logger.info(f"🔄 Ensemble Fold {fold_idx + 1}/{len(splits)}")
                
                # Preparar datos
                train_combinations = [data.iloc[i]['combination'] for i in train_idx]
                val_combinations = [data.iloc[i]['combination'] for i in val_idx]
                
                # Entrenar
                training_result = self.ensemble_trainer.train_ensemble(train_combinations)
                
                # Evaluar
                predictions = self.ensemble_trainer.predict_combinations(len(val_combinations))
                
                # Calcular métricas
                fold_result = self._evaluate_predictions(
                    predictions=[p['combination'] for p in predictions],
                    actual=val_combinations,
                    fold=fold_idx
                )
                
                fold_metrics.append(fold_result)
                results['fold_results'].append(fold_result)
            
            # Promediar métricas
            results['average_metrics'] = self._average_metrics(fold_metrics)
            results['best_fold'] = max(fold_metrics, key=lambda x: x['accuracy'])
            
        except Exception as e:
            logger.error(f"❌ Error entrenando Ensemble: {e}")
            results['error'] = str(e)
        
        finally:
            results['training_time'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Ensemble entrenado en {results['training_time']:.2f}s")
        return results

    def train_neural_network(self, data: pd.DataFrame, splits: List[Tuple[np.ndarray, np.ndarray]]) -> Dict[str, Any]:
        """Entrena y evalúa la red neuronal avanzada"""
        logger.info("🧠 Entrenando Red Neuronal Avanzada...")
        
        results = {
            'model_type': 'AdvancedNeuralNetwork',
            'fold_results': [],
            'average_metrics': {},
            'best_fold': None,
            'training_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Inicializar red neuronal
            self.neural_network = OmegaAdvancedNetwork()
            
            fold_metrics = []
            
            for fold_idx, (train_idx, val_idx) in enumerate(splits):
                logger.info(f"🔄 Neural Network Fold {fold_idx + 1}/{len(splits)}")
                
                # Preparar datos
                train_combinations = [data.iloc[i]['combination'] for i in train_idx]
                val_combinations = [data.iloc[i]['combination'] for i in val_idx]
                
                # Entrenar
                training_result = self.neural_network.train_model(train_combinations)
                
                # Evaluar
                predictions = self.neural_network.predict_combinations(len(val_combinations))
                
                # Calcular métricas
                fold_result = self._evaluate_predictions(
                    predictions=predictions,
                    actual=val_combinations,
                    fold=fold_idx
                )
                
                fold_metrics.append(fold_result)
                results['fold_results'].append(fold_result)
            
            # Promediar métricas
            results['average_metrics'] = self._average_metrics(fold_metrics)
            results['best_fold'] = max(fold_metrics, key=lambda x: x['accuracy'])
            
        except Exception as e:
            logger.error(f"❌ Error entrenando Neural Network: {e}")
            results['error'] = str(e)
        
        finally:
            results['training_time'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Neural Network entrenado en {results['training_time']:.2f}s")
        return results

    def optimize_jackpot_profiler(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Optimiza el Jackpot Profiler con datos reales"""
        logger.info("🎯 Optimizando Jackpot Profiler...")
        
        results = {
            'model_type': 'JackpotProfiler',
            'optimization_results': {},
            'calibration_metrics': {},
            'training_time': 0
        }
        
        start_time = datetime.now()
        
        try:
            # Inicializar profiler
            self.jackpot_profiler = JackpotProfiler()
            
            # Extraer combinaciones
            combinations = data['combination'].tolist()
            
            # Evaluar todas las combinaciones
            profiles = []
            for combo in combinations:
                try:
                    profile_result = self.jackpot_profiler.profile([combo])
                    if profile_result and len(profile_result) > 0:
                        profiles.append(profile_result[0]['jackpot_prob'])
                    else:
                        profiles.append(0.0)
                except Exception as e:
                    logger.warning(f"⚠️ Error perfilando {combo}: {e}")
                    profiles.append(0.0)
            
            # Calcular estadísticas de calibración
            profiles = np.array(profiles)
            results['calibration_metrics'] = {
                'mean_probability': float(np.mean(profiles)),
                'std_probability': float(np.std(profiles)),
                'min_probability': float(np.min(profiles)),
                'max_probability': float(np.max(profiles)),
                'unique_values': len(np.unique(profiles)),
                'distribution_range': float(np.max(profiles) - np.min(profiles))
            }
            
            # Evaluar si la distribución es adecuada
            results['optimization_results'] = {
                'is_well_calibrated': results['calibration_metrics']['distribution_range'] > 0.1,
                'has_variance': results['calibration_metrics']['std_probability'] > 0.01,
                'total_combinations_evaluated': len(combinations)
            }
            
        except Exception as e:
            logger.error(f"❌ Error optimizando Jackpot Profiler: {e}")
            results['error'] = str(e)
        
        finally:
            results['training_time'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Jackpot Profiler optimizado en {results['training_time']:.2f}s")
        return results

    def _evaluate_predictions(self, predictions: List[List[int]], actual: List[List[int]], fold: int) -> Dict[str, Any]:
        """Evalúa predicciones contra resultados reales"""
        
        if len(predictions) != len(actual):
            # Ajustar longitudes si es necesario
            min_len = min(len(predictions), len(actual))
            predictions = predictions[:min_len]
            actual = actual[:min_len]
        
        # Métricas de aciertos
        exact_matches = 0
        partial_matches = defaultdict(int)
        
        for pred, act in zip(predictions, actual):
            if pred == act:
                exact_matches += 1
            
            # Contar coincidencias parciales
            matches = len(set(pred) & set(act))
            partial_matches[matches] += 1
        
        total_predictions = len(predictions)
        
        # Calcular métricas
        accuracy = exact_matches / total_predictions if total_predictions > 0 else 0
        
        # Métricas detalladas
        metrics = {
            'fold': fold,
            'total_predictions': total_predictions,
            'exact_matches': exact_matches,
            'accuracy': accuracy,
            'partial_matches': dict(partial_matches),
            'average_partial_matches': sum(k * v for k, v in partial_matches.items()) / total_predictions if total_predictions > 0 else 0
        }
        
        # Calcular precisión por número de aciertos
        for i in range(1, 7):
            matches_i = partial_matches.get(i, 0)
            metrics[f'precision_{i}_numbers'] = matches_i / total_predictions if total_predictions > 0 else 0
        
        return metrics

    def _average_metrics(self, fold_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Promedia métricas de todos los folds"""
        if not fold_metrics:
            return {}
        
        # Métricas a promediar
        numeric_keys = ['accuracy', 'average_partial_matches']
        for i in range(1, 7):
            numeric_keys.append(f'precision_{i}_numbers')
        
        averaged = {}
        
        for key in numeric_keys:
            values = [fold.get(key, 0) for fold in fold_metrics]
            averaged[key] = np.mean(values)
            averaged[f'{key}_std'] = np.std(values)
        
        # Totales
        averaged['total_folds'] = len(fold_metrics)
        averaged['total_predictions'] = sum(fold.get('total_predictions', 0) for fold in fold_metrics)
        averaged['total_exact_matches'] = sum(fold.get('exact_matches', 0) for fold in fold_metrics)
        
        return averaged

    def run_complete_training(self) -> Dict[str, Any]:
        """Ejecuta el ciclo completo de entrenamiento y evaluación"""
        logger.info("🚀 Iniciando entrenamiento completo de OMEGA PRO AI")
        
        overall_start = datetime.now()
        
        # Cargar y preparar datos
        data = self.load_and_prepare_data()
        
        # Crear divisiones temporales
        splits = self.create_time_series_splits(data)
        
        # Entrenar todos los modelos
        training_results = {}
        
        if 'lstm' in self.config['models_to_train']:
            training_results['lstm'] = self.train_lstm_model(data, splits)
        
        if 'ensemble' in self.config['models_to_train']:
            training_results['ensemble'] = self.train_ensemble_model(data, splits)
        
        if 'neural_network' in self.config['models_to_train']:
            training_results['neural_network'] = self.train_neural_network(data, splits)
        
        if 'jackpot' in self.config['models_to_train']:
            training_results['jackpot'] = self.optimize_jackpot_profiler(data)
        
        # Compilar resultados finales
        final_results = {
            'training_session': {
                'start_time': overall_start.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration': (datetime.now() - overall_start).total_seconds(),
                'data_size': len(data),
                'lookback_periods': self.lookback_periods,
                'validation_splits': self.validation_splits
            },
            'model_results': training_results,
            'best_model': self._determine_best_model(training_results),
            'recommendations': self._generate_recommendations(training_results)
        }
        
        # Guardar resultados
        self.save_training_results(final_results)
        
        logger.info(f"✅ Entrenamiento completo finalizado en {final_results['training_session']['total_duration']:.2f}s")
        
        return final_results

    def _determine_best_model(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Determina el mejor modelo basado en métricas"""
        best_model = {'name': None, 'accuracy': 0, 'metrics': {}}
        
        for model_name, model_results in results.items():
            if 'average_metrics' in model_results and 'accuracy' in model_results['average_metrics']:
                accuracy = model_results['average_metrics']['accuracy']
                if accuracy > best_model['accuracy']:
                    best_model = {
                        'name': model_name,
                        'accuracy': accuracy,
                        'metrics': model_results['average_metrics']
                    }
        
        return best_model

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        recommendations = []
        
        # Analizar accuracy general
        accuracies = []
        for model_name, model_results in results.items():
            if 'average_metrics' in model_results and 'accuracy' in model_results['average_metrics']:
                acc = model_results['average_metrics']['accuracy']
                accuracies.append((model_name, acc))
        
        if accuracies:
            best_acc = max(accuracies, key=lambda x: x[1])
            
            if best_acc[1] < 0.05:  # Menos del 5%
                recommendations.append("📈 Accuracy muy baja - Considerar más datos de entrenamiento")
                recommendations.append("🔧 Revisar features y preprocesamiento de datos")
            elif best_acc[1] < 0.15:  # Menos del 15%
                recommendations.append("⚠️ Accuracy moderada - Optimizar hiperparámetros")
                recommendations.append("🎯 Considerar ensemble de modelos")
            else:
                recommendations.append(f"✅ Buen rendimiento del modelo {best_acc[0]} ({best_acc[1]:.2%})")
        
        # Recomendaciones específicas por modelo
        for model_name, model_results in results.items():
            if 'error' in model_results:
                recommendations.append(f"❌ Reparar errores en modelo {model_name}")
        
        return recommendations

    def save_training_results(self, results: Dict[str, Any]):
        """Guarda los resultados del entrenamiento"""
        output_dir = Path("results/training")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"enhanced_training_{timestamp}.json"
        
        # Convertir numpy types para JSON
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=convert_numpy)
            
            logger.info(f"💾 Resultados guardados: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando resultados: {e}")


# Función principal para ejecutar desde otros módulos
def run_enhanced_training(lookback_periods: int = 200, validation_splits: int = 5) -> Dict[str, Any]:
    """Ejecuta el entrenamiento mejorado"""
    trainer = EnhancedTrainingSystem(
        lookback_periods=lookback_periods,
        validation_splits=validation_splits
    )
    
    return trainer.run_complete_training()


if __name__ == "__main__":
    # Ejecutar entrenamiento completo
    results = run_enhanced_training(lookback_periods=200, validation_splits=5)
    
    print("\n" + "="*60)
    print("🎯 RESULTADOS DEL ENTRENAMIENTO MEJORADO")
    print("="*60)
    
    if 'best_model' in results:
        best = results['best_model']
        print(f"🏆 Mejor modelo: {best['name']} (Accuracy: {best['accuracy']:.2%})")
    
    if 'recommendations' in results:
        print("\n📋 RECOMENDACIONES:")
        for rec in results['recommendations']:
            print(f"  {rec}")
    
    print(f"\n⏱️ Tiempo total: {results['training_session']['total_duration']:.2f}s")
    print("="*60)
