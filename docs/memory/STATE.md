# Current state

## Updated

2026-09-07 — M2 analysis/forecasting implemented on `feat/forecast-workspace`.

## Implemented

- Compact data workspace with functional labels, larger charts, accessible tables,
  persistent snapshot shortcuts, CSV preview/import and mobile layouts.
- FRED and World Bank discovery/loading retained, with immutable source snapshots.
- Python calendar normalization, explicit missing periods, differences, percent
  changes, natural log, trailing means, summary statistics, ACF and ADF.
- Naive, drift, seasonal naive, additive ETS and configurable ARIMA/SARIMA models.
- Training-only scaling; expanding multi-step validation; separate final holdout;
  MAE/RMSE/MASE/coverage and per-horizon errors. No automatic model selection.
- Analytical intervals, residual diagnostics, holdout actual/prediction overlays,
  immutable saved runs, full JSON downloads and numerical environment identities.
- Single local job lock and bounded configurations. Generated frontend contracts.
- Five implementation commits are
  `49cbf82`, `87ad830`, `b1e6284`, `e9bedb4`, `c6d0836`.
- [Methods](../FORECASTING.md) and [ADR 0004](../decisions/0004-forecast-workspace.md)
  document supported methods, assumptions and limits.

## Verified

- Full `python scripts/project.py check`: 66 tests passed, none skipped, 98.52%
  combined statement/branch coverage. Repository, contracts, Ruff, strict mypy,
  frontend lint/types/build and formatting checks all pass.
- Targeted numerical tests: 22 pass, including analytical baseline formulas,
  random-walk equivalence, scale invariance, chronological isolation and failures.
- Frontend lint/types/production build pass after numerical-display refinements.
- Locked Python runtime/dev audit: no known vulnerabilities. npm audit: zero.
- Live FRED GDP: all three default models fit, evaluate and save; saved run reopens.
- Browser: CSV import with explicit quarterly frequency/units, transformed GDP
  statistics, sort/full precision/missing-only controls, saved shortcuts and runs.
- Mobile 390px viewport: document width equals viewport content width (375px with
  scrollbar); wide tables scroll internally. Default viewport restored.

## Open issues

- Historical evaluations use latest revisions, without verified historical vintages.
- Forecasts are univariate on regular calendars. Trading calendars, imputation,
  exogenous/multivariate models, scenarios and job cancellation are not implemented.
- Forecasts require complete internal observations; FRED UNRATE currently has an
  internal missing period in the recent range. Choose a complete range explicitly.
- Local jobs are synchronous. Storage retention, auth/hosting and backup UI deferred.
- Browser testing encountered stopped dev servers; restarting the documented launcher
  restored operation and CSV import passed. One existing AnyIO deprecation remains.
- Linux/hosted CI not run. Provider availability/terms and deferred license still apply.

## Next action

Review this branch and open a PR to `dev` for hosted gates. Launch the local app
with `python scripts/project.py dev`.
