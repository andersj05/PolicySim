# Handoff: project foundation

## Context

Bootstrap a clean README-only repository from `ea2b8a7`. No research implementation.
Process and memory were committed first in `54fa454`.

## Changes

- Established main/dev/feat flow, ADRs, current-state memory and handoff templates.
- Added Python/FastAPI health API, React/TypeScript/Vite placeholder and locked deps.
- Added terminal launcher, strict checks, tests, hooks, CI, audits and ruleset policy.
- Documented design references, data vintages, leakage prevention and reproducible runs.

## Verification

- `python scripts/project.py setup`: locked installs and Git hook installation pass.
- `python scripts/project.py check`: passes on Windows; one port-ownership test
  skipped while smoke-test servers occupied port 8000 (passed before servers started).
- API/policy/launcher suite: 11 tests; backend's minimal health module has 100% coverage.
- Direct health, frontend HTML and proxied health return success.
- Simulated Vite failure makes the launcher exit nonzero and stop its sibling.
- `npm --prefix frontend audit --audit-level=high`: no vulnerabilities.
- Locked Python requirements audited with pip-audit: no known vulnerabilities.
- Replaced deprecated ESLint major and httpx test dependency during verification.
- Fixed native Windows typing and TypeScript CSS declarations. Formatting now selects
  repository source files instead of traversing local caches.

## Open issues

Hosted CI and ruleset application are pending the final bootstrap steps.
One upstream Starlette/AnyIO deprecation warning remains visible.
This environment's terminal tool did not deliver Ctrl+C; failure-triggered cleanup
was verified instead. Normal terminal KeyboardInterrupt handling is implemented.
Data, models, persistence, authentication, production hosting and license choice
are deferred; see the roadmap and constraints.

## Next action

Publish checked bootstrap branches, verify hosted CI, activate/read back protections,
and record final evidence. Begin implementation later with one data-provider slice.
