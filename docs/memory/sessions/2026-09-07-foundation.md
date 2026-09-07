# Handoff: project foundation

## Context

Bootstrap a clean README-only repository from `ea2b8a7`. No research implementation.
Process/memory came first (`54fa454`), then scaffold/checks (`0edb258`) and portable
launcher fixes (`6219b27`). A final documentation commit closes the task.

## Changes

- Established main/dev/feat flow, ADRs, state memory and handoff templates.
- Added FastAPI health API, React/TypeScript/Vite placeholder and locked dependencies.
- Added terminal setup/dev/check/format, tests, hooks, CI, audits and GitHub policy.
- Documented design direction, data vintages, leakage prevention and run provenance.
- Published main, dev and feat/project-foundation using the documented one-time
  bootstrap. All later integration uses feature PRs to dev and dev promotion PRs.
- Configured merge-only integration, branch retention, alerts and private reporting.
  The checked-in branch policy defines the final remote protection settings;
  inspect live enforcement with the commands in [repository administration](../../REPOSITORY.md).

## Verification

- `python scripts/project.py setup`: locked installs and hook installation pass.
- `python scripts/project.py check`: all checks pass under normal Windows account.
- 11 tests pass without skips after stopping servers; minimal backend coverage 100%.
- Ruff, strict mypy, ESLint, TypeScript, Vite production build, Prettier and hooks pass.
- [CI run 34152415530](https://github.com/andersj05/PolicySim/actions/runs/34152415530):
  quality on Linux and Windows, dependency audits and quality-gate all pass.
- Direct health, frontend HTML and proxied health return success.
- Normal-account KeyboardInterrupt shutdown stops servers and releases their ports.
- npm audit and pip-audit of the final locked dependencies find no known vulnerabilities.

## Open issues

One upstream Starlette/AnyIO deprecation warning remains visible. No data provider,
model, persistence, authentication, production hosting or chosen license yet.

The sandbox terminal did not deliver Ctrl+C and its process permissions impeded
taskkill; a reload worker required separately verified cleanup. Normal-account
shutdown passed. The launcher now reports process-tree termination denial clearly
and attempts cleanup of every sibling instead of silently swallowing the failure.

The first hosted Linux run caught a Windows-only type constant. Explicit platform
branches fixed it; Linux type checking and both hosted OS jobs now pass. This is
why hosted validation is part of the foundation rather than a documentation claim.

## Next action

Start M1 with one provider/series slice; use `dev` as the feature branch base.
Read state, constraints and relevant ADRs before changing architecture.
