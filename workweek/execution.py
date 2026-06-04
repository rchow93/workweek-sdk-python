"""Execution module — run queries and track executions."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class ExecutionModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def run_query(self, query: str, team_id: Optional[int] = None) -> dict:
        """Submit a query for execution."""
        payload: dict = {"query": query}
        if team_id:
            payload["team_id"] = team_id
        return self._client.post("/api/v1/query", json=payload)

    def get_status(self, execution_id: str) -> dict:
        """Get execution status."""
        return self._client.get(f"/api/v1/executions/{execution_id}")

    def list_executions(self, limit: int = 20, offset: int = 0) -> dict:
        """List recent executions."""
        return self._client.get("/api/v1/executions", params={"limit": limit, "offset": offset})
