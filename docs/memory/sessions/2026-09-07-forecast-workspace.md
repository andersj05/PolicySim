# Handoff: forecasting workspace

## Context

Owner requested continued frontend refinement, concise functional copy, easier data
loading/manipulation and researched statistical forecasting, with frequent commits.
Created `feat/forecast-workspace` from `dev` (`72cf663`) and fast-forwarded the existing
M1 `feat/data-explorer` work (`d67a5b5`) into it. No protected branch was modified.

## Changes

- Replaced hero copy, source cards and redundant labels with a compact catalog,
  saved-data sidebar, series workspace and saved-run library. Tables sort numeric
  values, expose full precision and missing-only filters, and export unrounded CSV.
- CSV dialog previews column mappings and requires frequency/units. Input text and
  normalized local snapshots are immutable; no uploaded/provider data is committed.
- Pure Python analysis modules support explicit calendars, missing periods,
  transformations, descriptive statistics, autocorrelation and ADF diagnostics.
- Pure forecasting engine fits naive/drift/seasonal-naive benchmarks, additive ETS
  and configurable seasonal ARIMA. Validation uses expanding origins with matching
  multi-step blocks and a final holdout. No random splits or automatic model tuning.
- Forecast UI shows Gaussian prediction intervals, validation/holdout errors,
  per-horizon errors, residual diagnostics and full results. Changed settings keep
  previous output labeled as stale. Switching tabs preserves controls.
- Runs save configuration, exact inputs/outputs, source identity, commit/dirty state,
  code/lock hashes, package versions and assumptions. A local job lock serializes work.
- Added NumPy, pandas, SciPy and statsmodels with a committed uv lock; no frontend
  dependency or extra service. [ADR 0004](../../decisions/0004-forecast-workspace.md)
  and [methods guide](../../FORECASTING.md) document the research choices.
- Coherent implementation commits: `49cbf82`, `87ad830`, `b1e6284`, `e9bedb4`, `c6d0836`.

## Verification

- Full `python scripts/project.py check` with development ports free: 66 tests
  passed, none skipped, 98.52% combined statement/branch coverage. Repository,
  contracts, Ruff, strict mypy, frontend lint/types/build and formatting all pass.
- Targeted numerical suite: 22 pass. Baseline interval formulas checked against
  closed forms; ARIMA(0,1,0) matches naive point forecasts and horizon variance;
  scale invariance, holdout isolation, model failures, CSV/API roundtrips and run
  integrity are covered. Ruff, strict mypy and frontend lint/types/build pass.
- Python all-groups locked/hash-verified pip-audit and npm audit: no vulnerabilities.
- Live FRED GDP run completed all default models and persisted/reopened from the UI.
  Browser checks covered CSV import of those public observations, quarterly mapping,
  transformations, summary/ADF output, full precision, sorting and missing filters.
- Mobile forecast and data tables scroll internally; document width equals viewport
  width. Holdout actual/prediction chart and saved-data selector remain usable.
- Initial sandbox tests had temp/cache permission and launcher cleanup failures;
  outside-sandbox checks resolved those environmental failures. Both dev servers
  stopped during a long browser tool call; restarting restored data/import operation.
- During release, hosted Windows checks and dependency audit passed. Linux mypy
  found a Windows-only subprocess constant in a conditional expression; use a
  platform-guarded assignment, matching the launcher. Updated hosted gates pending.
  Local Linux-target mypy passes; the post-fix local test run passes 65 tests with
  the launcher test skipped because the review app occupies its ports (98.34% coverage).
  The pre-existing AnyIO deprecation remains.

## Open issues

Latest revisions make historical evaluation revision-biased. Models are univariate;
no verified vintage availability, business-day calendars, multivariate/exogenous
models, imputation, scenarios or causal claims. Internal gaps are rejected with dates
in the error. Naive remains usable for constant series; advanced models can fail
convergence or minimum sample checks. Intervals condition on fitted parameters.

Jobs are synchronous with bounded iterations/configuration and one local run at a
time. Navigating away does not cancel computation. No retention/deletion UI, auth,
hosting or backup/restore UI. Saved shortcuts depend on browser storage; run files
persist independently. UI browser testing is manual, not an automated accessibility
certification. Source terms and the owner's deferred license choice still apply.

## Next action

Review/open a PR to `dev` for hosted Linux/Windows checks. Launch the local app
with `python scripts/project.py dev`.
