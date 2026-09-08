"""Reference formulas, chronology and failure boundaries for added estimators."""

from datetime import date

import numpy as np
import pytest
from policysim.analysis import next_date
from policysim.domain import Observation
from policysim.forecasting import FitError, evaluate, fit_model
from policysim.research_contracts import ForecastRequest, ModelOptions


def ar_history() -> np.ndarray:
    rng = np.random.default_rng(8241)
    y = np.zeros(240)
    for i in range(1, len(y)):
        y[i] = 0.4 + 0.65 * y[i - 1] + rng.normal(0, 0.8)
    return y


def test_mean_forecast_and_estimation_variance() -> None:
    y = np.array([1.0, 4.0, 5.0, 10.0])
    fit = fit_model(y, "mean", 4, ModelOptions())
    np.testing.assert_allclose(fit.mean, [5, 5, 5, 5])
    np.testing.assert_allclose(fit.variance, np.var(y, ddof=1) * 1.25)
    np.testing.assert_allclose(fit.residuals, y - 5, atol=1e-14)
    constant = fit_model(np.ones(30), "mean", 3, ModelOptions())
    assert np.all(constant.variance == 0)


def test_autoreg_matches_ols_and_ar1_multistep_variance() -> None:
    y = ar_history()
    fit = fit_model(y, "autoreg", 6, ModelOptions(ar_lags=1))
    design = np.column_stack((np.ones(len(y) - 1), y[:-1]))
    intercept, phi = np.linalg.lstsq(design, y[1:], rcond=None)[0]
    expected = []
    value = y[-1]
    for _ in range(6):
        value = intercept + phi * value
        expected.append(value)
    np.testing.assert_allclose(fit.mean, expected, rtol=1e-12)
    errors = y[1:] - design @ np.array([intercept, phi])
    variance = np.mean(errors**2) * np.cumsum(phi ** (2 * np.arange(6)))
    np.testing.assert_allclose(fit.variance, variance, rtol=1e-12)
    scaled = fit_model(y * 1e9, "autoreg", 6, ModelOptions(ar_lags=1))
    np.testing.assert_allclose(scaled.mean / 1e9, fit.mean, rtol=1e-12)
    np.testing.assert_allclose(scaled.variance / 1e18, fit.variance, rtol=1e-12)
    assert len(fit.residuals) + fit.burn == len(y)
    assert (
        fit_model(
            y + np.arange(len(y)) * 0.1, "autoreg", 2, ModelOptions(ar_lags=2, ar_trend="linear")
        ).degrees
        == 2
    )


def test_autoreg_sample_constant_rank_and_unstable_boundaries() -> None:
    with pytest.raises(FitError, match="training window"):
        fit_model(ar_history()[:30], "autoreg", 3, ModelOptions(ar_lags=12))
    with pytest.raises(FitError, match="constant"):
        fit_model(np.ones(100), "autoreg", 3, ModelOptions())
    with pytest.raises(FitError, match="rank deficient"):
        fit_model(np.arange(100, dtype=float), "autoreg", 3, ModelOptions(ar_lags=3))
    rng = np.random.default_rng(81)
    explosive = np.array([1.06**i for i in range(100)]) + rng.normal(0, 0.001, 100)
    with pytest.raises(FitError, match="unstable"):
        fit_model(explosive, "autoreg", 3, ModelOptions(ar_lags=1))


def test_validation_ranking_is_independent_of_holdout_and_refit() -> None:
    rows = [
        Observation(date=next_date(date(2000, 1, 1), "monthly", i).isoformat(), value=float(v))
        for i, v in enumerate(ar_history())
    ]
    config = ForecastRequest(
        snapshot_id="a" * 64,
        horizon=4,
        folds=3,
        models=["mean", "autoreg"],
        options=ModelOptions(ar_lags=1),
    )
    before = evaluate(rows, "monthly", config)
    for row in rows[-4:]:
        row.value = (row.value or 0) + 2
    after = evaluate(rows, "monthly", config)
    assert all(item.status == "success" for item in before + after)
    for left, right in zip(before, after, strict=True):
        assert left.validation == right.validation
        assert left.validation_rank == right.validation_rank
        assert left.rmse_skill == right.rmse_skill
        assert [p.value for p in left.holdout_points] == [p.value for p in right.holdout_points]
        assert left.validation is not None and before[0].validation is not None
        assert left.rmse_skill == pytest.approx(
            1 - left.validation.rmse / before[0].validation.rmse
        )
        assert left.validation.bias == pytest.approx(
            np.mean([p.value - p.actual for p in left.validation_points])
        )
    assert min(item.validation_rank or 99 for item in before) == 1


def test_zero_error_rank_ties_and_undefined_skill() -> None:
    rows = [Observation(date=str(1900 + i), value=1) for i in range(40)]
    results = evaluate(
        rows,
        "annual",
        ForecastRequest(snapshot_id="a" * 64, horizon=2, folds=2, models=["mean", "autoreg"]),
    )
    assert [item.validation_rank for item in results] == [1, 1, None]
    assert all(item.rmse_skill is None for item in results)
