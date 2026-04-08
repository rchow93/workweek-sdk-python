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

    def with_team(
        self,
        team_id: str,
        message: str,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Iterator[ChatEvent]:
        """Stream a message through a declaratively-provisioned team (TD-102 Phase D).

        Routes through the gateway's team-chat path
        (POST /api/v1/teams/{team_id}/chat/sessions/{session_id}/message)
        which uses the team's TeamPromptContext + agents + tools instead of the
        generic chat agent. The team's specialty + backstory + tool grants
        come from the declarative team spec.

        First call: creates a new chat session under the team if no session_id
        is given, yields a 'session' event with the new id, then streams.
        Reuse the session_id on subsequent calls to accumulate conversation
        history within the same session.

        Usage::

            session_id = None
            for event in client.chat.with_team(team_id="<uuid>", message="..."):
                if event.type == "session":
                    session_id = event.data["session_id"]
                elif event.type == "token":
                    print(event.content, end="", flush=True)

        Args:
            team_id: UUID of the team (from `client.post('/api/v1/teams/declare', ...)` or
                the admin's team provisioning step).
            message: The user message to send.
            session_id: Optional existing session id for conversation continuity.
                If omitted, a new session is created.
            title: Optional title for the new session (used only when session_id is None).

        Yields:
            ChatEvent — first 'session' (only on new session), then a sequence
            of 'token' events (each carrying one token of raw text), then
            'done' to terminate.

        Note:
            The team-chat endpoint streams raw text tokens via SSE (`data: <text>`),
            not JSON-encoded events like the generic /chat/message stream. This
            method normalizes them into ChatEvent objects so callers don't have
            to care about the wire format difference.
        """
        from workweek.client import WorkWeekAPIError

        # 1. Create a session if needed
        if not session_id:
            session = self._client.post(
                f"/api/v1/teams/{team_id}/chat/sessions",
                json={"title": title or "SDK chat session"},
            )
            session_id = session.get("id")
            if not session_id:
                raise WorkWeekAPIError(
                    500,
                    f"Team chat session creation returned no id: {session!r}",
                )
            yield ChatEvent("session", {"session_id": session_id, "team_id": team_id})

        # 2. Stream the message
        with self._client._http.stream(
            "POST",
            f"/api/v1/teams/{team_id}/chat/sessions/{session_id}/message",
            json={"message": message},
        ) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode(errors="replace")
                raise WorkWeekAPIError(resp.status_code, body)

            saw_done_event = False
            for line in resp.iter_lines():
                if not line:
                    # SSE event terminator (blank line) — emit done if we just
                    # saw `event: done` in the previous line.
                    if saw_done_event:
                        yield ChatEvent("done", {"session_id": session_id})
                        return
                    continue
                if line.startswith("event: done"):
                    saw_done_event = True
                    continue
                if line.startswith("event: error"):
                    saw_done_event = False
                    continue
                if line.startswith("data: "):
                    payload = line[6:]
                    if saw_done_event:
                        # `data: complete` after `event: done` — sentinel, not content
                        continue
                    # Raw token text (not JSON for team-chat — different format
                    # from /api/v1/chat/message)
                    yield ChatEvent("token", {"content": payload})

            # If the stream closed without an explicit done event, still emit
            # one so callers can rely on the terminator.
            yield ChatEvent("done", {"session_id": session_id})
