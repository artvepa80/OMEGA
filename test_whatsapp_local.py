#!/usr/bin/env python3
"""
🧪 Test Local del Webhook de WhatsApp para Twilio
Simula mensajes desde tu número de WhatsApp
"""

import requests
import json

def test_whatsapp_webhook():
    """Simula el webhook de Twilio con tu número real"""
    
    # Tu configuración real de Twilio
    webhook_url = "http://localhost:8080/webhook/whatsapp"
    your_whatsapp = "whatsapp:+51972514235"  # Tu número registrado
    
    # Mensajes de prueba
    test_messages = [
        {
            "From": your_whatsapp,
            "To": "whatsapp:+14155238886",
            "Body": "hola",
            "MessageSid": "test_sid_1"
        },
        {
            "From": your_whatsapp,
            "To": "whatsapp:+14155238886", 
            "Body": "predice numeros de loteria para hoy",
            "MessageSid": "test_sid_2"
        },
        {
            "From": your_whatsapp,
            "To": "whatsapp:+14155238886",
            "Body": "help",
            "MessageSid": "test_sid_3"
        },
        {
            "From": your_whatsapp,
            "To": "whatsapp:+14155238886",
            "Body": "como funciona omega",
            "MessageSid": "test_sid_4"
        }
    ]
    
    print("🚀 Probando Webhook de WhatsApp con tu número real")
    print("=" * 60)
    print(f"📱 Número WhatsApp: {your_whatsapp}")
    print(f"🌐 Webhook URL: {webhook_url}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"📤 Test {i}: '{message['Body']}'")
        
        try:
            # Enviar como form data (como lo hace Twilio)
            response = requests.post(webhook_url, data=message, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Respuesta recibida:")
                
                # Mostrar la respuesta XML de Twilio
                xml_response = response.text
                print(f"📋 XML Response:")
                print(xml_response[:200] + "..." if len(xml_response) > 200 else xml_response)
                
                # Extraer el mensaje del XML
                if "<Message>" in xml_response and "</Message>" in xml_response:
                    start = xml_response.find("<Message>") + 9
                    end = xml_response.find("</Message>")
                    bot_message = xml_response[start:end]
                    print(f"🤖 Mensaje del Bot: {bot_message[:100]}...")
                
            else:
                print(f"❌ Error HTTP {response.status_code}")
                print(f"Response: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print("❌ No se pudo conectar al webhook")
            print("💡 Asegúrate de que el sistema esté corriendo en localhost:8080")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
        print()

def test_chat_api_direct():
    """Prueba directa de la API de chat"""
    
    chat_url = "http://localhost:8080/chat"
    your_phone = "+51972514235"
    
    test_messages = [
        "hola omega",
        "predice 6 numeros ganadores",
        "información del sistema",
        "ayuda por favor"
    ]
    
    print("🗣️  Probando API de Chat Directamente")
    print("=" * 60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"💬 Test {i}: '{message}'")
        
        payload = {
            "user_id": your_phone,
            "message": message,
            "phone_number": your_phone
        }
        
        try:
            response = requests.post(
                chat_url, 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Respuesta:")
                print(f"   🎯 Intención: {data['intent']}")
                print(f"   🗣️  Idioma: {data['language']}")
                print(f"   📊 Confianza: {data['confidence']:.2f}")
                print(f"   💬 Respuesta: {data['response'][:100]}...")
                print(f"   🔗 Sesión: {data['session_id'][:8]}...")
            else:
                print(f"❌ Error HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ No se pudo conectar a la API")
            print("💡 Asegúrate de que el sistema esté corriendo en localhost:8080")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    print("🧪 OMEGA AI - Test de WhatsApp con Twilio")
    print("=" * 60)
    print("📋 Este script simula mensajes desde tu WhatsApp registrado")
    print()
    
    # Verificar que el servicio esté corriendo
    try:
        health_response = requests.get("http://localhost:8080/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Servicio OMEGA AI detectado en localhost:8080")
            print()
            
            # Ejecutar pruebas
            test_chat_api_direct()
            print("\n" + "="*60 + "\n")
            test_whatsapp_webhook()
            
        else:
            print("⚠️  Servicio responde pero con error")
            
    except requests.exceptions.ConnectionError:
        print("❌ SERVICIO NO DETECTADO")
        print()
        print("🚀 Para ejecutar el servicio:")
        print("   python3 conversational_ai_system.py")
        print()
        print("🌐 O con Docker:")
        print("   docker run -d --name redis -p 6379:6379 redis:7-alpine")
        print("   python3 conversational_ai_system.py")