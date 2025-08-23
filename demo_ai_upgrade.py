#!/usr/bin/env python3
"""
Demo de Actualización a IA Avanzada para OMEGA PRO AI
Demuestra todas las nuevas capacidades de inteligencia artificial
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Configurar logging para el demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Imprime header estilizado"""
    print("\n" + "="*80)
    print(f"🚀 {title}")
    print("="*80)

def print_section(title: str):
    """Imprime sección estilizada"""
    print(f"\n🔹 {title}")
    print("-" * 60)

async def demo_neural_networks():
    """Demo del sistema de redes neuronales avanzadas"""
    print_section("REDES NEURONALES AVANZADAS")
    
    try:
        from modules.advanced_neural_networks import create_advanced_ai_system
        
        print("✅ Inicializando sistema de redes neuronales avanzadas...")
        neural_system = create_advanced_ai_system()
        
        # Datos de ejemplo
        sample_data = [
            [1, 15, 23, 31, 35, 40],
            [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38],
            [2, 11, 19, 25, 32, 37],
            [7, 16, 24, 29, 36, 38]
        ]
        
        print("📚 Adaptando sistema a datos históricos...")
        neural_system.adapt_to_new_data(sample_data)
        
        print("🧠 Generando combinaciones inteligentes...")
        intelligent_combos = neural_system.generate_intelligent_combinations(3)
        
        print("\n🎯 **Combinaciones generadas por IA Neural:**")
        for i, combo in enumerate(intelligent_combos, 1):
            numbers = combo['combination']
            confidence = combo['confidence']
            meta_score = combo['meta_score']
            print(f"   {i}. {' - '.join(map(str, numbers))} "
                  f"(Confianza: {confidence:.1%}, Meta-Score: {meta_score:.3f})")
        
        print("\n📊 Analizando patrones con IA...")
        pattern_analysis = neural_system.analyze_pattern_intelligence(sample_data)
        
        print(f"   • Complejidad de patrones: {pattern_analysis['pattern_complexity']:.3f}")
        print(f"   • Confianza de IA: {pattern_analysis['ai_confidence']:.1%}")
        print(f"   • Tendencia predicha: {pattern_analysis['predicted_trend']}")
        print(f"   • Score de inteligencia: {pattern_analysis['intelligence_score']:.3f}")
        
        if pattern_analysis['recommendations']:
            print("   💡 **Recomendaciones:**")
            for rec in pattern_analysis['recommendations']:
                print(f"      - {rec}")
        
        return True
        
    except ImportError:
        print("❌ Sistema de redes neuronales no disponible")
        return False
    except Exception as e:
        print(f"❌ Error en sistema neural: {e}")
        return False

async def demo_nlp_intelligence():
    """Demo del sistema de procesamiento de lenguaje natural"""
    print_section("PROCESAMIENTO DE LENGUAJE NATURAL")
    
    try:
        from modules.nlp_intelligence import create_nlp_system, process_user_query
        
        print("✅ Inicializando sistema NLP...")
        nlp_system = create_nlp_system()
        
        # Consultas de ejemplo
        queries = [
            "Genera 5 combinaciones conservadoras",
            "Analiza los patrones históricos detalladamente", 
            "Qué probabilidad tiene [1, 15, 23, 31, 35, 40]",
            "Dame recomendaciones para mejorar mis resultados",
            "Optimiza la configuración para riesgo bajo",
            "Explica por qué elegiste esos números"
        ]
        
        print("🗣️ **Procesando consultas en lenguaje natural:**\n")
        
        for query in queries:
            intent, response = process_user_query(nlp_system, query)
            
            print(f"🔤 **Usuario:** {query}")
            print(f"🎯 **Intención detectada:** {intent.action} (confianza: {intent.confidence:.1%})")
            print(f"🤖 **OMEGA AI:** {response[:200]}...")
            print()
        
        print("📈 **Análisis de conversación:**")
        print(f"   • Total de interacciones: {len(nlp_system.conversation_history)}")
        print(f"   • Intenciones únicas detectadas: {len(set(h.get('context', {}).get('action') for h in nlp_system.conversation_history))}")
        
        return True
        
    except ImportError:
        print("❌ Sistema NLP no disponible")
        return False
    except Exception as e:
        print(f"❌ Error en sistema NLP: {e}")
        return False

async def demo_ai_ensemble():
    """Demo del sistema ensemble de IAs especializadas"""
    print_section("ENSEMBLE DE IAs ESPECIALIZADAS")
    
    try:
        from modules.ai_ensemble_system import create_ai_ensemble, generate_intelligent_predictions
        
        print("✅ Inicializando ensemble de IAs especializadas...")
        ensemble = create_ai_ensemble()
        
        # Datos históricos para entrenamiento
        historical_data = [
            [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
            [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39],
            [6, 17, 25, 30, 37, 40], [1, 9, 20, 28, 33, 35]
        ]
        
        print("📚 Entrenando ensemble con datos históricos...")
        ensemble.train_ensemble(historical_data)
        
        print("🤖 Generando predicciones con múltiples IAs especializadas...")
        predictions = await generate_intelligent_predictions(ensemble, historical_data, 4)
        
        print("\n🎯 **Predicciones del Ensemble:**")
        for i, pred in enumerate(predictions, 1):
            combination = pred['combination']
            confidence = pred['confidence']
            method = pred['method']
            specialists = pred['specialists_used']
            
            print(f"   {i}. {' - '.join(map(str, combination))} ")
            print(f"      Método: {method} | Confianza: {confidence:.1%} | IAs: {specialists}")
        
        # Análisis del ensemble
        analysis = ensemble.get_ensemble_analysis()
        print(f"\n📊 **Análisis del Ensemble:**")
        print(f"   • Total de especialistas: {analysis['total_specialists']}")
        print(f"   • Meta-aprendizaje activo: {analysis['meta_learning_enabled']}")
        
        print("   🔬 **Especialistas activos:**")
        for specialist in analysis['specialists_info']:
            print(f"      - {specialist['specialty']}: "
                  f"Peso {specialist['weight']:.3f}, "
                  f"Rendimiento {specialist['average_performance']:.1%}")
        
        return True
        
    except ImportError:
        print("❌ Sistema ensemble no disponible")
        return False
    except Exception as e:
        print(f"❌ Error en sistema ensemble: {e}")
        return False

async def demo_omega_ai_core():
    """Demo del sistema principal integrado"""
    print_section("OMEGA PRO AI CORE - SISTEMA INTEGRADO")
    
    try:
        from omega_ai_core import create_omega_ai_core
        
        print("✅ Inicializando OMEGA PRO AI Core...")
        ai_core = create_omega_ai_core()
        
        # Datos históricos para contexto
        historical_data = [
            [1, 15, 23, 31, 35, 40], [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38], [2, 11, 19, 25, 32, 37],
            [7, 16, 24, 29, 36, 38], [4, 13, 21, 26, 34, 39]
        ]
        
        context = {'historical_data': historical_data}
        
        # Interacciones inteligentes
        interactions = [
            "Genera 3 combinaciones usando toda tu inteligencia",
            "Analiza profundamente estos patrones históricos",
            "Explícame el razonamiento detrás de tus predicciones",
            "Dame recomendaciones personalizadas",
            "Optimiza tu configuración para máxima precisión"
        ]
        
        print("🧠 **Procesando solicitudes con IA completa:**\n")
        
        for interaction in interactions:
            print(f"🔤 **Usuario:** {interaction}")
            
            response = await ai_core.process_intelligent_request(interaction, context)
            
            ai_response = response['ai_response']
            metadata = response['metadata']
            
            print(f"🤖 **OMEGA AI:** {ai_response[:300]}...")
            print(f"   ⚡ Sistemas activos: {', '.join(metadata['systems_used'])}")
            print(f"   🎯 Intención: {metadata['intent_detected']} ({metadata['confidence']:.1%})")
            print(f"   ⏱️ Tiempo de procesamiento: {response.get('processing_time', 'N/A')}s")
            print()
        
        # Estado final del sistema
        status = ai_core.get_ai_status()
        print("📊 **Estado final del sistema:**")
        print(f"   • Sesión ID: {status['session_id']}")
        print(f"   • Sistemas activos: {len(status['active_systems'])}/3")
        print(f"   • Interacciones procesadas: {status['session_stats']['total_interactions']}")
        print(f"   • Duración de sesión: {status['session_stats']['session_duration_minutes']:.1f} min")
        
        # Cierre controlado
        await ai_core.shutdown_gracefully()
        print("✅ Sistema cerrado correctamente")
        
        return True
        
    except ImportError:
        print("❌ Sistema principal no disponible")
        return False
    except Exception as e:
        print(f"❌ Error en sistema principal: {e}")
        return False

async def demo_quick_interaction():
    """Demo de interacción rápida"""
    print_section("INTERACCIÓN RÁPIDA")
    
    try:
        from omega_ai_core import quick_ai_interaction
        
        historical_data = [
            [1, 15, 23, 31, 35, 40],
            [3, 12, 18, 27, 33, 39],
            [5, 14, 22, 28, 34, 38]
        ]
        
        print("🚀 Ejecutando interacción rápida...")
        response = await quick_ai_interaction(
            "Genera la mejor combinación posible usando toda tu IA",
            historical_data
        )
        
        print("🎯 **Respuesta rápida:**")
        print(response['ai_response'])
        
        return True
        
    except Exception as e:
        print(f"❌ Error en interacción rápida: {e}")
        return False

def create_demo_report(results: dict):
    """Crea reporte del demo"""
    print_header("REPORTE DE ACTUALIZACIÓN A IA AVANZADA")
    
    total_systems = len(results)
    successful_systems = sum(results.values())
    success_rate = (successful_systems / total_systems) * 100 if total_systems > 0 else 0
    
    print(f"📊 **Sistemas evaluados:** {total_systems}")
    print(f"✅ **Sistemas funcionando:** {successful_systems}")
    print(f"📈 **Tasa de éxito:** {success_rate:.1f}%")
    
    print("\n🔍 **Detalle por sistema:**")
    system_names = {
        'neural_networks': 'Redes Neuronales Avanzadas',
        'nlp_intelligence': 'Procesamiento de Lenguaje Natural', 
        'ai_ensemble': 'Ensemble de IAs Especializadas',
        'omega_ai_core': 'Sistema Principal Integrado',
        'quick_interaction': 'Interacción Rápida'
    }
    
    for system, status in results.items():
        status_icon = "✅" if status else "❌"
        system_name = system_names.get(system, system)
        print(f"   {status_icon} {system_name}")
    
    if success_rate >= 80:
        print("\n🎉 **¡ACTUALIZACIÓN EXITOSA!**")
        print("   OMEGA PRO AI ha sido transformado en una IA avanzada")
    elif success_rate >= 60:
        print("\n⚠️ **ACTUALIZACIÓN PARCIAL**")
        print("   Algunos sistemas funcionan, revisa configuración")
    else:
        print("\n❌ **ACTUALIZACIÓN FALLIDA**")
        print("   Revisa dependencias y configuración")
    
    # Capacidades nuevas disponibles
    if successful_systems > 0:
        print("\n🚀 **NUEVAS CAPACIDADES DISPONIBLES:**")
        
        if results.get('neural_networks'):
            print("   🧠 Redes neuronales con mecanismo de atención")
            print("   📊 Análisis inteligente de patrones")
            print("   🎯 Aprendizaje adaptativo continuo")
        
        if results.get('nlp_intelligence'):
            print("   🗣️ Comprensión de lenguaje natural")
            print("   💬 Interacción conversacional inteligente")
            print("   🎯 Detección automática de intenciones")
        
        if results.get('ai_ensemble'):
            print("   🤖 Múltiples IAs especializadas trabajando juntas")
            print("   ⚖️ Votación ponderada y consenso inteligente")
            print("   📈 Meta-aprendizaje y auto-optimización")
        
        if results.get('omega_ai_core'):
            print("   🌟 Sistema integrado de IA completo")
            print("   📚 Aprendizaje continuo y memoria de sesión")
            print("   🔧 Auto-optimización basada en uso")

async def main():
    """Función principal del demo"""
    print_header("DEMO DE ACTUALIZACIÓN A IA AVANZADA - OMEGA PRO AI v10.1")
    
    print("🎯 Este demo muestra las nuevas capacidades de inteligencia artificial")
    print("   implementadas en OMEGA PRO AI para convertirlo en una IA verdadera.")
    print("\n⏱️  Tiempo estimado: 2-3 minutos")
    print("📋 Se probarán 5 sistemas principales de IA")
    
    input("\n🚀 Presiona Enter para comenzar el demo...")
    
    # Ejecutar demos de cada sistema
    results = {}
    
    print_header("INICIANDO EVALUACIÓN DE SISTEMAS DE IA")
    
    # 1. Redes Neuronales Avanzadas
    results['neural_networks'] = await demo_neural_networks()
    
    # 2. Procesamiento de Lenguaje Natural
    results['nlp_intelligence'] = await demo_nlp_intelligence()
    
    # 3. Ensemble de IAs Especializadas
    results['ai_ensemble'] = await demo_ai_ensemble()
    
    # 4. Sistema Principal Integrado
    results['omega_ai_core'] = await demo_omega_ai_core()
    
    # 5. Interacción Rápida
    results['quick_interaction'] = await demo_quick_interaction()
    
    # Generar reporte final
    create_demo_report(results)
    
    # Guardar reporte
    report_file = Path(f"logs/ai_upgrade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'summary': {
                    'total_systems': len(results),
                    'successful_systems': sum(results.values()),
                    'success_rate': (sum(results.values()) / len(results)) * 100
                }
            }, f, indent=2)
        
        print(f"\n💾 Reporte guardado en: {report_file}")
        
    except Exception as e:
        print(f"\n⚠️ Error guardando reporte: {e}")
    
    print("\n🎉 ¡Demo completado!")
    print("   OMEGA PRO AI está ahora equipado con inteligencia artificial avanzada.")

if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(main())
