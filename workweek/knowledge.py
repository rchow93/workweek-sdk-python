"""Knowledge module — collections and document search."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class KnowledgeModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def list_collections(self) -> dict:
        """List knowledge collections."""
        return self._client.get("/api/v1/knowledge/collections")

    def search(self, query: str, collection_id: str | None = None) -> dict:
        """Search knowledge base."""
        params = {"q": query}
        if collection_id:
            params["collection_id"] = collection_id
        return self._client.get("/api/v1/knowledge/search", params=params)
