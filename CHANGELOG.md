# Changelog

All notable changes to the WorkWeek Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
