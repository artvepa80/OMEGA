# notification_mcp.py — OMEGA MCP Notifications (Enterprise-Grade)
# -*- coding: utf-8 -*-
"""
Canales de notificación desacoplados con reintentos, backoff y logging estructurado.
Soporta: Consola, Slack (Webhook), Email (SMTP), Discord (Webhook).
Uso:
    from notification_mcp import NotificationService, NotificationMessage, Severity, NotificationConfig
    cfg = NotificationConfig.from_env()  # o .from_file("config.yaml|json")
    svc = NotificationService(cfg)
    svc.send(NotificationMessage(subject="Prueba", body="Hola", severity=Severity.INFO, tags=["demo"]))
"""
from __future__ import annotations
import os
import ssl
import smtplib
import json
import time
import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from email.message import EmailMessage
from typing import Dict, List, Optional, Any

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

# ---------------------------- Logging ---------------------------------

def setup_logger(name: str = "omega.mcp.notifications", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger

logger = setup_logger()

# ---------------------------- Tipos -----------------------------------

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class NotificationMessage:
    subject: str
    body: str
    severity: Severity = Severity.INFO
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Para email opcionalmente
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


@dataclass
class NotificationConfig:
    # Slack / Discord
    slack_webhook_url: Optional[str] = None
    discord_webhook_url: Optional[str] = None

    # Email SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    default_recipients: List[str] = field(default_factory=list)

    # Consola
    enable_console: bool = True

    # Parámetros de resiliencia
    timeout_seconds: int = 10
    max_retries: int = 3
    backoff_seconds: float = 1.5

    @staticmethod
    def from_env() -> "NotificationConfig":
        recips = os.getenv("OMEGA_NOTIFY_RECIPIENTS", "")
        recipients = [e.strip() for e in recips.split(",") if e.strip()]
        return NotificationConfig(
            slack_webhook_url=os.getenv("OMEGA_SLACK_WEBHOOK"),
            discord_webhook_url=os.getenv("OMEGA_DISCORD_WEBHOOK"),
            smtp_host=os.getenv("OMEGA_SMTP_HOST"),
            smtp_port=int(os.getenv("OMEGA_SMTP_PORT", "587")),
            smtp_user=os.getenv("OMEGA_SMTP_USER"),
            smtp_password=os.getenv("OMEGA_SMTP_PASSWORD"),
            smtp_from=os.getenv("OMEGA_SMTP_FROM"),
            default_recipients=recipients,
            enable_console=os.getenv("OMEGA_NOTIFY_CONSOLE", "1") == "1",
            timeout_seconds=int(os.getenv("OMEGA_NOTIFY_TIMEOUT", "10")),
            max_retries=int(os.getenv("OMEGA_NOTIFY_MAX_RETRIES", "3")),
            backoff_seconds=float(os.getenv("OMEGA_NOTIFY_BACKOFF", "1.5")),
        )

    @staticmethod
    def from_file(path: str) -> "NotificationConfig":
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(content)
        except Exception:
            data = json.loads(content)
        return NotificationConfig(**data)

# ---------------------------- Canales ---------------------------------

class BaseChannel:
    def __init__(self, cfg: NotificationConfig):
        self.cfg = cfg

    def _retry_backoff(self, fn, *args, **kwargs) -> bool:
        tries = self.cfg.max_retries
        delay = self.cfg.backoff_seconds
        for attempt in range(1, tries + 1):
            try:
                ok = fn(*args, **kwargs)
                if ok:
                    return True
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] intento {attempt}/{tries} falló: {e}")
                logger.debug(traceback.format_exc())
            time.sleep(delay * attempt)  # backoff lineal
        return False

    def send(self, msg: NotificationMessage) -> bool:
        raise NotImplementedError


class ConsoleChannel(BaseChannel):
    def send(self, msg: NotificationMessage) -> bool:
        payload = {
            "severity": msg.severity,
            "subject": msg.subject,
            "body": msg.body,
            "tags": msg.tags,
            "metadata": msg.metadata,
        }
        level = {
            Severity.INFO: logging.INFO,
            Severity.WARNING: logging.WARNING,
            Severity.ERROR: logging.ERROR,
            Severity.CRITICAL: logging.CRITICAL,
        }[msg.severity]
        logger.log(level, json.dumps(payload, ensure_ascii=False))
        return True


class SlackChannel(BaseChannel):
    def send(self, msg: NotificationMessage) -> bool:
        if not self.cfg.slack_webhook_url or not requests:
            return False

        def _post() -> bool:
            data = {
                "text": f"*{msg.severity}* — {msg.subject}\n{msg.body}\n_tags: {', '.join(msg.tags)}_"
            }
            r = requests.post(self.cfg.slack_webhook_url, json=data, timeout=self.cfg.timeout_seconds)
            return r.status_code // 100 == 2

        return self._retry_backoff(_post)


class DiscordChannel(BaseChannel):
    def send(self, msg: NotificationMessage) -> bool:
        if not self.cfg.discord_webhook_url or not requests:
            return False

        def _post() -> bool:
            data = {"content": f"**{msg.severity}** — {msg.subject}\n{msg.body}"}
            r = requests.post(self.cfg.discord_webhook_url, json=data, timeout=self.cfg.timeout_seconds)
            return r.status_code // 100 == 2

        return self._retry_backoff(_post)


class EmailChannel(BaseChannel):
    def send(self, msg: NotificationMessage) -> bool:
        if not self.cfg.smtp_host or not self.cfg.smtp_from:
            return False

        def _send() -> bool:
            recipients = msg.to or self.cfg.default_recipients
            if not recipients:
                logger.warning("[EmailChannel] No hay destinatarios, omitiendo envío.")
                return False

            em = EmailMessage()
            em["From"] = self.cfg.smtp_from
            em["To"] = ", ".join(recipients)
            if msg.cc:
                em["Cc"] = ", ".join(msg.cc)
            em["Subject"] = f"[{msg.severity}] {msg.subject}"
            em.set_content(msg.body)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.cfg.smtp_host, self.cfg.smtp_port, timeout=self.cfg.timeout_seconds) as server:
                server.starttls(context=context)
                if self.cfg.smtp_user and self.cfg.smtp_password:
                    server.login(self.cfg.smtp_user, self.cfg.smtp_password)
                server.send_message(em)
            return True

        return self._retry_backoff(_send)

# ---------------------------- Servicio --------------------------------

class NotificationService:
    def __init__(self, cfg: NotificationConfig):
        self.cfg = cfg
        self.channels: List[BaseChannel] = []
        if cfg.enable_console:
            self.channels.append(ConsoleChannel(cfg))
        self.channels.append(EmailChannel(cfg))
        self.channels.append(SlackChannel(cfg))
        self.channels.append(DiscordChannel(cfg))

    def send(self, msg: NotificationMessage) -> Dict[str, bool]:
        results = {}
        for ch in self.channels:
            ok = False
            try:
                ok = ch.send(msg)
            except Exception as e:  # pragma: no cover
                logger.error(f"Error enviando con {ch.__class__.__name__}: {e}")
                logger.debug(traceback.format_exc())
            results[ch.__class__.__name__] = ok
        return results

    def send_batch(self, messages: List[NotificationMessage]) -> Dict[int, Dict[str, bool]]:
        out = {}
        for idx, m in enumerate(messages):
            out[idx] = self.send(m)
        return out


if __name__ == "__main__":
    # Ejemplo rápido manual
    cfg = NotificationConfig.from_env()
    svc = NotificationService(cfg)
    res = svc.send(NotificationMessage(subject="Ping", body="Notificación de prueba.", severity=Severity.INFO, tags=["healthcheck"]))
    print(res)
