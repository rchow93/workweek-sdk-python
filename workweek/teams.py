"""Teams module — team management."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class TeamsModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def list(self) -> dict:
        """List teams."""
        return self._client.get("/api/v1/teams")

    def get(self, team_id: int) -> dict:
        """Get team details."""
        return self._client.get(f"/api/v1/teams/{team_id}")
