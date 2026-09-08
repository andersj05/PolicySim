# Current state

## Updated

2026-09-08 (UTC) — official data and research workbench on `feat/research-workbench`.
Created from current `origin/dev` (`ab9c9cd`); no protected branch changed.

## Implemented

- Four providers: existing FRED/World Bank catalog search, 10 supported direct BLS
  monthly labor/price series, 21 ECB monthly reference currencies plus exact EXR.M keys.
- Immutable raw responses/snapshots, explicit source scope, null preservation,
  BLS footnotes, ECB status flags and unit/identity checks. No new keys/dependencies.
- Seven methods: naive, historical mean, drift, seasonal naive, ETS, ARIMA/SARIMA
  and fixed-lag autoregression. Stable roots, full-rank designs and sample bounds.
- Validation-only RMSE ranks/skill and error bias. Chronological folds, separate
  final holdout, analytical intervals, immutable runs and old-run compatibility.
- Calendar/sample readiness with explicit complete-segment selection. No imputation;
  applying an earlier range changes the forecast origin visibly.
- New overview, source collections, dark navigation, saved library, focus mode,
  clearer model results and responsive tables. All source artwork is decorative CSS.
- Existing CSV import, transformations, statistics/ADF/ACF, downloads and provenance.
- [Source research](../SOURCE_RESEARCH.md), [methods](../FORECASTING.md), and
  [ADR 0005](../decisions/0005-research-workbench.md) explain scope and follow-ons.
- Seven implementation/research commits through `1e59129`; the handoff commit follows.

## Verified

- Full `python scripts/project.py check`: 89 tests pass, none skipped, 98.51%
  combined statement/branch coverage; contracts, repository policy, Ruff, strict
  mypy, frontend lint/types/build and Prettier all pass.
- Numerical reference tests cover mean variance, AR(1) OLS forecasts and multistep
  variance, scaling, unstable/rank-deficient fits, validation isolation and ties.
- Live ECB and BLS downloads preserve complete responses. All seven models fit on
  the live monthly ECB USD/EUR selection; the saved run reopens in the browser.
- Browser: overview/source navigation, BLS/ECB loading, model selection/ranking,
  saved runs, focus mode, source saving and explicit complete-history suggestion.
- Mobile 390px: document width 375px with scrollbar; wide comparison tables scroll
  internally. Header overlap fixed. Default viewport restored after review.
- Tab focus movement verified. Ctrl/Cmd+K and slash handling implemented; shortcut
  synthesis in the in-app browser did not trigger these, so not browser-verified.
- No dependency changes. Hosted Linux/Windows gates and dependency audits were not
  rerun in this task; one existing AnyIO deprecation warning remains.

## Open issues

- Evaluations use latest revisions, not verified historical information sets.
- BLS catalog is scoped to 10 series; unregistered API: 10 calendar years/request,
  25 requests/day. UI loads latest 10 calendar years; earlier requests via API.
- ECB supports monthly reference FX, not the full SDMX catalog or trading prices.
- Live ECB initially timed out; retry succeeded. Provider availability remains external.
- Forecasts remain univariate, with complete regular calendars and conditional
  intervals. No exogenous models, ensembles, causal scenarios or automatic tuning.
- Jobs are synchronous with one local lock. No cancellation, hosted auth, retention
  management or backup UI. Source terms and the owner's deferred license still apply.

## Next action

Review the new branch and open a PR to `dev` when ready. Start or reopen the local
app with `python scripts/project.py dev`; see the latest handoff for verification.
