# Current state

## Updated

2026-09-07 — M0 engineering foundation complete. Implementation starts at M1.

## Implemented

- main/dev/feat workflow, contribution rules, ADRs and Git-backed project memory.
- FastAPI health endpoint; React/TypeScript placeholder with Vite API proxy.
- Locked uv/npm installs, portable setup/dev/check/format commands and Git hooks.
- Linux/Windows CI, dependency audits, PR routing, templates and Dependabot updates.
- GitHub branch policy in `.github/branch-rules.json`; inspect live enforcement
  using [repository administration](../REPOSITORY.md), since remote settings can drift.
- Merge-commit-only integration, vulnerability alerts and private reporting enabled.
- Research provenance/reproducibility standards and Notion/Robinhood design direction.

## Verified

- Process/memory commit `54fa454` preceded scaffold `0edb258` and portability fix `6219b27`.
- `python scripts/project.py setup` and `check` pass on Windows.
- 11 tests pass, with 100% coverage of the minimal backend health module (not the
  entire tooling repository). Ruff, mypy, ESLint, TypeScript, build and hooks pass.
- [Hosted CI for 6219b27](https://github.com/andersj05/PolicySim/actions/runs/34152415530):
  Linux, Windows, dependency audits and aggregate quality gate pass.
- Live frontend/API/proxy smoke checks and normal-account KeyboardInterrupt cleanup pass.
- Python and npm dependency audits report no known vulnerabilities.
- Local runtime evidence: Python 3.12.14, Node 24.12.0, npm 10.8.1, uv 0.12.5.

## Open issues

- One upstream Starlette/AnyIO deprecation warning remains visible; no suppression.
- No provider, storage, model, authentication or deployment is implemented.
- License choice is deferred to the owner. Design guidance is not a final UI.
- Sandbox process permissions differ from normal terminal use; cleanup failures
  are reported explicitly. Use the normal Windows account for setup/server checks.

## Next action

Create `feat/first-data-source` from updated `dev`. With the user, choose one
provider and a small series set, define vintage/provenance requirements, and
record the storage decision before implementing [M1](../ROADMAP.md).
