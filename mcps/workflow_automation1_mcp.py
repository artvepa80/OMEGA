# workflow_automation_mcp.py — OMEGA MCP Workflow Orchestrator (Enterprise-Grade)
# -*- coding: utf-8 -*-
"""
Orquestador ligero de flujos (DAG) en Python puro con reintentos, logging y métricas.
Integra lottery_data_mcp y notification_mcp.
Uso CLI:
    python3 workflow_automation_mcp.py run --workflow ingest_kabala --config config_omega_mcp.yaml
"""
from __future__ import annotations
import os
import sys
import time
import json
import argparse
import logging
import traceback
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any

from datetime import datetime

from notification_mcp import NotificationService, NotificationConfig, NotificationMessage, Severity
from lottery_data_mcp import ProductionLotteryDataMCP, SourceConfig

# ---------------------------- Logging ---------------------------------

def setup_logger(name: str = "omega.mcp.workflow", level: int = logging.INFO) -> logging.Logger:
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

# ---------------------------- DAG -------------------------------------

@dataclass
class Task:
    name: str
    fn: Callable[..., Any]
    max_retries: int = 2
    backoff_seconds: float = 2.0


@dataclass
class Workflow:
    name: str
    tasks: List[Task] = field(default_factory=list)

    def run(self, **context) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for t in self.tasks:
            attempt = 0
            while True:
                attempt += 1
                try:
                    logger.info(f"▶️ Task: {t.name} (intento {attempt}/{t.max_retries + 1})")
                    results[t.name] = t.fn(**context)
                    break
                except Exception as e:
                    logger.warning(f"Task {t.name} falló: {e}")
                    logger.debug(traceback.format_exc())
                    if attempt > t.max_retries:
                        raise
                    time.sleep(t.backoff_seconds * attempt)
        return results

# ---------------------------- Config ----------------------------------

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(raw)
    except Exception:
        return json.loads(raw)

# ---------------------------- Tareas ----------------------------------

def task_ingest_data(**context):
    cfg = context["cfg"]
    ingest_cfg = cfg["ingest"]
    mcp = ProductionLotteryDataMCP(
        data_dir=ingest_cfg.get("data_dir", "data/lottery_ingestion"),
        write_parquet=ingest_cfg.get("write_parquet", False),
        partition_by_day=ingest_cfg.get("partition_by_day", True),
        keep_raw=ingest_cfg.get("keep_raw", True),
    )
    sources = []
    for s in ingest_cfg["sources"]:
        sources.append(SourceConfig(**s))
    res = mcp.ingest(sources)
    logger.info(f"📦 Ingest result: {json.dumps(res, ensure_ascii=False)}")
    return {"ingest_result": res}

def task_notify_success(**context):
    cfg = context["cfg"]
    note_cfg = cfg.get("notifications", {})
    ncfg = NotificationConfig(**note_cfg) if note_cfg else NotificationConfig.from_env()
    svc = NotificationService(ncfg)
    res = context["prev"]["ingest_result"]
    ok = [r for r in res if "error" not in r]
    err = [r for r in res if "error" in r]

    subject = f"OMEGA Ingest OK ({len(ok)} ✅ / {len(err)} ❌)"
    body = json.dumps(res, ensure_ascii=False, indent=2)
    msg = NotificationMessage(subject=subject, body=body, severity=Severity.INFO, tags=["ingest", "omega"])
    svc.send(msg)
    return {"notified": True}

def task_notify_failure(**context):
    cfg = context["cfg"]
    note_cfg = cfg.get("notifications", {})
    ncfg = NotificationConfig(**note_cfg) if note_cfg else NotificationConfig.from_env()
    svc = NotificationService(ncfg)
    err = context["error"]
    subject = "OMEGA Ingest FAILED"
    body = f"Error: {err}"
    msg = NotificationMessage(subject=subject, body=body, severity=Severity.CRITICAL, tags=["ingest", "omega"])
    svc.send(msg)
    return {"notified": True}

# ---------------------------- Workflows -------------------------------

def build_workflow_ingest(cfg: Dict[str, Any]) -> Workflow:
    return Workflow(
        name="ingest_kabala",
        tasks=[
            Task(name="ingest_data", fn=lambda **ctx: task_ingest_data(**ctx)),
            Task(name="notify_success", fn=lambda **ctx: task_notify_success(**ctx)),
        ],
    )

# ---------------------------- CLI -------------------------------------

def main():
    parser = argparse.ArgumentParser(description="OMEGA MCP Workflow Orchestrator")
    parser.add_argument("command", choices=["run"], help="Comando")
    parser.add_argument("--workflow", default="ingest_kabala", help="Nombre de workflow")
    parser.add_argument("--config", required=True, help="Ruta de archivo YAML/JSON de configuración")
    args = parser.parse_args()

    cfg = load_config(args.config)

    wf_map = {
        "ingest_kabala": build_workflow_ingest(cfg),
    }
    wf = wf_map.get(args.workflow)
    if not wf:
        raise ValueError(f"Workflow no encontrado: {args.workflow}")

    try:
        prev = wf.run(cfg=cfg, prev={})
    except Exception as e:
        logger.error(f"Workflow {wf.name} falló: {e}")
        logger.debug(traceback.format_exc())
        # Intentar notificar el fallo
        try:
            task_notify_failure(cfg=cfg, error=str(e))
        except Exception as e2:
            logger.error(f"No se pudo notificar fallo: {e2}")
        sys.exit(1)

    logger.info(f"✅ Workflow {wf.name} completado")

if __name__ == "__main__":
    main()
