# WorkWeek Python SDK

Official Python SDK for the [WorkWeek](https://workweek.io) platform.

Embed WorkWeek's data, agents, and chat capabilities into your own Python apps with
a thin, dependency-light HTTP client. Single runtime dependency: `httpx`.

## Install

From git (until published to PyPI):

```bash
pip install "workweek @ git+https://github.com/rchow93/workweek-sdk-python.git@v0.2.2"
```

For local development:

```bash
git clone https://github.com/rchow93/workweek-sdk-python.git
cd workweek-sdk-python
pip install -e .
```

## Quickstart

```python
from workweek import WorkWeekClient

client = WorkWeekClient(
    base_url="https://gw.askvai.com",
    api_key="wk_rpt_...",  # Get from Settings → API Keys in the WorkWeek portal
)

# Query an Iceberg dataset
result = client.data.query(
    dataset="sf_food_trucks_permits",
    sql="SELECT COUNT(*) AS n FROM tbl WHERE status = 'APPROVED'",
)
print(result["rows"])  # → [{"n": 163}]

# Stream a chat message (v0.2.0+)
for event in client.chat.stream("How many food trucks are active in SF?"):
    if event.type == "token":
        print(event.content, end="", flush=True)
```

## Authentication

All requests use API key authentication via the `X-API-Key` header. Create a key
in the WorkWeek portal under **Settings → API Keys**. Pass it to `WorkWeekClient`:

```python
client = WorkWeekClient(base_url="https://gw.askvai.com", api_key="wk_rpt_...")
```

The org and user context are derived from the API key — never pass `org_id` from
the client.

## Modules

| Module | Purpose |
|---|---|
| `client.data` | Query Iceberg datasets via SQL, list available datasets, inspect schemas |
| `client.chat` | Conversational AI with tool-calling and streaming responses |
| `client.apps` | Tenant app config, page data, dashboard frontend management |
| `client.agents` | Saved agent CRUD |
| `client.teams` | Team listing |
| `client.knowledge` | Knowledge collection search |
| `client.analysis` | BACI and statistical analysis |
| `client.execution` | Submit and track agent executions |

## Error Handling

```python
from workweek import WorkWeekAPIError

try:
    result = client.data.query(dataset="missing", sql="SELECT 1")
except WorkWeekAPIError as e:
    print(f"HTTP {e.status_code}: {e.message}")
```

## Requirements

- Python 3.10+
- `httpx>=0.27.0`

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Status

Alpha. API may change before 1.0. Pin to a specific version in production:

```bash
pip install "workweek @ git+https://github.com/rchow93/workweek-sdk-python.git@v0.2.2"
```
