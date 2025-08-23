"""
¡Vamos a mejorar los archivos que componen la IA OMEGA!
Webhook WhatsApp:
- GET verify (hub.challenge)
- POST mensajes -> comandos: PREDICT, STATUS, HELP
- Integra OmegaHybridSystem sin bloquear (BackgroundTasks)
"""

from __future__ import annotations
import logging
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

logger = logging.getLogger(__name__)


def get_router(hybrid_system, whatsapp_client) -> APIRouter:
    router = APIRouter()

    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "omega-verify-token")

    @router.get("")
    async def verify(
        hub_mode: Optional[str] = None,
        hub_challenge: Optional[str] = None,
        hub_verify_token: Optional[str] = None,
    ):
        if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
            try:
                return int(hub_challenge or 0)
            except Exception:
                return hub_challenge or "0"
        raise HTTPException(status_code=403, detail="Verify token mismatch")

    @router.post("")
    async def receive(req: Request, tasks: BackgroundTasks):
        body = await req.json()
        try:
            entries = body.get("entry", [])
            for entry in entries:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        if msg.get("type") == "text":
                            from_ = msg["from"]  # E.164
                            text = (msg.get("text", {}) or {}).get("body", "").strip().lower()
                            logger.info("WA INCOMING %s: %s", from_, text)
                            # Dispara en background para no bloquear webhook
                            tasks.add_task(_handle_command, hybrid_system, whatsapp_client, from_, text)
            return {"ok": True}
        except Exception as e:  # noqa: BLE001
            logger.exception("Error procesando webhook WA: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    return router


def _handle_command(hybrid_system, whatsapp_client, to: str, text: str):
    try:
        if text.startswith("predict"):
            result = hybrid_system.generate_prediction(mode="hybrid")
            if result.get("success"):
                combos = result.get("combinations", [])
                pretty = "\n".join(
                    [
                        f"• {c['numbers']}  conf={c.get('confidence',0):.2f} src={c.get('source','?')}"
                        for c in combos
                    ]
                ) or "Sin combinaciones."
                whatsapp_client.send_text(to, f"🤖 OMEGA Hybrid\n{pretty}")
            else:
                whatsapp_client.send_text(to, f"❌ Error: {result.get('errors')}")
        elif text.startswith("status"):
            s = hybrid_system.get_system_status()
            whatsapp_client.send_text(
                to,
                f"📊 Estado: {s['current_mode']} | total_preds={s['statistics']['total_predictions']}",
            )
        else:
            whatsapp_client.send_text(to, "Comandos: PREDICT | STATUS | HELP")
    except Exception as e:  # noqa: BLE001
        logger.exception("Error manejando comando WA: %s", e)


