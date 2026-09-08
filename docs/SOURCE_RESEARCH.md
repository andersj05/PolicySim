# Data and model research — September 2026

This implementation expands the local macroeconomic workflow. It adds no paid
service, runtime dependency or credential requirement. The priorities below are
engineering judgments based on official documentation, not measured promises of
forecast improvement.

## Implemented source coverage

| Source     | Discovery and observations                                                          | Why it belongs here                                        | Limits                                                                                                       |
| ---------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| FRED       | Existing remote keyword/ID search                                                   | Broad macroeconomic catalog                                | Backend API key; contributor terms; latest revisions                                                         |
| World Bank | Existing catalog across databases and country/aggregate selection                   | Cross-country development research                         | Frequency and units can vary by database                                                                     |
| BLS        | 10 supported monthly, seasonally adjusted labor/price indicators; keyword/ID search | Direct employment, participation, wages, headline/core CPI | 10 calendar years per unregistered request; 25 requests/day; UI initially loads the latest 10 calendar years |
| ECB        | 21 reference currencies in search, plus exact `EXR.M.CCC.EUR.SP00.A` keys           | Monthly FX research with explicit quote convention         | Monthly average, foreign currency per euro; not executable market prices or a full ECB catalog               |

BLS coverage includes unemployment, nonfarm/private/manufacturing payrolls,
employment, participation, employment-to-population ratio, average hourly earnings,
headline CPI and core CPI. Metadata is maintained explicitly for these supported
series because catalog metadata is not available in this unregistered workflow.
Annual-average rows are excluded from the monthly series; source footnotes stay
in snapshot notes and exact raw responses. The adapter rejects warning envelopes
that could indicate ignored dates or partial data. See the
[API signatures](https://www.bls.gov/developers/api_signature_v2.htm) and
[limits](https://www.bls.gov/developers/api_faqs.htm).

ECB requests specify the monthly frequency and reference-rate average dimensions.
The parser verifies the returned series key, currency and zero unit multiplier;
it preserves null observations and non-normal status flags. Full discovery across
ECB dataflows requires metadata-driven SDMX navigation, beyond this adapter.
See [ECB retrieval examples](https://data.ecb.europa.eu/help/api/useful-tips) and
[metadata API](https://data.ecb.europa.eu/help/api/metadata).

Both integrations persist exact response bytes and normalized snapshots. Retrieval
time is never represented as publication time. A requested monthly range includes
the months containing the boundary dates, labeled at the first day of each month.

## Implemented model improvements

The model bench adds a historical mean and fixed-lag OLS autoregression to the
existing five methods. Autoregression exposes 1–24 consecutive lags and optional
linear trend, rejects insufficient samples, rank-deficient designs and unstable
roots, and reports conditional analytical intervals. Reference tests compare AR(1)
point forecasts and innovation-variance propagation to independent formulas.
[AutoReg documentation](https://www.statsmodels.org/stable/generated/statsmodels.tsa.ar_model.AutoReg.html)
describes this estimator; [forecast accuracy](https://otexts.com/fpp3/accuracy.html)
motivates common-origin comparisons and explicit error measures.

Validation RMSE ranks and skill relative to naive are computed in Python and do
not use holdout observations. Bias is forecast minus actual. Calendar/sample
readiness runs before estimation and can suggest a complete segment; applying it
is explicit, changes the forecast origin and never fills gaps. No model is claimed
to dominate across datasets, and no hyperparameters are automatically tuned.

## Prioritized follow-on work

These features are researched proposals, not implemented product features.

| Priority | Candidate                                          | Value                                                      | Acceptance boundary                                                                                                     |
| -------- | -------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1        | Vintage-aware FRED/ALFRED evaluation               | Reduces revision look-ahead in historical tests            | Retrieve observations as available at each origin, preserve release/revision dates, and test publication-time isolation |
| 2        | OECD SDMX national accounts and leading indicators | Richer comparable cross-country macro data                 | Metadata-driven dimension selection, bounded queries/cache, release of complete validated pages only                    |
| 3        | BEA national accounts and regional data            | US sector, expenditure and regional research               | Backend-only key, explicit table/line/unit mapping, preserve notes and suppression codes                                |
| 4        | Dynamic regression / ARIMAX                        | Conditional forecasts with observed or scenario predictors | Align calendars; fit transformations inside each fold; require future predictor paths and label scenario uncertainty    |
| 5        | Forecast combinations                              | Compare simple ensembles against individual methods        | Fix members before holdout; estimate weights only inside validation; model correlated forecast errors for intervals     |

FRED exposes historical vintage dates, but vintage dates alone do not establish
the exact information set at every evaluation origin.
[FRED vintage-date API](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html).
OECD publishes SDMX APIs with metadata-aware query construction.
[OECD API guide](https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html).
BEA documents key-based API access and dataset-specific parameters.
[BEA user guide](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf).

Dynamic regression needs predictor information at forecast time, not merely
correlation in a downloaded history.
[Dynamic regression](https://otexts.com/fpp3/dynamic.html).
Ensemble uncertainty cannot be obtained by averaging interval endpoints without
justifying the joint error structure.
[Forecast combination review](https://arxiv.org/abs/2205.04216).

## Design rationale

The overview groups sources into four functional research collections. Persistent
navigation and saved snapshots keep context close, taking inspiration from
[Notion's sidebar](https://www.notion.com/help/navigate-with-the-sidebar).
Dark navigation, clear surface hierarchy, consistent controls and restrained
green accents draw on Spotify's emphasis on a shared accessible system.
[Spotify Encore accessibility](https://engineering.atspotify.com/2023/03/encore-x-accessibility-a-balancing-act).

The workspace adds focus mode, keyboard search, readable numerical hierarchy,
responsive internal table scrolling, explicit readiness messages and validation
comparisons. Decorative source artwork is CSS geometry, not fabricated data.
