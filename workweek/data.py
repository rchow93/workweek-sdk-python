"""Data module — query Iceberg datasets via the WorkWeek SDK gateway.

All methods hit /api/v1/sdk/* endpoints, which derive org_id from the API key
and validate that SQL is SELECT-only. Use 'tbl' as the table reference in your
SQL — every dataset is exposed under that name.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class DataModule:
    def __init__(self, client: WorkWeekClient):
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
                Only SELECT statements are permitted; INSERT/UPDATE/DELETE/
                DROP/ALTER/etc. are rejected with HTTP 422.
            limit: Optional row cap (1-500, defaults to 100 server-side).

        Returns:
            ``{"dataset": str, "row_count": int, "columns": [str], "rows": [dict]}``

        Example::

            result = client.data.query(
                dataset="sf_food_trucks_permits",
                sql="SELECT facilitytype, COUNT(*) AS n FROM tbl "
                    "WHERE status = 'APPROVED' GROUP BY facilitytype",
            )
            for row in result["rows"]:
                print(row)
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
        """Get the column schema for a dataset by sampling its first row.

        Args:
            dataset: Dataset name (e.g. ``"sf_food_trucks_permits"``).

        Returns:
            ``{"dataset": str, "columns": [str], "sample": dict | None}``
        """
        return self._client.get(f"/api/v1/sdk/datasets/{dataset}/schema")
