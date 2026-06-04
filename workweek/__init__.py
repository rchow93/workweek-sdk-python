"""WorkWeek Python SDK — platform integration for tenant apps.

Structured data calls (data, places) use Widget path (/sdk/* endpoints).
Conversational calls (chat) use Router path (/router/invoke).
"""

from workweek.client import WorkWeekClient, WorkWeekAPIError

__all__ = ["WorkWeekClient", "WorkWeekAPIError"]
__version__ = "0.5.0"
