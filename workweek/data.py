"""Data module — query datasets and list available data."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class DataModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def list_datasets(self, org_id: int) -> list[dict]:
        """List all Iceberg datasets for an organization."""
        return self._client.get(f"/api/v1/datasets", params={"org_id": org_id})

    def query(self, org_id: int, dataset_name: str, sql: str) -> dict:
        """Execute a DuckDB SQL query against an Iceberg dataset."""
        return self._client.post(
            "/api/v1/data/appdata/query",
            json={"org_id": org_id, "dataset_name": dataset_name, "sql": sql},
        )

    def get_schema(self, dataset_name: str) -> dict:
        """Get schema for a dataset."""
        return self._client.get(f"/api/v1/datasets/{dataset_name}")
