"""
WhatsApp Bridge (Enhanced)
--------------------------
- FastAPI webhook (GET verify + POST inbound)
- Envío saliente con httpx (async)
- Firma HMAC opcional (X-Hub-Signature-256)
- Lista blanca opcional de números (security)
- Comandos: predice | estado | modo <pipeline|agentic|hybrid> | help
- Integración directa con OmegaHybridSystem (con fallback dummy para tests)
- Mini CLI: enviar mensaje manual (python -m tools.whatsapp_bridge_enhanced --send "Hola")
"""

from __future__ import annotations
import os
import hmac
import hashlib
import json
import asyncio
import argparse
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "omega-verify")
W_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
APP_SECRET = os.getenv("APP_SECRET")
VERIFY_SIG = os.getenv("VERIFY_SIGNATURE", "false").lower() == "true"
WHITELIST_RAW = os.getenv("WHATSAPP_WHITELIST", "")
WHITELIST = {n.strip().lstrip("+") for n in WHITELIST_RAW.split(",") if n.strip()}
OMEGA_IMPORT = os.getenv("OMEGA_IMPORT_PATH", "omega_hybrid_integration:OmegaHybridSystem")

GRAPH_URL = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"


def import_omega_class(import_path: str):
    module_name, cls_name = import_path.split(":")
    mod = __import__(module_name, fromlist=[cls_name])
    return getattr(mod, cls_name)


# Fallback seguro para tests si no existe la clase real
try:
    OmegaHybridSystem = import_omega_class(OMEGA_IMPORT)
except Exception:  # noqa: BLE001
    class OmegaHybridSystem:  # type: ignore[no-redef]
        current_mode = "hybrid"

        def initialize_systems(self) -> bool:  # noqa: D401
            return True

        def get_system_status(self) -> Dict[str, Any]:  # noqa: D401
            return {
                "current_mode": self.current_mode,
                "system_health": {"pipeline": True, "agentic": True},
                "statistics": {"total_predictions": 0},
            }

        def switch_mode(self, mode: str, reason: str = "") -> None:  # noqa: D401
            self.current_mode = mode

        def generate_prediction(self, mode: str) -> Dict[str, Any]:  # noqa: D401
            return {"combinations": []}


app = FastAPI(title="OMEGA WhatsApp Bridge (Enhanced)")
omega = OmegaHybridSystem()
try:
    omega.initialize_systems()
except Exception:
    # En modo fallback no es crítico
    pass


def _ensure_e164(num: str) -> str:
    n = num.strip().replace(" ", "").lstrip("+")
    return f"+{n}"


def _is_allowed(num: str) -> bool:
    if not WHITELIST:
        return True
    return num.lstrip("+") in WHITELIST


def _verify_signature(raw_body: bytes, header_sig: Optional[str]) -> bool:
    if not VERIFY_SIG or not APP_SECRET:
        return True
    if not header_sig:
        return False
    try:
        prefix, provided = header_sig.split("=", 1)
        if prefix != "sha256":
            return False
    except Exception:
        return False
    mac = hmac.new(APP_SECRET.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, provided)


async def send_whatsapp_text(to: str, body: str) -> Dict[str, Any]:
    if not (W_TOKEN and PHONE_ID):
        raise RuntimeError("Faltan WHATSAPP_TOKEN o WHATSAPP_PHONE_ID en el entorno.")
    # Modo prueba para test unitario/CI
    if W_TOKEN == "DUMMY" or PHONE_ID == "DUMMY":
        return {"ok": True, "dry_run": True, "to": _ensure_e164(to), "body": body[:200]}

    headers = {"Authorization": f"Bearer {W_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": _ensure_e164(to),
        "type": "text",
        "text": {"preview_url": False, "body": body[:4096]},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(GRAPH_URL, headers=headers, json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:  # noqa: BLE001
            raise RuntimeError(f"WhatsApp API error {e.response.status_code}: {e.response.text}") from e
        return r.json()


def format_combinations(res: Dict[str, Any]) -> str:
    combos = res.get("combinations", [])
    if not combos:
        return "No pude generar combinaciones ahora. Intenta de nuevo."
    lines = []
    for i, c in enumerate(combos[:3], 1):
        nums = " ".join(f"{n:02d}" for n in c.get("numbers", [])[:6])
        conf = c.get("confidence", 0.0)
        src = c.get("source", "?")
        lines.append(f"{i}) {nums} | conf {conf:.2f} | {src}")
    return "🎯 OMEGA Hybrid\n" + "\n".join(lines)


def handle_command(txt: str) -> str:
    t = txt.strip().lower()
    if t in ("help", "/help", "ayuda", "/ayuda"):
        return (
            "Comandos:\n"
            "• predice → 3 combinaciones\n"
            "• estado → estado rápido\n"
            "• modo pipeline|agentic|hybrid → cambiar modo\n"
            "• help → esta ayuda"
        )
    if t.startswith("modo "):
        _, _, m = t.partition(" ")
        m = m.strip()
        if m not in {"pipeline", "agentic", "hybrid"}:
            return "Modos válidos: pipeline | agentic | hybrid"
        try:
            omega.switch_mode(m, reason="whatsapp")
            return f"Modo cambiado a: {m}"
        except Exception as e:  # noqa: BLE001
            return f"No pude cambiar el modo: {e}"
    if t in ("predice", "/predice", "predict"):
        try:
            res = omega.generate_prediction(mode=getattr(omega, "current_mode", "hybrid"))
        except Exception:
            res = {"combinations": []}
        return format_combinations(res)
    if t in ("estado", "/estado", "status", "/status"):
        try:
            st = omega.get_system_status()
            return (
                f"🔎 Estado: {st['current_mode']} | "
                f"pipeline={'OK' if st['system_health']['pipeline'] else 'X'}, "
                f"agentic={'OK' if st['system_health']['agentic'] else 'X'}\n"
                f"predicciones={st['statistics']['total_predictions']}"
            )
        except Exception:
            return "Estado no disponible"
    return (
        "Hola, soy OMEGA 🤖\n"
        "Comandos: predice | estado | modo <pipeline|agentic|hybrid> | help"
    )


@app.get("/webhook")
async def verify(request: Request):
    qp = request.query_params
    if qp.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(qp.get("hub.challenge", ""), status_code=200)
    return PlainTextResponse("forbidden", status_code=403)


@app.post("/webhook")
async def inbound(request: Request):
    raw = await request.body()
    if not _verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        return JSONResponse({"ok": True, "ignored": "invalid_signature"}, status_code=200)

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return JSONResponse({"ok": True, "ignored": "invalid_json"}, status_code=200)

    try:
        changes = data["entry"][0]["changes"][0]["value"]
        msgs = changes.get("messages", []) or []
        if not msgs:
            return {"ok": True}
        msg = msgs[0]
        from_number = msg["from"]
        if not _is_allowed(from_number):
            return {"ok": True, "ignored": "not_whitelisted"}

        txt = ""
        if "text" in msg and "body" in msg["text"]:
            txt = msg["text"]["body"]
        elif "interactive" in msg:
            it = msg["interactive"]
            if "button_reply" in it and "title" in it["button_reply"]:
                txt = it["button_reply"]["title"]
            elif "list_reply" in it and "title" in it["list_reply"]:
                txt = it["list_reply"]["title"]

        reply = handle_command(txt or "")
        try:
            await send_whatsapp_text(from_number, reply)
        except Exception:
            # Evitar reintentos de Meta pero no fallar
            pass
    except Exception as e:
        print("Inbound error:", e, str(raw)[:800])
    return {"ok": True}


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "omega_mode": getattr(omega, "current_mode", "hybrid")}


def _cli():
    parser = argparse.ArgumentParser(description="OMEGA WhatsApp Bridge CLI")
    parser.add_argument("--send", help="Enviar texto al número (E.164) indicado en --to")
    parser.add_argument("--to", help="Destino E.164 (ej: +51972514235)")
    args = parser.parse_args()

    if args.send:
        if not args.to:
            raise SystemExit("--to es requerido (E.164, ej: +51972514235)")
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(send_whatsapp_text(args.to, args.send))
        print("Enviado:", res)


if __name__ == "__main__":
    _cli()


