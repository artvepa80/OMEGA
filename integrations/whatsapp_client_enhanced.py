"""
¡Vamos a mejorar los archivos que componen la IA OMEGA!
Versión mejorada: WhatsAppClient con:
- Envío de texto, plantilla y documento
- Manejo de errores con backoff simple
- Compatibilidad requests/urllib
- Tipado y logging
"""

from __future__ import annotations
import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import requests  # type: ignore
    _HTTP = "requests"
except Exception:
    import urllib.request  # type: ignore
    import urllib.error  # type: ignore
    _HTTP = "urllib"


class WhatsAppClient:
    def __init__(
        self,
        token: str,
        phone_number_id: str,
        api_version: str = "v20.0",
        base_url: str = "https://graph.facebook.com",
        dry_run: bool = False,
        timeout: int = 15,
    ):
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self.timeout = timeout

    def _endpoint(self, path: str) -> str:
        return f"{self.base_url}/{self.api_version}/{self.phone_number_id}/{path.lstrip('/')}"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _post(self, url: str, payload: Dict[str, Any], retries: int = 2) -> Dict[str, Any]:
        if self.dry_run:
            logger.info("[WA DRY-RUN] POST %s %s", url, json.dumps(payload))
            return {"dry_run": True, "ok": True}

        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                if _HTTP == "requests":
                    resp = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
                    if resp.status_code // 100 != 2:
                        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
                    return resp.json() if resp.text else {"ok": True}
                else:
                    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=self._headers())
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # type: ignore
                        data = resp.read().decode("utf-8")
                        return json.loads(data) if data else {"ok": True}
            except Exception as e:  # noqa: BLE001
                last_exc = e
                logger.warning("WhatsApp POST fallo (intento %d/%d): %s", attempt + 1, retries + 1, e)
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"WhatsApp POST error definitivo: {last_exc}")

    # === Métodos públicos ===
    def send_text(self, to_e164: str, text: str) -> Dict[str, Any]:
        url = self._endpoint("messages")
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164,
            "type": "text",
            "text": {"body": text[:4000]},
        }
        return self._post(url, payload)

    def send_template(self, to_e164: str, template_name: str, lang: str = "es") -> Dict[str, Any]:
        url = self._endpoint("messages")
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164,
            "type": "template",
            "template": {"name": template_name, "language": {"code": lang}},
        }
        return self._post(url, payload)

    def send_document(self, to_e164: str, doc_url: str, caption: str = "") -> Dict[str, Any]:
        url = self._endpoint("messages")
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164,
            "type": "document",
            "document": {"link": doc_url, "caption": caption[:1024]},
        }
        return self._post(url, payload)


