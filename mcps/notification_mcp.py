#!/usr/bin/env python3
"""
📨 Production Notification MCP - HARDENED
Multi-channel notifications with bulletproof delivery and rate limiting
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class ProductionNotificationMCP:
    """Production-ready MCP para notificaciones multi-canal"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.channels = {}
        self.failed_deliveries = []
        
        # Thread-safe rate limiting
        self._rl_lock = asyncio.Lock()
        self._last_reset = datetime.now()
        
        # Inicializar canales disponibles
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Inicializar canales de notificación"""
        
        # WhatsApp via Twilio
        if all(key in self.credentials for key in ["twilio_account_sid", "twilio_auth_token"]):
            self.channels["whatsapp"] = {
                "enabled": True,
                "client": self._create_twilio_client(),
                "rate_limit": {"max_per_minute": 60, "current": 0},
                "max_message_length": 1600  # WhatsApp limit
            }
        
        # Telegram
        if "telegram_bot_token" in self.credentials:
            self.channels["telegram"] = {
                "enabled": True,
                "bot_token": self.credentials["telegram_bot_token"],
                "rate_limit": {"max_per_minute": 30, "current": 0},
                "max_message_length": 4096  # Telegram limit
            }
        
        # Discord
        if "discord_webhook_url" in self.credentials:
            self.channels["discord"] = {
                "enabled": True,
                "webhook_url": self.credentials["discord_webhook_url"],
                "rate_limit": {"max_per_minute": 30, "current": 0},
                "max_message_length": 2000  # Discord limit
            }
        
        # Email (SMTP)
        if all(key in self.credentials for key in ["smtp_host", "smtp_user", "smtp_password"]):
            self.channels["email"] = {
                "enabled": True,
                "smtp_config": {
                    "host": self.credentials["smtp_host"],
                    "port": int(self.credentials.get("smtp_port", 587)),
                    "user": self.credentials["smtp_user"],
                    "password": self.credentials["smtp_password"]
                },
                "rate_limit": {"max_per_minute": 120, "current": 0},
                "max_message_length": 50000
            }
        
        logger.info(f"✅ Initialized {len(self.channels)} notification channels: {list(self.channels.keys())}")
    
    def _create_twilio_client(self):
        """Crear cliente Twilio"""
        try:
            from twilio.rest import Client
            return Client(
                self.credentials["twilio_account_sid"],
                self.credentials["twilio_auth_token"]
            )
        except ImportError:
            logger.error("Twilio library not available - install with: pip install twilio")
            return None
    
    async def send_notification(self, 
                              message: str,
                              channels: List[str],
                              recipients: Dict[str, str],
                              priority: str = "normal",
                              retry_count: int = 3) -> Dict[str, Any]:
        """Enviar notificación por canales especificados - ✅ Enhanced"""
        
        results = {}
        message_id = self._generate_message_id()
        
        # Validar canales
        valid_channels = [ch for ch in channels if ch in self.channels and self.channels[ch]["enabled"]]
        
        if not valid_channels:
            return {
                "success": False,
                "error": f"No valid channels available from: {channels}",
                "attempted_channels": channels,
                "available_channels": list(self.channels.keys()),
                "message_id": message_id
            }
        
        # Split long messages if needed
        split_messages = self._split_message_for_channels(message, valid_channels)
        
        # Enviar por cada canal
        for channel in valid_channels:
            channel_message = split_messages.get(channel, message)
            
            for attempt in range(retry_count):
                try:
                    # Verificar rate limit
                    if await self._check_rate_limit(channel):
                        result = await self._send_to_channel(channel, channel_message, recipients, priority)
                        results[channel] = {
                            "success": True,
                            "result": result,
                            "attempt": attempt + 1,
                            "message_length": len(channel_message)
                        }
                        break
                    else:
                        logger.warning(f"Rate limit exceeded for {channel}")
                        await asyncio.sleep(60)  # Wait 1 minute
                        
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed for {channel}: {e}")
                    if attempt == retry_count - 1:  # Last attempt
                        results[channel] = {
                            "success": False,
                            "error": str(e),
                            "attempts": retry_count
                        }
                        self._log_failed_delivery(channel, channel_message, recipients, str(e))
                    else:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {
            "overall_success": any(r.get("success", False) for r in results.values()),
            "channels": results,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat(),
            "total_attempts": sum(r.get("attempts", r.get("attempt", 0)) for r in results.values())
        }
    
    def _split_message_for_channels(self, message: str, channels: List[str]) -> Dict[str, str]:
        """Split message according to channel limits - ✅ Smart splitting"""
        split_messages = {}
        
        for channel in channels:
            max_length = self.channels[channel]["max_message_length"]
            
            if len(message) <= max_length:
                split_messages[channel] = message
            else:
                # Smart split - try to break at natural points
                if channel in ["whatsapp", "telegram"]:
                    # Try to split at paragraph breaks first
                    paragraphs = message.split('\n\n')
                    truncated = ""
                    
                    for para in paragraphs:
                        if len(truncated + para) <= max_length - 20:  # Leave room for "(cont.)"
                            truncated += para + '\n\n'
                        else:
                            break
                    
                    if truncated:
                        split_messages[channel] = truncated.strip() + "\n\n(cont. via other channels)"
                    else:
                        # Hard truncate
                        split_messages[channel] = message[:max_length-10] + "...(cont.)"
                else:
                    # For email/discord, less aggressive truncation
                    split_messages[channel] = message[:max_length-10] + "...(truncated)"
        
        return split_messages
    
    async def _send_to_channel(self, channel: str, message: str, recipients: Dict[str, str], priority: str) -> Dict[str, Any]:
        """Enviar a canal específico - ✅ Async-safe"""
        
        if channel == "whatsapp":
            return await self._send_whatsapp(message, recipients.get("whatsapp"))
        
        elif channel == "telegram":
            return await self._send_telegram(message, recipients.get("telegram"))
        
        elif channel == "discord":
            return await self._send_discord(message, recipients.get("discord"))
        
        elif channel == "email":
            return await self._send_email(message, recipients.get("email"))
        
        else:
            raise ValueError(f"Unknown channel: {channel}")
    
    async def _send_whatsapp(self, message: str, recipient: str) -> Dict[str, Any]:
        """Enviar mensaje por WhatsApp via Twilio - ✅ Async safe"""
        client = self.channels["whatsapp"]["client"]
        
        if not client:
            raise Exception("Twilio client not available")
        
        if not recipient:
            raise Exception("WhatsApp recipient not provided")
        
        # Formatear número para WhatsApp
        whatsapp_number = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
        
        # Run Twilio call in thread to avoid blocking
        def _send():
            return client.messages.create(
                body=message,
                from_=self.credentials.get("twilio_whatsapp_from", "whatsapp:+14155238886"),
                to=whatsapp_number
            )
        
        twilio_message = await asyncio.to_thread(_send)
        
        return {
            "sid": twilio_message.sid,
            "status": twilio_message.status,
            "to": whatsapp_number,
            "message_length": len(message)
        }
    
    async def _send_telegram(self, message: str, chat_id: str) -> Dict[str, Any]:
        """Enviar mensaje por Telegram - ✅ Enhanced error handling"""
        bot_token = self.channels["telegram"]["bot_token"]
        
        if not chat_id:
            raise Exception("Telegram chat_id not provided")
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "message_id": result["result"]["message_id"],
                        "chat_id": chat_id,
                        "status": "sent"
                    }
                elif response.status == 429:
                    # Rate limited
                    retry_after = (await response.json()).get("parameters", {}).get("retry_after", 1)
                    await asyncio.sleep(retry_after)
                    # Retry once
                    async with session.post(url, json=payload) as retry_response:
                        if retry_response.status == 200:
                            result = await retry_response.json()
                            return {
                                "message_id": result["result"]["message_id"],
                                "chat_id": chat_id,
                                "status": "sent_after_retry"
                            }
                        else:
                            error_text = await retry_response.text()
                            raise Exception(f"Telegram API error after retry: {retry_response.status} - {error_text}")
                else:
                    error_text = await response.text()
                    raise Exception(f"Telegram API error: {response.status} - {error_text}")
    
    async def _send_discord(self, message: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Enviar mensaje por Discord webhook - ✅ 429 handling"""
        url = webhook_url or self.channels["discord"]["webhook_url"]
        
        payload = {
            "content": message,
            "username": "OMEGA AI",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, json=payload) as response:
                if response.status in [200, 204]:
                    return {"status": "sent", "webhook": "discord"}
                elif response.status == 429:
                    # Rate limited - get retry_after
                    try:
                        error_data = await response.json()
                        retry_after = error_data.get("retry_after", 1)
                    except:
                        retry_after = 1
                    
                    logger.warning(f"Discord rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    
                    # Retry once
                    async with session.post(url, json=payload) as retry_response:
                        if retry_response.status in [200, 204]:
                            return {"status": "sent_after_retry", "webhook": "discord"}
                        else:
                            error_text = await retry_response.text()
                            raise Exception(f"Discord webhook error after retry: {retry_response.status} - {error_text}")
                else:
                    error_text = await response.text()
                    raise Exception(f"Discord webhook error: {response.status} - {error_text}")
    
    async def _send_email(self, message: str, recipient: str) -> Dict[str, Any]:
        """Enviar email via SMTP - ✅ Async safe"""
        if not recipient:
            raise Exception("Email recipient not provided")
        
        smtp_config = self.channels["email"]["smtp_config"]
        
        # Run SMTP in thread to avoid blocking
        def _send():
            msg = MIMEMultipart()
            msg['From'] = smtp_config["user"]
            msg['To'] = recipient
            msg['Subject'] = "🤖 OMEGA AI Notification"
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
                server.starttls()
                server.login(smtp_config["user"], smtp_config["password"])
                server.send_message(msg)
            
            return {"status": "sent", "recipient": recipient}
        
        try:
            return await asyncio.to_thread(_send)
        except Exception as e:
            raise Exception(f"SMTP error: {str(e)}")
    
    async def _check_rate_limit(self, channel: str) -> bool:
        """Verificar rate limit para canal - ✅ Thread-safe"""
        async with self._rl_lock:
            rate_limit = self.channels[channel]["rate_limit"]
            current_time = datetime.now()
            
            # Reset counter every minute
            if (current_time - self._last_reset).seconds >= 60:
                for ch in self.channels.values():
                    ch["rate_limit"]["current"] = 0
                self._last_reset = current_time
            
            if rate_limit["current"] < rate_limit["max_per_minute"]:
                rate_limit["current"] += 1
                return True
            
            return False
    
    def _log_failed_delivery(self, channel: str, message: str, recipients: Dict[str, str], error: str):
        """Log failed delivery para retry posterior"""
        self.failed_deliveries.append({
            "channel": channel,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "recipients": recipients,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener solo últimos 100 fallos
        if len(self.failed_deliveries) > 100:
            self.failed_deliveries.pop(0)
    
    def _generate_message_id(self) -> str:
        """Generar ID único para mensaje"""
        return str(uuid.uuid4())[:8]
    
    async def send_prediction_alert(self, 
                                  prediction_data: Dict[str, Any],
                                  user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar alerta de predicción personalizada - ✅ Enhanced formatting"""
        
        # Formatear mensaje según preferencias y canales
        messages = self._format_prediction_messages(prediction_data, user_preferences)
        
        # Determinar canales y recipients
        channels = user_preferences.get("notification_channels", ["whatsapp"])
        recipients = user_preferences.get("contact_info", {})
        
        # Use appropriate message for primary channel
        primary_channel = channels[0] if channels else "whatsapp"
        message = messages.get(primary_channel, messages.get("default", "No prediction data"))
        
        # Enviar notificación
        return await self.send_notification(
            message=message,
            channels=channels,
            recipients=recipients,
            priority="high"
        )
    
    def _format_prediction_messages(self, prediction_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, str]:
        """Formatear mensajes de predicción por canal - ✅ Multi-format"""
        
        lottery_name = prediction_data.get("game_name", "Lottery")
        items = prediction_data.get("items", [])[:3]  # Top 3
        
        messages = {}
        
        # WhatsApp format (emoji-rich, concise)
        wa_message = f"🤖 *OMEGA AI* - {lottery_name}\n\n"
        for i, item in enumerate(items, 1):
            numbers = " - ".join([f"{n:02d}" for n in item.get("numbers", [])])
            score = item.get("ens_score", 0)
            wa_message += f"*{i}.* `{numbers}` _(conf: {score:.2f})_\n"
        
        if "jackpot_analysis" in prediction_data:
            ja = prediction_data["jackpot_analysis"]
            ev = ja.get("expected_value", 0)
            wa_message += f"\n💰 Jackpot: ${ja.get('current_jackpot_usd', 0):,}"
            wa_message += f"\n📊 EV: ${ev:.2f}"
        
        if user_preferences.get("include_disclaimer", True):
            wa_message += "\n\n⚠️ _Juega responsablemente. No hay garantías._"
        
        messages["whatsapp"] = wa_message
        
        # Telegram format (markdown, detailed)
        tg_message = f"🤖 **OMEGA AI** - {lottery_name}\n\n"
        for i, item in enumerate(items, 1):
            numbers = " - ".join([f"{n:02d}" for n in item.get("numbers", [])])
            score = item.get("ens_score", 0)
            tg_message += f"**{i}.** `{numbers}` _(confidence: {score:.2f})_\n"
        
        if "jackpot_analysis" in prediction_data:
            ja = prediction_data["jackpot_analysis"]
            ev = ja.get("expected_value", 0)
            recommendation = prediction_data.get("opportunity_analysis", {}).get("recommendation", "")
            
            tg_message += f"\n💰 **Jackpot:** ${ja.get('current_jackpot_usd', 0):,}"
            tg_message += f"\n📊 **Expected Value:** ${ev:.2f}"
            tg_message += f"\n🎯 **Recommendation:** {recommendation}"
        
        if user_preferences.get("include_disclaimer", True):
            tg_message += "\n\n⚠️ _Play responsibly. No guarantees._"
        
        messages["telegram"] = tg_message
        
        # Discord format (embed-style)
        discord_message = f"🤖 **OMEGA AI** - {lottery_name}\n\n"
        discord_message += "```\nTop Predictions:\n"
        for i, item in enumerate(items, 1):
            numbers = " - ".join([f"{n:02d}" for n in item.get("numbers", [])])
            score = item.get("ens_score", 0)
            discord_message += f"{i}. {numbers} (conf: {score:.2f})\n"
        discord_message += "```"
        
        if "jackpot_analysis" in prediction_data:
            ja = prediction_data["jackpot_analysis"]
            discord_message += f"\n💰 Jackpot: ${ja.get('current_jackpot_usd', 0):,}"
            discord_message += f"\n📊 EV: ${ja.get('expected_value', 0):.2f}"
        
        messages["discord"] = discord_message
        
        # Email format (clean, professional)
        email_message = f"OMEGA AI Prediction Report - {lottery_name}\n\n"
        email_message += "Top Predictions:\n"
        for i, item in enumerate(items, 1):
            numbers = " - ".join([f"{n:02d}" for n in item.get("numbers", [])])
            score = item.get("ens_score", 0)
            email_message += f"{i}. {numbers} (confidence: {score:.2f})\n"
        
        if "jackpot_analysis" in prediction_data:
            ja = prediction_data["jackpot_analysis"]
            email_message += f"\nCurrent Jackpot: ${ja.get('current_jackpot_usd', 0):,}"
            email_message += f"\nExpected Value: ${ja.get('expected_value', 0):.2f}"
        
        email_message += "\n\nGenerated by OMEGA AI - Play responsibly."
        
        messages["email"] = email_message
        
        # Default fallback
        messages["default"] = wa_message.replace("*", "").replace("_", "").replace("`", "")
        
        return messages
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de entregas - ✅ Enhanced"""
        current_limits = {}
        for channel, data in self.channels.items():
            rl = data["rate_limit"]
            current_limits[channel] = {
                "current": rl["current"],
                "max_per_minute": rl["max_per_minute"],
                "utilization_pct": (rl["current"] / rl["max_per_minute"]) * 100
            }
        
        return {
            "available_channels": list(self.channels.keys()),
            "failed_deliveries_count": len(self.failed_deliveries),
            "recent_failures": self.failed_deliveries[-5:] if self.failed_deliveries else [],
            "rate_limits": current_limits,
            "last_reset": self._last_reset.isoformat(),
            "total_channels_configured": len(self.channels)
        }
    
    async def test_channels(self) -> Dict[str, Any]:
        """Test all configured channels - ✅ Health check"""
        test_message = "🧪 OMEGA AI Test Message - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_recipients = {
            "whatsapp": self.credentials.get("test_whatsapp"),
            "telegram": self.credentials.get("test_telegram_chat_id"),
            "discord": None,  # Uses default webhook
            "email": self.credentials.get("test_email")
        }
        
        results = {}
        
        for channel in self.channels.keys():
            if test_recipients.get(channel) or channel == "discord":
                try:
                    result = await self._send_to_channel(
                        channel, 
                        test_message, 
                        test_recipients, 
                        "normal"
                    )
                    results[channel] = {"success": True, "result": result}
                except Exception as e:
                    results[channel] = {"success": False, "error": str(e)}
            else:
                results[channel] = {"success": False, "error": "No test recipient configured"}
        
        return {
            "test_timestamp": datetime.now().isoformat(),
            "channels_tested": len(results),
            "channels_working": sum(1 for r in results.values() if r["success"]),
            "results": results
        }