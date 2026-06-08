"""Pydantic models for the switch contract."""
from typing import Optional

from pydantic import BaseModel


class DispatchRequest(BaseModel):
    team_id: str
    capability: str
    message: str
    stream: bool = False
    routing_metadata: dict = {}
    parameters: dict = {}


class DispatchResponse(BaseModel):
    output: str
    agent_id: str
    agent_name: str
    latency_ms: int
    tokens_used: Optional[int] = None


class CapabilityInfo(BaseModel):
    name: str
    description: str = ""
    is_primary: bool = True
    status: str = "active"
    agent: Optional[dict] = None


class ManifestResponse(BaseModel):
    team_id: str
    team_name: str
    version: str
    last_updated: str
    health: str
    capabilities: list[CapabilityInfo]


class RegisterResult(BaseModel):
    """Response from POST /api/v1/apps/register."""
    app_id: int
    team_id: str
    team_name: str
    api_key: Optional[str] = None
    api_key_prefix: Optional[str] = None
    capabilities_registered: list[str] = []
    already_existed: bool = False
    switch_url: Optional[str] = None
