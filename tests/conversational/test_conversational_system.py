#!/usr/bin/env python3
"""
🧪 OMEGA Conversational System Tests
Comprehensive testing of the honest statistical communication system
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import json
from datetime import datetime

# Import our conversational modules
from conversation.intent_classifier import OmegaIntentClassifier, IntentType
from conversation.context_store import ContextStore, ConversationContext
from conversation.personality_engine import OmegaPersonality
from conversation.conversation_manager import OmegaConversationManager
from conversation.response_templates import ResponseTemplates
from messaging.whatsapp_conversational import WhatsAppConversationalBot, WhatsAppFormatter


class TestIntentClassifier:
    """Test intent classification accuracy and honesty triggers"""
    
    @pytest.fixture
    def classifier(self):
        return OmegaIntentClassifier()
    
    def test_recommendation_intent_spanish(self, classifier):
        """Test recommendation request classification in Spanish"""
        test_cases = [
            "Dame los mejores números para Kábala",
            "¿Qué números me recomiendas para hoy?",
            "Quiero 5 combinaciones para jugar",
            "Sugiere números para Mega Sena"
        ]
        
        for message in test_cases:
            result = classifier.classify(message)
            assert result.intent_type == IntentType.RECOMMENDATION_REQUEST
            assert result.confidence > 0.6
    
    def test_prediction_honesty_triggers(self, classifier):
        """Test that prediction language triggers honesty warnings"""
        prediction_messages = [
            "Predice qué números van a salir mañana",
            "¿Qué números saldrán seguro en el próximo sorteo?",
            "Dame los números exactos que van a ganar",
            "Garantiza que estos números van a salir"
        ]
        
        for message in prediction_messages:
            result = classifier.classify(message)
            assert result.honesty_trigger == True
            assert result.intent_type in [IntentType.RECOMMENDATION_REQUEST, IntentType.UNKNOWN]
    
    def test_statistical_questions(self, classifier):
        """Test statistical question classification"""
        stat_questions = [
            "¿Cuál es la probabilidad de ganar en Kábala?",
            "Explica el valor esperado de la lotería",
            "¿Cómo calculas las probabilidades?",
            "What are the odds of winning?"
        ]
        
        for question in stat_questions:
            result = classifier.classify(question)
            assert result.intent_type == IntentType.STATISTICAL_QUESTION
            assert result.confidence > 0.5
    
    def test_explanation_requests(self, classifier):
        """Test explanation request classification"""
        explanations = [
            "Explica cómo funciona OMEGA",
            "¿Qué es análisis estadístico?",
            "How does the system work?",
            "No entiendo el algoritmo"
        ]
        
        for question in explanations:
            result = classifier.classify(question)
            assert result.intent_type == IntentType.EXPLANATION_REQUEST
            assert result.confidence > 0.5
    
    def test_multilanguage_robustness(self, classifier):
        """Test classification with accents and language mixing"""
        mixed_cases = [
            "analiza los numeros mas frecuentes",  # no accents
            "análisis de patrones históricos",      # with accents
            "que probabilidad hay de ganar?",       # mixed
            "explain probability por favor"         # mixed languages
        ]
        
        for message in mixed_cases:
            result = classifier.classify(message)
            assert result.intent_type != IntentType.UNKNOWN
            assert result.confidence > 0.3


class TestContextStore:
    """Test conversation context management"""
    
    @pytest.fixture
    def context_store(self):
        # Use memory fallback for testing
        return ContextStore(redis_url="redis://invalid:6379")  # Will fallback to memory
    
    @pytest.mark.asyncio
    async def test_context_creation(self, context_store):
        """Test creating new conversation context"""
        user_id = "test_user_001"
        conversation_id = "conv_001"
        initial_message = "Hola, explica cómo funciona OMEGA para un principiante"
        
        context = await context_store.create_context(
            user_id=user_id,
            conversation_id=conversation_id,
            initial_message=initial_message,
            locale="es"
        )
        
        assert context.user_id == user_id
        assert context.conversation_id == conversation_id
        assert context.user_expertise_level == "beginner"  # Inferred from message
        assert context.locale == "es"
        assert context.preferred_explanation_style == "accessible"
    
    @pytest.mark.asyncio
    async def test_message_storage(self, context_store):
        """Test message storage and retrieval"""
        user_id = "test_user_002"
        conversation_id = "conv_002"
        
        # Create context
        context = await context_store.create_context(
            user_id, conversation_id, "Test message", "es"
        )
        
        # Add messages
        await context_store.add_message(
            user_id, conversation_id, "user", "First message",
            {"intent_type": "general_conversation"}
        )
        
        await context_store.add_message(
            user_id, conversation_id, "assistant", "Response message"
        )
        
        # Retrieve context
        updated_context = await context_store.get_context(user_id, conversation_id)
        
        assert len(updated_context.last_messages) == 2
        assert updated_context.message_count == 2
        assert updated_context.last_messages[0]["role"] == "user"
        assert updated_context.last_messages[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_expertise_inference(self, context_store):
        """Test user expertise inference from messages"""
        test_cases = [
            ("Soy nuevo en esto, explica simple", "beginner"),
            ("Explica el algoritmo de machine learning", "intermediate"),
            ("Analiza el Brier score y calibration metrics del ensemble", "expert"),
            ("How does the backtest anti-leakage work?", "expert")
        ]
        
        for message, expected_expertise in test_cases:
            context = await context_store.create_context(
                f"user_{hash(message)}", f"conv_{hash(message)}", message, "es"
            )
            assert context.user_expertise_level == expected_expertise


class TestPersonalityEngine:
    """Test personality adaptation and response styling"""
    
    @pytest.fixture
    def personality(self):
        return OmegaPersonality()
    
    @pytest.fixture
    def mock_context(self):
        return ConversationContext(
            user_id="test_user",
            conversation_id="test_conv",
            last_messages=[],
            user_expertise_level="intermediate",
            preferred_explanation_style="accessible",
            conversation_topic="lottery_analysis",
            technical_depth=0.5,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            message_count=5,
            locale="es",
            honesty_preferences={"show_disclaimers": True, "emphasize_randomness": True}
        )
    
    def test_disclaimer_generation(self, personality):
        """Test disclaimer generation for different contexts"""
        
        # Mild disclaimer for analysis
        mild = personality.generate_honesty_disclaimer(
            IntentType.ANALYSIS_REQUEST, "mild", "es"
        )
        assert "análisis" in mild.lower()
        assert "aleatorios" in mild.lower()
        
        # Strong disclaimer for recommendations with honesty trigger
        strong = personality.generate_honesty_disclaimer(
            IntentType.RECOMMENDATION_REQUEST, "strong", "es"
        )
        assert "IMPORTANTE" in strong
        assert "COMPLETAMENTE ALEATORIOS" in strong
        assert "permitirte perder" in strong.lower()
    
    def test_responsible_gaming_detection(self, personality, mock_context):
        """Test responsible gaming message triggering"""
        
        concerning_messages = [
            "Necesito ganar para pagar mis deudas",
            "He perdido mucho dinero, necesito recuperarlo",
            "Esta es mi última oportunidad de ganar",
            "Presté dinero para jugar a la lotería"
        ]
        
        for message in concerning_messages:
            should_redirect = personality.should_redirect_to_responsible_gaming(
                message, mock_context
            )
            assert should_redirect == True
    
    def test_educational_content_generation(self, personality):
        """Test educational content adaptation by expertise level"""
        
        # Beginner level
        beginner_content = personality.generate_educational_context(
            "probability_basics", "beginner", "es"
        )
        assert "moneda" in beginner_content.lower()  # Uses coin analogy
        assert "imagina" in beginner_content.lower()  # Uses accessible language
        
        # Expert level  
        expert_content = personality.generate_educational_context(
            "probability_basics", "expert", "es"
        )
        assert "c(" in expert_content.lower()  # Uses mathematical notation
        assert "distribución" in expert_content.lower()  # Technical terms


class TestConversationManager:
    """Test the main conversation management system"""
    
    @pytest.fixture
    def mock_omega_control(self):
        """Mock OMEGA control center"""
        mock = Mock()
        mock.analyze_opportunity = AsyncMock(return_value={
            "game_name": "Kábala Perú",
            "items": [
                {"numbers": [1, 5, 12, 23, 28, 35], "ens_score": 0.75, "source": "ensemble"},
                {"numbers": [3, 8, 15, 22, 31, 38], "ens_score": 0.72, "source": "neural"},
                {"numbers": [2, 9, 17, 24, 29, 36], "ens_score": 0.68, "source": "genetic"}
            ],
            "jackpot_analysis": {
                "current_jackpot_usd": 500000,
                "expected_value": -1.85
            },
            "opportunity_analysis": {
                "recommendation": "SKIP"
            }
        })
        return mock
    
    @pytest.fixture
    def conversation_manager(self, mock_omega_control):
        return OmegaConversationManager(mock_omega_control, "redis://invalid:6379")
    
    @pytest.mark.asyncio
    async def test_recommendation_request_processing(self, conversation_manager):
        """Test processing of recommendation requests with honest disclaimers"""
        
        response = await conversation_manager.process_message(
            user_id="test_user",
            message="Dame 3 números para jugar en Kábala",
            locale="es"
        )
        
        assert response["metadata"]["type"] == "recommendation"
        assert "kábala" in response["text"].lower()
        assert len(response["metadata"]["recommendations"]) <= 3
        
        # Should include strong disclaimer
        assert "importante" in response["text"].lower() or "aleatorio" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_statistical_question_handling(self, conversation_manager):
        """Test statistical question responses"""
        
        response = await conversation_manager.process_message(
            user_id="test_user",
            message="¿Cuál es la probabilidad real de ganar en Kábala?",
            locale="es"
        )
        
        assert response["metadata"]["type"] == "statistical_explanation"
        assert "probabilidad" in response["text"].lower()
        # Should include mathematical reality disclaimer
        assert "independiente" in response["text"].lower() or "aleatoriedad" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_prediction_language_triggers_strong_honesty(self, conversation_manager):
        """Test that prediction language triggers strong honesty responses"""
        
        response = await conversation_manager.process_message(
            user_id="test_user",
            message="Predice exactamente qué números van a salir mañana seguro",
            locale="es"
        )
        
        # Should trigger strong honesty response
        assert response["metadata"]["honesty_trigger"] == True
        assert "advertencia" in response["text"].lower() or "importante" in response["text"].lower()
    
    @pytest.mark.asyncio 
    async def test_conversation_context_persistence(self, conversation_manager):
        """Test that conversation context persists across messages"""
        
        user_id = "test_context_user"
        
        # First message - should infer beginner level
        response1 = await conversation_manager.process_message(
            user_id=user_id,
            message="Soy nuevo, explica simple cómo funciona",
            locale="es"
        )
        
        conversation_id = response1["metadata"]["conversation_id"]
        
        # Second message - should maintain context
        response2 = await conversation_manager.process_message(
            user_id=user_id,
            message="Dame números para principiantes",
            conversation_id=conversation_id,
            locale="es"
        )
        
        assert response2["metadata"]["conversation_id"] == conversation_id
        assert response2["metadata"]["user_expertise"] == "beginner"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_manager):
        """Test error handling and graceful degradation"""
        
        # Mock OMEGA control to fail
        conversation_manager.omega_control.analyze_opportunity = AsyncMock(
            side_effect=Exception("Mock API failure")
        )
        
        response = await conversation_manager.process_message(
            user_id="test_user",
            message="Dame números para Kábala",
            locale="es"
        )
        
        assert response["metadata"]["type"] == "error"
        assert "error" in response["text"].lower()
    
    @pytest.mark.asyncio
    async def test_input_validation(self, conversation_manager):
        """Test input validation and security"""
        
        # Empty message
        response = await conversation_manager.process_message(
            user_id="test_user",
            message="",
            locale="es"
        )
        assert response["metadata"]["type"] == "error"
        
        # Too long message
        long_message = "a" * 2001
        response = await conversation_manager.process_message(
            user_id="test_user", 
            message=long_message,
            locale="es"
        )
        assert response["metadata"]["type"] == "error"


class TestWhatsAppBot:
    """Test WhatsApp conversational bot functionality"""
    
    @pytest.fixture
    def mock_omega_control(self):
        mock = Mock()
        mock.analyze_opportunity = AsyncMock(return_value={
            "game_name": "Kábala",
            "items": [{"numbers": [1, 2, 3, 4, 5, 6], "ens_score": 0.8, "source": "test"}]
        })
        return mock
    
    @pytest.fixture
    def whatsapp_bot(self, mock_omega_control):
        return WhatsAppConversationalBot(mock_omega_control, "redis://invalid:6379")
    
    @pytest.fixture 
    def formatter(self):
        return WhatsAppFormatter()
    
    def test_whatsapp_formatting(self, formatter):
        """Test WhatsApp message formatting"""
        
        # Test markdown conversion
        text_with_markdown = "**Bold text** and _italic text_ and `code`"
        formatted = formatter.format_for_whatsapp(text_with_markdown)
        
        assert "*Bold text*" in formatted  # **text** -> *text*
        assert "_italic text_" in formatted  # _text_ stays same
        assert "```code```" in formatted  # `text` -> ```text```
    
    def test_long_message_splitting(self, formatter):
        """Test intelligent message splitting for WhatsApp"""
        
        long_message = "Este es un mensaje muy largo. " * 100  # ~2500 chars
        
        messages = formatter.split_long_message(long_message)
        
        assert len(messages) > 1  # Should be split
        assert all(len(msg) <= 1600 for msg in messages)  # Within WhatsApp limits
        assert any("continúa" in msg for msg in messages)  # Should indicate continuation
    
    @pytest.mark.asyncio
    async def test_shortcut_detection(self, whatsapp_bot):
        """Test shortcut command detection and responses"""
        
        shortcut_responses = await whatsapp_bot.handle_incoming_message(
            "whatsapp:+1234567890",
            "ayuda"
        )
        
        assert len(shortcut_responses) == 1
        assert "comandos" in shortcut_responses[0].lower()
        assert "omega" in shortcut_responses[0].lower()
    
    @pytest.mark.asyncio
    async def test_locale_detection(self, whatsapp_bot):
        """Test automatic locale detection from messages and phone numbers"""
        
        # Spanish indicators
        spanish_responses = await whatsapp_bot.handle_incoming_message(
            "whatsapp:+51987654321",  # Peru number
            "Hola, necesito ayuda con números"
        )
        
        # Should detect Spanish
        assert any("análisis" in resp.lower() or "números" in resp for resp in spanish_responses)
        
        # English indicators
        english_responses = await whatsapp_bot.handle_incoming_message(
            "whatsapp:+1234567890",  # US number
            "Hello, I need help with numbers"
        )
        
        # Should detect English context
        assert len(english_responses) >= 1
    
    @pytest.mark.asyncio
    async def test_proactive_messaging(self, whatsapp_bot):
        """Test proactive message generation"""
        
        alert_messages = await whatsapp_bot.send_proactive_message(
            "whatsapp:+1234567890",
            "prediction_alert", 
            {"game": "kabala_pe"}
        )
        
        assert len(alert_messages) >= 1
        assert "omega" in alert_messages[0].lower()
    
    @pytest.mark.asyncio
    async def test_responsible_gaming_message(self, whatsapp_bot):
        """Test responsible gaming message generation"""
        
        rg_messages = await whatsapp_bot.send_proactive_message(
            "whatsapp:+1234567890",
            "responsible_gaming_check"
        )
        
        assert len(rg_messages) == 1
        assert "responsable" in rg_messages[0].lower() or "responsible" in rg_messages[0].lower()
        assert "ayuda" in rg_messages[0].lower() or "help" in rg_messages[0].lower()


class TestResponseTemplates:
    """Test response template system"""
    
    @pytest.fixture
    def templates(self):
        return ResponseTemplates()
    
    def test_disclaimer_templates(self, templates):
        """Test disclaimer template retrieval"""
        
        # Test different disclaimer levels
        mild = templates.get_template("disclaimers", "mild", "es")
        standard = templates.get_template("disclaimers", "standard", "es")
        strong = templates.get_template("disclaimers", "strong", "es")
        
        assert len(strong) > len(standard) > len(mild)
        assert "importante" in standard.lower()
        assert "advertencia" in strong.lower()
    
    def test_educational_templates(self, templates):
        """Test educational content templates"""
        
        prob_basics = templates.get_template("education", "probability_basics", "es")
        expected_value = templates.get_template("education", "expected_value", "es") 
        
        assert "probabilidad" in prob_basics.lower()
        assert "valor esperado" in expected_value.lower()
        assert "ev =" in expected_value.lower()  # Should include formula
    
    def test_template_formatting(self, templates):
        """Test template formatting with variables"""
        
        formatted = templates.get_template(
            "errors", "invalid_game", "es",
            game="TestGame", available_games="Game1, Game2"
        )
        
        assert "TestGame" in formatted
        assert "Game1, Game2" in formatted
    
    def test_multilingual_support(self, templates):
        """Test English/Spanish template support"""
        
        es_greeting = templates.get_template("conversation", "greeting", "es")
        en_greeting = templates.get_template("conversation", "greeting", "en")
        
        assert "hola" in es_greeting.lower()
        assert "hello" in en_greeting.lower()
        
        # Both should contain OMEGA reference
        assert "omega" in es_greeting.lower()
        assert "omega" in en_greeting.lower()


class TestIntegrationScenarios:
    """Integration tests for complete conversation flows"""
    
    @pytest.fixture
    def full_system(self):
        """Set up complete conversational system"""
        mock_omega = Mock()
        mock_omega.analyze_opportunity = AsyncMock(return_value={
            "game_name": "Kábala Perú",
            "items": [
                {"numbers": [7, 14, 21, 28, 35, 42], "ens_score": 0.82, "source": "ensemble"},
                {"numbers": [3, 10, 17, 24, 31, 38], "ens_score": 0.79, "source": "neural"}
            ],
            "jackpot_analysis": {"current_jackpot_usd": 750000, "expected_value": -1.75},
            "opportunity_analysis": {"recommendation": "SKIP"}
        })
        
        conversation_manager = OmegaConversationManager(mock_omega, "redis://invalid:6379")
        whatsapp_bot = WhatsAppConversationalBot(mock_omega, "redis://invalid:6379")
        
        return {
            "conversation_manager": conversation_manager,
            "whatsapp_bot": whatsapp_bot,
            "mock_omega": mock_omega
        }
    
    @pytest.mark.asyncio
    async def test_beginner_user_flow(self, full_system):
        """Test complete flow for beginner user"""
        
        cm = full_system["conversation_manager"]
        user_id = "beginner_user_001"
        
        # 1. Initial greeting and explanation request
        response1 = await cm.process_message(
            user_id=user_id,
            message="Hola, soy nuevo. ¿Qué es OMEGA y cómo funciona?",
            locale="es"
        )
        
        assert response1["metadata"]["user_expertise"] == "beginner"
        assert "simple" in response1["text"].lower() or "principiante" in response1["text"].lower()
        
        # 2. Ask for recommendations
        response2 = await cm.process_message(
            user_id=user_id,
            message="Dame números para jugar en Kábala",
            conversation_id=response1["metadata"]["conversation_id"],
            locale="es"
        )
        
        # Should include strong disclaimer for beginners
        assert "importante" in response2["text"].lower() or "aleatorio" in response2["text"].lower()
        assert response2["metadata"]["type"] == "recommendation"
        
        # 3. Ask about probabilities
        response3 = await cm.process_message(
            user_id=user_id,
            message="¿Qué probabilidad tengo de ganar?",
            conversation_id=response1["metadata"]["conversation_id"],
            locale="es"
        )
        
        # Should provide accessible explanation
        assert "moneda" in response3["text"].lower() or "millones" in response3["text"].lower()
        assert response3["metadata"]["type"] == "statistical_explanation"
    
    @pytest.mark.asyncio
    async def test_expert_user_flow(self, full_system):
        """Test complete flow for expert user"""
        
        cm = full_system["conversation_manager"] 
        user_id = "expert_user_001"
        
        # 1. Technical question
        response1 = await cm.process_message(
            user_id=user_id,
            message="Explica el ensemble calibration y las métricas de Brier score",
            locale="es"
        )
        
        assert response1["metadata"]["user_expertise"] == "expert"
        
        # 2. Request for analysis with technical language
        response2 = await cm.process_message(
            user_id=user_id,
            message="Analiza la distribución estadística y los pesos del ensemble",
            conversation_id=response1["metadata"]["conversation_id"],
            locale="es"
        )
        
        # Should provide technical response
        assert len(response2["text"]) > 200  # More detailed for experts
    
    @pytest.mark.asyncio
    async def test_whatsapp_complete_conversation(self, full_system):
        """Test complete WhatsApp conversation with formatting"""
        
        wb = full_system["whatsapp_bot"]
        
        # 1. User asks for help
        responses1 = await wb.handle_incoming_message(
            "whatsapp:+51987654321",
            "ayuda"
        )
        
        assert len(responses1) == 1
        assert all(len(resp) <= 1600 for resp in responses1)  # WhatsApp limit
        
        # 2. User asks for recommendations
        responses2 = await wb.handle_incoming_message(
            "whatsapp:+51987654321", 
            "Dame 3 números para Kábala"
        )
        
        assert len(responses2) >= 1
        # Should be formatted for WhatsApp
        combined_text = " ".join(responses2)
        assert "*" in combined_text or "_" in combined_text  # WhatsApp formatting
        
        # 3. User asks concerning question
        responses3 = await wb.handle_incoming_message(
            "whatsapp:+51987654321",
            "Necesito ganar para pagar mis deudas"
        )
        
        # Should trigger responsible gaming response
        combined_text = " ".join(responses3).lower()
        assert "responsable" in combined_text or "ayuda" in combined_text


# ============================================================================
# PERFORMANCE AND LOAD TESTS
# ============================================================================

class TestPerformanceAndScalability:
    """Test system performance under various loads"""
    
    @pytest.mark.asyncio
    async def test_concurrent_conversations(self):
        """Test system under concurrent load"""
        
        mock_omega = Mock()
        mock_omega.analyze_opportunity = AsyncMock(return_value={
            "game_name": "Test Game",
            "items": [{"numbers": [1, 2, 3, 4, 5, 6], "ens_score": 0.8, "source": "test"}]
        })
        
        cm = OmegaConversationManager(mock_omega, "redis://invalid:6379")
        
        # Simulate 20 concurrent users
        tasks = []
        for i in range(20):
            task = cm.process_message(
                user_id=f"load_test_user_{i}",
                message=f"Dame números para usuario {i}",
                locale="es"
            )
            tasks.append(task)
        
        start_time = asyncio.get_event_loop().time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        
        # All requests should complete
        assert len(responses) == 20
        
        # No exceptions
        exceptions = [r for r in responses if isinstance(r, Exception)]
        assert len(exceptions) == 0
        
        # Reasonable performance (under 5 seconds for 20 concurrent)
        total_time = end_time - start_time
        assert total_time < 5.0
        
        # All responses should be valid
        valid_responses = [r for r in responses if isinstance(r, dict) and "text" in r]
        assert len(valid_responses) == 20
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_context_cleanup(self):
        """Test memory management with context cleanup"""
        
        mock_omega = Mock()
        cm = OmegaConversationManager(mock_omega, "redis://invalid:6379")
        
        # Create many conversations
        for i in range(100):
            await cm.process_message(
                user_id=f"memory_test_user_{i}",
                message="Test message",
                locale="es"
            )
        
        # Check that context store has reasonable memory usage
        store_info = cm.context_store.get_store_info()
        
        # Should be using memory fallback
        assert store_info["backend"] == "memory"
        
        # Memory store should not grow indefinitely (has TTL cleanup)
        # This is a basic check - in real scenarios, monitor actual memory usage


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
    # Run tests with: python -m pytest tests/conversational/test_conversational_system.py -v
    pytest.main([__file__, "-v", "--tb=short"])