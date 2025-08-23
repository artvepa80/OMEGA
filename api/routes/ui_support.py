from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os, json, subprocess, shlex
from pathlib import Path

router = APIRouter(prefix="/ui", tags=["ui-support"])


class PredictRequest(BaseModel):
    mode: str = "hybrid"
    top_n: Optional[int] = 3


@router.post("/predict")
def ui_predict(req: PredictRequest):
    from omega_hybrid_integration import OmegaHybridSystem  # tu clase híbrida
    hs = OmegaHybridSystem()
    hs.initialize_systems()
    res = hs.generate_prediction(mode=req.mode)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("errors", ["unknown"]))
    return res


class BacktestRequest(BaseModel):
    data: str = "data/historial_kabala_github_fixed.csv"
    models: str = "consensus,transformer_deep,lstm_v2,genetico,montecarlo,apriori"
    windows: str = "rolling_200"
    top_n: int = 10
    seed: int = 42
    out: str = "results/accuracy_analysis/run_ui"


@router.post("/eval/backtest")
def ui_backtest(req: BacktestRequest, bg: BackgroundTasks):
    outdir = Path(req.out)
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = (
        f"python -m tools.eval_harness.cli backtest "
        f"--data {shlex.quote(req.data)} "
        f"--models {shlex.quote(req.models)} "
        f"--windows {shlex.quote(req.windows)} "
        f"--top_n {req.top_n} "
        f"--seed {req.seed} "
        f"--out {shlex.quote(req.out)}"
    )

    def run_job():
        subprocess.run(cmd, shell=True, check=False)

    bg.add_task(run_job)
    return {"status": "started", "cmd": cmd, "out": str(outdir)}


@router.get("/outputs/list")
def list_outputs(ext: Optional[str] = None) -> Dict[str, List[str]]:
    base_dirs = [Path("outputs"), Path("results/accuracy_analysis")]
    files: List[str] = []
    for d in base_dirs:
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file() and (not ext or p.suffix.lower() == f".{ext.lower()}"):
                    files.append(str(p))
    return {"files": sorted(files)}


@router.get("/outputs/get")
def get_output(path: str):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "file not found")
    return {"path": str(p.resolve())}


class TwilioMsg(BaseModel):
    to: Optional[str] = None
    body: str


@router.post("/integrations/twilio/test")
def twilio_test(msg: TwilioMsg):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM_NUMBER")
    to_num = msg.to or os.getenv("TWILIO_TO_NUMBER")
    if not all([sid, token, from_num, to_num]):
        raise HTTPException(400, "Twilio env vars missing")
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        r = client.messages.create(to=to_num, from_=from_num, body=msg.body)
        return {"sid": r.sid, "status": r.status}
    except Exception as e:
        raise HTTPException(500, f"Twilio error: {e}")


