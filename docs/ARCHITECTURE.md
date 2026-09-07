# Architecture

Status: foundation; research capabilities are planned.

One repository, one Python package, one React app. FastAPI owns HTTP and OpenAPI.
Python owns data normalization and calculations; React owns interaction and charts.
Keep domain calculations importable without starting a web server.

```text
React → /api/v1 → FastAPI → application services → domain calculations
                                    ↓
                          provider/storage adapters
```

Only `GET /api/v1/health` exists now. The Vite development proxy forwards `/api` to
the loopback API without extra CORS. Production routing is deferred. HTTP handlers
validate and orchestrate; they do not contain model equations. Start as a modular
monolith, without microservices or background job infrastructure.

## Growth plan (not implemented)

- `policysim/data/`: provider adapters and normalized series metadata.
- `policysim/research/`: calculations, scenarios and backtesting.
- `policysim/services/`: use cases and run orchestration.
- `policysim/storage/`: persistence once a workload defines its requirements.
- `frontend/src/features/`: feature-local screens, state and API interaction.

Create modules when used, not empty abstraction layers. Evaluate Parquet/DuckDB for
analytical data and SQLite for metadata before hosted storage, but choose after the
first ingestion/query workload. Introduce a generated TypeScript OpenAPI client
with a drift check in the first real API feature. The placeholder calls no API and
duplicates no domain types. CPU-heavy simulations will need bounded execution,
durable run IDs and cancellation; do not block async HTTP workers.

## Evidence

- [ADR 0001](decisions/0001-foundation-stack.md)
- [FastAPI modular applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Vite runtime requirements](https://vite.dev/guide/)
- [uv locked CI installs](https://docs.astral.sh/uv/guides/integration/github/)

Documentation consulted 2026-09-07. Lockfiles and check results establish the
dependency versions actually used.
