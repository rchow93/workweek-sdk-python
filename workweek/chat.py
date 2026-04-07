"""Chat module — conversational AI with SSE streaming.

Wraps the chat-service /api/v1/chat/message Server-Sent Events stream into
a Python iterator of typed events. Supports tool-calling progress
(tool_start/tool_end) and incremental token output.
"""

from __future__ import annotations
import json
from typing import TYPE_CHECKING, Iterator, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class ChatEvent:
    """A single SSE event from the chat-service /message stream.

    Event types:
        session     — initial session id confirmation
        tool_start  — an MCP tool invocation began
        tool_end    — an MCP tool invocation finished (with duration_ms)
        token       — a partial assistant message token
        done        — stream finished (final event)
        error       — an error occurred mid-stream
    """

    def __init__(self, event_type: str, data: dict):
        self.type = event_type
        self.data = data

    @property
    def content(self) -> str:
        """For 'token' events, the partial text. Empty string otherwise."""
        return self.data.get("content", "") if self.type == "token" else ""

    def __repr__(self) -> str:
        return f"ChatEvent(type={self.type!r}, data={self.data!r})"


class ChatModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def stream(
        self,
        message: str,
        session_id: Optional[str] = None,
    ) -> Iterator[ChatEvent]:
        """Stream a chat message response from chat-service /message.

        Yields ChatEvent objects until the 'done' event is received.

        Usage::

            for event in client.chat.stream("How many food trucks are active?"):
                if event.type == "token":
                    print(event.content, end="", flush=True)
                elif event.type == "tool_start":
                    print(f"\\n[tool: {event.data.get('tool_name')}]")

        Args:
            message: The user message to send.
            session_id: Optional session id for conversation continuity. If
                omitted, the server creates a new session and returns its id
                in the first 'session' event.

        Yields:
            ChatEvent — one per SSE event from the upstream stream.
        """
        # Import lazily to avoid circular import on package init.
        from workweek.client import WorkWeekAPIError

        payload: dict = {"message": message}
        if session_id:
            payload["session_id"] = session_id

        with self._client._http.stream(
            "POST",
            "/api/v1/chat/message",
            json=payload,
        ) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode(errors="replace")
                raise WorkWeekAPIError(resp.status_code, body)

            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue

                event_type = data.get("type", "unknown")
                yield ChatEvent(event_type, data)
                if event_type == "done":
                    return

    def send(self, message: str, session_id: Optional[str] = None) -> str:
        """Convenience: collect all tokens from stream() into a single string.

        Returns the assembled assistant message text. Use stream() if you need
        intermediate tool events or token-by-token rendering.
        """
        chunks: list[str] = []
        for event in self.stream(message, session_id=session_id):
            if event.type == "token":
                chunks.append(event.content)
        return "".join(chunks)
