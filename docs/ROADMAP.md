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

Baseline model, run manifest, transformations, deterministic tests, rolling-origin
evaluation and saved results. Verify numerical tolerances against references.

## M3 — research workspace

Scenario editor, run lifecycle/cancellation, comparison, uncertainty, saved notes
and exports. Review accessibility and representative research workflows.

## M4 — distribution

Choose local packaging or hosting based on users. Add appropriate authentication,
job isolation, secrets management, backup/restore and observability. Not M0 scope.
