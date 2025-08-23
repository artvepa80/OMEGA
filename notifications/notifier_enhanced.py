from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Protocol

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def notify(self, message: str) -> None: ...


@dataclass
class WhatsAppNotifier:
    client: any
    recipients: List[str]

    def notify(self, message: str) -> None:
        for r in self.recipients:
            try:
                self.client.send_text(r, message)
            except Exception as e:  # noqa: BLE001
                logger.warning("WA notify fallo para %s: %s", r, e)


