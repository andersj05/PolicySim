# ADR 0001: Foundation stack

- Status: Accepted
- Date: 2026-09-07

## Context

Terminal-friendly economic research app with Python calculations/server and a
reactive TypeScript UI. This milestone establishes tooling, not research features.

## Decision

Python 3.12, uv 0.12.5 and committed lockfile; FastAPI/Uvicorn; React, strict
TypeScript, Vite, Node 24 and npm with committed lockfile. Runtime files select
supported minor/major lines to permit patch updates; future run manifests record
exact versions. Ruff, mypy and pytest check Python; ESLint, TypeScript and Prettier
check frontend and prose. A root Python package includes `backend/src/policysim`;
frontend dependencies are separate. A standard-library Python launcher provides
portable setup/dev/check commands without a global framework CLI.

## Consequences

Python 3.12 provides a conservative numerical ecosystem baseline. Two runtimes
are required. Locked dependencies do not promise identical floating-point results
across platforms. Defer storage, charting, auth, provider SDKs, model frameworks
and worker infrastructure until a feature establishes requirements.
