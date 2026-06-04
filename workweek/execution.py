"""Execution module — run queries, deep research, and track executions."""

from __future__ import annotations
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from workweek.client import WorkWeekClient


class ExecutionModule:
    def __init__(self, client: WorkWeekClient):
        self._client = client

    def run_query(
        self,
        query: str,
        team_id: Optional[str] = None,
        path_type: Optional[str] = None,
        template_id: Optional[str] = None,
        execution_metadata: Optional[dict] = None,
        custom_instructions: Optional[str] = None,
    ) -> dict:
        """Submit a query for execution.

        Args:
            query: The research query or task description.
            team_id: Team ID to scope the execution to.
            path_type: Execution path — "crew", "single", "architect", "deep_research", "chat".
            template_id: Research template ID (e.g. "candidate_dossier", "market_analysis").
            execution_metadata: Additional metadata passed to the execution engine.
            custom_instructions: Free-form instructions injected into agent prompts.

        Returns:
            dict with execution_id, status, message.
        """
        payload: dict = {"query": query}
        if team_id:
            payload["team_id"] = team_id
        if path_type:
            payload["path_type"] = path_type
        if custom_instructions:
            payload["custom_instructions"] = custom_instructions

        meta = dict(execution_metadata or {})
        if template_id:
            meta["template_id"] = template_id
        if meta:
            payload["execution_metadata"] = meta

        return self._client.post("/api/v1/query", json=payload)

    def run_research(
        self,
        query: str,
        template_id: Optional[str] = None,
        team_id: Optional[str] = None,
        max_steps: Optional[int] = None,
        custom_instructions: Optional[str] = None,
        execution_metadata: Optional[dict] = None,
    ) -> dict:
        """Submit a deep research query.

        Args:
            query: The research question or subject to investigate.
            template_id: Research template — "candidate_dossier", "market_analysis",
                "competitive_landscape", "technical_deep_dive", etc.
            team_id: Team ID to scope the execution to.
            max_steps: Override the template's default step budget (10-150).
            custom_instructions: Additional guidance for the research engine.
            execution_metadata: Additional metadata merged with template_id + max_steps.

        Returns:
            dict with execution_id, status, message.
        """
        meta: dict = dict(execution_metadata or {})
        if template_id:
            meta["template_id"] = template_id
        if max_steps is not None:
            meta["max_steps"] = max_steps

        return self.run_query(
            query=query,
            team_id=team_id,
            path_type="deep_research",
            execution_metadata=meta or None,
            custom_instructions=custom_instructions,
        )

    def wait_for_completion(
        self,
        execution_id: str,
        poll_interval: float = 10.0,
        timeout: float = 1800.0,
    ) -> dict:
        """Poll until execution completes or fails.

        Args:
            execution_id: The execution to wait for.
            poll_interval: Seconds between status checks (default 10s).
            timeout: Max seconds to wait (default 1800s / 30 min).

        Returns:
            Full execution dict with result.

        Raises:
            TimeoutError: If execution doesn't complete within timeout.
        """
        start = time.time()
        while True:
            data = self.get_status(execution_id)
            status = data.get("status", "")
            if status in ("completed", "failed"):
                return data
            if time.time() - start > timeout:
                raise TimeoutError(
                    f"Execution {execution_id} still '{status}' after {timeout}s"
                )
            time.sleep(poll_interval)

    def get_status(self, execution_id: str) -> dict:
        """Get execution status."""
        return self._client.get(f"/api/v1/executions/{execution_id}")

    def list_executions(self, limit: int = 20, offset: int = 0) -> dict:
        """List recent executions."""
        return self._client.get("/api/v1/executions", params={"limit": limit, "offset": offset})
