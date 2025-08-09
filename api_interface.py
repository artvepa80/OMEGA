from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Body
from fastapi.middleware.cors import CORSMiddleware
import os, asyncio
from pathlib import Path
from typing import Any, Dict, Optional, List

app = FastAPI(title="OMEGA API")

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas UI support
from api.routes.ui_support import router as ui_router  # noqa: E402
app.include_router(ui_router)

# ====== OmegaHybridSystem instancia única ======
try:
    from omega_hybrid_integration import OmegaHybridSystem  # type: ignore
    hybrid = OmegaHybridSystem()
    hybrid.initialize_systems()
except Exception:
    hybrid = None  # type: ignore

# ====== WhatsApp Webhook integrado (Cloud API) ======
try:
    from integrations.whatsapp_client_enhanced import WhatsAppClient  # type: ignore
    from integrations.whatsapp_webhook_enhanced import get_router  # type: ignore

    wa_client = WhatsAppClient(
        token=os.getenv("WHATSAPP_TOKEN", ""),
        phone_number_id=os.getenv("WHATSAPP_PHONE_ID", ""),
        dry_run=not bool(os.getenv("WHATSAPP_TOKEN")),
    )
    if hybrid is not None:
        app.include_router(get_router(hybrid, wa_client), prefix="/webhooks/whatsapp", tags=["whatsapp"])  # type: ignore
except Exception:
    # WhatsApp integración opcional
    pass

# ====== Twilio Webhook integrado (SMS/WhatsApp via Twilio) ======
try:
    from integrations.twilio_webhook import get_twilio_router  # type: ignore
    if hybrid is not None:
        app.include_router(get_twilio_router(hybrid), prefix="/webhooks/twilio", tags=["twilio"])  # type: ignore
except Exception:
    # Twilio integración opcional
    pass


@app.get("/status")
def status():
    try:
        if hybrid is None:
            return {"ok": False, "error": "Hybrid system not available"}
        st = hybrid.get_system_status()
        return {"ok": True, "status": st}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


# WebSocket simple para logs en vivo
@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket):
    await ws.accept()
    log_file = Path("logs/omega_system.log")
    log_file.parent.mkdir(exist_ok=True)
    log_file.touch(exist_ok=True)

    try:
        # tail -f básico en Python
        with log_file.open("r") as f:
            f.seek(0, 2)  # al final
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                await ws.send_text(line.rstrip("\n"))
    except WebSocketDisconnect:
        return
    except Exception as e:  # noqa: BLE001
        try:
            await ws.send_text(f"[ERROR] {e}")
        except Exception:
            pass

# --- Scheduler opcional (si APScheduler está disponible) ---
try:  # pragma: no cover
    from services.scheduler_service import (
        start_scheduler,
        get_schedule,
        update_schedule,
        reload_scheduler,
        next_runs,
    )

    async def _on_fire(cfg: Dict[str, Any]):
        if hybrid is None:
            return {"ok": False, "error": "Hybrid not ready"}
        res = hybrid.generate_prediction(mode="hybrid")
        # Notificación opcional por WhatsApp a admins
        try:
            admins_raw = os.getenv("WHATSAPP_ADMIN", "")
            admins: List[str] = [x.strip() for x in admins_raw.split(",") if x.strip()]
            if admins and 'wa_client' in globals():
                body = f"OMEGA 🔔 {len(res.get('combinations', []))} combos generados"
                for to in admins:
                    try:
                        wa_client.send_text(to, body)  # type: ignore
                    except Exception:
                        continue
        except Exception:
            pass
        return {"ok": True, "result": bool(res.get("success", True))}

    # Iniciar scheduler con callback
    start_scheduler(_on_fire)

    # Endpoints UI Scheduler
    sched_router = APIRouter(prefix="/ui", tags=["scheduler"])

    @sched_router.get("/scheduler")
    def ui_get_schedule():
        cfg = get_schedule()
        return {"config": cfg, "next_runs": next_runs(5)}

    @sched_router.post("/scheduler")
    def ui_set_schedule(payload: Dict[str, Any] = Body(...)):
        cfg = update_schedule(payload or {})
        return {"config": cfg, "next_runs": next_runs(5)}

    @sched_router.post("/scheduler/reload")
    def ui_reload_sched():
        res = reload_scheduler()
        return {"status": "reloaded", "config": res["config"], "next_runs": next_runs(5)}

    @sched_router.post("/scheduler/fire-now")
    async def ui_fire_now():
        cfg = get_schedule()
        return await _on_fire(cfg)

    app.include_router(sched_router)
except Exception:
    # Sin scheduler, continuar normalmente
    pass


