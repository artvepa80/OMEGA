# [OMEGA] {step_name} – {scope}

## Objetivo
Breve: ¿qué cambia y por qué?

## Checklist (no merges si algo falla)
- [ ] Imports absolutos (sin `.` ni `..`)
- [ ] Sin cambios de **firmas públicas** ni rutas
- [ ] Sin `print()` en core (solo `get_logger`)
- [ ] Errores tipados (`utils.errors.*`) con `exc_info=True`
- [ ] Pasa `pytest -m smoke`
- [ ] `main.py --dry-run --limit 5` OK
- [ ] No se tocaron esquemas CSV/JSON ni nombres de columnas
- [ ] Logs consistentes en `logs/omega.log`

## Cambios clave
- **Archivos tocados**: (lista corta)
- **Riesgos**: (qué podría romperse y por qué es bajo)
- **Compatibilidad**: (si hay deprecations o shims)

## Evidencia (pega outputs)
```bash
pytest -q -m smoke
# pega resumen ✓

python3 main.py --dry-run --limit 5
# pega primeras líneas de salida
```

## Cómo probar
1. python3 -m venv venv && source venv/bin/activate
2. pip install -r requirements.txt
3. bash scripts/ci_local.sh

## Plan de rollback
- Revert: `git revert -m 1 <merge_commit_sha>`
- Restaurar `requirements.txt` y limpiar cachés temporales (`.retrotracker_cache/`, `__pycache__/`)


