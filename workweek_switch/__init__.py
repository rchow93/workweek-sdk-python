"""WorkWeek Switch SDK — implement the switch contract for external agent teams.

Usage:
    from workweek_switch import WorkWeekSwitch

    switch = WorkWeekSwitch(team_id="your-team-uuid", webhook_secret="wk_secret_...")

    @switch.capability("weather", description="Weather forecasts and alerts")
    async def weather(message: str, context: dict) -> str:
        return f"The weather today is sunny."

    @switch.capability("stocks", description="Stock market data")
    async def stocks(message: str, context: dict) -> str:
        return f"AAPL is up 2%."

    app = switch.as_fastapi_app()
    # uvicorn app:app --port 8000
"""

from workweek_switch._switch import WorkWeekSwitch
from workweek_switch._models import (
    DispatchRequest,
    DispatchResponse,
    ManifestResponse,
    CapabilityInfo,
    RegisterResult,
)

__all__ = [
    "WorkWeekSwitch",
    "DispatchRequest",
    "DispatchResponse",
    "ManifestResponse",
    "CapabilityInfo",
    "RegisterResult",
]

__version__ = "0.3.0"
