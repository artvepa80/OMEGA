#!/usr/bin/env python3
"""
🔞 OMEGA Age Verification System - Peru Compliance
Age verification system compliant with Peruvian Law (Código Penal Art. 279)
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    """Age verification statuses"""
    NOT_VERIFIED = "not_verified"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class VerificationMethod(Enum):
    """Age verification methods"""
    SELF_DECLARATION = "self_declaration"
    DOCUMENT_UPLOAD = "document_upload" 
    PHONE_VERIFICATION = "phone_verification"
    THIRD_PARTY = "third_party"

@dataclass
class AgeVerificationResult:
    """Result of age verification attempt"""
    status: VerificationStatus
    method: VerificationMethod
    verified_age: Optional[int]
    verification_date: datetime
    expires_at: Optional[datetime]
    additional_info: Dict[str, Any]
    legal_compliance_met: bool

class PeruAgeVerificationSystem:
    """Peru-specific age verification system"""
    
    def __init__(self):
        self.minimum_age = 18  # Peru legal minimum
        self.verification_expiry_days = 90  # Reverify every 90 days
        self.verification_attempts = {}  # Track failed attempts
        self.verified_users = {}  # Cache of verified users
        
        # Legal references
        self.legal_authority = "Código Penal Peruano Art. 279"
        self.enforcement_agency = "MINJUS"
        
    def check_age_verification_required(self, message: str, user_context: Dict[str, Any]) -> bool:
        """Check if age verification is required for this message/user"""
        
        # Already verified and not expired
        if self._is_user_verified(user_context.get("user_id", "")):
            return False
        
        # Check for gambling-related keywords that trigger verification
        gambling_keywords = [
            # Spanish
            "lotería", "loteria", "jugar", "apostar", "kábala", "kabala", 
            "sorteo", "boleto", "números", "numeros", "ganar", "premio",
            "jackpot", "chance", "suerte", "dinero",
            
            # English  
            "lottery", "play", "bet", "betting", "gambling", "numbers",
            "win", "prize", "jackpot", "money", "cash"
        ]
        
        message_lower = message.lower()
        
        # Require verification if gambling terms detected
        for keyword in gambling_keywords:
            if keyword in message_lower:
                return True
        
        # Check user context for gambling indicators
        if user_context.get("requesting_recommendations", False):
            return True
        
        if user_context.get("asking_about_odds", False):
            return True
        
        return False
    
    def _is_user_verified(self, user_id: str) -> bool:
        """Check if user is currently verified"""
        
        if user_id not in self.verified_users:
            return False
        
        verification = self.verified_users[user_id]
        
        # Check if verification expired
        if verification.expires_at and datetime.now() > verification.expires_at:
            self.verified_users.pop(user_id, None)
            return False
        
        return verification.status == VerificationStatus.VERIFIED
    
    def generate_verification_prompt(self, user_context: Dict[str, Any], locale: str = "es") -> str:
        """Generate age verification prompt"""
        
        user_id = user_context.get("user_id", "")
        failed_attempts = self.verification_attempts.get(user_id, 0)
        
        if locale == "es":
            if failed_attempts > 0:
                prompt = f"""🔞 **VERIFICACIÓN DE EDAD REQUERIDA - INTENTO {failed_attempts + 1}/3**

⚖️ **MARCO LEGAL PERUANO**:
Según el Código Penal Peruano Art. 279, el acceso a información sobre juegos de azar está PROHIBIDO para menores de 18 años.

❌ **Intento anterior no completado**. Por favor completa la verificación:

✅ **CONFIRMA que eres MAYOR DE 18 AÑOS**
✅ **CONFIRMA que comprendes que los juegos pueden ser adictivos**  
✅ **CONFIRMA que usarás esta información solo con fines educativos**

**Para continuar, responde exactamente**: `CONFIRMO EDAD PERU +18`

⚠️ **Advertencia**: Información falsa sobre edad constituye violación de la ley peruana."""
            
            else:
                prompt = """🔞 **VERIFICACIÓN DE EDAD OBLIGATORIA - PERÚ**

⚖️ **CUMPLIMIENTO LEGAL**:
De acuerdo al Código Penal Peruano Art. 279, debes ser MAYOR DE 18 AÑOS para acceder a información sobre juegos de azar.

📋 **DECLARACIÓN REQUERIDA**:
✅ Soy mayor de 18 años de edad
✅ Entiendo que los juegos de azar pueden causar adicción
✅ Usaré esta información únicamente con fines educativos e informativos  
✅ Asumo la responsabilidad legal de mi edad

**Para verificar tu edad, responde**: `CONFIRMO EDAD PERU +18`

🛡️ **Protección**: Esta verificación protege a menores según la ley peruana y promueve el juego responsable."""
        
        else:  # English
            if failed_attempts > 0:
                prompt = f"""🔞 **AGE VERIFICATION REQUIRED - ATTEMPT {failed_attempts + 1}/3**

⚖️ **PERUVIAN LEGAL FRAMEWORK**:
According to Peruvian Penal Code Art. 279, access to gambling information is PROHIBITED for minors under 18.

❌ **Previous attempt incomplete**. Please complete verification:

✅ **CONFIRM you are OVER 18 YEARS OLD**
✅ **CONFIRM you understand gambling can be addictive**
✅ **CONFIRM you will use this information for educational purposes only**

**To continue, respond exactly**: `CONFIRM AGE PERU +18`

⚠️ **Warning**: False age information constitutes violation of Peruvian law."""
            
            else:
                prompt = """🔞 **MANDATORY AGE VERIFICATION - PERU**

⚖️ **LEGAL COMPLIANCE**:
According to Peruvian Penal Code Art. 279, you must be OVER 18 YEARS OLD to access gambling information.

📋 **REQUIRED DECLARATION**:
✅ I am over 18 years of age
✅ I understand gambling can cause addiction  
✅ I will use this information solely for educational and informational purposes
✅ I assume legal responsibility for my age

**To verify your age, respond**: `CONFIRM AGE PERU +18`

🛡️ **Protection**: This verification protects minors according to Peruvian law and promotes responsible gambling."""
        
        return prompt
    
    def process_verification_response(self, user_id: str, response: str, 
                                   user_context: Dict[str, Any]) -> AgeVerificationResult:
        """Process user's verification response"""
        
        response_clean = response.strip().upper()
        
        # Check for correct verification responses
        valid_responses_es = [
            "CONFIRMO EDAD PERU +18",
            "CONFIRMO EDAD PERÚ +18", 
            "CONFIRMO EDAD PERU 18+",
            "CONFIRMO EDAD PERU MAYOR 18"
        ]
        
        valid_responses_en = [
            "CONFIRM AGE PERU +18",
            "CONFIRM AGE PERU 18+", 
            "I CONFIRM AGE PERU +18"
        ]
        
        is_valid = any(valid_resp in response_clean for valid_resp in valid_responses_es + valid_responses_en)
        
        if is_valid:
            # Successful verification
            verification_result = AgeVerificationResult(
                status=VerificationStatus.VERIFIED,
                method=VerificationMethod.SELF_DECLARATION,
                verified_age=18,  # Minimum legal age
                verification_date=datetime.now(),
                expires_at=datetime.now() + timedelta(days=self.verification_expiry_days),
                additional_info={
                    "legal_authority": self.legal_authority,
                    "user_ip": user_context.get("ip_address"),
                    "user_agent": user_context.get("user_agent"),
                    "phone_country": user_context.get("phone_country"),
                    "verification_method": "self_declaration_peru"
                },
                legal_compliance_met=True
            )
            
            # Cache verification
            self.verified_users[user_id] = verification_result
            
            # Reset failed attempts
            self.verification_attempts.pop(user_id, None)
            
            logger.info(f"Age verification successful for user {user_id}")
            
            return verification_result
        
        else:
            # Failed verification attempt
            self.verification_attempts[user_id] = self.verification_attempts.get(user_id, 0) + 1
            
            verification_result = AgeVerificationResult(
                status=VerificationStatus.FAILED,
                method=VerificationMethod.SELF_DECLARATION,
                verified_age=None,
                verification_date=datetime.now(),
                expires_at=None,
                additional_info={
                    "failed_attempts": self.verification_attempts[user_id],
                    "response_provided": response_clean[:50],  # Log first 50 chars
                    "max_attempts": 3
                },
                legal_compliance_met=False
            )
            
            logger.warning(f"Age verification failed for user {user_id}, attempt {self.verification_attempts[user_id]}")
            
            return verification_result
    
    def get_verification_failure_message(self, attempts: int, max_attempts: int = 3, 
                                       locale: str = "es") -> str:
        """Get message for verification failure"""
        
        if locale == "es":
            if attempts >= max_attempts:
                return """❌ **VERIFICACIÓN DE EDAD FALLIDA**

Has excedido el número máximo de intentos de verificación de edad.

⚖️ **CUMPLIMIENTO LEGAL**: Según la ley peruana, no podemos proporcionar información sobre juegos de azar sin verificación de edad apropiada.

🔄 **Para intentar nuevamente**: Espera 24 horas o contacta soporte.

📞 **Ayuda**: Si eres mayor de edad y tienes problemas, contacta soporte técnico."""
            
            else:
                return f"""⚠️ **VERIFICACIÓN INCORRECTA** (Intento {attempts}/{max_attempts})

La respuesta de verificación no es correcta.

**Debes responder exactamente**: `CONFIRMO EDAD PERU +18`

💡 **Importante**: Copia y pega la respuesta exacta para verificar tu edad.

🔄 **Intentos restantes**: {max_attempts - attempts}"""
        
        else:  # English
            if attempts >= max_attempts:
                return """❌ **AGE VERIFICATION FAILED**

You have exceeded the maximum number of age verification attempts.

⚖️ **LEGAL COMPLIANCE**: According to Peruvian law, we cannot provide gambling information without proper age verification.

🔄 **To try again**: Wait 24 hours or contact support.

📞 **Help**: If you are of legal age and having issues, contact technical support."""
            
            else:
                return f"""⚠️ **INCORRECT VERIFICATION** (Attempt {attempts}/{max_attempts})

The verification response is not correct.

**You must respond exactly**: `CONFIRM AGE PERU +18`

💡 **Important**: Copy and paste the exact response to verify your age.

🔄 **Remaining attempts**: {max_attempts - attempts}"""
    
    def get_verification_success_message(self, locale: str = "es") -> str:
        """Get message for successful verification"""
        
        if locale == "es":
            return """✅ **VERIFICACIÓN DE EDAD EXITOSA**

Has confirmado exitosamente ser mayor de 18 años según la ley peruana.

📋 **RECORDATORIOS IMPORTANTES**:
• Esta verificación es válida por 90 días
• OMEGA proporciona análisis estadístico educativo únicamente
• Los juegos de azar pueden ser adictivos
• Juega responsablemente y dentro de tus posibilidades

🎯 **Ahora puedes**: Solicitar análisis estadísticos y información educativa sobre loterías.

🛡️ **Juego Responsable**: Si necesitas ayuda, llama al 113 (línea gratuita MINJUS)."""
        
        else:
            return """✅ **AGE VERIFICATION SUCCESSFUL**

You have successfully confirmed being over 18 years old according to Peruvian law.

📋 **IMPORTANT REMINDERS**:
• This verification is valid for 90 days
• OMEGA provides educational statistical analysis only
• Gambling can be addictive  
• Play responsibly and within your means

🎯 **You can now**: Request statistical analysis and educational lottery information.

🛡️ **Responsible Gaming**: If you need help, call 113 (free MINJUS line)."""
    
    def get_user_verification_status(self, user_id: str) -> Dict[str, Any]:
        """Get current verification status for user"""
        
        if user_id not in self.verified_users:
            return {
                "status": VerificationStatus.NOT_VERIFIED.value,
                "verified": False,
                "expires_at": None,
                "failed_attempts": self.verification_attempts.get(user_id, 0)
            }
        
        verification = self.verified_users[user_id]
        
        return {
            "status": verification.status.value,
            "verified": verification.status == VerificationStatus.VERIFIED,
            "verification_date": verification.verification_date.isoformat(),
            "expires_at": verification.expires_at.isoformat() if verification.expires_at else None,
            "method": verification.method.value,
            "legal_compliance": verification.legal_compliance_met
        }
    
    def clean_expired_verifications(self):
        """Clean up expired verifications"""
        
        current_time = datetime.now()
        expired_users = []
        
        for user_id, verification in self.verified_users.items():
            if verification.expires_at and current_time > verification.expires_at:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.verified_users.pop(user_id, None)
            logger.info(f"Removed expired verification for user {user_id}")
        
        return len(expired_users)
    
    def generate_verification_report(self) -> Dict[str, Any]:
        """Generate verification system report"""
        
        total_verified = len(self.verified_users)
        total_failed_attempts = len(self.verification_attempts)
        
        # Clean expired first
        expired_count = self.clean_expired_verifications()
        
        active_verifications = len(self.verified_users)
        
        report = {
            "report_date": datetime.now().isoformat(),
            "total_verified_users": total_verified,
            "active_verifications": active_verifications,
            "expired_verifications_cleaned": expired_count,
            "users_with_failed_attempts": total_failed_attempts,
            "verification_expiry_days": self.verification_expiry_days,
            "legal_compliance": {
                "authority": self.legal_authority,
                "enforcement_agency": self.enforcement_agency,
                "minimum_age": self.minimum_age
            },
            "system_status": "operational"
        }
        
        return report
    
    async def batch_verify_users(self, user_ids: List[str]) -> Dict[str, AgeVerificationResult]:
        """Batch verify multiple users (for migration/testing)"""
        
        results = {}
        
        for user_id in user_ids:
            # Simulate verification for existing users
            verification_result = AgeVerificationResult(
                status=VerificationStatus.VERIFIED,
                method=VerificationMethod.THIRD_PARTY,
                verified_age=18,
                verification_date=datetime.now(),
                expires_at=datetime.now() + timedelta(days=self.verification_expiry_days),
                additional_info={"batch_migration": True},
                legal_compliance_met=True
            )
            
            self.verified_users[user_id] = verification_result
            results[user_id] = verification_result
        
        logger.info(f"Batch verified {len(user_ids)} users")
        return results


# Global instance
peru_age_verification = PeruAgeVerificationSystem()