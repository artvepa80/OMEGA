#!/usr/bin/env python3
"""
🤖 OMEGA Conversational AI - Main Entry Point
Honest statistical analysis with Claude-like conversational interface

Usage:
    python main_conversational.py --mode api                    # Start conversational API
    python main_conversational.py --mode whatsapp              # Start WhatsApp bot
    python main_conversational.py --mode test                  # Test conversation
    python main_conversational.py --mode chat                  # Interactive chat
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import conversational system
from conversation.conversation_manager import OmegaConversationManager
from api.conversational_api import create_conversational_api
from messaging.whatsapp_conversational import WhatsAppConversationalBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('conversational_ai.log')
    ]
)

logger = logging.getLogger(__name__)

class MockOmegaControlCenter:
    """
    Mock OMEGA control center for testing and development
    Replace with real control center in production
    """
    
    def __init__(self):
        self.games = {
            "kabala_pe": "Kábala Perú",
            "megasena_br": "Mega-Sena Brasil", 
            "powerball_us": "Powerball USA"
        }
        logger.info("🎮 Mock OMEGA Control Center initialized")
    
    async def analyze_opportunity(self, domain: str, game_id: str) -> Dict[str, Any]:
        """Mock analysis - replace with real OMEGA engine"""
        
        if game_id not in self.games:
            raise ValueError(f"Game '{game_id}' not supported")
        
        # Simulate analysis delay
        await asyncio.sleep(0.1)
        
        # Mock realistic lottery analysis response
        import random
        
        game_configs = {
            "kabala_pe": {"range": [1, 40], "count": 6},
            "megasena_br": {"range": [1, 60], "count": 6}, 
            "powerball_us": {"range": [1, 69], "count": 5}
        }
        
        config = game_configs.get(game_id, {"range": [1, 40], "count": 6})
        
        # Generate mock predictions
        items = []
        for i in range(5):
            numbers = sorted(random.sample(
                range(config["range"][0], config["range"][1] + 1), 
                config["count"]
            ))
            
            items.append({
                "numbers": numbers,
                "ens_score": round(random.uniform(0.65, 0.85), 2),
                "source": random.choice(["ensemble", "neural", "genetic", "statistical"]),
                "rank": i + 1
            })
        
        # Mock jackpot analysis
        jackpot_usd = random.randint(100000, 2000000)
        ticket_cost = 2.0
        
        # Calculate mock expected value (always negative in reality)
        total_combinations = {
            "kabala_pe": 3_838_380,
            "megasena_br": 50_063_860,
            "powerball_us": 292_201_338
        }
        
        combinations = total_combinations.get(game_id, 3_838_380)
        win_probability = 1 / combinations
        expected_value = (jackpot_usd * win_probability) - ticket_cost
        
        # Mock recommendation based on EV
        if expected_value > 0:
            recommendation = "CONSIDER_PLAYING"
        elif expected_value > -1.5:
            recommendation = "ANALYZE"
        else:
            recommendation = "SKIP"
        
        return {
            "game_name": self.games[game_id],
            "game_id": game_id,
            "items": items,
            "analysis_info": {
                "methodology": "Ensemble de modelos estadísticos",
                "data_points": random.randint(500, 2000),
                "confidence": random.uniform(0.7, 0.9)
            },
            "jackpot_analysis": {
                "current_jackpot_usd": jackpot_usd,
                "expected_value": round(expected_value, 2),
                "win_probability": win_probability,
                "total_combinations": combinations
            },
            "opportunity_analysis": {
                "recommendation": recommendation,
                "reasoning": f"EV: ${expected_value:.2f}, probabilidad: 1 en {combinations:,}"
            },
            "generated_at": asyncio.get_event_loop().time(),
            "mock_data": True  # Indicator this is mock data
        }
    
    async def get_analysis_summary(self, period: str = "recent") -> Dict[str, Any]:
        """Mock analysis summary"""
        return {
            "period": period,
            "total_draws": random.randint(50, 200),
            "pattern_analysis": "Distribución normal observada en frecuencias",
            "statistical_summary": "Comportamiento aleatorio consistente",
            "most_frequent": [7, 14, 21, 28, 35],
            "least_frequent": [2, 13, 26, 39, 40]
        }


async def run_api_mode(args: argparse.Namespace):
    """Run conversational API server"""
    try:
        import uvicorn
        from fastapi import FastAPI
        
        # Initialize control center
        if args.mock:
            omega_control = MockOmegaControlCenter()
            logger.info("🎭 Using mock OMEGA control center")
        else:
            # TODO: Import and initialize real OMEGA control center
            logger.warning("⚠️ Real OMEGA control center not implemented, using mock")
            omega_control = MockOmegaControlCenter()
        
        # Create conversational API
        redis_url = args.redis_url or "redis://localhost:6379"
        app = create_conversational_api(omega_control, redis_url)
        
        logger.info(f"🚀 Starting OMEGA Conversational API on {args.host}:{args.port}")
        logger.info(f"📖 Documentation: http://{args.host}:{args.port}/docs")
        
        # Start server
        config = uvicorn.Config(
            app=app,
            host=args.host,
            port=args.port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except ImportError:
        logger.error("❌ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ API server error: {e}")
        sys.exit(1)


async def run_whatsapp_mode(args: argparse.Namespace):
    """Run WhatsApp conversational bot"""
    try:
        # Initialize control center
        if args.mock:
            omega_control = MockOmegaControlCenter()
            logger.info("🎭 Using mock OMEGA control center")
        else:
            logger.warning("⚠️ Real OMEGA control center not implemented, using mock")
            omega_control = MockOmegaControlCenter()
        
        # Initialize WhatsApp bot
        redis_url = args.redis_url or "redis://localhost:6379"
        whatsapp_bot = WhatsAppConversationalBot(omega_control, redis_url)
        
        logger.info("📱 OMEGA WhatsApp Conversational Bot ready")
        logger.info("🔗 Integrate with Twilio webhook at /webhook/whatsapp")
        
        # For demonstration, show some test interactions
        print("\n🧪 Testing WhatsApp bot functionality:")
        
        test_cases = [
            ("whatsapp:+51987654321", "Hola, explica cómo funciona OMEGA"),
            ("whatsapp:+51987654321", "Dame números para Kábala"),
            ("whatsapp:+51987654321", "¿Cuál es la probabilidad de ganar?"),
            ("whatsapp:+51987654321", "ayuda")
        ]
        
        for from_number, message in test_cases:
            print(f"\n👤 User ({from_number}): {message}")
            responses = await whatsapp_bot.handle_incoming_message(from_number, message)
            
            for i, response in enumerate(responses, 1):
                print(f"🤖 OMEGA ({i}/{len(responses)}): {response[:100]}{'...' if len(response) > 100 else ''}")
        
        # In production, this would set up webhook server
        logger.info("ℹ️ In production, set up Twilio webhook integration")
        
    except Exception as e:
        logger.error(f"❌ WhatsApp bot error: {e}")
        sys.exit(1)


async def run_test_mode(args: argparse.Namespace):
    """Run test conversations"""
    try:
        # Initialize system
        omega_control = MockOmegaControlCenter()
        redis_url = args.redis_url or "redis://localhost:6379" 
        conversation_manager = OmegaConversationManager(omega_control, redis_url)
        
        logger.info("🧪 Running OMEGA Conversational AI tests")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Beginner User Flow",
                "user_id": "test_beginner",
                "locale": "es",
                "messages": [
                    "Hola, soy nuevo. ¿Qué es OMEGA?",
                    "Dame números para jugar en Kábala",
                    "¿Qué probabilidad tengo de ganar?"
                ]
            },
            {
                "name": "Expert User Flow", 
                "user_id": "test_expert",
                "locale": "es",
                "messages": [
                    "Explica el ensemble calibration y métricas de Brier score",
                    "Analiza la distribución estadística de Kábala últimos 100 sorteos",
                    "¿Cuál es el EV actual considerando el jackpot?"
                ]
            },
            {
                "name": "Responsible Gaming Trigger",
                "user_id": "test_concern",
                "locale": "es", 
                "messages": [
                    "Necesito ganar para pagar mis deudas urgentes",
                    "He perdido mucho dinero, debo recuperarlo"
                ]
            },
            {
                "name": "English User",
                "user_id": "test_english",
                "locale": "en",
                "messages": [
                    "Hello, explain how OMEGA works",
                    "What are the odds of winning the lottery?",
                    "Give me number recommendations"
                ]
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n{'='*60}")
            print(f"🎯 Testing: {scenario['name']}")
            print('='*60)
            
            conversation_id = None
            
            for i, message in enumerate(scenario['messages'], 1):
                print(f"\n👤 User: {message}")
                
                response = await conversation_manager.process_message(
                    user_id=scenario['user_id'],
                    message=message,
                    conversation_id=conversation_id,
                    locale=scenario['locale']
                )
                
                conversation_id = response['metadata']['conversation_id']
                
                print(f"🤖 OMEGA ({response['metadata']['intent']}):")
                print(response['text'])
                
                # Show metadata for first message
                if i == 1:
                    print(f"\n📊 Metadata: expertise={response['metadata']['user_expertise']}, "
                          f"honesty_trigger={response['metadata'].get('honesty_trigger', False)}")
        
        # Performance stats
        print(f"\n{'='*60}")
        print("📈 Performance Statistics")
        print('='*60)
        
        stats = conversation_manager.get_performance_stats()
        for key, value in stats.items():
            if key != "context_store_status":
                print(f"• {key}: {value}")
        
        logger.info("✅ All tests completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Test mode error: {e}")
        raise


async def run_interactive_chat(args: argparse.Namespace):
    """Run interactive chat mode"""
    try:
        # Initialize system
        omega_control = MockOmegaControlCenter()
        redis_url = args.redis_url or "redis://localhost:6379"
        conversation_manager = OmegaConversationManager(omega_control, redis_url)
        
        print("🤖 OMEGA Conversational AI - Interactive Chat")
        print("=" * 50)
        print("Type 'quit', 'exit', or 'salir' to end the conversation")
        print("Type 'help' or 'ayuda' for available commands")
        print("=" * 50)
        
        user_id = args.user_id or "interactive_user"
        locale = args.locale or "es"
        conversation_id = None
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n{user_id}> ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'salir', 'q']:
                    print("\n👋 ¡Hasta luego! Remember to play responsibly.")
                    break
                
                # Process message
                response = await conversation_manager.process_message(
                    user_id=user_id,
                    message=user_input,
                    conversation_id=conversation_id,
                    locale=locale
                )
                
                conversation_id = response['metadata']['conversation_id']
                
                # Display response
                print(f"\n🤖 OMEGA:")
                print("-" * 40)
                print(response['text'])
                
                # Show intent and confidence for debugging
                if args.debug:
                    print(f"\n[DEBUG] Intent: {response['metadata']['intent']}, "
                          f"Confidence: {response['metadata'].get('confidence', 'N/A')}, "
                          f"Honesty trigger: {response['metadata'].get('honesty_trigger', False)}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'quit' to exit.")
        
    except Exception as e:
        logger.error(f"❌ Interactive chat error: {e}")
        sys.exit(1)


def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="OMEGA Conversational AI - Honest Statistical Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode api                          # Start API server on localhost:8000
  %(prog)s --mode api --port 5000             # Start API on port 5000
  %(prog)s --mode whatsapp                    # Test WhatsApp bot
  %(prog)s --mode test                        # Run test scenarios
  %(prog)s --mode chat                        # Interactive chat mode
  %(prog)s --mode chat --locale en            # English interactive chat
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["api", "whatsapp", "test", "chat"],
        default="api",
        help="Execution mode (default: api)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000, 
        help="API server port (default: 8000)"
    )
    
    parser.add_argument(
        "--redis-url",
        help="Redis URL for context storage (default: redis://localhost:6379)"
    )
    
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock OMEGA control center (default for now)"
    )
    
    parser.add_argument(
        "--user-id",
        default="interactive_user",
        help="User ID for interactive chat mode"
    )
    
    parser.add_argument(
        "--locale",
        choices=["es", "en"],
        default="es",
        help="Language locale (default: es)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="Enable debug output"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    return parser


async def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Display startup banner
    print(f"""
🤖 OMEGA Conversational AI v3.0
{'='*40}
Mode: {args.mode.upper()}
Locale: {args.locale.upper()}
Mock Mode: {args.mock or 'True (default)'}
{'='*40}
    """)
    
    try:
        # Route to appropriate mode
        if args.mode == "api":
            await run_api_mode(args)
        elif args.mode == "whatsapp":
            await run_whatsapp_mode(args)
        elif args.mode == "test":
            await run_test_mode(args)
        elif args.mode == "chat":
            await run_interactive_chat(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("👋 OMEGA Conversational AI stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())