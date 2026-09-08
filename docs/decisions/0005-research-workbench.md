# ADR 0005: Official sources and an expert research workbench

- Status: Accepted
- Date: 2026-09-08

## Context

The owner requests additional sources, forecasting improvements, a complete UI/UX
pass inspired by Notion and Spotify, and frequent commits. This extends the earlier
provider deferral in ADR 0003. The existing explorer and forecasting engine are on dev.

## Decision

Add direct BLS monthly labor/price data and ECB monthly exchange rates without
credentials or additional services. Publish the supported catalog scope explicitly;
keep FRED and World Bank catalog search. Preserve exact response bytes, reported
units, missing values, observation flags and retrieval provenance. Never silently
truncate a provider response or claim historical-vintage availability.

Extend the statistical model bench with a historical mean baseline and configurable
autoregression. Use the same chronological validation and final holdout as existing
models. Rank comparisons by validation RMSE and report improvement over naive in
Python. Do not automatically tune parameters or select models using holdout scores.
Preserve compatibility with immutable runs saved by the previous engine.

Use a neutral canvas, dark persistent navigation, restrained green actions, clear
numerical hierarchy, accessible contrast and progressive disclosure. Organize
source discovery, data inspection, model configuration and saved work consistently.
Use semantic controls, keyboard focus, explicit empty/error states and responsive
layouts. Calculations remain in Python; TypeScript presents results.

## Consequences

BLS unregistered access has limited history and daily quotas. ECB integration is
scoped to monthly reference FX series, avoiding an implied trading calendar.
Additional models are candidates, not claims of superior forecasts. Revision bias,
univariate scope and conditional intervals remain visible limitations. No new
runtime dependencies, hosting, API keys or synthetic product data are necessary.

## References

- [BLS API signatures](https://www.bls.gov/developers/api_signature_v2.htm)
- [BLS API limits](https://www.bls.gov/developers/api_faqs.htm)
- [ECB API examples](https://data.ecb.europa.eu/help/api/useful-tips)
- [AutoReg](https://www.statsmodels.org/stable/generated/statsmodels.tsa.ar_model.AutoReg.html)
- [Forecast accuracy](https://otexts.com/fpp3/accuracy.html)
- [Notion navigation](https://www.notion.com/help/navigate-with-the-sidebar)
- [Spotify accessibility](https://engineering.atspotify.com/2023/03/encore-x-accessibility-a-balancing-act)
