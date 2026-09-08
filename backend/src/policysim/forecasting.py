"""Univariate models and chronological evaluation, independent of I/O boundaries."""

import warnings
from dataclasses import dataclass, field
from math import isfinite
from statistics import NormalDist

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from numpy.typing import NDArray
from statsmodels.stats.diagnostic import acorr_ljungbox  # type: ignore[import-untyped]
from statsmodels.tsa.ar_model import AutoReg  # type: ignore[import-untyped]
from statsmodels.tsa.exponential_smoothing.ets import ETSModel  # type: ignore[import-untyped]
from statsmodels.tsa.statespace.sarimax import SARIMAX  # type: ignore[import-untyped]

from policysim.analysis import calendar_rows, next_date, parse_date
from policysim.domain import DataError, Observation
from policysim.research_contracts import (
    Accuracy,
    EvaluationPoint,
    ForecastPoint,
    ForecastReadiness,
    ForecastRequest,
    HorizonAccuracy,
    ModelName,
    ModelOptions,
    ModelResult,
    NamedValue,
    ResidualDiagnostics,
)

Vector = NDArray[np.float64]
ENGINE_VERSION = "1.1.0"


class FitError(Exception):
    """A model failed validation or numerical estimation; safe for the interface."""


@dataclass
class Fit:
    mean: Vector
    variance: Vector
    residuals: Vector
    burn: int
    degrees: int = 0
    parameters: list[NamedValue] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def readiness(
    observations: list[Observation], frequency: str, request: ForecastRequest
) -> ForecastReadiness:
    """Check calendar/sample feasibility without fitting; suggest, never apply, a range."""
    rows, _ = calendar_rows(observations, frequency, request.start, request.end)
    required = 20 + (request.folds + 1) * request.horizon
    result = ForecastReadiness(
        ready=False,
        message="",
        periods=len(rows),
        required_periods=required,
        missing_periods=sum(row.value is None for row in rows),
    )
    try:
        prepared, _ = prepare(observations, frequency, request)
        result.periods = len(prepared)
        result.ready = True
        result.message = "Calendar and sample checks passed. Individual model fits may still fail."
    except DataError as exc:
        result.message = str(exc)
        # Prefer the longest complete segment, then the more recent segment on ties.
        best_start = best_length = current_start = 0
        for index, row in enumerate(rows):
            if row.value is None:
                current_start = index + 1
            else:
                length = index - current_start + 1
                if length >= best_length:
                    best_start, best_length = current_start, length
        if result.missing_periods and required <= best_length <= 2000:
            result.suggested_start = rows[best_start].date
            result.suggested_end = rows[best_start + best_length - 1].date
    return result


def prepare(
    observations: list[Observation], frequency: str, request: ForecastRequest
) -> tuple[list[Observation], list[str]]:
    rows, inserted = calendar_rows(observations, frequency, request.start, request.end)
    notes = [f"{inserted} absent calendar periods were detected."] if inserted else []
    if request.missing == "trim_edges":
        indices = [i for i, row in enumerate(rows) if row.value is not None]
        if not indices:
            raise DataError("There are no numeric observations to forecast.", 422)
        left, right = indices[0], indices[-1]
        if left or right < len(rows) - 1:
            notes.append(
                f"Trimmed {left} leading and {len(rows) - right - 1} trailing missing periods; "
                f"forecast origin is {rows[right].date}."
            )
        rows = rows[left : right + 1]
    if any(row.value is None for row in rows):
        missing_dates = ", ".join(row.date for row in rows if row.value is None)[:160]
        raise DataError(
            f"Missing periods: {missing_dates}. Choose a complete date range; "
            "the engine does not fill gaps.",
            422,
        )
    if len(rows) > 2000:
        raise DataError("Select at most 2,000 periods for a local forecast run.", 422)
    if any(abs(row.value or 0) > 1e100 for row in rows):
        raise DataError("Values exceed the engine's numerical range. Rescale the input units.", 422)
    initial = len(rows) - (request.folds + 1) * request.horizon
    if initial < 20:
        raise DataError(
            f"This setup needs at least {20 + (request.folds + 1) * request.horizon} "
            "complete periods. Shorten the horizon or reduce validation windows.",
            422,
        )
    if len(set(request.models)) != len(request.models):
        raise DataError("Choose each model only once.", 422)
    options = request.options
    seasonal = options.seasonal_p + options.seasonal_d + options.seasonal_q
    if options.seasonal_period == 1 and (
        ("sarima" in request.models and seasonal)
        or ("ets" in request.models and options.ets_seasonal)
        or "seasonal_naive" in request.models
    ):
        raise DataError("Seasonal models need a seasonal period of at least 2.", 422)
    if "ets" in request.models and options.ets_damped and not options.ets_trend:
        raise DataError("Damping requires an ETS trend.", 422)
    return rows, notes


def fit_model(values: Vector, name: ModelName, horizon: int, options: ModelOptions) -> Fit:
    """Scale using only this training set. Every output returns to source units."""
    scale = float(np.std(values)) or float(np.max(np.abs(values))) or 1.0
    y = values / scale
    period = options.seasonal_period
    seasonal = (
        name == "seasonal_naive"
        or (name == "ets" and options.ets_seasonal)
        or (name == "sarima" and options.seasonal_p + options.seasonal_d + options.seasonal_q > 0)
    )
    if seasonal and len(y) < 3 * period:
        raise FitError(
            f"Each training window needs at least {3 * period} periods for this seasonality."
        )
    steps = np.arange(1, horizon + 1, dtype=float)
    if name == "mean":
        residuals = y - np.mean(y)
        mean_variance = float(np.var(y, ddof=1)) * (1 + 1 / len(y))
        fit = Fit(
            np.full(horizon, np.mean(y)),
            np.full(horizon, mean_variance),
            residuals,
            0,
            1,
            notes=["Mean-model intervals include estimation uncertainty in the sample mean."],
        )
    elif name == "autoreg":
        fit = fit_autoreg(y, horizon, options)
        fit.parameters.append(NamedValue(name="training_scale", value=f"{scale:.12g}"))
    elif name in ("naive", "drift", "seasonal_naive"):
        lag = period if name == "seasonal_naive" else 1
        residuals = y[lag:] - y[:-lag]
        drift = float(np.mean(residuals)) if name == "drift" else 0.0
        residuals = residuals - drift
        dof = len(residuals) - (1 if name == "drift" else 0)
        sigma2 = float(np.sum(residuals**2) / dof)
        if name == "seasonal_naive":
            mean = np.array([y[-period + i % period] for i in range(horizon)])
            variance = sigma2 * (np.floor((steps - 1) / period) + 1)
        else:
            mean = y[-1] + steps * drift
            variance = sigma2 * steps * (1 + steps / (len(y) - 1) if name == "drift" else 1)
        fit = Fit(mean, variance, residuals, lag)
    else:
        if float(np.ptp(y)) < 1e-12:
            raise FitError("This series is effectively constant. Use a naive baseline.")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                if name == "ets":
                    model = ETSModel(
                        pd.Series(y),
                        error="add",
                        trend="add" if options.ets_trend else None,
                        damped_trend=options.ets_damped,
                        seasonal="add" if options.ets_seasonal else None,
                        seasonal_periods=period if options.ets_seasonal else None,
                        initialization_method="estimated",
                    )
                    result = model.fit(disp=False, maxiter=500)
                    prediction = result.get_prediction(
                        start=len(y), end=len(y) + horizon - 1, method="exact"
                    )
                    burn = max(period if options.ets_seasonal else 0, 2)
                    degrees = len(result.params)
                else:
                    degrees = options.p + options.q + options.seasonal_p + options.seasonal_q
                    needed = max(20, 5 * (degrees + 1) + options.d + options.seasonal_d * period)
                    if len(y) < needed:
                        raise FitError(
                            f"These ARIMA orders need at least {needed} training periods."
                        )
                    model = SARIMAX(
                        y,
                        order=(options.p, options.d, options.q),
                        seasonal_order=(
                            options.seasonal_p,
                            options.seasonal_d,
                            options.seasonal_q,
                            period,
                        )
                        if seasonal
                        else (0, 0, 0, 0),
                        trend="c" if options.sarima_trend == "constant" else "n",
                        enforce_stationarity=True,
                        enforce_invertibility=True,
                    )
                    result = model.fit(disp=False, maxiter=200)
                    prediction = result.get_forecast(steps=horizon)
                    burn = max(
                        int(result.loglikelihood_burn), options.d + options.seasonal_d * period, 1
                    )
                if not result.mle_retvals.get("converged", False):
                    raise FitError(
                        "Estimation did not converge. Try simpler orders or a longer range."
                    )
                fit = Fit(
                    np.asarray(prediction.predicted_mean, dtype=float),
                    np.asarray(prediction.var_pred_mean, dtype=float),
                    np.asarray(result.resid[burn:], dtype=float),
                    burn,
                    degrees,
                    [
                        NamedValue(name=str(key), value=f"{float(value):.12g}")
                        for key, value in zip(result.param_names, result.params, strict=True)
                    ],
                    ["Estimation emitted numerical warnings; inspect validation and residuals."]
                    if caught
                    else [],
                )
            except (ValueError, np.linalg.LinAlgError, FloatingPointError, OverflowError):
                raise FitError(
                    "The model could not be estimated reliably for this data and configuration."
                ) from None
        fit.parameters.append(NamedValue(name="training_scale", value=f"{scale:.12g}"))
    fit.mean *= scale
    fit.variance *= scale**2
    fit.residuals *= scale
    if not all(
        np.all(np.isfinite(array)) for array in (fit.mean, fit.variance, fit.residuals)
    ) or np.any(fit.variance < 0):
        raise FitError("The model produced non-finite results or invalid prediction variance.")
    return fit


def fit_autoreg(y: Vector, horizon: int, options: ModelOptions) -> Fit:
    """OLS autoregression with fixed consecutive lags; no parameter search."""
    lag = options.ar_lags
    needed = max(20, 5 * (lag + (2 if options.ar_trend == "linear" else 1)) + lag)
    if len(y) < needed:
        raise FitError(f"AR({lag}) needs at least {needed} periods in every training window.")
    if float(np.ptp(y)) < 1e-12:
        raise FitError("This series is effectively constant. Use a naive or mean baseline.")
    try:
        result = AutoReg(
            y, lags=lag, trend="ct" if options.ar_trend == "linear" else "c", old_names=False
        ).fit()
        if np.linalg.matrix_rank(result.model._x) < result.model._x.shape[1]:
            raise FitError("The autoregression design is rank deficient. Reduce lags.")
        if np.any(np.abs(result.roots) <= 1):
            raise FitError(
                "The fitted autoregression is unstable. Try fewer lags, a linear "
                "trend, or a differenced ARIMA model."
            )
        prediction = result.get_prediction(start=len(y), end=len(y) + horizon - 1)
        return Fit(
            np.asarray(prediction.predicted_mean, dtype=float),
            np.asarray(prediction.var_pred_mean, dtype=float),
            np.asarray(result.resid, dtype=float),
            lag,
            lag,
            [
                NamedValue(name=str(key), value=f"{float(value):.12g}")
                for key, value in zip(result.model.exog_names, result.params, strict=True)
            ],
            [
                "Autoregression intervals use fitted innovation variance; coefficient uncertainty "
                "is excluded. Stable AR roots are required."
            ],
        )
    except (ValueError, np.linalg.LinAlgError, FloatingPointError, OverflowError):
        raise FitError("Autoregression could not be estimated reliably. Reduce lags.") from None


def points(fit: Fit, dates: list[str], interval: int) -> list[ForecastPoint]:
    z = NormalDist().inv_cdf(0.5 + interval / 200)
    delta = z * np.sqrt(fit.variance)
    return [
        ForecastPoint(
            date=label, value=float(mean), lower=float(mean - margin), upper=float(mean + margin)
        )
        for label, mean, margin in zip(dates, fit.mean, delta, strict=True)
    ]


def accuracy(rows: list[EvaluationPoint]) -> Accuracy:
    errors = np.array([row.actual - row.value for row in rows])
    scaled = [abs(row.actual - row.value) / row.scale for row in rows if row.scale]
    return Accuracy(
        count=len(rows),
        mae=float(np.mean(np.abs(errors))),
        rmse=float(np.sqrt(np.mean(errors**2))),
        mase=float(np.mean(scaled))
        if len(scaled) == len(rows) and all(isfinite(value) for value in scaled)
        else None,
        coverage=sum(row.lower <= row.actual <= row.upper for row in rows) / len(rows),
        bias=float(np.mean(-errors)),
    )


def residual_diagnostics(fit: Fit) -> ResidualDiagnostics:
    residuals = fit.residuals
    lag = min(10, len(residuals) // 5)
    pvalue = None
    if lag > fit.degrees and float(np.std(residuals)) > 0:
        result = acorr_ljungbox(residuals, lags=[lag], model_df=fit.degrees, return_df=True)
        value = float(result["lb_pvalue"].iloc[0])
        pvalue = value if isfinite(value) else None
    return ResidualDiagnostics(
        count=len(residuals),
        mean=float(np.mean(residuals)),
        ljung_box_lag=lag,
        ljung_box_pvalue=pvalue,
        degrees_of_freedom=lag - fit.degrees,
    )


def evaluate(
    rows: list[Observation], frequency: str, request: ForecastRequest
) -> list[ModelResult]:
    """Validation ends before the final untouched holdout. No automatic selection."""
    y = np.array([row.value for row in rows], dtype=float)
    h = request.horizon
    origins = [len(y) - (request.folds + 1 - i) * h for i in range(request.folds + 1)]
    future_dates = [
        next_date(parse_date(rows[-1].date), frequency, i).isoformat() for i in range(1, h + 1)
    ]
    names: list[ModelName] = list(dict.fromkeys(["naive", *request.models]))
    results = []
    for name in names:
        try:
            validation: list[EvaluationPoint] = []
            holdout: list[EvaluationPoint] = []
            notes: list[str] = []
            for fold, origin in enumerate(origins):
                fit = fit_model(y[:origin], name, h, request.options)
                notes.extend(fit.notes)
                lag = request.options.seasonal_period
                scale = (
                    float(np.mean(np.abs(y[lag:origin] - y[: origin - lag])))
                    if origin > lag
                    else 0.0
                )
                forecast = points(
                    fit, [row.date for row in rows[origin : origin + h]], request.interval
                )
                evaluated = [
                    EvaluationPoint(
                        **point.model_dump(),
                        origin=rows[origin - 1].date,
                        horizon=i + 1,
                        actual=float(y[origin + i]),
                        scale=scale or None,
                    )
                    for i, point in enumerate(forecast)
                ]
                (holdout if fold == request.folds else validation).extend(evaluated)
            final = fit_model(y, name, h, request.options)
            notes.extend(final.notes)
            results.append(
                ModelResult(
                    model=name,
                    status="success",
                    forecast=points(final, future_dates, request.interval),
                    validation=accuracy(validation),
                    holdout=accuracy(holdout),
                    by_horizon=[
                        HorizonAccuracy(
                            **accuracy(
                                [row for row in validation if row.horizon == i]
                            ).model_dump(),
                            horizon=i,
                        )
                        for i in range(1, h + 1)
                    ],
                    validation_points=validation,
                    holdout_points=holdout,
                    residuals=[
                        Observation(date=row.date, value=float(value))
                        for row, value in zip(rows[final.burn :], final.residuals, strict=True)
                    ],
                    diagnostics=residual_diagnostics(final),
                    parameters=final.parameters,
                    warnings=list(dict.fromkeys(notes)),
                )
            )
        except FitError as exc:
            results.append(ModelResult(model=name, status="failed", error=str(exc)))
    rank_models(results)
    return results


def rank_models(results: list[ModelResult]) -> None:
    """Annotate comparable successful models using validation only; preserve model order."""
    valid = [item for item in results if item.status == "success" and item.validation is not None]
    baseline = next((item.validation for item in valid if item.model == "naive"), None)
    scores = [item.validation.rmse for item in valid if item.validation is not None]
    for item in valid:
        assert item.validation is not None
        item.validation_rank = 1 + sum(score < item.validation.rmse for score in scores)
        item.rmse_skill = (
            1 - item.validation.rmse / baseline.rmse if baseline and baseline.rmse > 0 else None
        )
