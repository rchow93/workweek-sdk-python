"""Base HTTP client for WorkWeek API."""

from __future__ import annotations

import httpx

from workweek.data import DataModule
from workweek.apps import AppsModule
from workweek.agents import AgentsModule
from workweek.analysis import AnalysisModule
from workweek.knowledge import KnowledgeModule
from workweek.chat import ChatModule
from workweek.teams import TeamsModule
from workweek.execution import ExecutionModule
from workweek.places import PlacesModule


class WorkWeekAPIError(Exception):
    """Raised when the WorkWeek API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class WorkWeekClient:
    """WorkWeek Python SDK client.

    Usage::

        from workweek import WorkWeekClient

        client = WorkWeekClient(
            base_url="https://gw.askvai.com",
            api_key="wk_rpt_...",
        )
        result = client.data.query(
            dataset="sf_food_trucks_permits",
            sql="SELECT COUNT(*) AS n FROM tbl WHERE status = 'APPROVED'",
        )
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        # TD-125: chat streams (chat.stream, chat.with_team) can run well
        # past 30s for multi-tool turns. Give streaming endpoints a
        # longer read timeout; short connect timeout keeps cold-start
        # failure detection quick. Non-stream requests still use the
        # caller's `timeout` value via per-request overrides in modules.
        stream_timeout = httpx.Timeout(
            connect=10.0,
            read=120.0,
            write=timeout,
            pool=timeout,
        )
        self._http = httpx.Client(
            base_url=self._base_url,
            headers={"X-API-Key": api_key},
            timeout=stream_timeout,
        )

        # Module accessors
        self.data = DataModule(self)
        self.apps = AppsModule(self)
        self.agents = AgentsModule(self)
        self.analysis = AnalysisModule(self)
        self.knowledge = KnowledgeModule(self)
        self.chat = ChatModule(self)
        self.teams = TeamsModule(self)
        self.execution = ExecutionModule(self)
        self.places = PlacesModule(self)  # TD-107b — Google Places via Tier 3 BYOK

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated request and return JSON response."""
        resp = self._http.request(method, path, **kwargs)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise WorkWeekAPIError(resp.status_code, detail)
        if resp.status_code == 204:
            return {}
        return resp.json()

    def get(self, path: str, **kwargs) -> dict:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> dict:
        return self._request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs) -> dict:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> dict:
        return self._request("DELETE", path, **kwargs)

    def get_bytes(self, path: str, **kwargs) -> tuple[bytes, str]:
        """GET a binary response (e.g. DOCX export). Returns (body, content_type)."""
        resp = self._http.get(path, **kwargs)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text[:500]
            raise WorkWeekAPIError(resp.status_code, detail)
        content_type = resp.headers.get("content-type", "application/octet-stream")
        return resp.content, content_type

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
