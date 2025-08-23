#!/usr/bin/env python3
"""
🏛️ OMEGA Legal Compliance System
Peru-specific legal compliance for lottery analysis and responsible gaming
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re

class JurisdictionType(Enum):
    """Supported legal jurisdictions"""
    PERU = "peru"
    INTERNATIONAL = "international"

class ComplianceLevel(Enum):
    """Compliance warning levels"""
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"
    BLOCKING = "blocking"

@dataclass
class ComplianceResult:
    """Result of compliance check"""
    is_compliant: bool
    level: ComplianceLevel
    message: str
    required_disclaimers: List[str]
    age_verification_required: bool
    gambling_addiction_warning: bool
    legal_references: List[str]

class PeruLegalCompliance:
    """Peru-specific legal compliance implementation"""
    
    def __init__(self):
        self.jurisdiction = JurisdictionType.PERU
        self.min_age = 18
        self.responsible_gaming_keywords = [
            "deudas", "prestamo", "préstamo", "recuperar dinero", "perdido mucho",
            "última oportunidad", "necesito ganar", "debo pagar", "urgente",
            "no puedo pagar", "empeñé", "vendí", "vendido", "hipoteca"
        ]
        self.prediction_blocking_keywords = [
            "garantiza", "seguro que", "va a salir", "saldrá", "exactamente",
            "con certeza", "aseguro", "prometo", "sin fallas"
        ]
    
    def check_message_compliance(
        self, 
        message: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> ComplianceResult:
        """Check if message complies with Peru legal requirements"""
        
        message_lower = message.lower()
        required_disclaimers = []
        level = ComplianceLevel.INFO
        age_verification_required = False
        gambling_addiction_warning = False
        legal_references = []
        
        # Check for gambling addiction indicators
        addiction_triggers = [kw for kw in self.responsible_gaming_keywords if kw in message_lower]
        if addiction_triggers:
            gambling_addiction_warning = True
            level = ComplianceLevel.CRITICAL
            required_disclaimers.append("peru_gambling_addiction_help")
            legal_references.append("MINJUS_Decreto_038_2021")
        
        # Check for illegal prediction guarantees
        prediction_blocks = [kw for kw in self.prediction_blocking_keywords if kw in message_lower]
        if prediction_blocks:
            level = ComplianceLevel.BLOCKING
            required_disclaimers.append("peru_no_prediction_guarantee")
            legal_references.append("Ley_27153_Juegos_de_Casino")
        
        # Check for recommendation requests (require disclaimers)
        if any(word in message_lower for word in ["recomienda", "sugiere", "dame números", "números para"]):
            required_disclaimers.append("peru_analysis_not_prediction")
            required_disclaimers.append("peru_lottery_randomness")
            if level == ComplianceLevel.INFO:
                level = ComplianceLevel.WARNING
        
        # Age verification for gambling-related content
        if any(word in message_lower for word in ["jugar", "apostar", "lotería", "kábala", "sorteo"]):
            age_verification_required = True
            required_disclaimers.append("peru_age_verification")
            legal_references.append("Codigo_Penal_Art_279")
        
        # Determine compliance
        is_compliant = level != ComplianceLevel.BLOCKING
        
        # Generate compliance message
        if level == ComplianceLevel.BLOCKING:
            compliance_message = "No puedo proporcionar garantías de predicción exacta según las regulaciones peruanas."
        elif level == ComplianceLevel.CRITICAL:
            compliance_message = "Detecté indicadores de posible ludopatía. Se requieren recursos de ayuda."
        elif level == ComplianceLevel.WARNING:
            compliance_message = "Contenido de juegos requiere disclaimers legales según normativa peruana."
        else:
            compliance_message = "Contenido cumple con regulaciones básicas peruanas."
        
        return ComplianceResult(
            is_compliant=is_compliant,
            level=level,
            message=compliance_message,
            required_disclaimers=required_disclaimers,
            age_verification_required=age_verification_required,
            gambling_addiction_warning=gambling_addiction_warning,
            legal_references=legal_references
        )
    
    def get_legal_disclaimer(self, disclaimer_type: str, locale: str = "es") -> str:
        """Get specific legal disclaimer for Peru"""
        
        disclaimers = {
            "peru_analysis_not_prediction": {
                "es": """🏛️ AVISO LEGAL PERÚ:
OMEGA es un sistema de ANÁLISIS ESTADÍSTICO, NO de predicción. Según la normativa peruana, ningún sistema puede predecir resultados de juegos de azar. Solo analizamos patrones históricos para fines educativos e informativos.""",
                "en": """🏛️ PERU LEGAL NOTICE:
OMEGA is a STATISTICAL ANALYSIS system, NOT a prediction system. According to Peruvian regulations, no system can predict gambling results. We only analyze historical patterns for educational and informational purposes."""
            },
            
            "peru_lottery_randomness": {
                "es": """⚖️ TRANSPARENCIA LEGAL:
Conforme a la Ley Peruana 27153 sobre Juegos de Casino y Máquinas Tragamonedas, todos los sorteos de lotería son COMPLETAMENTE ALEATORIOS. Ningún análisis matemático puede alterar estas probabilidades independientes.""",
                "en": """⚖️ LEGAL TRANSPARENCY:
In compliance with Peruvian Law 27153 on Casino Games and Slot Machines, all lottery draws are COMPLETELY RANDOM. No mathematical analysis can alter these independent probabilities."""
            },
            
            "peru_age_verification": {
                "es": """🔞 VERIFICACIÓN DE EDAD PERÚ:
Según el Código Penal Peruano Art. 279, la participación en juegos de azar está PROHIBIDA para menores de 18 años. Al usar OMEGA, confirmas ser mayor de edad y aceptas esta responsabilidad legal.""",
                "en": """🔞 PERU AGE VERIFICATION:
According to Peruvian Penal Code Art. 279, participation in gambling is PROHIBITED for minors under 18 years. By using OMEGA, you confirm being of legal age and accept this legal responsibility."""
            },
            
            "peru_gambling_addiction_help": {
                "es": """🆘 AYUDA LUDOPATÍA PERÚ:
Si tienes problemas con juegos de azar, busca ayuda profesional:

📞 MINJUS Línea 113 (gratuita)
🏥 Instituto Nacional de Salud Mental
📧 CEDRO: (01) 445-6665
🌐 Jugadores Anónimos Lima

OMEGA NO ES UNA SOLUCIÓN a problemas financieros. Los juegos de azar pueden causar adicción.""",
                "en": """🆘 PERU GAMBLING ADDICTION HELP:
If you have gambling problems, seek professional help:

📞 MINJUS Line 113 (free)
🏥 National Institute of Mental Health  
📧 CEDRO: (01) 445-6665
🌐 Gamblers Anonymous Lima

OMEGA IS NOT A SOLUTION to financial problems. Gambling can cause addiction."""
            },
            
            "peru_no_prediction_guarantee": {
                "es": """❌ PROHIBIDO POR LEY PERUANA:
Según regulaciones del MINJUS y Ley 27153, está PROHIBIDO garantizar resultados en juegos de azar. OMEGA solo proporciona análisis estadístico histórico sin garantías de éxito futuro.""",
                "en": """❌ PROHIBITED BY PERUVIAN LAW:
According to MINJUS regulations and Law 27153, it is PROHIBITED to guarantee results in gambling. OMEGA only provides historical statistical analysis without guarantees of future success."""
            },
            
            "peru_consumer_protection": {
                "es": """🛡️ PROTECCIÓN AL CONSUMIDOR PERÚ:
Conforme al Código de Protección al Consumidor (Ley 29571), tienes derecho a información veraz. OMEGA te informa que NO incrementamos tus probabilidades reales de ganar en ningún juego de azar.""",
                "en": """🛡️ PERU CONSUMER PROTECTION:
In compliance with Consumer Protection Code (Law 29571), you have the right to truthful information. OMEGA informs you that we do NOT increase your actual probabilities of winning any gambling games."""
            }
        }
        
        return disclaimers.get(disclaimer_type, {}).get(locale, disclaimers.get(disclaimer_type, {}).get("es", ""))
    
    def get_responsible_gaming_resources(self, locale: str = "es") -> Dict[str, Any]:
        """Get Peru-specific responsible gaming resources"""
        
        if locale == "es":
            return {
                "title": "Recursos de Juego Responsable - Perú",
                "emergency_line": "113 (MINJUS - Gratuita)",
                "organizations": [
                    {
                        "name": "CEDRO - Centro de Información y Educación para la Prevención del Abuso de Drogas",
                        "phone": "(01) 445-6665",
                        "website": "https://www.cedro.org.pe",
                        "service": "Tratamiento de adicciones incluyendo ludopatía"
                    },
                    {
                        "name": "Instituto Nacional de Salud Mental",
                        "phone": "(01) 613-4800",
                        "address": "Av. Honorio Delgado 262, San Martín de Porres",
                        "service": "Atención psiquiátrica y psicológica"
                    },
                    {
                        "name": "Jugadores Anónimos Lima",
                        "phone": "(01) 999-123-456",
                        "meeting_info": "Reuniones semanales gratuitas",
                        "service": "Grupos de apoyo"
                    }
                ],
                "warning_signs": [
                    "Apostar más dinero del que puedes permitirte perder",
                    "Mentir sobre tus actividades de juego",
                    "Pedir prestado dinero para jugar",
                    "Sentir ansiedad cuando no puedes jugar",
                    "Descuidar trabajo, familia o responsabilidades"
                ],
                "legal_notice": "En Perú, la ludopatía es reconocida como enfermedad según el Ministerio de Salud."
            }
        else:
            return {
                "title": "Responsible Gaming Resources - Peru",
                "emergency_line": "113 (MINJUS - Free)",
                "organizations": [
                    {
                        "name": "CEDRO - Center for Information and Education for Drug Abuse Prevention",
                        "phone": "(01) 445-6665",
                        "website": "https://www.cedro.org.pe",
                        "service": "Addiction treatment including gambling addiction"
                    },
                    {
                        "name": "National Institute of Mental Health",
                        "phone": "(01) 613-4800",
                        "address": "Av. Honorio Delgado 262, San Martín de Porres",
                        "service": "Psychiatric and psychological care"
                    },
                    {
                        "name": "Gamblers Anonymous Lima",
                        "phone": "(01) 999-123-456",
                        "meeting_info": "Free weekly meetings",
                        "service": "Support groups"
                    }
                ],
                "warning_signs": [
                    "Betting more money than you can afford to lose",
                    "Lying about your gambling activities", 
                    "Borrowing money to gamble",
                    "Feeling anxiety when you can't gamble",
                    "Neglecting work, family or responsibilities"
                ],
                "legal_notice": "In Peru, gambling addiction is recognized as a disease by the Ministry of Health."
            }
    
    def validate_user_age(self, user_context: Dict[str, Any]) -> bool:
        """Validate user meets minimum age requirement"""
        
        # Check if age verification was already completed
        if user_context.get("age_verified", False):
            return True
        
        # Check if user provided age information
        user_age = user_context.get("age")
        if user_age and isinstance(user_age, int):
            return user_age >= self.min_age
        
        # Age not verified - require verification
        return False
    
    def get_age_verification_prompt(self, locale: str = "es") -> str:
        """Get age verification prompt"""
        
        if locale == "es":
            return """🔞 VERIFICACIÓN DE EDAD REQUERIDA
            
Según la legislación peruana (Código Penal Art. 279), debes ser MAYOR DE 18 AÑOS para acceder a información sobre juegos de azar.

Por favor confirma:
✅ Soy mayor de 18 años
✅ Entiendo que los juegos de azar pueden ser adictivos
✅ Acepto usar esta información solo con fines educativos

Responde "CONFIRMO EDAD" para continuar."""
        else:
            return """🔞 AGE VERIFICATION REQUIRED
            
According to Peruvian legislation (Penal Code Art. 279), you must be OVER 18 YEARS OLD to access gambling information.

Please confirm:
✅ I am over 18 years old
✅ I understand that gambling can be addictive
✅ I agree to use this information for educational purposes only

Reply "CONFIRM AGE" to continue."""
    
    def check_jurisdiction_applicability(self, user_context: Dict[str, Any]) -> bool:
        """Check if Peru jurisdiction applies to this user"""
        
        # Check phone number (Peru uses +51)
        phone = user_context.get("phone_number", "")
        if phone and "+51" in phone:
            return True
        
        # Check IP location if available
        location = user_context.get("location", {})
        country = location.get("country", "").lower()
        if country in ["pe", "peru", "perú"]:
            return True
        
        # Check explicit locale setting
        locale = user_context.get("locale", "")
        if locale == "es-PE":
            return True
        
        # Default to applying Peru rules for Spanish speakers as safety measure
        if user_context.get("locale", "").startswith("es"):
            return True
        
        return False
    
    def generate_compliance_report(self, messages: List[str], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance report for conversation"""
        
        report = {
            "jurisdiction": "Peru",
            "compliance_checks": [],
            "total_violations": 0,
            "critical_issues": [],
            "required_actions": [],
            "legal_references": set(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        for i, message in enumerate(messages):
            check_result = self.check_message_compliance(message, user_context)
            
            report["compliance_checks"].append({
                "message_index": i,
                "message_preview": message[:50] + "..." if len(message) > 50 else message,
                "compliance_level": check_result.level.value,
                "is_compliant": check_result.is_compliant,
                "required_disclaimers": check_result.required_disclaimers
            })
            
            if not check_result.is_compliant:
                report["total_violations"] += 1
            
            if check_result.level == ComplianceLevel.CRITICAL:
                report["critical_issues"].append({
                    "message_index": i,
                    "issue": check_result.message,
                    "action_required": "Provide gambling addiction resources"
                })
            
            if check_result.level == ComplianceLevel.BLOCKING:
                report["required_actions"].append({
                    "type": "block_response",
                    "message_index": i,
                    "reason": check_result.message
                })
            
            report["legal_references"].update(check_result.legal_references)
        
        report["legal_references"] = list(report["legal_references"])
        
        return report


class InternationalLegalCompliance:
    """Basic international legal compliance"""
    
    def __init__(self):
        self.jurisdiction = JurisdictionType.INTERNATIONAL
        self.min_age = 18
    
    def check_message_compliance(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> ComplianceResult:
        """Basic international compliance check"""
        
        # Basic checks for obviously problematic content
        if any(word in message.lower() for word in ["guarantee win", "100% sure", "definite numbers"]):
            return ComplianceResult(
                is_compliant=False,
                level=ComplianceLevel.WARNING,
                message="Avoid guarantee language",
                required_disclaimers=["general_no_guarantees"],
                age_verification_required=False,
                gambling_addiction_warning=False,
                legal_references=[]
            )
        
        return ComplianceResult(
            is_compliant=True,
            level=ComplianceLevel.INFO,
            message="Basic compliance met",
            required_disclaimers=[],
            age_verification_required=False,
            gambling_addiction_warning=False,
            legal_references=[]
        )


class LegalComplianceManager:
    """Main legal compliance manager"""
    
    def __init__(self):
        self.peru_compliance = PeruLegalCompliance()
        self.international_compliance = InternationalLegalCompliance()
    
    def get_compliance_handler(self, user_context: Dict[str, Any]) -> Any:
        """Get appropriate compliance handler based on jurisdiction"""
        
        if self.peru_compliance.check_jurisdiction_applicability(user_context):
            return self.peru_compliance
        else:
            return self.international_compliance
    
    def check_message_compliance(self, message: str, user_context: Dict[str, Any]) -> ComplianceResult:
        """Check message compliance using appropriate jurisdiction"""
        
        handler = self.get_compliance_handler(user_context)
        return handler.check_message_compliance(message, user_context)
    
    def get_required_disclaimers(self, compliance_result: ComplianceResult, user_context: Dict[str, Any]) -> List[str]:
        """Get formatted disclaimers for compliance result"""
        
        handler = self.get_compliance_handler(user_context)
        locale = user_context.get("locale", "es")
        
        disclaimers = []
        for disclaimer_type in compliance_result.required_disclaimers:
            if hasattr(handler, 'get_legal_disclaimer'):
                disclaimer_text = handler.get_legal_disclaimer(disclaimer_type, locale)
                if disclaimer_text:
                    disclaimers.append(disclaimer_text)
        
        return disclaimers