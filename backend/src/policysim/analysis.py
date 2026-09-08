"""Calendar validation and descriptive statistics; no HTTP, storage or providers."""

import re
import warnings
from datetime import date, timedelta
from math import isfinite, log

import numpy as np
from statsmodels.tsa.stattools import acf, adfuller  # type: ignore[import-untyped]

from policysim.domain import DataError, Observation
from policysim.research_contracts import (
    AnalysisRequest,
    AnalysisResult,
    Correlation,
    Frequency,
    Statistics,
)


def resolve_frequency(requested: Frequency, label: str) -> str:
    if requested != "auto":
        return requested
    name = label.lower().strip()
    for frequency in ("annual", "quarterly", "monthly", "weekly", "daily"):
        if name == frequency or name.startswith(frequency + ","):
            return frequency
    raise DataError(
        "Choose the data frequency; the source does not specify a supported calendar.", 422
    )


def parse_date(value: str) -> date:
    try:
        if re.fullmatch(r"\d{4}", value):
            return date(int(value), 1, 1)
        quarter = re.fullmatch(r"(\d{4})Q([1-4])", value)
        if quarter:
            return date(int(quarter[1]), (int(quarter[2]) - 1) * 3 + 1, 1)
        month = re.fullmatch(r"(\d{4})[M-](\d{2})", value)
        if month:
            return date(int(month[1]), int(month[2]), 1)
        return date.fromisoformat(value)
    except ValueError:
        raise DataError("Use YYYY, YYYY-MM, YYYYQ1 or ISO YYYY-MM-DD dates.", 422) from None


def period_start(value: date, frequency: str) -> date:
    if frequency == "annual":
        return date(value.year, 1, 1)
    if frequency == "quarterly":
        return date(value.year, (value.month - 1) // 3 * 3 + 1, 1)
    if frequency == "monthly":
        return date(value.year, value.month, 1)
    return value


def next_date(value: date, frequency: str, steps: int = 1) -> date:
    try:
        if frequency in ("daily", "weekly"):
            return value + timedelta(days=steps * (7 if frequency == "weekly" else 1))
        months = {"annual": 12, "quarterly": 3, "monthly": 1}[frequency] * steps
        index = value.year * 12 + value.month - 1 + months
        return date(index // 12, index % 12 + 1, 1)
    except (ValueError, OverflowError):
        raise DataError("The requested horizon exceeds the supported date range.", 422) from None


def calendar_rows(
    rows: list[Observation], frequency: str, start: str = "", end: str = ""
) -> tuple[list[Observation], int]:
    """Canonical period labels, with absent periods explicitly inserted as null."""
    lower = period_start(parse_date(start), frequency) if start else date.min
    upper = period_start(parse_date(end), frequency) if end else date.max
    if lower > upper:
        raise DataError("The start date must be on or before the end date.", 422)
    selected: list[Observation] = []
    previous = date.min
    for row in rows:
        current = period_start(parse_date(row.date), frequency)
        if current <= previous:
            raise DataError("Dates must be ordered with one observation per selected period.", 422)
        previous = current
        if lower <= current <= upper:
            selected.append(row.model_copy(update={"date": current.isoformat()}))
    if not selected:
        raise DataError("No observations in the selected dates.", 422)
    by_date = {row.date: row for row in selected}
    current = parse_date(selected[0].date)
    last = parse_date(selected[-1].date)
    result: list[Observation] = []
    while current <= last:
        if len(result) >= 25000:
            raise DataError("Select a smaller range (at most 25,000 calendar periods).", 422)
        key = current.isoformat()
        result.append(by_date.pop(key, Observation(date=key, value=None)))
        if current == last:
            break
        current = next_date(current, frequency)
    if by_date:
        raise DataError("Dates do not follow the selected calendar. Check the frequency.", 422)
    return result, len(result) - len(selected)


def describe(rows: list[Observation]) -> tuple[Statistics, list[Correlation]]:
    values = np.array([row.value for row in rows if row.value is not None], dtype=float)
    if np.any(np.abs(values) > 1e100):
        raise DataError("Values exceed the numerical range. Rescale the input units.", 422)
    n = len(values)
    kwargs: dict[str, float | None] = dict.fromkeys(
        ("mean", "median", "std", "minimum", "maximum", "q25", "q75"), None
    )
    if n:
        kwargs.update(
            mean=float(np.mean(values)),
            median=float(np.median(values)),
            std=float(np.std(values, ddof=1)) if n > 1 else None,
            minimum=float(np.min(values)),
            maximum=float(np.max(values)),
            q25=float(np.quantile(values, 0.25)),
            q75=float(np.quantile(values, 0.75)),
        )
    adf_stat, adf_p, adf_lags = None, None, None
    correlations: list[Correlation] = []
    # Never collapse internal gaps for lag-based statistics. Edge nulls are excluded.
    numeric_indices = [i for i, row in enumerate(rows) if row.value is not None]
    contiguous = bool(numeric_indices) and numeric_indices[-1] - numeric_indices[0] + 1 == n
    if n >= 12 and contiguous and float(np.ptp(values)) > 0:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = adfuller(values, regression="c", autolag="AIC", maxlag=min(12, n // 2 - 2))
            adf_stat, adf_p, adf_lags = float(result[0]), float(result[1]), int(result[2])
            correlations = [
                Correlation(lag=i, value=float(value))
                for i, value in enumerate(acf(values, nlags=min(24, n // 3), fft=True))
                if i
            ]
    return Statistics(
        count=n,
        missing=len(rows) - n,
        **kwargs,
        adf_statistic=adf_stat,
        adf_pvalue=adf_p,
        adf_lags=adf_lags,
    ), correlations


def analyze(
    observations: list[Observation], frequency: str, units: str, request: AnalysisRequest
) -> AnalysisResult:
    rows, inserted = calendar_rows(observations, frequency, request.start, request.end)
    notes = [f"{inserted} absent calendar periods shown as missing."] if inserted else []
    transformed: list[Observation] = []
    for i, row in enumerate(rows):
        value = row.value
        if request.transform == "log" and value is not None:
            if value <= 0:
                raise DataError(
                    "Log requires strictly positive values. Choose a different transform.", 422
                )
            value = log(value)
        elif request.transform in ("difference", "pct_change"):
            prior = rows[i - request.lag].value if i >= request.lag else None
            if prior is None or value is None or (request.transform == "pct_change" and prior == 0):
                value = None
            else:
                value = (
                    value - prior
                    if request.transform == "difference"
                    else (value / prior - 1) * 100
                )
        elif request.transform == "rolling_mean":
            window = rows[max(0, i - request.window + 1) : i + 1]
            value = (
                float(np.mean([item.value for item in window]))
                if len(window) == request.window and all(item.value is not None for item in window)
                else None
            )
        if value is not None and not isfinite(value):
            raise DataError(
                "This transformation exceeds numerical limits. Rescale the source values.", 422
            )
        transformed.append(Observation(date=row.date, value=value))
    if request.transform == "pct_change":
        units = "% change"
        notes.append("Change uses the selected lag. A zero denominator produces a missing value.")
    elif request.transform == "log":
        units = f"ln({units})"
    elif request.transform == "difference":
        units = f"Change in {units}"
    stats, correlations = describe(transformed)
    if stats.adf_pvalue is None:
        notes.append(
            "ADF and autocorrelation need at least 12 nonconstant, consecutive numeric values."
        )
    return AnalysisResult(
        snapshot_id=request.snapshot_id,
        request=request,
        frequency=frequency,
        transform=request.transform,
        units=units,
        observations=transformed,
        statistics=stats,
        autocorrelation=correlations,
        warnings=notes,
    )
