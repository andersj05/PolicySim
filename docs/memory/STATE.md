# Current state

## Updated

2026-09-07 — foundation on `feat/project-foundation`.

## Implemented

- Local main/dev/feat workflow, contribution rules, ADRs and Git-backed memory.
- FastAPI health endpoint; React/TypeScript placeholder with Vite API proxy.
- Locked uv/npm installs, cross-platform setup/dev/check/format launcher and hooks.
- CI quality matrix, dependency audits, PR routing, ruleset configuration and templates.
- Research provenance/reproducibility standards and Notion/Robinhood design direction.

## Verified

- Clean starting repository at `ea2b8a7`; process/memory commit `54fa454` came first.
- Windows setup, lint, strict types, frontend production build and formatting pass.
- API and repository-policy tests pass; minimal backend coverage is 100%.
- Live API and frontend HTTP smoke checks and proxy succeeded.
- Killing the smoke-test frontend caused the launcher to stop its sibling and fail.
- Python and npm dependency audits report no known vulnerabilities.

## Open issues

- Publishing and hosted CI/protection verification are the remaining bootstrap steps.
- One upstream Starlette/AnyIO deprecation warning is visible; no suppression.
- No data provider, storage, model, authentication or deployment is implemented.

## Next action

Finish hosted verification, then choose M1's provider and series from
[the roadmap](../ROADMAP.md) with the user.
