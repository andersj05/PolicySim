# ADR 0004: Local analysis and forecasting workspace

- Status: Accepted
- Date: 2026-09-07

## Context

The owner expands M2 to statistical analysis, configurable forecasting, local data
loading and a quieter interface. Existing M1 commits are brought into a new branch
created from dev. Raw inputs and Python research independence remain required.

## Decision

Use NumPy, SciPy, pandas and statsmodels with committed locks. Keep numerical
functions separate from HTTP, storage and provider adapters. Support univariate
naive, drift, seasonal naive, additive ETS and seasonal ARIMA. Expose orders and
seasonal periods explicitly; do not infer that seasonal data needs differencing.
No automatic parameter search, external regressors or causal interpretation.

Use expanding-window, non-overlapping, multi-step validation blocks followed by a
separate final holdout of the same horizon. Evaluate every selected model and a
naive benchmark on identical origins. Show MAE, RMSE, MASE, interval coverage and
per-horizon errors. Refit on all selected observations for the future forecast.
Validation is for comparison; repeated manual tuning against the holdout invalidates
its independence. Latest-revision inputs make historical evaluation revision-biased.

Forecast only regular supported calendars with complete internal observations.
Allow explicitly requested trimming of leading/trailing missing values, recording
the excluded periods. Never fill gaps or silently resample. Scale within each fit
using training data only, then restore original units. Surface failed convergence
per model, retaining successful models without substituting another estimator.

Intervals use Gaussian forecast distributions conditional on estimated parameters:
closed-form benchmark variance and statsmodels analytical ETS/state-space variance.
These omit parameter/model uncertainty, future policy changes and data revisions.
No random simulations are needed; manifests state that no RNG is used.

Save content-addressed immutable run records with input snapshot, selected history,
configuration, exact outputs, code/environment identities and assumptions. Bound
input sizes, orders, horizon and fold counts; serialize local numerical jobs. This
is a local synchronous engine, not a hosted multi-user job service.

CSV imports preserve exact uploaded text locally and require explicit date/value
columns, frequency and units. CSV values never acquire provider provenance. The
UI uses compact provider tabs, large charts, direct Data/Statistics/Forecast tabs,
progressive model controls and a saved-runs view. Technical identities belong in
expandable run details and exports, not primary product copy.

## Consequences

Numerical results can vary slightly across platforms. Dependency locks are necessary
but insufficient for bitwise reproducibility. Monthly, quarterly, annual, weekly
and calendar-daily periods are supported; trading calendars, mixed frequencies,
multivariate VAR/VECM, exogenous scenarios and historical vintages require additional
data contracts and validation. No arbitrary complexity or model superiority claim.

## References

- [Time series cross-validation](https://otexts.com/fpp3/tscv.html)
- [Accuracy and scaled errors](https://otexts.com/fpp3/accuracy.html)
- [Prediction intervals and benchmark variances](https://otexts.com/fpp3/prediction-intervals.html)
- [Residual diagnostics](https://otexts.com/fpp3/diagnostics.html)
- [ETS implementation](https://www.statsmodels.org/stable/examples/notebooks/generated/ets.html)
- [SARIMAX implementation](https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html)
