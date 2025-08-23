#!/usr/bin/env python3
"""
🇵🇪 Peru Legal Compliance Tests
Test Peru-specific legal compliance features for OMEGA Conversational AI
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import json
from datetime import datetime

# Import Peru compliance modules
from conversation.legal_compliance import (
    PeruLegalCompliance, LegalComplianceManager,
    ComplianceLevel, ComplianceResult
)
from conversation.conversation_manager import OmegaConversationManager
from conversation.context_store import ContextStore

class TestPeruLegalCompliance:
    """Test Peru-specific legal compliance implementation"""
    
    @pytest.fixture
    def peru_compliance(self):
        return PeruLegalCompliance()
    
    def test_prediction_guarantee_blocking(self, peru_compliance):
        """Test that prediction guarantees are blocked per Peru law"""
        
        blocking_messages = [
            "Garantiza que estos números van a salir",
            "¿Qué números saldrán seguro mañana?",
            "Aseguro que el 7 va a salir",
            "Prometo que estos números van a ganar"
        ]
        
        for message in blocking_messages:
            result = peru_compliance.check_message_compliance(message)
            
            assert result.is_compliant == False
            assert result.level == ComplianceLevel.BLOCKING
            assert "peru_no_prediction_guarantee" in result.required_disclaimers
            assert "Ley_27153_Juegos_de_Casino" in result.legal_references
    
    def test_gambling_addiction_detection(self, peru_compliance):
        """Test gambling addiction detection triggers Peru resources"""
        
        addiction_indicators = [
            "Necesito ganar para pagar mis deudas urgentes",
            "He perdido mucho dinero, debo recuperarlo",
            "Presté dinero para jugar a la lotería", 
            "Esta es mi última oportunidad de ganar",
            "No puedo pagar el alquiler si no gano"
        ]
        
        for message in addiction_indicators:
            result = peru_compliance.check_message_compliance(message)
            
            assert result.gambling_addiction_warning == True
            assert result.level == ComplianceLevel.CRITICAL
            assert "peru_gambling_addiction_help" in result.required_disclaimers
            assert "MINJUS_Decreto_038_2021" in result.legal_references
    
    def test_age_verification_requirement(self, peru_compliance):
        """Test age verification is required for gambling content"""
        
        gambling_messages = [
            "Quiero jugar a la lotería",
            "¿Dónde apuesto en Kábala?",
            "Dame números para el sorteo",
            "Información sobre loterías"
        ]
        
        for message in gambling_messages:
            result = peru_compliance.check_message_compliance(message)
            
            assert result.age_verification_required == True
            assert "peru_age_verification" in result.required_disclaimers
            assert "Codigo_Penal_Art_279" in result.legal_references
    
    def test_recommendation_disclaimers(self, peru_compliance):
        """Test that recommendations require Peru-specific disclaimers"""
        
        recommendation_messages = [
            "Dame números para Kábala",
            "¿Qué números me recomiendas?",
            "Sugiere combinaciones para hoy",
            "¿Cuáles son los mejores números?"
        ]
        
        for message in recommendation_messages:
            result = peru_compliance.check_message_compliance(message)
            
            assert result.is_compliant == True
            assert result.level in [ComplianceLevel.WARNING, ComplianceLevel.INFO]
            assert "peru_analysis_not_prediction" in result.required_disclaimers
            assert "peru_lottery_randomness" in result.required_disclaimers
    
    def test_legal_disclaimer_content(self, peru_compliance):
        """Test that Peru legal disclaimers contain required content"""
        
        # Test Peru analysis disclaimer
        analysis_disclaimer = peru_compliance.get_legal_disclaimer("peru_analysis_not_prediction", "es")
        assert "OMEGA es un sistema de ANÁLISIS ESTADÍSTICO" in analysis_disclaimer
        assert "normativa peruana" in analysis_disclaimer
        assert "NO de predicción" in analysis_disclaimer
        
        # Test Peru randomness disclaimer  
        randomness_disclaimer = peru_compliance.get_legal_disclaimer("peru_lottery_randomness", "es")
        assert "Ley Peruana 27153" in randomness_disclaimer
        assert "COMPLETAMENTE ALEATORIOS" in randomness_disclaimer
        
        # Test age verification
        age_disclaimer = peru_compliance.get_legal_disclaimer("peru_age_verification", "es")
        assert "Código Penal Peruano Art. 279" in age_disclaimer
        assert "MAYOR DE 18 AÑOS" in age_disclaimer
        assert "PROHIBIDA para menores" in age_disclaimer
        
        # Test gambling addiction help
        addiction_help = peru_compliance.get_legal_disclaimer("peru_gambling_addiction_help", "es")
        assert "MINJUS Línea 113" in addiction_help
        assert "CEDRO: (01) 445-6665" in addiction_help
        assert "Instituto Nacional de Salud Mental" in addiction_help
        assert "Jugadores Anónimos Lima" in addiction_help
    
    def test_responsible_gaming_resources(self, peru_compliance):
        """Test Peru-specific responsible gaming resources"""
        
        resources = peru_compliance.get_responsible_gaming_resources("es")
        
        assert resources["title"] == "Recursos de Juego Responsable - Perú"
        assert resources["emergency_line"] == "113 (MINJUS - Gratuita)"
        
        # Check CEDRO is included
        cedro_found = any(org["name"].startswith("CEDRO") for org in resources["organizations"])
        assert cedro_found == True
        
        # Check Peru mental health institute
        insm_found = any("Nacional de Salud Mental" in org["name"] for org in resources["organizations"])
        assert insm_found == True
        
        # Check legal notice about Peru recognition of gambling addiction
        assert "Perú, la ludopatía es reconocida como enfermedad" in resources["legal_notice"]
    
    def test_age_validation(self, peru_compliance):
        """Test age validation against Peru minimum age (18)"""
        
        # User under 18
        underage_context = {"age": 17}
        assert peru_compliance.validate_user_age(underage_context) == False
        
        # User over 18
        adult_context = {"age": 19}
        assert peru_compliance.validate_user_age(adult_context) == True
        
        # Previously verified
        verified_context = {"age_verified": True}
        assert peru_compliance.validate_user_age(verified_context) == True
        
        # No age info
        no_age_context = {}
        assert peru_compliance.validate_user_age(no_age_context) == False
    
    def test_jurisdiction_applicability(self, peru_compliance):
        """Test Peru jurisdiction detection"""
        
        # Peru phone number
        peru_phone_context = {"phone_number": "+51987654321"}
        assert peru_compliance.check_jurisdiction_applicability(peru_phone_context) == True
        
        # Peru country code
        peru_country_context = {"location": {"country": "PE"}}
        assert peru_compliance.check_jurisdiction_applicability(peru_country_context) == True
        
        # Peru explicit locale
        peru_locale_context = {"locale": "es-PE"}
        assert peru_compliance.check_jurisdiction_applicability(peru_locale_context) == True
        
        # Spanish default (safety)
        spanish_context = {"locale": "es"}
        assert peru_compliance.check_jurisdiction_applicability(spanish_context) == True
        
        # Non-Peru context
        us_context = {"phone_number": "+14155551234", "locale": "en"}
        assert peru_compliance.check_jurisdiction_applicability(us_context) == False
    
    def test_compliance_report_generation(self, peru_compliance):
        """Test comprehensive compliance report generation"""
        
        test_messages = [
            "Dame números para Kábala",  # Normal recommendation
            "Garantizo que el 7 va a salir",  # Blocking
            "Necesito ganar para pagar deudas"  # Critical addiction warning
        ]
        
        user_context = {"locale": "es", "phone_number": "+51987654321"}
        
        report = peru_compliance.generate_compliance_report(test_messages, user_context)
        
        assert report["jurisdiction"] == "Peru"
        assert len(report["compliance_checks"]) == 3
        assert report["total_violations"] == 1  # Only the guarantee message
        assert len(report["critical_issues"]) == 1  # Addiction warning
        assert len(report["required_actions"]) == 1  # Block guarantee
        
        # Check legal references are included
        assert "Ley_27153_Juegos_de_Casino" in report["legal_references"]
        assert "MINJUS_Decreto_038_2021" in report["legal_references"]


class TestLegalComplianceManager:
    """Test the main legal compliance manager"""
    
    @pytest.fixture
    def compliance_manager(self):
        return LegalComplianceManager()
    
    def test_peru_handler_selection(self, compliance_manager):
        """Test that Peru users get Peru compliance handler"""
        
        peru_context = {"phone_number": "+51987654321", "locale": "es"}
        handler = compliance_manager.get_compliance_handler(peru_context)
        
        assert handler.__class__.__name__ == "PeruLegalCompliance"
    
    def test_international_handler_selection(self, compliance_manager):
        """Test that non-Peru users get international handler"""
        
        us_context = {"phone_number": "+14155551234", "locale": "en"}
        handler = compliance_manager.get_compliance_handler(us_context)
        
        assert handler.__class__.__name__ == "InternationalLegalCompliance"
    
    def test_compliance_check_routing(self, compliance_manager):
        """Test compliance checks are routed to correct handler"""
        
        # Peru user with blocking content
        peru_context = {"phone_number": "+51987654321", "locale": "es"}
        result = compliance_manager.check_message_compliance(
            "Garantizo que estos números van a salir", 
            peru_context
        )
        
        assert result.is_compliant == False
        assert result.level == ComplianceLevel.BLOCKING
        
        # International user with same content
        intl_context = {"phone_number": "+14155551234", "locale": "en"}
        result = compliance_manager.check_message_compliance(
            "I guarantee these numbers will come up",
            intl_context
        )
        
        # Should be less strict for international
        assert result.level != ComplianceLevel.BLOCKING


class TestConversationManagerCompliance:
    """Test integration of compliance into conversation manager"""
    
    @pytest.fixture
    def mock_omega_control(self):
        mock = Mock()
        mock.analyze_opportunity = AsyncMock(return_value={
            "game_name": "Kábala Perú",
            "items": [{"numbers": [1, 2, 3, 4, 5, 6], "ens_score": 0.8, "source": "test"}],
            "jackpot_analysis": {"current_jackpot_usd": 100000}
        })
        return mock
    
    @pytest.fixture
    def conversation_manager(self, mock_omega_control):
        return OmegaConversationManager(mock_omega_control, "redis://invalid:6379")
    
    @pytest.mark.asyncio
    async def test_peru_blocking_compliance(self, conversation_manager):
        """Test that Peru compliance blocks illegal content"""
        
        response = await conversation_manager.process_message(
            user_id="whatsapp:+51987654321",  # Peru phone
            message="Garantiza que estos números van a salir exactamente",
            locale="es"
        )
        
        assert response["metadata"]["type"] == "compliance_block"
        assert response["metadata"]["compliance_level"] == "blocking"
        assert "prohibido" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_peru_addiction_warning(self, conversation_manager):
        """Test addiction warning triggers Peru resources"""
        
        response = await conversation_manager.process_message(
            user_id="whatsapp:+51987654321",
            message="Necesito ganar urgentemente para pagar mis deudas",
            locale="es"
        )
        
        # Should trigger responsible gaming redirect
        assert response["metadata"]["type"] == "responsible_gaming"
        assert "CEDRO" in response["text"]
        assert "113" in response["text"]  # Peru emergency line
    
    @pytest.mark.asyncio
    async def test_peru_disclaimers_in_recommendations(self, conversation_manager):
        """Test Peru disclaimers are added to recommendations"""
        
        response = await conversation_manager.process_message(
            user_id="whatsapp:+51987654321",
            message="Dame números para Kábala",
            locale="es"
        )
        
        # Should include recommendations with Peru disclaimers
        assert response["metadata"]["type"] == "recommendation"
        assert "normativa peruana" in response["text"] or "Ley Peruana" in response["text"]
        assert "ANÁLISIS ESTADÍSTICO" in response["text"]
    
    @pytest.mark.asyncio
    async def test_age_verification_prompt(self, conversation_manager):
        """Test age verification is prompted for Peru gambling content"""
        
        # Simulate new user without age verification
        response = await conversation_manager.process_message(
            user_id="whatsapp:+51999888777",
            message="Quiero información sobre apostar en loterías",
            locale="es"
        )
        
        # Should include age verification in response
        text_lower = response["text"].lower()
        assert any(keyword in text_lower for keyword in ["mayor de edad", "18 años", "verificación"])


class TestPeruComplianceIntegration:
    """Integration tests for complete Peru compliance system"""
    
    @pytest.fixture
    def full_system(self):
        """Set up complete system with Peru compliance"""
        mock_omega = Mock()
        mock_omega.analyze_opportunity = AsyncMock(return_value={
            "game_name": "Kábala Perú",
            "items": [
                {"numbers": [7, 14, 21, 28, 35, 42], "ens_score": 0.82, "source": "ensemble"},
                {"numbers": [3, 10, 17, 24, 31, 38], "ens_score": 0.79, "source": "neural"}
            ],
            "jackpot_analysis": {"current_jackpot_usd": 750000, "expected_value": -1.75}
        })
        
        conversation_manager = OmegaConversationManager(mock_omega, "redis://invalid:6379")
        return {"conversation_manager": conversation_manager, "mock_omega": mock_omega}
    
    @pytest.mark.asyncio
    async def test_complete_peru_user_flow(self, full_system):
        """Test complete conversation flow with Peru compliance"""
        
        cm = full_system["conversation_manager"]
        user_id = "whatsapp:+51987654321"  # Peru phone number
        
        # 1. Initial legitimate request
        response1 = await cm.process_message(
            user_id=user_id,
            message="Explica cómo funciona OMEGA",
            locale="es"
        )
        
        # Should work normally with Peru disclaimers
        assert response1["metadata"]["type"] != "compliance_block"
        
        # 2. Request for numbers (should include Peru disclaimers)
        response2 = await cm.process_message(
            user_id=user_id,
            message="Dame números para Kábala",
            conversation_id=response1["metadata"]["conversation_id"],
            locale="es"
        )
        
        assert response2["metadata"]["type"] == "recommendation"
        # Should include Peru-specific legal language
        text_lower = response2["text"].lower()
        assert any(keyword in text_lower for keyword in ["peruana", "minjus", "aleatorios", "análisis estadístico"])
        
        # 3. Attempt illegal guarantee (should be blocked)
        response3 = await cm.process_message(
            user_id=user_id,
            message="Garantiza que esos números van a salir seguro",
            conversation_id=response1["metadata"]["conversation_id"],
            locale="es"
        )
        
        assert response3["metadata"]["type"] == "compliance_block"
        assert response3["metadata"]["compliance_level"] == "blocking"
        assert "27153" in response3["text"] or "prohibido" in response3["text"].lower()
        
        # 4. Show addiction signs (should trigger resources)
        response4 = await cm.process_message(
            user_id=user_id,
            message="He perdido mucho dinero y necesito recuperarlo urgente",
            locale="es"
        )
        
        assert response4["metadata"]["type"] == "responsible_gaming"
        # Should include Peru-specific help resources
        assert "CEDRO" in response4["text"]
        assert "113" in response4["text"]
        assert "MINJUS" in response4["text"]
    
    @pytest.mark.asyncio
    async def test_multilingual_compliance(self, full_system):
        """Test Peru compliance works in both Spanish and English"""
        
        cm = full_system["conversation_manager"]
        
        # Spanish user with Peru phone
        es_response = await cm.process_message(
            user_id="whatsapp:+51987654321",
            message="Garantiza números exactos",
            locale="es"
        )
        
        # English user with Peru phone  
        en_response = await cm.process_message(
            user_id="whatsapp:+51987654322",
            message="Guarantee exact numbers",
            locale="en"
        )
        
        # Both should be blocked but with appropriate language
        assert es_response["metadata"]["type"] == "compliance_block"
        assert en_response["metadata"]["type"] == "compliance_block"
        
        # Spanish should have Spanish disclaimers
        assert any(word in es_response["text"] for word in ["prohibido", "ley", "peruana"])
        
        # English should have English disclaimers  
        assert any(word in en_response["text"] for word in ["prohibited", "law", "peruvian"])


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/conversational/test_peru_compliance.py -v
    pytest.main([__file__, "-v", "--tb=short"])