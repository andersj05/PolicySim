# Roadmap

## M0 — foundation

Versioned memory/ADRs, main/dev/feat workflow, locked toolchains, terminal launcher,
health API, frontend placeholder, CI, audits, hooks and contributor guidance.
See current memory for measured verification.

## M1 — first data vertical slice

Expanded by the owner to FRED and World Bank. Search provider catalogs and load
series with country/date selection, charts, tables, provenance snapshots and
explicit failure/empty/loading states. Generated API types and deterministic
provider fixtures are implemented. See [ADR 0003](decisions/0003-data-explorer.md)
and [current verification](memory/STATE.md).

## M2 — reproducible analysis

Implemented: baseline and configurable ETS/SARIMA models, immutable run manifests,
transformations, CSV import, statistical diagnostics, rolling-origin validation,
separate holdout and saved results. Numerical fixtures check closed forms, scale
invariance and temporal isolation. See [methods](FORECASTING.md) and [ADR 0004](decisions/0004-forecast-workspace.md).

## M3 — research workspace

Delivered alongside M2: responsive workspace, model comparison, uncertainty charts,
saved-run browsing and exports. Remaining: scenario editor, run cancellation,
multivariate/exogenous models and saved research notes. Continue accessibility review.

## M4 — distribution

Choose local packaging or hosting based on users. Add appropriate authentication,
job isolation, secrets management, backup/restore and observability. Not M0 scope.
