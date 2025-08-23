#!/usr/bin/env python3
# OMEGA_PRO_AI_v10.1/run_optimized_omega.py - Sistema OMEGA Completamente Optimizado
"""
Script maestro para ejecutar OMEGA PRO AI con todas las optimizaciones:
- Entrenamiento con últimos 200 sorteos
- Validación cruzada temporal  
- Heurísticas optimizadas con datos reales
- Multiprocessing optimizado
- Análisis de precisión avanzado
"""

import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# Agregar directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Imports del sistema optimizado
from modules.enhanced_training import EnhancedTrainingSystem
from modules.validation_system import LotteryValidationSystem
from modules.heuristic_optimizer import optimize_jackpot_heuristics, EnhancedJackpotProfiler
from main import main as omega_main

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/optimized_omega_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

class OptimizedOmegaSystem:
    """Sistema OMEGA optimizado completo"""
    
    def __init__(self, lookback_periods: int = 200):
        self.lookback_periods = lookback_periods
        self.optimization_results = {}
        self.training_results = {}
        self.validation_results = {}
        
        # Crear directorios necesarios
        self._create_directories()
        
        logger.info(f"🚀 Sistema OMEGA optimizado inicializado - Analizando últimos {lookback_periods} sorteos")

    def _create_directories(self):
        """Crea directorios necesarios"""
        directories = [
            'logs',
            'results/training',
            'results/validation', 
            'results/heuristic_optimization',
            'results/optimized_runs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def run_heuristic_optimization(self) -> bool:
        """Ejecuta optimización de heurísticas"""
        logger.info("🎯 FASE 1: Optimización de heurísticas...")
        
        try:
            self.optimization_results = optimize_jackpot_heuristics()
            
            logger.info("✅ Optimización de heurísticas completada")
            logger.info(f"📊 Analizadas {self.optimization_results['historical_analysis']['total_combinations']} combinaciones")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en optimización de heurísticas: {e}")
            return False

    def run_enhanced_training(self) -> bool:
        """Ejecuta entrenamiento mejorado"""
        logger.info("🧠 FASE 2: Entrenamiento mejorado de modelos...")
        
        try:
            trainer = EnhancedTrainingSystem(
                lookback_periods=self.lookback_periods,
                validation_splits=5
            )
            
            self.training_results = trainer.run_complete_training()
            
            # Mostrar resumen de entrenamiento
            if 'best_model' in self.training_results:
                best = self.training_results['best_model']
                if best['name']:
                    logger.info(f"🏆 Mejor modelo: {best['name']} (Accuracy: {best['accuracy']:.2%})")
                else:
                    logger.warning("⚠️ No se pudo determinar el mejor modelo")
            
            logger.info("✅ Entrenamiento mejorado completado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en entrenamiento mejorado: {e}")
            return False

    def run_validation_analysis(self) -> bool:
        """Ejecuta análisis de validación"""
        logger.info("📊 FASE 3: Análisis de validación...")
        
        try:
            validator = LotteryValidationSystem()
            
            # Validación básica de datos
            self.validation_results = validator.run_comprehensive_validation()
            
            if 'data_analysis' in self.validation_results:
                analysis = self.validation_results['data_analysis']
                logger.info(f"📈 Calidad de datos: {analysis['data_quality']:.2%}")
                logger.info(f"📊 Últimos 200 disponibles: {'✅' if analysis['last_200_available'] else '❌'}")
            
            logger.info("✅ Análisis de validación completado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en validación: {e}")
            return False

    def run_optimized_omega(self) -> bool:
        """Ejecuta OMEGA con todas las optimizaciones"""
        logger.info("🎯 FASE 4: Ejecutando OMEGA optimizado...")
        
        try:
            # Configurar parámetros optimizados
            omega_params = {
                'data_path': "data/historial_kabala_github_fixed.csv",
                'top_n': 30,
                'svi_profile': "default",
                'retrain': False,  # Ya entrenamos en fase anterior
                'evaluate': True,
                'backtest': False,
                'disable_multiprocessing': False  # Usar multiprocessing optimizado
            }
            
            # Ejecutar OMEGA principal
            start_time = time.time()
            
            results = omega_main(**omega_params)
            
            execution_time = time.time() - start_time
            
            logger.info(f"✅ OMEGA ejecutado en {execution_time:.2f}s")
            
            # Analizar resultados
            if results and len(results) > 0:
                logger.info(f"🎯 Generadas {len(results)} combinaciones")
                
                # Mostrar mejores combinaciones
                for i, combo in enumerate(results[:5], 1):
                    combination = combo.get('combination', [])
                    score = combo.get('score', 0)
                    source = combo.get('source', 'unknown')
                    
                    combo_str = ' - '.join([f'{num:02d}' for num in combination])
                    logger.info(f"  {i}. {source.upper()} | {combo_str} | Score: {score:.3f}")
                
                # Verificar si son predicciones reales (no solo fallbacks)
                sources = [combo.get('source', '') for combo in results]
                fallback_count = sum(1 for s in sources if 'fallback' in s.lower())
                real_predictions = len(results) - fallback_count
                
                logger.info(f"📊 Predicciones reales: {real_predictions}/{len(results)} ({real_predictions/len(results)*100:.1f}%)")
                
                return True
            else:
                logger.warning("⚠️ No se generaron resultados")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando OMEGA optimizado: {e}")
            return False

    def generate_optimization_report(self):
        """Genera reporte completo de optimización"""
        logger.info("📋 Generando reporte de optimización...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(f"results/optimized_runs/optimization_report_{timestamp}.txt")
        
        try:
            with open(report_file, 'w') as f:
                f.write("="*80 + "\n")
                f.write("🚀 REPORTE DE OPTIMIZACIÓN OMEGA PRO AI\n")
                f.write("="*80 + "\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Períodos analizados: {self.lookback_periods}\n\n")
                
                # Heurísticas
                if self.optimization_results:
                    f.write("🎯 OPTIMIZACIÓN DE HEURÍSTICAS\n")
                    f.write("-" * 40 + "\n")
                    
                    analysis = self.optimization_results.get('historical_analysis', {})
                    if analysis:
                        f.write(f"Combinaciones analizadas: {analysis.get('total_combinations', 0)}\n")
                        
                        sum_stats = analysis.get('sum_statistics', {})
                        if sum_stats:
                            f.write(f"Suma promedio: {sum_stats.get('mean', 0):.1f}\n")
                            f.write(f"Rango de sumas: {sum_stats.get('min', 0)} - {sum_stats.get('max', 0)}\n")
                    
                    params = self.optimization_results.get('optimized_parameters', {})
                    if params:
                        f.write(f"Rango suma optimizado: {params.get('ideal_sum_range', 'N/A')}\n")
                        f.write(f"Gap ideal: {params.get('ideal_gap', 0):.2f}\n")
                        f.write(f"Probabilidad base: {params.get('base_prob', 0):.2f}\n")
                    
                    f.write("\n")
                
                # Entrenamiento
                if self.training_results:
                    f.write("🧠 RESULTADOS DE ENTRENAMIENTO\n")
                    f.write("-" * 40 + "\n")
                    
                    session = self.training_results.get('training_session', {})
                    if session:
                        f.write(f"Duración total: {session.get('total_duration', 0):.2f}s\n")
                        f.write(f"Tamaño de datos: {session.get('data_size', 0)}\n")
                        f.write(f"Validaciones: {session.get('validation_splits', 0)}\n")
                    
                    best_model = self.training_results.get('best_model', {})
                    if best_model and best_model.get('name'):
                        f.write(f"Mejor modelo: {best_model['name']}\n")
                        f.write(f"Accuracy: {best_model['accuracy']:.2%}\n")
                    
                    recommendations = self.training_results.get('recommendations', [])
                    if recommendations:
                        f.write("Recomendaciones:\n")
                        for rec in recommendations:
                            f.write(f"  - {rec}\n")
                    
                    f.write("\n")
                
                # Validación
                if self.validation_results:
                    f.write("📊 ANÁLISIS DE VALIDACIÓN\n")
                    f.write("-" * 40 + "\n")
                    
                    data_analysis = self.validation_results.get('data_analysis', {})
                    if data_analysis:
                        f.write(f"Combinaciones totales: {data_analysis.get('total_combinations', 0)}\n")
                        f.write(f"Calidad de datos: {data_analysis.get('data_quality', 0):.2%}\n")
                        f.write(f"Últimos 200 disponibles: {'✅' if data_analysis.get('last_200_available', False) else '❌'}\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("🎉 OPTIMIZACIÓN COMPLETADA\n")
                f.write("="*80 + "\n")
            
            logger.info(f"📋 Reporte guardado: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte: {e}")

    def run_complete_optimization(self) -> bool:
        """Ejecuta el ciclo completo de optimización"""
        logger.info("🚀 INICIANDO OPTIMIZACIÓN COMPLETA DE OMEGA PRO AI")
        logger.info("="*80)
        
        start_time = time.time()
        success_phases = 0
        total_phases = 4
        
        # Fase 1: Optimización de heurísticas
        if self.run_heuristic_optimization():
            success_phases += 1
        
        # Fase 2: Entrenamiento mejorado
        if self.run_enhanced_training():
            success_phases += 1
        
        # Fase 3: Validación
        if self.run_validation_analysis():
            success_phases += 1
        
        # Fase 4: Ejecución optimizada
        if self.run_optimized_omega():
            success_phases += 1
        
        # Generar reporte
        self.generate_optimization_report()
        
        total_time = time.time() - start_time
        
        logger.info("="*80)
        logger.info(f"🎉 OPTIMIZACIÓN COMPLETA FINALIZADA")
        logger.info(f"⏱️ Tiempo total: {total_time:.2f}s")
        logger.info(f"✅ Fases exitosas: {success_phases}/{total_phases}")
        
        if success_phases == total_phases:
            logger.info("🎯 ¡TODAS LAS OPTIMIZACIONES COMPLETADAS EXITOSAMENTE!")
            return True
        else:
            logger.warning(f"⚠️ {total_phases - success_phases} fases fallaron - Ver logs para detalles")
            return False


def main():
    """Función principal"""
    print("\n" + "🚀 " + "="*76 + " 🚀")
    print("    OMEGA PRO AI - SISTEMA COMPLETAMENTE OPTIMIZADO")
    print("🚀 " + "="*76 + " 🚀\n")
    
    print("🎯 Configuración:")
    print("   • Análisis de últimos 200 sorteos")
    print("   • Validación cruzada temporal (5 folds)")
    print("   • Heurísticas optimizadas con datos reales")
    print("   • Multiprocessing mejorado")
    print("   • Métricas de precisión avanzadas")
    print()
    
    # Crear sistema optimizado
    omega_system = OptimizedOmegaSystem(lookback_periods=200)
    
    # Ejecutar optimización completa
    success = omega_system.run_complete_optimization()
    
    if success:
        print("\n🎉 ¡OPTIMIZACIÓN EXITOSA!")
        print("📊 OMEGA PRO AI está ahora completamente optimizado")
        print("🎯 Predicciones mejoradas con análisis de 200 sorteos")
        print("💾 Resultados y reportes guardados en /results/")
    else:
        print("\n⚠️ Optimización parcial completada")
        print("📋 Revisar logs para detalles de errores")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Protección para multiprocessing
    import multiprocessing
    multiprocessing.freeze_support()
    
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass  # Ya configurado
    
    main()
