from __future__ import annotations
import json
from datetime import datetime

class Critic:
    def reflect(self, state: dict, results: list, chosen_sig: str, out_path):
        safe = []
        for sig, *_, r in results:
            try:
                safe.append((sig, (r or {}).get("reward", 0.0)))
            except Exception:
                safe.append((sig, 0.0))
        top = sorted(safe, key=lambda x: x[1], reverse=True)
        insight = {
            "ts": datetime.utcnow().isoformat(),
            "chosen": chosen_sig,
            "top": top,
            "note": "Mantener peso alto en neural_enhanced; revisar error de pickling si reaparece."
        }
        with open(out_path, "a") as f:
            f.write(json.dumps(insight) + "\n")
