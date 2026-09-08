# Forecasting and analysis

## Workflow

Open FRED or World Bank data, or import a comma-delimited UTF-8 CSV. CSV import
requires a date column, a numeric value column, units and an explicit frequency.
The preview shows five rows. Blank, NA, N/A, null and dot values remain missing;
duplicates within a period are rejected. The original uploaded text is saved
locally. Imported data is labeled Local CSV, without acquiring provider provenance.

Save series to reopen their immutable snapshots. The browser stores at most 30
shortcuts; the underlying data lives in the ignored local `data/` directory.
Removing a shortcut does not delete a snapshot. Clearing browser storage removes
shortcuts, but saved forecasts remain accessible through the Forecasts page.

Data and Statistics share date selection and transformation settings. Available
transforms are lagged difference, lagged percent change, natural log and trailing
rolling mean. No annualization is implicit. A zero percent-change denominator is
missing; log rejects nonpositive observations; rolling windows require all values.
Forecasts always use the selected original series in its original units, separately
from display transformations. Table values can be sorted and filtered for missingness,
with optional full precision. CSV and JSON exports retain unrounded values.

Statistics include sample standard deviation, mean, median, quartiles, bounds,
autocorrelation and an augmented Dickey–Fuller test. ADF uses a constant and AIC lag
selection up to min(12, floor(n/2) − 2). Lag diagnostics require at least 12 consecutive,
nonconstant numeric observations; internal missing periods are never compressed out.
A small ADF p-value is evidence against its unit-root null, not a model-selection rule.

## Models

The engine implements five univariate methods. Naive is included in every comparison.

| Method         | Configuration                                 | Forecast behavior                                                          |
| -------------- | --------------------------------------------- | -------------------------------------------------------------------------- |
| Naive          | None                                          | Last observation; random-walk innovation variance                          |
| Drift          | None                                          | Last observation plus average historical change                            |
| Seasonal naive | Seasonal period m                             | Repeat the last m observations                                             |
| ETS            | Additive trend, damping, additive seasonality | Estimated additive-error exponential smoothing                             |
| ARIMA / SARIMA | p,d,q; P,D,Q,m; optional constant             | State-space maximum likelihood with stationarity/invertibility enforcement |

Seasonal period is user-selected: 1 is nonseasonal, 4 can represent annual cycles
in quarterly data, and 12 can represent annual cycles in monthly data. This is not
a claim that a particular series is seasonal. ETS seasonal components and SARIMA
seasonal orders remain separate explicit settings. A SARIMA constant acts as drift
after first differencing; it is not an unconditional level intercept in every model.

Every fit is scaled by its own training standard deviation (with a constant-series
fallback). Predictions, variances and residuals return to original units. No statistic
from a future evaluation window enters scaling. Parameter details record this scale.
ETS uses estimated initialization and at most 500 optimizer iterations; SARIMA uses
at most 200. Nonconvergence or invalid numerical output fails that model explicitly.
Successful baselines remain visible; no alternate estimator is silently substituted.

## Evaluation and uncertainty

For n observations, horizon h and k validation windows, the first training size is
n − (k + 1)h. Each origin expands its training data by h observations. The k validation
blocks precede a separate final h-period holdout. All models share those origins.
There is no automated hyperparameter search or automatic selection. The final future
forecast refits each successful model on all selected observations. Repeated manual
tuning against the holdout undermines its independence.

Results report MAE, RMSE, MASE, observed interval coverage, and validation errors by
forecast horizon. MASE divides absolute errors by training-only mean absolute lag-m
changes; m=1 gives the nonseasonal scale. Zero or numerically unusable scaling makes
MASE unavailable. Coverage from a small number of predictions is not a calibration
guarantee. Comparisons of errors in different source units are not meaningful.

Prediction intervals use 80% or 95% Gaussian quantiles. Benchmarks implement analytical
forecast-error variances, including horizon growth and drift-estimation uncertainty.
ETS and SARIMA use statsmodels analytical prediction variances. Intervals are
conditional on fitted models and parameters; they omit model/parameter uncertainty,
future structural breaks and revisions. They are not causal policy scenarios.

The final fit includes residual mean and an approximate Ljung–Box diagnostic.
The lag is min(10, floor(residual_count/5)); ARIMA adjusts for AR/MA orders and ETS
for estimated parameters. An unavailable p-value is shown when adjusted degrees of
freedom or residual variation are insufficient. Residual checks supplement, rather
than replace, out-of-sample evaluation.

## Boundaries and records

Supported calendars are annual, quarterly, monthly, weekly and calendar-daily.
Labels are normalized to period starts without aggregating values. Absent calendar
periods become explicit nulls. Forecasts reject internal missingness; the optional
edge-trimming policy records the excluded periods and resulting forecast origin.
Trading-day calendars and mixed frequencies are unsupported. A complete selected
range is required; the engine does not impute data.

Local forecast limits: 2,000 selected periods, horizon 1–36, 2–5 validation windows,
and seasonal period 1–24. The initial training window needs at least 20 observations;
seasonal models need three cycles and higher ARIMA orders impose additional limits.
Only one forecast runs at a time. Requests are synchronous; navigating away does not
cancel server computation, and completed runs are saved. Worker cancellation,
multi-user job isolation, multivariate models and exogenous inputs remain future work.

Run JSON includes the snapshot ID, selected history, all settings and outputs,
UTC creation time, engine version, commit/dirty state, backend source hash, lock hashes,
package versions, platform and assumptions. No RNG is used. Run files are atomically
published under SHA-256 names; reads verify integrity. Latest-revision source inputs
make historical evaluations revision-biased, without verified information availability
at each origin. Floating-point output can vary slightly across platforms.

## Method references

- [Time series cross-validation](https://otexts.com/fpp3/tscv.html)
- [Forecast accuracy](https://otexts.com/fpp3/accuracy.html)
- [Benchmark prediction intervals](https://otexts.com/fpp3/prediction-intervals.html)
- [Residual diagnostics](https://otexts.com/fpp3/diagnostics.html)
- [statsmodels ETS](https://www.statsmodels.org/stable/examples/notebooks/generated/ets.html)
- [statsmodels SARIMAX](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html)
- [ADF implementation](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html)

The committed lock selects statsmodels 0.14.6. Installed APIs and deterministic
reference tests, including random-walk equivalence, verify the implementation.
