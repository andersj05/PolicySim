# Architecture

Status: local data explorer, statistical analysis and forecasting workspace.

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
- `research_contracts.py`: validated analysis/model/import/run contracts.
- `analysis.py`: provider-independent calendars, transformations and statistics.
- `forecasting.py`: pure numerical estimators and chronological evaluation.
- `research_service.py`: CSV normalization, snapshot analysis, serialized local
  forecast execution, reproducibility metadata and immutable run persistence.
- `main.py`: health, provider configuration, search, countries, observations and
  verified snapshots, CSV import/exports, analysis and saved forecast endpoints.
- `frontend/src/`: compact explorer, saved-series shortcuts, import dialog,
  sortable tables, statistics, model settings and persistent forecast results.
- `scripts/generate_contracts.py`: domain-schema TypeScript generation and drift check.

The Vite proxy forwards `/api` to the loopback API. Credentialed network requests
run only in Python. Synchronous HTTP handlers run in FastAPI's worker threadpool.
Calculation modules have no HTTP, filesystem or provider-adapter dependencies.

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

## Research storage and execution

CSV source text is stored using the same content-addressed raw store. Imported
snapshots identify their local origin and selected columns. Research requests
address immutable snapshot IDs, never browser-supplied observation arrays.
Forecast manifests contain exact history/configuration/results and code/environment
identities. A nonblocking process lock serializes forecast requests; another run
receives HTTP 409. Numerical jobs are bounded but synchronous and not cancellable.

The browser persists only saved-series references and displays immutable run JSON
from Python. Dates/units/transformation logic and model evaluation stay in Python.
Presentation formatting and chart coordinate calculations stay in TypeScript.

## Growth plan (not implemented)

Keep this as a modular monolith. Authentication, hosting, retention UI, model
cancellation, multivariate scenarios and historical vintages are not implemented.
Filesystem storage is intended for one local user; revisit storage and job
orchestration before multi-user deployment. See [methods](FORECASTING.md).

## Evidence

- [ADR 0001](decisions/0001-foundation-stack.md)
- [ADR 0003](decisions/0003-data-explorer.md)
- [ADR 0004](decisions/0004-forecast-workspace.md)
- [FastAPI modular applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Vite runtime requirements](https://vite.dev/guide/)
- [uv locked CI installs](https://docs.astral.sh/uv/guides/integration/github/)

Documentation consulted 2026-09-07. Lockfiles and check results establish the
dependency versions actually used.
