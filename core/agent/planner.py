from __future__ import annotations
import random, copy

class Planner:
    def __init__(self, policy_cfg: dict):
        self.policy_cfg = policy_cfg

    def _neighbors(self, base: dict):
        # pequeñas variaciones seguras en pesos y perfil SVI
        for delta in (-0.05, 0.0, 0.05):
            cfg = copy.deepcopy(base)
            w = cfg["ensemble_weights"]
            for k in w:
                w[k] = max(0.0, min(1.0, w[k] + delta*(1 if k=="neural_enhanced" else -1)))
            s = sum(w.values())
            for k in w: w[k] /= s or 1.0
            cfg["svi_profile"] = random.choice(["default","conservative","aggressive","neural_optimized"])
            yield cfg

    def _baseline_cfg(self):
        return {
            "svi_profile": self.policy_cfg.get("baseline_profile","default"),
            "ensemble_weights": {
                "neural_enhanced": 0.45,
                "transformer_deep": 0.15,
                "genetico": 0.15,
                "analizador_200": 0.12,
                "montecarlo": 0.05,
                "lstm_v2": 0.03,
                "clustering": 0.01
            },
            "filters": {"max_consecutivos": 3, "par_impar_balance": True},
            "seeds": [None]
        }

    def propose(self, state: dict, n: int = 3):
        base = self._baseline_cfg()
        cands = list(self._neighbors(base))
        random.shuffle(cands)
        return cands[:n]
