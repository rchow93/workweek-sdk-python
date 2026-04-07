"""Apps module — tenant app config and page data."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class AppsModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def get_config(self, slug: str) -> dict:
        """Get full app config (pages, charts, branding) for a tenant app."""
        return self._client.get(f"/api/v1/app-api/{slug}/config")

    def get_page_data(self, slug: str, page: str, filters: Optional[dict] = None) -> dict:
        """Get chart data for a specific page, optionally with filters."""
        params = {}
        if filters:
            params.update(filters)
        return self._client.get(f"/api/v1/app-api/{slug}/page/{page}/data", params=params)

    def get_filter_options(self, slug: str, page: str, filter_key: str) -> dict:
        """Get available filter options for a page filter."""
        return self._client.get(
            f"/api/v1/app-api/{slug}/page/{page}/filter-options",
            params={"filter_key": filter_key},
        )

    def update_frontend_config(self, slug: str, config: dict) -> dict:
        """Update the frontend config for an app (pages, charts, branding)."""
        return self._client.patch(
            f"/api/v1/app-api/{slug}/frontend-config",
            json=config,
        )

    def list_apps(self) -> dict:
        """List all apps for the authenticated organization."""
        return self._client.get("/api/v1/apps")
