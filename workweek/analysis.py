"""Analysis module — BACI and statistical analysis."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class AnalysisModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def run_baci(self, slug: str, params: dict) -> dict:
        """Run BACI (Before-After-Control-Impact) analysis for an app."""
        return self._client.post(f"/api/v1/app-api/{slug}/baci", json=params)
