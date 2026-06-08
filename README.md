# WorkWeek Python SDK

Official Python SDK for the [WorkWeek AI Marketplace](https://workxspeed.com) — composable AI services with built-in commerce.

Query data with natural language, stream conversational AI, upload files, run deep research, and integrate 1,300+ AI tools — all through one SDK.

## Install

```bash
pip install https://github.com/rchow93/workweek-sdk-python/releases/download/v0.7.0/workweek-0.7.0-py3-none-any.whl
```

## Quickstart

```python
from workweek import WorkWeekClient

client = WorkWeekClient(
    base_url="https://gw.askvai.com",
    api_key="wk_rpt_...",
)

# Ask questions about your data (NL→SQL)
result = client.data.ask("How many active users this month?", dataset="my_dataset")

# Upload a file to your data warehouse (no S3 access needed)
client.data.upload("my_dataset", "/path/to/data.csv")

# Stream a chat message with tool calling
for event in client.chat.stream("What are the top food trucks in SF?"):
    if event.type == "token":
        print(event.content, end="", flush=True)

# Team-scoped chat with data tools
for event in client.chat.with_team(team_id="uuid", message="Show candidates above 8"):
    if event.type == "token":
        print(event.content, end="", flush=True)

# Deep research with citations
result = client.execution.run_research(
    query="Market opportunity for AI recruiting tools",
    template_id="market_analysis",
)
```

## Modules

| Module | Purpose |
|--------|---------|
| `client.data` | Query datasets (SQL + NL→SQL), upload files, list datasets, export dashboards |
| `client.chat` | Conversational AI with tool calling, SSE streaming, team-scoped chat |
| `client.execution` | Run queries, deep research, track executions |
| `client.knowledge` | Knowledge collection search, document management |
| `client.places` | Google Places search, details, street view (BYOK) |
| `client.apps` | App config, page data, dashboard management |
| `client.agents` | Saved agent CRUD |
| `client.teams` | Team listing and management |
| `client.analysis` | BACI and statistical analysis |

## Authentication

All requests use API key authentication via the `X-API-Key` header:

```python
client = WorkWeekClient(base_url="https://gw.askvai.com", api_key="wk_rpt_...")
```

Org and user context are derived from the key — never pass `org_id` from the client.

## Two SDKs

| Package | Purpose | Install |
|---------|---------|---------|
| **workweek** | Consume AI services (data, chat, research) | [v0.7.0 wheel](https://github.com/rchow93/workweek-sdk-python/releases/download/v0.7.0/workweek-0.7.0-py3-none-any.whl) |
| **workweek-switch** | Provide capabilities to the marketplace | [v0.3.0 wheel](https://github.com/rchow93/workweek-sdk-python/releases/download/v0.5.0/workweek_switch-0.3.0-py3-none-any.whl) |

## Requirements

- Python 3.10+
- `httpx>=0.27.0`

## License

Apache License 2.0
