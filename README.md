# WorkWeek Python SDK

Official Python SDK for the [WorkWeek](https://portal.workxspeed.com) AI Agent Marketplace.

Two packages in this repo:

| Package | Purpose | Version |
|---------|---------|---------|
| **workweek** | Client SDK — query data, chat, manage apps/teams/agents | 0.5.0 |
| **workweek-switch** | Provider SDK — expose capabilities for the marketplace | 0.3.0 |

## Install

Install from GitHub releases (no auth required):

```bash
# Client SDK (for consuming platform services)
pip install https://github.com/rchow93/workweek-sdk-python/releases/download/v0.5.0/workweek-0.5.0-py3-none-any.whl

# Switch SDK (for providing capabilities to the marketplace)
pip install https://github.com/rchow93/workweek-sdk-python/releases/download/v0.5.0/workweek_switch-0.3.0-py3-none-any.whl
```

Or in `requirements.txt`:

```
workweek @ https://github.com/rchow93/workweek-sdk-python/releases/download/v0.5.0/workweek-0.5.0-py3-none-any.whl
workweek-switch @ https://github.com/rchow93/workweek-sdk-python/releases/download/v0.5.0/workweek_switch-0.3.0-py3-none-any.whl
```

For local development:

```bash
git clone https://github.com/rchow93/workweek-sdk-python.git
cd workweek-sdk-python
pip install -e .                                    # workweek client
pip install -e . --config-settings="--build-option=--switch"  # or manually:
pip install workweek_switch/                        # workweek-switch
```

## Authentication

All requests use API key authentication via the `X-API-Key` header. Create a key in the WorkWeek portal under **Settings > API Keys**.

```python
client = WorkWeekClient(base_url="https://gw.askvai.com", api_key="wk_rpt_...")
```

The SDK is public — anyone can install it. The API key controls access to platform services.

---

## Package 1: workweek (Client SDK)

For tenant apps that **consume** WorkWeek services (data queries, chat, places).

### Quickstart

```python
from workweek import WorkWeekClient

client = WorkWeekClient(
    base_url="https://gw.askvai.com",
    api_key="wk_rpt_...",
)

# Query an Iceberg dataset
result = client.data.query(
    dataset="sf_food_trucks_permits",
    sql="SELECT COUNT(*) AS n FROM tbl WHERE status = 'APPROVED'",
)
print(result["rows"])  # [{"n": 163}]

# Stream a chat message
for event in client.chat.stream("How many food trucks are active in SF?"):
    if event.type == "token":
        print(event.content, end="", flush=True)
```

### Modules

| Module | Purpose |
|--------|---------|
| `client.data` | Query Iceberg datasets via SQL, list datasets, inspect schemas |
| `client.chat` | Conversational AI with tool-calling and streaming |
| `client.places` | Google Places search, details, street view |
| `client.apps` | Tenant app config, page data, dashboard management |
| `client.agents` | Saved agent CRUD |
| `client.teams` | Team listing and management |
| `client.knowledge` | Knowledge collection search |
| `client.analysis` | BACI and statistical analysis |
| `client.execution` | Submit and track agent executions |

---

## Package 2: workweek-switch (Provider SDK)

For tenant apps that **provide** capabilities to the marketplace. Implements the switch contract (manifest + dispatch).

### Quickstart

```python
from workweek_switch import WorkWeekSwitch

switch = WorkWeekSwitch(
    team_id="your-team-uuid",
    team_name="My Service",
    gateway_url="https://gw.askvai.com",
    api_key="wk_rpt_...",
)

@switch.capability(
    "my_capability",
    description="What this capability does",
    agent_name="My Agent",
    agent_role="Specialist",
)
async def my_handler(message: str, context: dict) -> str:
    return f"Response to: {message}"

# Self-register on startup
await switch.register(switch_url="http://my-service:8000")

# Mount in FastAPI
app.include_router(switch.as_fastapi_router())
```

### Switch Contract Endpoints

The SDK auto-generates these endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /switch/manifest` | Returns registered capabilities (polled by platform) |
| `POST /dispatch` | Routes incoming requests to the matching handler |
| `GET /health` | Liveness check |

### Streaming Handlers

Handlers can stream SSE tokens:

```python
@switch.capability("chat_assistant", description="Streaming chat")
async def chat_handler(message: str, context: dict):
    # Async generator = streaming mode
    yield {"type": "token", "content": "Hello "}
    yield {"type": "token", "content": "world!"}
```

### HMAC Verification

Optional webhook signature verification:

```python
switch = WorkWeekSwitch(
    team_id="...",
    webhook_secret="wk_secret_...",  # Enables HMAC verification on /dispatch
)
```

---

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
- `httpx>=0.27.0` (both packages)
- `fastapi>=0.100.0` (workweek-switch only)
- `pydantic>=2.0.0` (workweek-switch only)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
