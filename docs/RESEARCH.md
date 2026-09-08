# Research correctness contract

Correctness requirements for implemented and future research features. See the
[forecasting methods guide](FORECASTING.md) for current behavior and limitations.

## Economic data

Preserve provider/series IDs, source URL/license, units, frequency, timezone,
seasonal adjustment, observation dates, retrieval time and release/vintage metadata.
Separate immutable raw inputs from transformed series. Identify exact inputs with
checksums or equivalent content identifiers.

Observation, publication and retrieval time are distinct. Backtests may use only
information available at the forecast origin. Without historical vintages, label
results revision-biased rather than real-time historical forecasts.

Missing is not zero. Never silently fill, resample, annualize, adjust inflation or
change units. Record transformation parameters/order. Provider failures must not
be replaced with plausible synthetic data.

## Simulations and forecasts

Each run should record ID, UTC timestamp, data snapshot IDs/checksums, code commit
and dirty state, environment/lock identity, model version, configuration,
assumptions, random seed/generator and outputs. Use explicit random generators.
Record platform/numerical tolerances when bitwise reproducibility is unrealistic.

Begin with a documented baseline. Use time-ordered splits and rolling-origin
evaluation, fitting preprocessing only on training data. Report horizon-specific
errors against baseline; separate holdout from tuning. Explain uncertainty
intervals. Conditional scenarios are not automatically causal estimates.

Validate shapes, ordered times, duplicates, units, bounds, finite values, missingness,
deterministic seeds and failure modes. Add invariants and reference-result tests
with the first calculations. Separate network tests from deterministic offline
tests and respect provider rate limits.
