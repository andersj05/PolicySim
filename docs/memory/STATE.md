# Current state

## Updated

2026-09-07 � M1 data explorer implemented on `feat/data-explorer` from `dev`.

## Implemented

- Live FRED keyword/ID search and observations; backend-only ignored local key.
- World Bank Indicators API catalog search across databases and country/aggregate
  selection. Entire catalog is indexed with a one-hour in-process cache.
- Calm responsive explorer, provider cards, source results, charts, exact-value
  tables, calendar-year chart ranges, retrieval dates and source guide.
- Nulls and original values preserved; explicit loading, failure and empty states.
- Atomic SHA-256 raw response files and normalized snapshot manifests under ignored
  `data/`; verified JSON attachment endpoint for saved snapshots.
- Generated TypeScript domain contracts and drift check; deterministic fixtures for
  pagination, errors, provenance, concurrent storage, exports and secret redaction.
- Foundation workflow/CI remains; no new dependencies or services were introduced.

## Verified

- `python scripts/project.py check`: passes with 44 tests, no skips and 100%
  backend branch coverage. Ruff, mypy, contracts, frontend lint/types/build and format pass.
- Live FRED search and UNRATE observations work with local backend configuration.
- Complete World Bank catalog search returns 594 GDP matches; WDI GDP loads for
  United States and Canada. Country/aggregate catalog loads.
- Browser: provider switching, catalog pagination, table view, empty search,
  Ctrl+K, modal Escape, responsive desktop/mobile and no narrow-window overflow.
- Snapshot HTTP attachment returns status 200 and complete normalized observations.
- Custom 2025 FRED date retrieval returns 12 monthly periods with nulls retained.
- Configured key absent from tracked files and frontend build; `.env` is ignored.

## Open issues

- Some World Bank requests return upstream timeouts/gateway errors; a live source-37
  probe timed out. Source-specific behavior has deterministic coverage, but not all
  databases have been live-verified. Retry errors; never substitute invented values.
- Latest revisions only, not historical-vintage datasets. Catalog metadata may omit
  units/frequency; UI labels omissions. World Bank date selection uses calendar years.
- Recent navigation is session-local. No saved workspace, models, auth, hosting or
  storage retention UI. Snapshots require manual local cleanup.
- One existing Starlette/AnyIO deprecation warning. Hosted CI not run for this branch.
- License remains deferred. Public source datasets remain subject to provider terms.

## Next action

Review this feature branch, then open a PR to `dev` and run hosted Linux/Windows
quality gates before integration. M2 research models require a separate scope.
