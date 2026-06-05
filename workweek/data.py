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

    def ask(self, question: str, dataset: str, limit: int = 100) -> dict:
        """NL→SQL — ask a natural language question against a dataset.

        Args:
            question: Natural language question (e.g. "How many approved food trucks?").
            dataset: Dataset name to query.
            limit: Max rows to return (default 100).

        Returns:
            ``{"dataset": str, "question": str, "sql": str, "columns": [str],
              "rows": [dict], "row_count": int, "explanation": str}``
        """
        return self._client.post(
            f"/api/v1/sdk/datasets/{dataset}/ask",
            json={"question": question, "limit": limit},
        )

    def list_dashboards(self) -> dict:
        """List dashboards visible to the API key's organization.

        Returns:
            ``{"count": int, "dashboards": [{"id": int, "name": str, ...}]}``
        """
        return self._client.get("/api/v1/sdk/dashboards")

    def export_dashboard(self, dashboard_id: int, format: str = "json") -> dict:
        """Export a dashboard as JSON or CSV.

        Args:
            dashboard_id: Dashboard ID to export.
            format: Export format — "json" or "csv".

        Returns:
            Dashboard data in the requested format.
        """
        return self._client.get(
            f"/api/v1/sdk/dashboards/{dashboard_id}/export",
            params={"format": format},
        )

    def ingest(self, dataset: str, s3_path: str, format: str = "parquet") -> dict:
        """Ingest data from S3 into an Iceberg dataset.

        Upload your data to S3 first, then call this to trigger ingestion.

        Args:
            dataset: Target dataset name.
            s3_path: S3 path to the source file (e.g. "s3://my-bucket/data.parquet").
            format: Source format — "parquet" or "csv".

        Returns:
            Ingestion job status.
        """
        return self._client.post(
            "/api/v1/sdk/ingest",
            json={"dataset": dataset, "s3_path": s3_path, "format": format},
        )
