#!/usr/bin/env python3
"""
CLI unificado OMEGA (enhanced):
- omega notify --via whatsapp --msg "..." [--to +51XXXX,+57YYYY] [--dry-run]
"""

from __future__ import annotations
import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omega.cli")


def _split_list(val: str) -> list[str]:
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def cmd_notify(args: argparse.Namespace) -> int:
    via = args.via.lower()
    msg = args.msg.strip()
    recipients = _split_list(args.to) or _split_list(os.getenv("WHATSAPP_ADMIN", ""))
    if not recipients:
        logger.error("No hay destinatarios. Usa --to +E164 o env WHATSAPP_ADMIN.")
        return 2

    if via == "whatsapp":
        try:
            from integrations.whatsapp_client_enhanced import WhatsAppClient
        except Exception as e:  # noqa: BLE001
            logger.error("Falta módulo WhatsAppClient: %s", e)
            return 2

        client = WhatsAppClient(
            token=os.getenv("WHATSAPP_TOKEN", ""),
            phone_number_id=os.getenv("WHATSAPP_PHONE_ID", ""),
            dry_run=args.dry_run or not bool(os.getenv("WHATSAPP_TOKEN")),
        )
        ok = True
        for r in recipients:
            try:
                client.send_text(r, msg)
                logger.info("Enviado a %s", r)
            except Exception as e:  # noqa: BLE001
                logger.error("Falló envío a %s: %s", r, e)
                ok = False
        return 0 if ok else 1

    logger.error("Canal no soportado: %s", via)
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="omega", description="CLI OMEGA")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("notify", help="Enviar notificaciones")
    n.add_argument("--via", default="whatsapp", choices=["whatsapp"], help="Canal de notificación")
    n.add_argument("--msg", required=True, help="Mensaje a enviar")
    n.add_argument("--to", help="Destinatarios E.164 separados por coma. Si vacío, usa WHATSAPP_ADMIN")
    n.add_argument("--dry-run", action="store_true", help="No envía; solo log")
    n.set_defaults(func=cmd_notify)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


