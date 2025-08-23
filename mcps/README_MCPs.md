# OMEGA MCPs (Enterprise-Grade)

Este paquete incluye tres módulos MCP listos para producción:

1) `notification_mcp.py`
   - Servicio desacoplado de notificaciones.
   - Canales: Consola, Email (SMTP), Slack/Discord por webhook.
   - Reintentos con backoff, logging estructurado, configuración por YAML o variables de entorno.
   - Uso rápido:
     ```python
     from notification_mcp import NotificationService, NotificationMessage, Severity, NotificationConfig
     cfg = NotificationConfig.from_env()
     svc = NotificationService(cfg)
     svc.send(NotificationMessage(subject="Ping", body="Hola", severity=Severity.INFO))
     ```

2) `lottery_data_mcp.py`
   - Ingesta de CSV/JSON/API con validación básica de estructura.
   - Particionado por fecha (YYYY/MM/DD), compresión (CSV.GZ) y metadatos (`.metadata.json`).
   - Uso:
     ```python
     from lottery_data_mcp import ProductionLotteryDataMCP, SourceConfig
     mcp = ProductionLotteryDataMCP(data_dir="data/lottery_ingestion")
     res = mcp.ingest([SourceConfig(kind="csv", name="kabala_hist_local", local_path="data/historial_kabala_github.csv")])
     print(res)
     ```

3) `workflow_automation_mcp.py`
   - Orquestador ligero (tipo DAG) con reintentos.
   - Integra ingestión + notificación.
   - CLI:
     ```bash
     python3 workflow_automation_mcp.py run --workflow ingest_kabala --config config_omega_mcp.yaml
     ```

## Variables de Entorno (opcionales)

- `OMEGA_SLACK_WEBHOOK`, `OMEGA_DISCORD_WEBHOOK`
- `OMEGA_SMTP_HOST`, `OMEGA_SMTP_PORT`, `OMEGA_SMTP_USER`, `OMEGA_SMTP_PASSWORD`, `OMEGA_SMTP_FROM`
- `OMEGA_NOTIFY_RECIPIENTS` (lista separada por comas)
- `OMEGA_NOTIFY_CONSOLE` (1/0), `OMEGA_NOTIFY_TIMEOUT`, `OMEGA_NOTIFY_MAX_RETRIES`, `OMEGA_NOTIFY_BACKOFF`

## Notas

- Si tienes `pyarrow` instalado puedes activar `write_parquet: true` en el YAML.
- `lottery_data_mcp` intenta mapear columnas con nombres flexibles (e.g., `Bolilla 1`, `n1`, `number1`). Si la validación cae por debajo de 0.8, revisa el mapeo de columnas.
- Integra fácilmente estos MCPs con `main.py` de OMEGA para pipelines de datos y alertas confiables.
