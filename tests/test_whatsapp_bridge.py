import os
import json
from fastapi.testclient import TestClient

# Preparar entorno mínimo (modo dry-run)
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "omega-verify")
os.environ.setdefault("WHATSAPP_TOKEN", "DUMMY")  # usado para evitar llamadas reales
os.environ.setdefault("WHATSAPP_PHONE_ID", "DUMMY")
os.environ.setdefault("VERIFY_SIGNATURE", "false")

from tools.whatsapp_bridge_enhanced import app  # noqa: E402

client = TestClient(app)


def test_verify():
    r = client.get("/webhook", params={"hub.verify_token": "omega-verify", "hub.challenge": "123"})
    assert r.status_code == 200
    assert r.text == "123"


def test_inbound_minimal():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "51972514235",
                                    "id": "wamid.ID",
                                    "timestamp": "1690000000",
                                    "text": {"body": "estado"},
                                    "type": "text",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    r = client.post("/webhook", data=json.dumps(payload))
    assert r.status_code == 200
    assert r.json().get("ok") is True


