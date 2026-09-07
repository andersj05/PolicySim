# Architecture

Status: local data explorer; research models are planned.

One repository, one Python package, one React app. FastAPI owns HTTP and OpenAPI.
Python owns data normalization and calculations; React owns interaction and charts.
Keep domain calculations importable without starting a web server.

```text
React → /api/v1 → FastAPI → application services → domain calculations
                                    ↓
                          provider/storage adapters
```

## Implemented modules

- `domain.py`: Pydantic contracts independent of HTTP/provider JSON.
- `providers.py`: fixed-host FRED and World Bank adapters, bounded pagination,
  explicit nulls and a one-hour World Bank indicator catalog cache.
- `storage.py`: atomically published immutable SHA-256 response objects and manifests.
- `settings.py`: backend-only FRED key and local storage location.
- `main.py`: health, provider configuration, search, countries, observations and
  verified saved-snapshot downloads.
- `frontend/src/`: explorer, detail/chart/table components and abortable requests.
- `scripts/generate_contracts.py`: domain-schema TypeScript generation and drift check.

The Vite proxy forwards `/api` to the loopback API. Credentialed network requests
run only in Python. Synchronous HTTP handlers run in FastAPI's worker threadpool.
Keep calculations in independent Python domain modules when M2 begins.

World Bank full histories are retrieved in small pages, with source identity
checked on each page, then selected by calendar year. Exact input bytes are kept.
WDI uses the default provider source after explicit response validation; other
sources use the source query parameter. This avoids observed gateway failures on
unnecessary first-page/date query combinations. Data outside the selected range
remains only in raw provenance objects. Missing values are never interpolated.

Snapshots contain requested dates, country, UTC retrieval time, normalized
metadata, available vintage fields and raw content hashes. The manifest filename
is the SHA-256 of the serialized manifest before its own ID is populated. Downloaded
JSON includes that ID. The local raw files are required to reproduce normalization;
the browser download contains normalized data and raw hashes, not raw bytes.

## Growth plan (not implemented)

Keep this as a modular monolith. Add research services when models require them,
not empty abstraction layers. No authentication, hosting, retention UI, saved
workspace, transformations or forecasts are implemented. Recent series are
session-local navigation. Filesystem storage is intended for one local user;
revisit storage and job orchestration before multi-user deployment.

## Evidence

- [ADR 0001](decisions/0001-foundation-stack.md)
- [ADR 0003](decisions/0003-data-explorer.md)
- [FastAPI modular applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Vite runtime requirements](https://vite.dev/guide/)
- [uv locked CI installs](https://docs.astral.sh/uv/guides/integration/github/)

Documentation consulted 2026-09-07. Lockfiles and check results establish the
dependency versions actually used.
