"""Data module — query Iceberg datasets via the WorkWeek SDK gateway.

Calls /api/v1/sdk/* endpoints (Widget path — structured, no LLM).
Auth via X-API-Key. BYOK + grants enforced at gateway.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class DataModule:
    def __init__(self, client: "WorkWeekClient"):
        self._client = client

    def query(
        self,
        dataset: str,
        sql: str,
        limit: Optional[int] = None,
    ) -> dict:
        """Execute a SELECT query against an Iceberg dataset.

        Args:
            dataset: Dataset name (e.g. ``"sf_food_trucks_permits"``).
            sql: DuckDB SELECT query. Use ``tbl`` as the table reference.
            limit: Optional row cap (1-500, defaults to 100 server-side).

        Returns:
            ``{"dataset": str, "row_count": int, "columns": [str], "rows": [dict]}``
        """
        payload: dict = {"dataset": dataset, "sql": sql}
        if limit is not None:
            payload["limit"] = limit
        return self._client.post("/api/v1/sdk/query", json=payload)

    def list_datasets(self) -> dict:
        """List Iceberg datasets accessible to the API key's organization.

        Returns:
            ``{"count": int, "datasets": [{"name": str, "row_count": int}]}``
        """
        return self._client.get("/api/v1/sdk/datasets")

    def get_schema(self, dataset: str) -> dict:
        """Get the column schema for a dataset.

        Args:
            dataset: Dataset name (e.g. ``"sf_food_trucks_permits"``).

        Returns:
            ``{"dataset": str, "columns": [str], "sample": dict | None}``
        """
        return self._client.get(f"/api/v1/sdk/datasets/{dataset}/schema")
