# Handoff: official sources and research workbench

## Context

Owner requested a new branch, more data sources, stronger forecasting, researched
feature opportunities, a full Notion/Spotify-inspired UI/UX pass and frequent commits.
Fetched origin and created `feat/research-workbench` from `origin/dev` (`ab9c9cd`).
The working tree was clean. Earlier forecasting work was already integrated in dev;
older state/handoff prose describing an outstanding feature PR was stale.

## Changes

- Credential-free BLS adapter for 10 monthly labor/price indicators, with bounded
  unregistered history, source footnotes, warning-envelope rejection and raw snapshots.
- ECB monthly reference FX adapter with 21 discoverable currencies and exact EXR.M
  keys. Validates identity, dates and units; preserves nulls and status flags.
- Historical mean and fixed-lag OLS autoregression added to the original five
  models. Rejects unstable/rank-deficient AR fits. No automatic parameter search.
- Python validation-only ranks, relative RMSE skill and bias, with defaults to keep
  older immutable runs readable. Analytical reference and chronology tests added.
- Readiness endpoint and UI identify gaps/sample limitations and suggest the longest
  complete segment. Applying a suggestion is explicit and changes the origin visibly.
- New overview/source collections, dark navigation, saved-library continuation,
  focus mode, compact forecast headers, clearer comparison tables and mobile layout.
- Source research includes prioritized ALFRED/vintages, OECD, BEA, dynamic regression
  and forecast combinations, each with acceptance boundaries and primary sources.
- No new dependencies, services, credentials, hosted deployment or synthetic product
  data. Calculations remain Python; TypeScript handles presentation and interaction.
- Commits: `d8b1460`, `c021ae5`, `4af4ef7`, `931716e`, `829458d`, `23738a1`, `1e59129`.

## Verification

- Full `python scripts/project.py check` passed: 89 tests, none skipped, 98.51%
  combined statement/branch coverage. Includes launcher tests, repository policy,
  generated contracts, Ruff, strict mypy, frontend lint/types/build and formatting.
- Provider tests verify dates/nulls, identity, units, malformed/warning responses,
  catalog scope, request limits, exact raw persistence and API boundaries.
- Mean intervals match closed forms. AR(1) forecasts/variance match independent OLS
  and innovation propagation; scaling, rank deficiency, instability, holdout isolation,
  equal-rank ties and undefined zero-baseline skill are covered.
- Live complete BLS and ECB downloads succeeded. A real ECB monthly USD/EUR run
  completed all seven methods and reopened from Saved forecasts without refitting.
- Browser checked discovery, sources, selection, validation/ranking, saving, focus
  mode and missing-period readiness. BLS complete-segment selection changed dates
  and passed the subsequent readiness check without filling any observations.
- Mobile at 390px: document/content viewport 375px, wide tables scroll inside panels.
  Fixed a header overlap found in visual QA; desktop viewport restored.
- Keyboard Tab focus works. Ctrl/Cmd+K and slash are implemented but the in-app
  browser's synthesized shortcut presses did not activate them; this remains unverified.
- Initial sandbox test failures were temp-directory/npm-runtime access errors;
  running checks as the owning user resolved them. Live ECB's first UI load timed
  out; retry and direct complete retrieval succeeded. Existing AnyIO warning remains.
- No audits or hosted CI runs in this task; dependency locks are unchanged.

## Open issues

Latest-revision evaluations remain revision-biased. Sources have explicit scope:
BLS is not a full catalog, ECB is monthly reference FX only. BLS's UI source range
is the latest 10 calendar years; earlier ranges can be requested through the API.
Individual models may fail even after calendar/sample readiness succeeds.

Univariate regular calendars only; no imputation, vintage-correct evaluation,
external regressors, model combinations, causal forecasts or automated tuning.
One synchronous local job; no cancellation/auth/retention/backup UI. Formal
accessibility certification and keyboard-shortcut verification remain outstanding.
Provider terms and the owner's deferred repository license apply.

## Next action

Review `feat/research-workbench` and open a PR targeting `dev` for hosted gates.
Run `python scripts/project.py dev` to open the app locally. The verified existing
launcher was stopped to free both ports for the full check; restart it for review.
No branch push, PR, merge or deployment was requested or performed.
