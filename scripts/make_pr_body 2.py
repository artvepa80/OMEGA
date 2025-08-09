#!/usr/bin/env python3
"""
Genera el cuerpo de PR para OMEGA según la rama actual.
- Detecta rama: omega/refactor-imports, omega/logging-unification, etc.
- Lista archivos tocados vs rama base indicada.
- (Opcional) ejecuta pytest -m smoke y main.py --dry-run --limit 5 y anexa la evidencia.

Uso:
  python3 scripts/make_pr_body.py
  python3 scripts/make_pr_body.py --base develop --limit 5
  python3 scripts/make_pr_body.py --skip-tests

Requisitos: stdlib y git disponible.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import subprocess
from textwrap import dedent


TEMPLATES = {
    "omega/refactor-imports": {
        "title": "[OMEGA] Normalize imports – repo",
        "objective": (
            "Convertir todos los imports relativos a absolutos desde la raíz "
            "para evitar sys.path hacks y ambigüedades."
        ),
        "checklist": [
            "Imports absolutos (sin `.` ni `..`)",
            "Sin cambios de **firmas públicas** ni rutas",
            "Pasa `pytest -m smoke`",
            "`main.py --dry-run --limit 5` OK",
            "Logs consistentes en `logs/omega.log`",
        ],
        "evidence_cmds": ["pytest -q -m smoke", "python3 main.py --dry-run --limit {limit}"],
    },
    "omega/logging-unification": {
        "title": "[OMEGA] Unify logging – core/, modules/, utils/",
        "objective": "Centralizar logging con utils.logging.get_logger(__name__) y RotatingFile + Stream.",
        "checklist": [
            "Sin `print()` en core",
            "RotatingFileHandler (10MB/5)",
            "Nivel vía `OMEGA_LOGLEVEL`",
            "Smoke tests OK",
            "Dry-run OK",
        ],
        "evidence_cmds": ["pytest -q -m smoke", "python3 main.py --dry-run --limit {limit}"],
    },
    "omega/typed-errors": {
        "title": "[OMEGA] Typed errors & IO guards – core/, modules/",
        "objective": "Tipar puntos de I/O y re-lanzar como utils.errors.* con exc_info=True.",
        "checklist": [
            "Errores tipados en I/O",
            "Log con `exc_info=True`",
            "Smoke OK, dry-run OK",
            "Sin cambios de firmas públicas",
        ],
        "evidence_cmds": [
            "pytest -q -m smoke",
            "python3 main.py --dry-run --limit {limit}",
            "tail -n 50 logs/omega.log || true",
        ],
    },
    "omega/validation-cleaner": {
        "title": "[OMEGA] History validation – utils/validation.py",
        "objective": "Implementar detect_columns(df) y clean_historial_df(df) robustos.",
        "checklist": [
            "Funciones nuevas con docstrings y tests",
            "No se modifican esquemas externos",
            "Smoke OK y dry-run OK",
        ],
        "evidence_cmds": [
            "pytest -q -m smoke -k validation",
            "python3 main.py --dry-run --limit {limit}",
        ],
    },
    "omega/predictor-helpers": {
        "title": "[OMEGA] Predictor helpers extraction – core/predictor.py",
        "objective": "Extraer funciones puras de run_all_models() a core/predictor_helpers.py sin cambiar la API.",
        "checklist": [
            "Firma pública intacta",
            "Salida `{combination, score, svi, model}`",
            "Smoke OK y dry-run OK",
        ],
        "evidence_cmds": [
            "pytest -q -m smoke -k predictor",
            "python3 main.py --dry-run --limit {limit}",
        ],
    },
    "omega/consensus-validate": {
        "title": "[OMEGA] Consensus hardening – core/consensus_engine.py",
        "objective": "Blindar validate_combination(...) y log de causas de rechazo.",
        "checklist": ["API inalterada", "Rechazos logueados", "Smoke OK"],
        "evidence_cmds": [
            "pytest -q -m smoke -k validate",
            "tail -n 50 logs/omega.log || true",
        ],
    },
    "omega/ghost-penalty": {
        "title": "[OMEGA] Ghost RNG penalty – modules/filters/",
        "objective": "Penalización por patrón de seed sospechoso (fast-path).",
        "checklist": ["Sin imports circulares", "Latencia baja (fast-path)", "Smoke OK"],
        "evidence_cmds": ["pytest -q -m smoke -k ghost"],
    },
    "omega/transformer-3inputs": {
        "title": "[OMEGA] Transformer: 3 inputs – transformer_data_utils.py, predict_transformers_v2.py",
        "objective": "Asegurar que LotteryTransformer reciba (numbers, temporal, positions).",
        "checklist": [
            "Sin cambios en la interfaz del modelo",
            "Shapes logueadas",
            "Entrenamiento/predicción no crashea",
        ],
        "evidence_cmds": [
            "python3 modules/train_transformer_v16.py || true",
            "tail -n 100 logs/omega.log || true",
        ],
    },
    "omega/main-flags": {
        "title": "[OMEGA] Main flags & seed – main.py",
        "objective": "Agregar --dry-run, --limit y lectura de seed global OMEGA_SEED.",
        "checklist": [
            "Dry-run desactiva exportadores",
            "Limit recorta resultados",
            "Smoke OK",
        ],
        "evidence_cmds": ["python3 main.py --dry-run --limit {limit}"],
    },
    "omega/combiner-v2": {
        "title": "[OMEGA] Master combiner v2.0 – modules/utils/combinador_maestro.py",
        "objective": "Consolidación 70%/30%; excluir hot últimos 3; flag de riesgo.",
        "checklist": [
            "Firma pública intacta",
            "Export combinacion_maestra.csv (no en dry-run)",
            "Smoke OK",
        ],
        "evidence_cmds": [
            "pytest -q -m smoke -k maestro",
            "python3 main.py --dry-run --limit {limit}",
        ],
    },
    "omega/smoke-tests": {
        "title": "[OMEGA] Smoke tests – tests/",
        "objective": "Añadir suite mínima para detectar roturas temprano.",
        "checklist": [
            "Tests sin dependencias externas",
            "Rápidos (<10s)",
            "Documentados",
        ],
        "evidence_cmds": ["pytest -q -m smoke"],
    },
    "omega/ci-local": {
        "title": "[OMEGA] Local CI script – scripts/ci_local.sh",
        "objective": "Script express para validar PRs localmente.",
        "checklist": [
            "Script con set -euo pipefail",
            "Ejecutable (chmod +x)",
            "Documentado en ARCHITECTURE.md",
        ],
        "evidence_cmds": ["bash scripts/ci_local.sh || true"],
    },
    "omega/pr-audit": {
        "title": "[OMEGA] PR audit – repo",
        "objective": "Auditoría automática de PRs con checklist y resumen de evidencia.",
        "checklist": [
            "Template visible por defecto",
            "Acciones corren en PR",
            "Salida de smoke y dry-run anexada",
        ],
        "evidence_cmds": [],
    },
}


def run(cmd: str, timeout: int = 180) -> str:
    try:
        out = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT, timeout=timeout
        )
        return out.decode("utf-8", errors="ignore").strip()
    except subprocess.CalledProcessError as e:
        return (
            f"$ {cmd}\n(exit {e.returncode})\n"
            f"{e.output.decode('utf-8', errors='ignore')}"
        ).strip()
    except Exception as e:
        return f"$ {cmd}\n{type(e).__name__}: {e}"


def current_branch() -> str:
    return run("git rev-parse --abbrev-ref HEAD").splitlines()[0].strip()


def changed_files(base: str) -> str:
    return run(f"git diff --name-only {base}...HEAD")


def pick_template(branch: str) -> dict:
    tpl = TEMPLATES.get(branch)
    if tpl:
        return tpl
    for key in TEMPLATES:
        if branch.startswith(key):
            return TEMPLATES[key]
    return {
        "title": f"[OMEGA] {branch} – cambios",
        "objective": "Refactor o mejora en OMEGA (template genérico).",
        "checklist": [
            "Imports absolutos (sin `.` ni `..`)",
            "Sin cambios de **firmas públicas** ni rutas",
            "Sin `print()` en core (solo `get_logger`)",
            "Errores tipados (`utils.errors.*`) con `exc_info=True`",
            "Pasa `pytest -m smoke`",
            "`main.py --dry-run --limit 5` OK",
        ],
        "evidence_cmds": ["pytest -q -m smoke", "python3 main.py --dry-run --limit {limit}"],
    }


def pr_markdown(branch: str, base: str, limit: int, skip_tests: bool) -> str:
    template = pick_template(branch)
    files = changed_files(base)
    files_md = (
        "\n".join(f"- {line}" for line in files.splitlines())
        if files.strip()
        else "_(sin cambios detectados)_"
    )

    evidence = ""
    if not skip_tests:
        cmds = [c.format(limit=limit) for c in template.get("evidence_cmds", [])]
        chunks = []
        for c in cmds:
            chunks.append(f"```bash\n$ {c}\n{run(c)}\n```")
        if chunks:
            evidence = "\n\n## Evidencia\n" + "\n\n".join(chunks)

    checklist_md = "\n".join(f"- [ ] {item}" for item in template["checklist"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body = f"""# {template['title']}

## Objetivo
{template['objective']}

## Checklist (no merges si algo falla)
{checklist_md}

## Archivos tocados
{files_md}
{evidence}

## Cómo probar
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
bash scripts/ci_local.sh || true
```

Notas
- Rama: {branch}
- Base: {base}
- Generado: {now}

## Plan de rollback
- git revert -m 1 <merge_commit_sha>
"""
    return dedent(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default="origin/main",
        help="Rama base para calcular diff (por defecto origin/main)",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Límite para dry-run de main.py",
    )
    ap.add_argument(
        "--skip-tests",
        action="store_true",
        help="No ejecutar comandos de evidencia",
    )
    args = ap.parse_args()

    branch = current_branch()
    md = pr_markdown(branch=branch, base=args.base, limit=args.limit, skip_tests=args.skip_tests)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


