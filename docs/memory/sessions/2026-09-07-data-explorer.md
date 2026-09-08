# Handoff: data explorer

## Context

Owner requested initial implementation with polished Notion/Robinhood-inspired
UI/UX and easy FRED/World Bank search/loading, with frequent commits. Started from
updated `dev` at `72cf663`; all work is on `feat/data-explorer`. M1 expanded from
one provider to two; no additional providers, models or dependencies were added.

## Changes

- [ADR 0003](../../decisions/0003-data-explorer.md) records provider scope, storage,
  credential handling and design direction. Constraints/roadmap now match M1.
- Python adapters normalize FRED and World Bank series, preserve nulls, paginate
  fully, validate World Bank database identity and surface safe upstream errors.
- World Bank catalog indexes all indicator metadata; WDI sorts first, with source
  IDs retained for other databases. Observation histories use small pages without
  redundant page-1/date parameters; Python selects the requested calendar years.
- Exact response bytes and normalized manifests are published atomically via
  content-addressed files under ignored `data/`. Downloads verify manifest integrity.
- Key is configured only in ignored root `.env`; environment overrides are supported.
  No credential value, source dataset or generated research output is committed.
- React explorer offers source switching, keyword search, recent session navigation,
  country selection, chart/table views, date filters, provenance and JSON downloads.
  Chart axes retain readable pixel sizes on mobile and do not bridge nulls.
- Generated TypeScript contracts are checked by the standard project gate.
- Six small implementation/design/fix commits precede this documentation handoff.

## Verification

- `python scripts/project.py check`: 44 passed, no skips, 100% backend branch
  coverage; every offline quality gate passes on Windows.
- Ruff, strict mypy, ESLint, TypeScript and production Vite build pass.
- Live FRED search and UNRATE loading pass. World Bank WDI GDP loads for USA/Canada;
  full catalog search finds 594 GDP matches and country/aggregate lookup works.
- Desktop and 390px viewport browser review: charts/tables, provider selection,
  country switching, search pagination, empty search, Ctrl+K and modal Escape work.
  A custom 2025 FRED retrieval returns 12 periods, including the original null.
  Mobile document width equals content width; provenance remains readable.
- Snapshot attachment endpoint returns 200, attachment filename and all 944 UNRATE
  observations for the initial full-history load. Offline tests compare downloaded
  content with the normalized snapshot. The in-app browser did not expose a Blob
  download event, so export now uses a normal server attachment URL.
- Source-37 live load timed out; the app correctly surfaces provider failure.
- Credential scan: the configured key is absent from tracked files and frontend
  build output; `.env` is ignored.
- No dependency manifests/locks changed. Hosted CI and fresh networked dependency
  audits were not run during this local implementation task.

## Open issues

Latest-revision data is unsuitable for vintage-correct backtests. World Bank
catalog metadata can omit units/frequency, and upstream availability varies.
Only supported provider API datasets are in scope, not every file/product on the
organizations' websites. Recent navigation is not persisted across page reloads.
Storage is local to one user with manual retention. Auth/deployment, models,
transforms and forecasts remain unimplemented. Existing AnyIO deprecation remains.

## Next action

Review the feature branch and open a PR to `dev` for hosted gates. Launch locally
with `python scripts/project.py dev`; World Bank needs no key, and FRED reads the
existing ignored backend configuration. Scope M2 separately before adding models.
