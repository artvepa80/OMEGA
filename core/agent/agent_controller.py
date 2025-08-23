from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from .planner import Planner
from .executor import Executor
from .evaluator import Evaluator
from .memory import Memory
from .policies.bandit import UCB1Policy
from .critic import Critic

CFG = Path("config/agent_policy.json")

class AgentController:
    def __init__(self, cfg_path=CFG):
        self.policy_cfg = json.loads(Path(cfg_path).read_text())
        self.planner = Planner(self.policy_cfg)
        self.executor = Executor()
        self.evaluator = Evaluator(self.policy_cfg)
        self.memory = Memory(Path("results/agent_memory.parquet"))
        self.policy = UCB1Policy()
        self.critic = Critic()

    def _sig(self, cfg: dict) -> str:
        return hashlib.md5(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:10]

    def cycle(self):
        state = self.memory.summarize(last_k=50)
        candidates = self.planner.propose(state, n=self.policy_cfg["max_experiments_per_cycle"])
        results = []
        for cfg in candidates:
            run_out = self.executor.run(cfg)
            eval_out = self.evaluator.score(run_out, baseline_profile=self.policy_cfg["baseline_profile"])
            sig = self._sig(cfg)
            results.append((sig, cfg, run_out, eval_out))
            self.memory.log(sig, cfg, run_out, eval_out)

        # seleccionar mejor
        arms = {}
        for sig, cfg, run_out, eval_out in results:
            if isinstance(eval_out, dict) and "reward" in eval_out:
                arms[sig] = eval_out["reward"]
            else:
                # Fallback en caso de eval_out inválido
                arms[sig] = 0.5
        chosen_sig = self.policy.select(arms)
        chosen_cfg = next(cfg for sig, cfg, *_ in results if sig == chosen_sig)

        # aplicar cambios (p.ej. actualizar pesos del ensemble)
        self.executor.apply(chosen_cfg, guardrails=self.policy_cfg["guardrails"])

        # reflexión
        self.critic.reflect(state, results, chosen_sig, out_path=Path("results/agent_decisions.jsonl"))

    def run_forever(self):
        every = self.policy_cfg["schedule_seconds"]
        while True:
            try:
                self.cycle()
            except Exception as e:
                print(f"[AGENT] error ciclo: {e}")
            time.sleep(every)

if __name__ == "__main__":
    AgentController().run_forever()
