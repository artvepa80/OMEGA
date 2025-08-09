from __future__ import annotations
import re, json
from pathlib import Path

class Evaluator:
    def __init__(self, policy_cfg: dict):
        self.w = policy_cfg["reward_weights"]
        self.min_q = policy_cfg["min_quality_threshold"]

    def _extract_metric(self, stdout: str, pattern: str, default=0.0):
        m = re.search(pattern, stdout)
        if not m: return default
        try: return float(m.group(1))
        except: return default

    def score(self, run_out: dict, baseline_profile: str) -> dict:
        try:
            # Validar entrada
            if not isinstance(run_out, dict):
                return {"reward": 0.1, "quality_ok": False, "signals": {}, "error": "Invalid run_out"}
            
            stdout = run_out.get("stdout", "")
            returncode = run_out.get("returncode", 1)
            
            # Parsea señales del log (ya aparecen en tus logs)
            svi = self._extract_metric(stdout, r"SVI[:=]\s*([0-9.]+)", 0.7)
            filters_pass = 1.0 if "Generadas" in stdout else 0.5
            jackpot = self._extract_metric(stdout, r"Perfil detectado:\s*([0-9.]+)", 0.0)
            diversity = 0.8 if "✅ 17 combinaciones" in stdout else 0.5

            reward = (
                self.w.get("svi", 0.5)*svi +
                self.w.get("diversity", 0.2)*diversity +
                self.w.get("jackpot_profile", 0.2)*jackpot +
                self.w.get("filters_pass_rate", 0.1)*filters_pass
            )

            quality_ok = (svi >= self.min_q) and (returncode == 0)
            
            return {
                "reward": float(reward),
                "quality_ok": bool(quality_ok),
                "signals": {
                    "svi": float(svi),
                    "diversity": float(diversity),
                    "jackpot": float(jackpot),
                    "filters_pass": float(filters_pass)
                }
            }
            
        except Exception as e:
            # Fallback seguro en caso de cualquier error
            return {
                "reward": 0.1,
                "quality_ok": False,
                "signals": {"svi": 0.0, "diversity": 0.0, "jackpot": 0.0, "filters_pass": 0.0},
                "error": str(e)
            }
