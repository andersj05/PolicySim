# ADR 0003: Provider-backed data explorer

- Status: Accepted
- Date: 2026-09-07

## Context

The owner requests the first implementation and a polished research workspace,
with keyword/ID search and observation loading from both FRED and World Bank.
This expands the original single-provider M1. Analysis and forecasting remain M2.

## Decision

Use backend adapters for the FRED v1 and World Bank v2 Indicators APIs. Search
FRED remotely; index World Bank indicator metadata with a bounded local cache,
preserving database IDs because indicator codes can occur in multiple databases.
Expose countries and aggregates from World Bank. This covers these APIs, not every
file or product on either organization's website. Do not add another provider yet.

Keep normalized series and observation contracts independent of HTTP and adapters.
Generate TypeScript contracts from Pydantic schemas and check drift. Preserve nulls,
units, frequency where reported, seasonal adjustment, source notes, source links,
retrieval times, observation dates and available vintage metadata. Never silently
truncate paginated downloads or transform observations. Charts are presentation only.

Store exact observation/metadata response bytes as immutable SHA-256-addressed
files under ignored `data/`, with normalized snapshot manifests. No database or
research model is needed. Local downloads retain provenance; provider-specific
terms still apply. Latest-revision data is unsuitable for vintage-correct backtests.

The FRED key is read only by Python from environment or ignored root `.env`.
Never return it, include it in persisted request URLs, or relay provider exception
text to the UI. Requests use fixed provider hosts, bounded timeouts and pagination.
This is a loopback local app; authentication and public deployment remain deferred.

The UI uses a quiet sidebar, generous whitespace, a single emerald accent, a
search-first catalog, readable numerical hierarchy, a time chart and accessible
observation table. All actions must work; no mock economic values or pretend tools.

## Consequences

World Bank's first catalog search can take longer while metadata is indexed.
Provider availability and quotas remain external dependencies. Local snapshots
consume disk until manually removed; retention management is deferred. A filesystem
store is sufficient for this milestone but is not a multi-user storage design.

## References

- [FRED search](https://fred.stlouisfed.org/docs/api/fred/series_search.html)
- [FRED observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)
- [World Bank indicators](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries)
- [World Bank API structure](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures)
