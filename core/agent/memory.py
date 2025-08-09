from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

class Memory:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, sig: str, cfg: dict, run_out: dict, eval_out: dict):
        row = {
            "ts": datetime.utcnow().isoformat(),
            "sig": sig,
            "cfg": json.dumps(cfg, sort_keys=True),
            "reward": (eval_out or {}).get("reward", 0.0),
            "quality_ok": (eval_out or {}).get("quality_ok", False),
            "signals": json.dumps((eval_out or {}).get("signals", {})),
            "returncode": run_out["returncode"]
        }
        df_new = pd.DataFrame([row])
        
        if self.path.exists():
            # Leer existente y concatenar
            try:
                df_existing = pd.read_parquet(self.path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined.to_parquet(self.path, index=False)
            except Exception:
                # Si falla lectura, sobrescribir
                df_new.to_parquet(self.path, index=False)
        else:
            df_new.to_parquet(self.path, index=False)

    def summarize(self, last_k=50) -> dict:
        if not self.path.exists():
            return {"recent_rewards": [], "n": 0}
        df = pd.read_parquet(self.path).tail(last_k)
        return {"recent_rewards": df["reward"].tolist(), "n": int(df.shape[0])}
