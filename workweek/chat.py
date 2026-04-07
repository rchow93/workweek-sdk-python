"""Chat module — conversational AI."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class ChatModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def send_message(self, message: str, session_id: Optional[str] = None) -> dict:
        """Send a chat message."""
        payload: dict = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        return self._client.post("/api/v1/chat", json=payload)
