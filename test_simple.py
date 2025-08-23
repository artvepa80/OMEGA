#!/usr/bin/env python3
"""
🧪 Prueba Simple del Sistema Conversacional OMEGA
Test básico sin dependencias externas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_intent_classifier():
    """Test del clasificador de intenciones"""
    print("🧪 Probando clasificador de intenciones...")
    
    try:
        # Import the system components
        from conversational_ai_system import IntentClassifier, Language, IntentType
        
        classifier = IntentClassifier()
        
        # Test messages
        test_cases = [
            ("hola", Language.SPANISH, IntentType.GREETING),
            ("predice numeros", Language.SPANISH, IntentType.LOTTERY_PREDICTION),
            ("hello", Language.ENGLISH, IntentType.GREETING),
            ("predict numbers", Language.ENGLISH, IntentType.LOTTERY_PREDICTION),
            ("ayuda", Language.SPANISH, IntentType.HELP),
            ("help", Language.ENGLISH, IntentType.HELP),
        ]
        
        print("\n📋 Resultados de Clasificación:")
        print("-" * 60)
        
        all_passed = True
        for message, expected_lang, expected_intent in test_cases:
            # Test language detection
            detected_lang = classifier.detect_language(message)
            
            # Test intent classification
            intent, confidence = classifier.classify_intent(message, detected_lang)
            
            # Check results
            lang_correct = detected_lang == expected_lang
            intent_correct = intent == expected_intent
            
            status = "✅" if (lang_correct and intent_correct) else "❌"
            print(f"{status} '{message}':")
            print(f"   Idioma: {detected_lang.value} ({'✓' if lang_correct else '✗'})")
            print(f"   Intención: {intent.value} ({'✓' if intent_correct else '✗'})")
            print(f"   Confianza: {confidence:.2f}")
            print()
            
            if not (lang_correct and intent_correct):
                all_passed = False
        
        if all_passed:
            print("🎉 ¡Todos los tests del clasificador pasaron!")
            return True
        else:
            print("⚠️  Algunos tests fallaron")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("💡 Ejecuta: pip install scikit-learn")
        return False
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_response_generator():
    """Test del generador de respuestas"""
    print("\n🤖 Probando generador de respuestas...")
    
    try:
        from conversational_ai_system import ResponseGenerator, IntentType, Language
        
        generator = ResponseGenerator()
        
        test_cases = [
            (IntentType.GREETING, Language.SPANISH),
            (IntentType.GREETING, Language.ENGLISH),
            (IntentType.LOTTERY_PREDICTION, Language.SPANISH),
            (IntentType.LOTTERY_PREDICTION, Language.ENGLISH),
            (IntentType.HELP, Language.SPANISH),
            (IntentType.HELP, Language.ENGLISH),
        ]
        
        print("\n📝 Respuestas Generadas:")
        print("-" * 60)
        
        for intent, language in test_cases:
            response = generator.generate_response(intent, language)
            lang_name = "Español" if language == Language.SPANISH else "English"
            print(f"🎯 {intent.value} ({lang_name}):")
            print(f"   {response[:100]}{'...' if len(response) > 100 else ''}")
            print()
        
        print("✅ Generador de respuestas funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de respuestas: {e}")
        return False

def test_system_components():
    """Test de componentes del sistema"""
    print("\n⚙️  Probando componentes del sistema...")
    
    try:
        # Test enums and data models
        from conversational_ai_system import IntentType, Language, UserContext
        from datetime import datetime
        
        # Test UserContext creation
        context = UserContext(
            user_id="test_user",
            session_id="test_session",
            language=Language.SPANISH,
            last_intent=IntentType.GREETING,
            conversation_history=[],
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test serialization
        context_dict = context.to_dict()
        restored_context = UserContext.from_dict(context_dict)
        
        print("✅ UserContext serialización/deserialización funciona")
        print("✅ Enums y modelos de datos funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de componentes: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 OMEGA AI - Pruebas del Sistema Conversacional")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Componentes del Sistema", test_system_components()))
    results.append(("Clasificador de Intenciones", test_intent_classifier()))
    results.append(("Generador de Respuestas", test_response_generator()))
    
    # Summary
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
        print("\n🚀 Siguiente paso: Ejecutar el sistema completo con:")
        print("   python conversational_ai_system.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} pruebas fallaron. Revisar los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())