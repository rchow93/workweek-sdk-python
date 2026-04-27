# RecruiterPilot — WorkWeek IdeaIQ Integration Guide

## What This Is

WorkWeek's IdeaIQ is a deep research engine that decomposes complex queries into focused stages, runs each stage with dedicated tools, and synthesizes analyst-grade reports. RecruiterPilot (RP) has been onboarded as an SDK tenant on the WorkWeek platform (org 3 / iwink4u.com). This means RP can submit candidate research requests via API and receive structured dossiers back — without managing LLM infrastructure, web search tools, or research orchestration.

## Architecture Overview

When RP submits a research query via the SDK, here's what happens:

```
RP App (SDK call)
  → WorkWeek Gateway (API key auth, org 3)
    → Validator (bypasses LLM resolution — orchestrator manages its own keys)
      → Research Orchestrator (SQS queue, 3 replicas)
        → Phase 0: Chief of Staff decomposes into focused stages
        → Stage 1: LinkedIn fetch (if LinkedIn tool available)
        → Stage 2: Web research (Serper Google Search + Firecrawl scraping)
        → Stage 3: Synthesis (compile 13-section dossier)
      → Result stored in S3 + PostgreSQL
    → SQS → WebSocket (real-time progress for portal UI)
  → RP polls GET /executions/{id} for result
```

**Key point:** The research orchestrator has its own Azure OpenAI keys and manages all LLM calls internally. RP doesn't need to provide LLM keys for research. We've also provisioned Serper (Google Search API) and Firecrawl (web scraping) entitlements for org 3, so web research tools are available out of the box.

## Credentials

```
API Key:    wk_rpt_vMOl8QuINtve5tspDhWN7vCV8TCpSwfUXUFqZ2KWbPE
Base URL:   https://gw.askvai.com
Team ID:    eca3ac33-fcf9-4a00-bd28-4254f6066cb9  (RP Research team)
Org ID:     3 (iwink4u.com)
App ID:     28 (recruiter-pilot)
```

**API Key Scopes:**
- `execute:queries` — submit research queries
- `read:executions` — check execution status and results
- `execute:executions` — trigger re-runs
- `read:teams` — list teams
- `read:agents` — list agents on teams
- `read:genome` — read genome learning data

**Portal login (for UI testing):**
- URL: https://portal.workxspeed.com
- Email: `aaron@iwink4u.com`
- Password: `RPDemo2026!`

## SDK Installation

The SDK is a Python package. Install from the local repo or pip:

```bash
# From source
cd /path/to/workweek-sdk-python
pip install -e .

# Or copy the workweek/ directory into your project
```

**Requirements:** Python 3.9+, httpx

## Quick Start — 3 Lines to a Dossier

```python
from workweek import WorkWeekClient

client = WorkWeekClient(
    base_url="https://gw.askvai.com",
    api_key="wk_rpt_vMOl8QuINtve5tspDhWN7vCV8TCpSwfUXUFqZ2KWbPE",
)

# Submit candidate dossier research
result = client.execution.run_research(
    query="Research candidate: Jensen Huang, CEO of NVIDIA. Produce a comprehensive candidate dossier.",
    template_id="candidate_dossier",
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
)
print(f"Execution started: {result['execution_id']}")

# Wait for completion (polls every 15s, times out at 30 min)
final = client.execution.wait_for_completion(
    result["execution_id"],
    poll_interval=15.0,
    timeout=1800.0,
)

if final["status"] == "completed":
    report = final["result"]
    print(f"Title: {report.get('title')}")
    print(f"Confidence: {report.get('confidence')}")
    print(f"Report: {len(report.get('report', ''))} chars")
    
    # The report is markdown — save it
    with open("dossier.md", "w") as f:
        f.write(report["report"])
else:
    print(f"Failed: {final.get('error')}")
```

## SDK Methods Reference

### `client.execution.run_research()`

Convenience method for deep research queries. Sets `path_type="deep_research"` automatically.

```python
result = client.execution.run_research(
    query="Research candidate: ...",       # Required — the research question
    template_id="candidate_dossier",       # Optional — research template (see below)
    team_id="eca3ac33-...",                # Optional — scopes execution to a team
    max_steps=40,                          # Optional — override step budget (10-150)
    custom_instructions="Focus on...",     # Optional — injected into agent prompts
)
# Returns: {"execution_id": "...", "status": "submitted", "message": "..."}
```

### `client.execution.run_query()`

Lower-level method — use this if you need full control over the request.

```python
result = client.execution.run_query(
    query="Research candidate: ...",
    path_type="deep_research",             # "crew", "single", "architect", "deep_research", "chat"
    team_id="eca3ac33-...",
    template_id="candidate_dossier",       # Shorthand — merged into execution_metadata
    execution_metadata={                   # Raw metadata dict (merged with template_id)
        "template_id": "candidate_dossier",
        "max_steps": 40,
    },
    custom_instructions="...",
)
```

### `client.execution.wait_for_completion()`

Polls until execution completes or fails.

```python
final = client.execution.wait_for_completion(
    execution_id="...",
    poll_interval=15.0,   # Seconds between polls (default 10s)
    timeout=1800.0,       # Max wait time (default 30 min)
)
# Returns: full execution dict with result
# Raises: TimeoutError if execution doesn't finish in time
```

### `client.execution.get_status()`

Single status check (no polling).

```python
status = client.execution.get_status("execution-id-here")
# Returns: {"id": "...", "status": "executing", "path_type": "deep_research", ...}
```

### `client.execution.list_executions()`

List recent executions for the authenticated org.

```python
execs = client.execution.list_executions(limit=10, offset=0)
```

## Available Research Templates

Templates control how the research engine operates — what prompt prefix to use, how many steps to budget, and (for some templates) which tools to assign to each stage.

| Template ID | Name | Steps | Timeout | Best For |
|-------------|------|-------|---------|----------|
| `candidate_dossier` | Candidate Dossier | 40 | 30 min | **RP primary use case** — 13-section analyst-grade dossier |
| `market_analysis` | Market Analysis | 60 | 30 min | TAM/SAM/SOM, competitive landscape, trends |
| `competitive_landscape` | Competitive Landscape | 50 | 25 min | 5-10 competitor deep analysis |
| `technical_deep_dive` | Technical Deep Dive | 50 | 25 min | Academic papers, benchmarks, architecture |
| `financial_analysis` | Financial Analysis | 50 | 25 min | Revenue, margins, valuation, projections |
| `safety_report` | Safety & Data Report | 60 | 30 min | Statistical analysis, data visualizations |
| `quick_lookup` | Quick Lookup | 15 | 5 min | Fast factual answers |

### Candidate Dossier Template Details

The `candidate_dossier` template produces a 13-section dossier with these exact headers:

1. Executive Summary
2. Contact & Identifiers
3. Career History
4. Current Role — Deep Dive
5. Growth Record & Business Impact
6. Leadership & Management Style
7. Education & Credentials
8. Public Presence & Thought Leadership
9. Skills & Expertise
10. Network & Affiliations
11. Risk & Gap Analysis
12. Recruiter's Read
13. Sources

Every factual claim is tagged with source: `[Web]`, `[LinkedIn]`, `[Both]`, or `"Not found"`.

The template uses **focused tool stages** (TD-180):
- **Stage 1 — LinkedIn fetch** (20% of budget): Worker gets ONLY `linkedin_get_profile`. If LinkedIn tool isn't available, this stage is skipped and the dossier is built from web sources only.
- **Stage 2 — Web research** (50% of budget): Worker gets ONLY `search_web`, `search_news`, `search_scholar`, `browse_web`, `read_webpage`, `smart_scrape`. Finds press, talks, publications, impact metrics.
- **Stage 3 — Synthesis** (30% of budget): Worker gets ONLY `read_file`, `write_file`. Compiles the dossier from all evidence gathered in stages 1 and 2.

This focused gating prevents tool confusion — workers can't call the wrong tools because they literally don't have access to them.

## Result Format

When an execution completes, the `result` field contains:

```json
{
  "report": "# Jensen Huang Comprehensive Candidate Dossier\n\n## 1. Executive Summary\n...",
  "title": "Jensen Huang Comprehensive Candidate Dossier",
  "confidence": 0.8,
  "confidence_label": "HIGH",
  "steps_used": 39,
  "duration_seconds": 806,
  "tokens_used": 337297,
  "cost_usd": 0.19,
  "sources_visited": 3,
  "citations_verified": 3,
  "external_urls": 80,
  "workspace_files": [
    {"name": "planner_output.json", "size": 2048},
    {"name": "worker_findings.md", "size": 15000},
    {"name": "jensen_huang_dossier.md", "size": 42000}
  ],
  "timestamp": "2026-04-27T04:07:19.922822+00:00"
}
```

**Key fields:**
- `report` — The full markdown dossier (typically 30,000-50,000 chars)
- `confidence` — 0.0 to 1.0 quality score. 0.8+ = HIGH, 0.6-0.8 = MEDIUM, below 0.6 = LOW
- `steps_used` / `duration_seconds` — how much compute was used
- `cost_usd` — total LLM + search tool cost for this execution

## How RP's LinkedIn Integration Fits

Currently, the platform's `candidate_dossier` template Stage 1 uses the internal `linkedin_get_profile` tool. This tool requires a LinkedIn API entitlement (BYOK). If RP wants to inject their own LinkedIn data (from `lisa-mcp`), there are two paths:

### Path A: Pre-fetch and inject via query context (Recommended for now)

RP fetches the LinkedIn profile using their own `lisa-mcp` tool, then includes the profile data in the query text. The research engine treats it as authoritative context.

```python
# RP fetches LinkedIn profile data via their own pipeline
linkedin_data = rp_fetch_linkedin_profile("jensen-huang")

# Include it in the research query
result = client.execution.run_research(
    query=f"""Research candidate: Jensen Huang, CEO of NVIDIA.

Pre-fetched LinkedIn profile context:
{linkedin_data}

Produce a comprehensive 13-section candidate dossier. Use the LinkedIn data above as authoritative evidence for career history, education, and skills. Cross-reference with web sources.""",
    template_id="candidate_dossier",
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
)
```

This works today — no platform changes needed. The prompt prefix for `candidate_dossier` already says: *"Pre-fetched LinkedIn profile context is supplied verbatim in the query — treat it as authoritative evidence."*

### Path B: LinkedIn BYOK entitlement on the platform (Future)

Register RP's LinkedIn API credentials as a BYOK entitlement on org 3. Then Stage 1 of the template will call `linkedin_get_profile` automatically using RP's credentials. This is cleaner but requires:
1. RP registers LinkedIn credentials via the entitlements API
2. Cookie persistence is stable (their current blocker)
3. The platform's LinkedIn MCP tool is compatible with RP's cookie format

**Recommendation: Start with Path A.** It works today, gives RP full control over LinkedIn data quality, and doesn't depend on cookie stability. Path B is the long-term solution once LinkedIn auth is reliable.

## Polling vs Webhooks

The SDK currently uses polling (`wait_for_completion()`). For production integration, RP can either:

1. **Poll** — call `get_status()` every 10-15 seconds. Simple, works now.
2. **Webhook** — register a `webhook_callback_url` on the RP Research team. The platform will POST to that URL when execution completes. This requires RP to expose an HTTP endpoint.

Polling is fine for now. Webhook support is available via the team's `webhook_callback_url` field (set during onboarding or via team update API).

## Testing Checklist

1. **Smoke test — quick lookup:**
```python
result = client.execution.run_research(
    query="What is Jensen Huang's current title at NVIDIA?",
    template_id="quick_lookup",
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
)
final = client.execution.wait_for_completion(result["execution_id"], timeout=300)
print(final["result"]["report"])
```
Expected: Fast answer in ~2-5 minutes, short report.

2. **Full dossier — without LinkedIn:**
```python
result = client.execution.run_research(
    query="Research candidate: Satya Nadella, CEO of Microsoft. Produce a comprehensive candidate dossier.",
    template_id="candidate_dossier",
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
)
final = client.execution.wait_for_completion(result["execution_id"])
```
Expected: 30,000-50,000 char dossier, confidence 0.7-0.9, 8-15 minutes.

3. **Full dossier — with LinkedIn context (Path A):**
```python
linkedin_profile = "... profile data from lisa-mcp ..."
result = client.execution.run_research(
    query=f"Research candidate: Jensen Huang. LinkedIn context:\n{linkedin_profile}\n\nProduce a comprehensive candidate dossier.",
    template_id="candidate_dossier",
    team_id="eca3ac33-fcf9-4a00-bd28-4254f6066cb9",
)
final = client.execution.wait_for_completion(result["execution_id"])
```
Expected: Higher confidence (0.8+) with LinkedIn data, source tags include `[LinkedIn]`.

4. **Portal UI test:**
   - Log into https://portal.workxspeed.com as `aaron@iwink4u.com` / `RPDemo2026!`
   - Navigate to IdeaIQ page
   - Submit a research query with the candidate_dossier template
   - Watch real-time progress (scoping → gathering → cross-referencing → synthesis)
   - View the completed dossier, export as DOCX

## Rate Limits

| Scope | Limit |
|-------|-------|
| API key requests | 60/min |
| Deep research concurrent | No hard limit (SQS-based, 3 orchestrator replicas) |
| Serper search calls | 48,000+ credits remaining |
| LLM tokens per execution | ~300,000-400,000 (managed by orchestrator) |

## Cost Per Execution

| Component | Typical Cost |
|-----------|-------------|
| LLM (planner + workers + synthesis) | $0.10 - $0.20 |
| Serper web searches | $0.005 - $0.01 |
| **Total per dossier** | **~$0.15 - $0.25** |

## Support

- Platform issues: contact Richard (rchow@mitns.com)
- SDK bugs: file in the workweek-sdk-python repo
- Research quality issues: include the `execution_id` when reporting — we can pull full orchestrator logs, worker traces, and S3 workspace files for debugging
