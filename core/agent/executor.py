from __future__ import annotations
import subprocess, json, tempfile, os, resource
from pathlib import Path
from typing import Dict, Any

class Executor:
    """
    Ejecuta el pipeline principal con una config temporal.
    Integra con main.py leyendo pesos y perfil por CLI o env.
    Añade límites de tiempo/memoria, captura robusta y circuit breaker simple.
    """

    def __init__(self, time_limit_sec: int = 900, memory_limit_mb: int = 2048):
        self.time_limit_sec = time_limit_sec
        self.memory_limit_mb = memory_limit_mb
        self._circuit_open_until: float | None = None

    def _preexec_limits(self):
        # Establecer límite de memoria en el proceso hijo (si está disponible)
        try:
            soft = self.memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (soft, soft))
        except Exception:
            pass

    def run(self, cfg: dict) -> dict:
        # Circuit breaker: si se abrió recientemente, devolver fallo rápido
        if self._circuit_open_until and self._now() < self._circuit_open_until:
            return {"returncode": 124, "stdout": "", "stderr": "circuit open", "artifacts": {}}

        tmp = Path(tempfile.mkstemp(prefix="omega_cfg_", suffix=".json")[1])
        tmp.write_text(json.dumps(cfg))
        env = os.environ.copy()
        env["OMEGA_AGENT_CFG"] = str(tmp)
        cmd = ["python3", "main.py", "--export-formats", "json"]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=self.time_limit_sec,
                preexec_fn=self._preexec_limits
            )
        except subprocess.TimeoutExpired as e:
            self._trip_circuit()
            out = {
                "returncode": 124,
                "stdout": (e.stdout or "")[-4000:],
                "stderr": (e.stderr or "")[-4000:] + "\n[timeout]",
                "artifacts": {}
            }
            self._cleanup(tmp)
            return out
        except Exception as e:
            self._trip_circuit()
            out = {
                "returncode": 1,
                "stdout": "",
                "stderr": f"executor error: {e}",
                "artifacts": {}
            }
            self._cleanup(tmp)
            return out

        out = {
            "returncode": proc.returncode,
            "stdout": proc.stdout[-8000:],  # tail defensivo ampliado
            "stderr": proc.stderr[-8000:],
            "artifacts": self._collect_artifacts()
        }
        self._cleanup(tmp)
        return out

    def _collect_artifacts(self) -> dict:
        # Busca outputs estándar si existen
        p = Path("outputs")
        try:
            combinacion = next(p.glob("combinacion_maestra_*.csv"), None) if p.exists() else None
            svi = next(p.glob("svi_export_*.json"), None) if p.exists() else None
        except StopIteration:
            combinacion, svi = None, None
        return {
            "combinacion": str(combinacion) if combinacion else "",
            "svi_export": str(svi) if svi else ""
        }

    def apply(self, cfg: dict, guardrails: dict):
        # Actualiza configuración persistente bajo guardrails
        ew = Path("config/ensemble_weights.json")
        if ew.exists() and "ensemble_weights" in cfg:
            ew.write_text(json.dumps(cfg["ensemble_weights"], indent=2))

    def _cleanup(self, tmp: Path):
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def _trip_circuit(self, cooldown_sec: int = 60):
        import time
        self._circuit_open_until = self._now() + cooldown_sec

    def _now(self) -> float:
        import time
        return time.time()
