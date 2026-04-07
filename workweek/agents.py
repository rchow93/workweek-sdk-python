"""Agents module — manage saved agents."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class AgentsModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def list(self, limit: int = 50, offset: int = 0) -> dict:
        """List saved agents."""
        return self._client.get("/api/v1/agents", params={"limit": limit, "offset": offset})

    def get(self, agent_id: str) -> dict:
        """Get agent details."""
        return self._client.get(f"/api/v1/agents/{agent_id}")

    def create(self, data: dict) -> dict:
        """Create a new agent."""
        return self._client.post("/api/v1/agents", json=data)
