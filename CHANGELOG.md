# Changelog

All notable changes to the WorkWeek Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-04-07

### Changed
- **`data.query(dataset, sql, limit=None)`** — Rewritten to call the new
  public `POST /api/v1/sdk/query` endpoint. `org_id` is no longer a parameter
  (it is derived from the API key server-side). SQL must be SELECT-only and
  reference `tbl` as the table name. Returns
  `{"dataset", "row_count", "columns", "rows"}`.
- **`data.list_datasets()`** — Now hits `GET /api/v1/sdk/datasets`. No
  parameters; org is derived from API key.
- **`data.get_schema(dataset)`** — Now hits
  `GET /api/v1/sdk/datasets/{dataset}/schema`.
- **`chat.send_message(...)`** removed. Replaced by:
  - **`chat.stream(message, session_id=None)`** — Iterator of `ChatEvent`
    yielding `session`, `tool_start`, `tool_end`, `token`, `done`, and
    `error` events from the chat-service `/api/v1/chat/message` SSE stream.
  - **`chat.send(message, session_id=None)`** — Convenience that collects
    all `token` events from `stream()` into a single string.

### Added
- New `ChatEvent` dataclass-like class with `.type`, `.data`, and `.content`
  accessors.
- Both `WorkWeekClient` and `WorkWeekAPIError` now exported from the package
  root: `from workweek import WorkWeekClient, WorkWeekAPIError`.

### Notes
- This is the first version that actually works against `gw.askvai.com`.
  v0.1.0 was a faithful snapshot of the legacy monorepo SDK and pointed at
  internal-only endpoints — do not use it.

## [0.1.0] — 2026-04-07

### Added
- Initial SDK extracted from the WorkWeek monorepo as a standalone package.
- `WorkWeekClient` base HTTP client with API key auth (`X-API-Key`).
- 8 modules: `data`, `apps`, `agents`, `analysis`, `knowledge`, `chat`, `teams`, `execution`.
- `WorkWeekAPIError` exception with `status_code` and `message`.
- Apache 2.0 license, Python 3.11+ support, single dep on `httpx`.

### Notes
- This is the same SDK code that previously lived at `Services/python-sdk/` in the
  workweek monorepo (TD-076). Extracting it into a standalone repo so tenants can
  install it without monorepo access.
- The `data.query()` and `chat.send_message()` methods in v0.1.0 hit internal
  endpoints that are not exposed externally. v0.2.0 will fix these to use the
  public `/api/v1/sdk/*` and `/api/v1/chat/message` endpoints.
