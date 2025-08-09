import os
from integrations.whatsapp_client_enhanced import WhatsAppClient


if __name__ == "__main__":
    client = WhatsAppClient(
        token=os.getenv("WHATSAPP_TOKEN", ""),
        phone_number_id=os.getenv("WHATSAPP_PHONE_ID", ""),
        dry_run=not bool(os.getenv("WHATSAPP_TOKEN")),
    )
    to = os.getenv("WHATSAPP_ADMIN", "+00000000000")
    print(client.send_text(to, "Prueba de integración WhatsApp ✅"))


