#!/usr/bin/env python3
# OMEGA_PRO_AI_v10.1/test_performance_monitoring.py
# Test script para validar el sistema de monitoreo de rendimiento

import time
import random
import threading
from modules.performance_monitor import get_performance_monitor, initialize_performance_monitoring
from modules.performance_alerts import get_alert_system

def simulate_model_execution(monitor, model_name, duration_range=(1, 10)):
    """Simular ejecución de un modelo con duración variable"""
    duration = random.uniform(*duration_range)
    
    with monitor.track_model_execution(model_name, expected_duration=5.0):
        print(f"🎯 Simulando ejecución de {model_name} por {duration:.1f}s")
        time.sleep(duration)
        
        # Simular posible error (10% probabilidad)
        if random.random() < 0.1:
            raise Exception(f"Error simulado en {model_name}")

def simulate_timeout_model(monitor, model_name):
    """Simular modelo que hace timeout"""
    with monitor.track_model_execution(model_name, expected_duration=3.0):
        print(f"⏰ Simulando timeout en {model_name}")
        time.sleep(8)  # Exceder el tiempo esperado

def test_performance_monitoring():
    """Prueba completa del sistema de monitoreo"""
    print("🔍 Iniciando prueba del sistema de monitoreo de rendimiento")
    print("="*60)
    
    # Inicializar monitoreo con configuración de prueba
    monitor = initialize_performance_monitoring({
        'monitor_interval': 0.5,  # Monitoreo más frecuente para pruebas
        'alert_thresholds': {
            'max_execution_time': 5.0,  # Umbral bajo para generar alertas
            'max_memory_percent': 70.0,
            'min_success_rate': 0.8
        }
    })
    
    # Obtener sistema de alertas
    alert_system = get_alert_system()
    
    print(f"✅ Monitor inicializado")
    print(f"🚨 Sistema de alertas activo: {len(alert_system.alert_rules)} reglas")
    print()
    
    # Lista de modelos para simular
    models = [
        "consensus",
        "lstm_v2", 
        "transformer_deep",
        "montecarlo",
        "clustering",
        "genetico"
    ]
    
    # Fase 1: Ejecuciones normales
    print("📊 FASE 1: Ejecuciones normales")
    print("-" * 30)
    
    for i in range(15):
        model = random.choice(models)
        
        try:
            # Variar duración - algunas serán lentas
            if random.random() < 0.3:  # 30% de modelos lentos
                simulate_model_execution(monitor, model, (4, 8))
            else:
                simulate_model_execution(monitor, model, (1, 3))
            
        except Exception as e:
            print(f"❌ Error capturado: {e}")
            monitor.record_fallback_usage(model, f"Error: {str(e)[:30]}")
        
        time.sleep(0.2)  # Pausa breve entre ejecuciones
    
    # Fase 2: Generar timeouts
    print("\n⏰ FASE 2: Generando timeouts")
    print("-" * 30)
    
    for model in ["lstm_v2", "transformer_deep"]:
        try:
            simulate_timeout_model(monitor, model)
        except Exception as e:
            print(f"⏰ Timeout capturado para {model}")
            monitor.record_fallback_usage(model, "timeout")
    
    # Fase 3: Simular múltiples fallbacks
    print("\n🔄 FASE 3: Generando fallbacks múltiples")
    print("-" * 30)
    
    problem_model = "clustering"
    for i in range(5):
        monitor.record_fallback_usage(problem_model, f"Error simulado #{i+1}")
        time.sleep(0.1)
    
    # Esperar un momento para que se procesen las alertas
    time.sleep(2)
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("📊 RESULTADOS DE LA PRUEBA")
    print("="*60)
    
    # Resumen de rendimiento
    monitor.print_performance_summary()
    
    # Alertas generadas
    active_alerts = alert_system.get_active_alerts()
    print(f"\n🚨 ALERTAS GENERADAS: {len(active_alerts)}")
    print("-" * 40)
    
    for alert in active_alerts[-10:]:  # Mostrar últimas 10 alertas
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(alert.severity, "•")
        print(f"{severity_emoji} [{alert.severity.upper()}] {alert.message}")
        if alert.model_name:
            print(f"    Modelo: {alert.model_name}")
        print(f"    Valor: {alert.metric_value:.2f} | Umbral: {alert.threshold_value:.2f}")
        print()
    
    # Estadísticas de alertas
    stats = alert_system.get_alert_statistics()
    print("📈 ESTADÍSTICAS DE ALERTAS:")
    print(f"   Total alertas: {stats['total_alerts']}")
    print(f"   Alertas activas: {stats['active_alerts']}")
    print(f"   Por severidad: {dict(stats['alerts_by_severity'])}")
    print(f"   Por modelo: {dict(stats['alerts_by_model'])}")
    
    # Exportar reportes
    print("\n📄 GENERANDO REPORTES...")
    print("-" * 30)
    
    try:
        # Exportar reporte de rendimiento
        report_path = monitor.export_performance_report()
        print(f"✅ Reporte de rendimiento: {report_path}")
        
        # Exportar reporte de alertas
        alerts_report = alert_system.export_alerts_report()
        print(f"✅ Reporte de alertas: {alerts_report}")
        
        # Generar reporte completo con gráficos (requiere matplotlib)
        try:
            from modules.performance_reporter import PerformanceReporter
            reporter = PerformanceReporter(monitor)
            html_report = reporter.generate_comprehensive_report()
            print(f"✅ Reporte HTML completo: {html_report}")
        except ImportError:
            print("⚠️ matplotlib no disponible - reporte HTML omitido")
    
    except Exception as e:
        print(f"❌ Error generando reportes: {e}")
    
    # Detener monitoreo
    monitor.stop_monitoring()
    
    print("\n🎯 PRUEBA COMPLETADA")
    print("="*60)
    
    # Análisis de cuellos de botella
    bottlenecks = monitor._analyze_bottlenecks()
    if any(bottlenecks.values()):
        print("\n🚧 CUELLOS DE BOTELLA DETECTADOS:")
        
        if bottlenecks['slowest_models']:
            print("⏳ Modelos más lentos:")
            for model_info in bottlenecks['slowest_models']:
                print(f"   • {model_info['model']}: {model_info['avg_time']:.1f}s")
        
        if bottlenecks['timeout_models']:
            print("⏰ Modelos con timeouts:")
            for model_info in bottlenecks['timeout_models']:
                print(f"   • {model_info['model']}: {model_info['timeout_count']} timeouts")
    
    # Recomendaciones
    recommendations = monitor._get_optimization_recommendations()
    if recommendations:
        print("\n💡 RECOMENDACIONES DE OPTIMIZACIÓN:")
        for rec in recommendations[:5]:  # Top 5
            priority_emoji = {"high": "🔥", "medium": "⚠️", "low": "ℹ️"}.get(rec.get('priority'), "•")
            print(f"   {priority_emoji} {rec['recommendation']}")
    
    print("\n🏁 Prueba finalizada exitosamente")

if __name__ == "__main__":
    test_performance_monitoring()