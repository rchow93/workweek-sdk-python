# RecruiterPilot — Correct Integration Pattern

## Current Problem

RP is calling `POST /api/v1/query` directly with their API key. This bypasses the marketplace model — no router classification, no grant tracking, no cross-org visibility. It works but it's not how tenants should integrate.

## Correct Pattern

RP should use the WorkWeek SDK for everything. There are two interaction models:

### 1. Chat-based interactions (real-time)

For features where a user asks a question and gets a response:
- "Find me candidates for VP Finance in fintech"
- "What's the status of my sourcing pipeline?"

```python
from workweek import WorkWeekClient

client = WorkWeekClient(
    base_url="https://gw.askvai.com",
    api_key="wk_rpt_vMOl8QuINtve5tspDhWN7vCV8TCpSwfUXUFqZ2KWbPE",
)

# Chat with the RP Research team
# This goes through the router → grant check → team dispatch
for event in client.chat.with_team(
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
    message="Find VP Finance candidates in Bay Area fintech",
):
    print(event.content, end="", flush=True)
```

### 2. Research/execution (long-running)

For dossier generation and deep research:

```python
# Submit research via the SDK (correct method)
result = client.execution.run_research(
    query="Research candidate: Tim Reidy, VP Finance at SpotOn",
    template_id="candidate_dossier",
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
)

# Wait for completion
final = client.execution.wait_for_completion(
    result["execution_id"],
    poll_interval=15.0,
    timeout=1800.0,
)

print(final["result"]["report"])
```

### 3. Webhook handler (for cross-team dispatch)

When OTHER tenants want to use RP's capabilities, they go through the marketplace. RP needs a webhook endpoint that handles incoming requests:

```python
# In RP's backend — handle webhook from WorkWeek router
@app.post("/api/chat")
async def handle_workweek_webhook(req: WebhookRequest) -> WebhookResponse:
    """Called when another tenant's chat routes to RP's team."""
    
    # Parse what they need
    if "candidate" in req.message.lower() and "search" in req.message.lower():
        candidates = await search_candidates(req.message)
        text = format_candidate_list(candidates)
    elif "dossier" in req.message.lower():
        # Trigger dossier generation
        exec_id = await start_dossier(req.message)
        text = f"Dossier generation started (ID: {exec_id}). This takes 8-15 minutes."
    else:
        text = "I can help with candidate search and dossier generation. Try: 'search for VP Finance candidates' or 'generate dossier for Jane Smith'"
    
    return WebhookResponse(response=text)
```

## What RP Should NOT Do

1. **Don't call `POST /api/v1/query` directly** — use `client.execution.run_research()` instead. The SDK handles auth, team scoping, and template selection correctly.

2. **Don't forge JWTs** — authenticate via `POST /api/v1/auth/login` or use the API key.

3. **Don't hit internal service URLs** — always go through `gw.askvai.com`.

4. **Don't bypass the router** — all real-time interactions should go through chat, which the router can classify and meter.

## RP Credentials

```
API Key:    wk_rpt_vMOl8QuINtve5tspDhWN7vCV8TCpSwfUXUFqZ2KWbPE
Team ID:    eca3ac33-fcf9-4a00-bd28-4254f6066cb9
Base URL:   https://gw.askvai.com
Org:        3 (iwink4u.com)
App:        28 (recruiter-pilot)
```

## Login (for JWT if needed)

```bash
curl -s -X POST "https://gw.askvai.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "aaron@iwink4u.com", "password": "RPDemo2026!"}'
```

Returns: `{"access_token": "eyJ..."}` — use as `Authorization: Bearer <token>`

## Future: Tool Registration (TD-184)

When TD-184 ships, RP will register individual capabilities as structured tools:

```python
client.tools.register([
    {"name": "rp_search_candidates", "endpoint": "https://...", "pricing": {"per_call": 0.10}},
    {"name": "rp_generate_dossier", "endpoint": "https://...", "pricing": {"per_call": 0.50}},
    {"name": "rp_schedule_interview", "endpoint": "https://...", "pricing": {"per_call": 0.25}},
])
```

This makes each capability individually discoverable, grantable, and billable in the marketplace.
