"""
Twilio Webhook Handler
----------------------
- Recibe mensajes SMS/WhatsApp entrantes de Twilio
- Procesa comandos y responde automáticamente
- Integración con OmegaHybridSystem para predicciones
- Manejo seguro con validación de firma opcional
"""

from __future__ import annotations
import os
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from fastapi import FastAPI, Request, Form, HTTPException, APIRouter
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def verify_twilio_signature(request_url: str, post_data: dict, signature: str, auth_token: str) -> bool:
    """Verifica la firma de Twilio para autenticidad del webhook"""
    try:
        # Construir la cadena de verificación
        base_string = request_url
        if post_data:
            query_string = urlencode(sorted(post_data.items()))
            base_string += query_string
        
        # Generar HMAC-SHA1
        expected_signature = base64.b64encode(
            hmac.new(
                auth_token.encode('utf-8'),
                base_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


def process_twilio_command(command: str, hybrid_system) -> str:
    """Procesa comandos del usuario vía Twilio"""
    command = command.lower().strip()
    
    if command in ["predict", "predice", "predicción"]:
        try:
            if hybrid_system is None:
                return "❌ Sistema OMEGA no disponible. Intenta más tarde."
            
            result = hybrid_system.generate_prediction(mode="hybrid")
            if not result.get("success", False):
                return f"❌ Error en predicción: {result.get('errors', ['Unknown error'])}"
            
            pred = result.get("prediction", {})
            numbers = pred.get("numbers", [])
            confidence = pred.get("confidence", 0)
            
            if numbers:
                nums_str = " ".join(f"{n:02d}" for n in numbers)
                return f"🎯 OMEGA Predicción\n{nums_str}\nConfianza: {confidence:.1%}"
            else:
                return "❌ No se pudo generar predicción válida."
                
        except Exception as e:
            return f"❌ Error interno: {str(e)}"
    
    elif command in ["status", "estado", "ping"]:
        try:
            if hybrid_system is None:
                return "❌ Sistema OMEGA offline"
            
            status = hybrid_system.get_system_status()
            return f"✅ OMEGA Online\nModelos: {status.get('models_loaded', 0)}\nÚltima pred: {status.get('last_prediction_time', 'N/A')}"
            
        except Exception as e:
            return f"❌ Error de estado: {str(e)}"
    
    elif command in ["help", "ayuda", "?"]:
        return (
            "🤖 OMEGA AI - Comandos:\n"
            "• predice - Nueva predicción\n"
            "• estado - Estado del sistema\n"
            "• help - Esta ayuda\n\n"
            "Envía cualquier comando para interactuar."
        )
    
    else:
        return (
            f"🤖 Recibido: '{command}'\n"
            "Comandos: predice | estado | help\n"
            "¿Quieres una predicción? Envía 'predice'"
        )


def get_twilio_router(hybrid_system=None) -> APIRouter:
    """Retorna el router de FastAPI para el webhook de Twilio"""
    
    router = APIRouter()
    
    @router.post("/sms")
    async def twilio_webhook(
        request: Request,
        From: str = Form(...),
        Body: str = Form(...),
        To: Optional[str] = Form(None),
        MessageSid: Optional[str] = Form(None),
        AccountSid: Optional[str] = Form(None),
    ):
        """
        Webhook para mensajes SMS/WhatsApp entrantes de Twilio
        """
        
        # Verificar firma de Twilio (opcional pero recomendado)
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        verify_sig = os.getenv("TWILIO_VERIFY_SIGNATURE", "false").lower() == "true"
        
        if verify_sig and auth_token:
            signature = request.headers.get("X-Twilio-Signature", "")
            if not signature:
                raise HTTPException(status_code=401, detail="Missing Twilio signature")
            
            # Obtener URL completa y datos del formulario
            request_url = str(request.url)
            form_data = await request.form()
            post_data = dict(form_data)
            
            if not verify_twilio_signature(request_url, post_data, signature, auth_token):
                raise HTTPException(status_code=401, detail="Invalid Twilio signature")
        
        # Lista blanca opcional de números
        whitelist_raw = os.getenv("TWILIO_WHITELIST", "")
        if whitelist_raw:
            whitelist = {n.strip().lstrip("+") for n in whitelist_raw.split(",") if n.strip()}
            from_number = From.lstrip("+")
            if from_number not in whitelist:
                # Responder pero no procesar comando
                response = MessagingResponse()
                response.message("🚫 Número no autorizado para usar OMEGA.")
                return Response(content=str(response), media_type="application/xml")
        
        # Procesar comando
        try:
            response_text = process_twilio_command(Body, hybrid_system)
        except Exception as e:
            response_text = f"❌ Error procesando comando: {str(e)}"
        
        # Responder con TwiML
        response = MessagingResponse()
        response.message(response_text)
        
        # Log para debugging
        print(f"[Twilio] {From} -> {Body} | Response: {response_text[:50]}...")
        
        return Response(content=str(response), media_type="application/xml")
    
    @router.get("/sms")
    def twilio_webhook_get():
        """GET endpoint para verificación básica"""
        return {"status": "Twilio webhook active", "service": "OMEGA AI"}
    
    return router


# ===============================================
# Standalone para testing con uvicorn
# ===============================================
if __name__ == "__main__":
    app = FastAPI(title="Twilio Webhook")
    
    # Simular híbrido para pruebas
    class MockHybridSystem:
        def generate_prediction(self, mode="hybrid"):
            return {
                "success": True,
                "prediction": {"numbers": [12, 34, 56, 78, 90, 99], "confidence": 0.75},
                "prediction_id": "test-123"
            }
        
        def get_system_status(self):
            return {"models_loaded": 3, "last_prediction_time": "2024-01-08 20:30"}
    
    mock_hybrid = MockHybridSystem()
    app.include_router(get_twilio_router(mock_hybrid), prefix="/webhooks/twilio", tags=["twilio"])
    
    @app.get("/")
    def root():
        return {"message": "Twilio Webhook for OMEGA AI", "webhook_url": "/webhooks/twilio/sms"}
    
    print("🚀 Twilio webhook running on http://localhost:8000")
    print("📱 Webhook URL: http://localhost:8000/webhooks/twilio/sms")

