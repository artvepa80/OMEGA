"""
Scheduler de OMEGA: programa disparos en días/horas específicas (tz-aware).
Usa APScheduler + CronTrigger. Persiste configuración en JSON.
"""

from __future__ import annotations
import json
import asyncio
from pathlib import Path
from typing import Callable, Dict, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

CONFIG_PATH = Path("config/scheduler_config.json")
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_CFG = {
    "days": ["tue", "thu", "sat"],
    "time": "20:30",
    "tz": "America/Lima",
    "playlist_url": "",
    "notify_twilio": True,
}

scheduler: Optional[BackgroundScheduler] = None
_on_fire_cb: Optional[Callable[[Dict], None]] = None


def _load_cfg() -> Dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        out = DEFAULT_CFG.copy()
        out.update(cfg or {})
        return out
    return DEFAULT_CFG.copy()


def _save_cfg(cfg: Dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get_schedule() -> Dict:
    return _load_cfg()


def update_schedule(new_cfg: Dict) -> Dict:
    cfg = _load_cfg()
    cfg.update({k: v for k, v in new_cfg.items() if v is not None})
    _save_cfg(cfg)
    _reschedule_jobs(cfg)
    return cfg


def _parse_time_str(t: str) -> tuple[int, int]:
    hh, mm = t.split(":")
    return int(hh), int(mm)


def _job_wrapper(cfg: Dict):
    if _on_fire_cb is None:
        return
    res = _on_fire_cb(cfg)
    if asyncio.iscoroutine(res):
        asyncio.run(res)


def _reschedule_jobs(cfg: Dict):
    global scheduler
    if scheduler is None:
        return
    try:
        scheduler.remove_job("lottery_watch")
    except Exception:
        pass

    tz = ZoneInfo(cfg.get("tz", DEFAULT_CFG["tz"]))
    hh, mm = _parse_time_str(cfg.get("time", DEFAULT_CFG["time"]))
    days = cfg.get("days", DEFAULT_CFG["days"])  # list[str]
    day_map = {
        "mon": "mon",
        "tue": "tue",
        "wed": "wed",
        "thu": "thu",
        "fri": "fri",
        "sat": "sat",
        "sun": "sun",
        "lunes": "mon",
        "martes": "tue",
        "miercoles": "wed",
        "miércoles": "wed",
        "jueves": "thu",
        "viernes": "fri",
        "sabado": "sat",
        "sábado": "sat",
        "domingo": "sun",
    }
    dof = ",".join(day_map.get(d.lower(), d.lower()) for d in days)

    trigger = CronTrigger(day_of_week=dof, hour=hh, minute=mm, timezone=tz)
    scheduler.add_job(_job_wrapper, trigger, id="lottery_watch", args=[cfg], replace_existing=True)


def start_scheduler(on_fire: Callable[[Dict], None]) -> None:
    global scheduler, _on_fire_cb
    _on_fire_cb = on_fire
    if scheduler is None:
        scheduler = BackgroundScheduler(timezone=ZoneInfo(_load_cfg().get("tz", DEFAULT_CFG["tz"])))
        scheduler.start(paused=False)
    _reschedule_jobs(_load_cfg())


def reload_scheduler() -> Dict:
    cfg = _load_cfg()
    _reschedule_jobs(cfg)
    return {"reloaded": True, "config": cfg}


def next_runs(n: int = 3) -> List[str]:
    if scheduler is None:
        return []
    job = scheduler.get_job("lottery_watch")
    if not job:
        return []
    times: List[str] = []
    nxt = job.trigger.get_next_fire_time(None, datetime.now(tz=job.trigger.timezone))
    for _ in range(n):
        if not nxt:
            break
        times.append(nxt.isoformat())
        nxt = job.trigger.get_next_fire_time(nxt, nxt)
    return times


