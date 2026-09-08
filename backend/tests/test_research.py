"""Deterministic numerical fixtures only; never presented as economic observations."""

import hashlib
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from policysim import analysis, forecasting, research_service, storage
from policysim.domain import DataError, Observation
from policysim.forecasting import FitError, fit_model
from policysim.main import app
from policysim.research_contracts import (
    AnalysisRequest,
    CsvImportRequest,
    ForecastRequest,
    ModelOptions,
)


def rows(n: int = 96) -> list[Observation]:
    rng = np.random.default_rng(20260907)
    values = 100 + np.arange(n) * 0.2 + 2 * np.sin(np.arange(n) * np.pi / 6) + rng.normal(0, 0.5, n)
    return [
        Observation(
            date=analysis.next_date(date(2000, 1, 1), "monthly", i).isoformat(), value=float(v)
        )
        for i, v in enumerate(values)
    ]


def request(**kwargs: Any) -> ForecastRequest:
    return ForecastRequest(snapshot_id="a" * 64, horizon=3, folds=2, **kwargs)


def test_closed_form_baselines_and_interval_variance() -> None:
    y = np.array([1.0, 2.0, 4.0, 7.0])
    naive = fit_model(y, "naive", 3, ModelOptions())
    np.testing.assert_allclose(naive.mean, [7, 7, 7])
    np.testing.assert_allclose(naive.variance, np.array([1, 2, 3]) * 14 / 3)
    drift = fit_model(y, "drift", 3, ModelOptions())
    np.testing.assert_allclose(drift.mean, [9, 11, 13])
    np.testing.assert_allclose(drift.variance, [4 / 3, 10 / 3, 6])
    seasonal = fit_model(
        np.array([1.0, 5.0, 2.0, 6.0, 3.0, 7.0]),
        "seasonal_naive",
        5,
        ModelOptions(seasonal_period=2),
    )
    np.testing.assert_allclose(seasonal.mean, [3, 7, 3, 7, 3])
    np.testing.assert_allclose(seasonal.variance, [1, 1, 2, 2, 3])
    intervals = forecasting.points(naive, ["2020", "2021", "2022"], 95)
    assert intervals[0].upper == pytest.approx(7 + 1.95996398454 * np.sqrt(14 / 3))
    assert intervals[2].upper - 7 > intervals[0].upper - 7


def test_chronology_holdout_isolation_metrics_and_reproducibility() -> None:
    data = rows()
    config = request(models=["drift"])
    result = forecasting.evaluate(data, "monthly", config)
    assert [model.model for model in result] == ["naive", "drift"]
    changed = [row.model_copy(deep=True) for row in data]
    changed[-1].value = 10000
    second = forecasting.evaluate(changed, "monthly", config)
    for original, altered in zip(result, second, strict=True):
        assert original.validation_points == altered.validation_points
        assert [row.value for row in original.holdout_points] == [
            row.value for row in altered.holdout_points
        ]
        assert original.holdout != altered.holdout
        assert original.validation is not None and original.holdout is not None
        assert original.validation.count == 6 and original.holdout.count == 3
        assert all(
            row.origin < row.date for row in original.validation_points + original.holdout_points
        )
        assert (
            max(row.date for row in original.validation_points) <= original.holdout_points[0].origin
        )
        errors = [abs(point.actual - point.value) for point in original.validation_points]
        assert original.validation.mae == pytest.approx(np.mean(errors))
        assert original.validation.rmse == pytest.approx(np.sqrt(np.mean(np.square(errors))))
        assert original.by_horizon[0].count == 2
    assert result == forecasting.evaluate(data, "monthly", config)


@pytest.mark.parametrize("model", ["ets", "sarima"])
def test_statistical_models_finite_scale_equivariant(model: Any) -> None:
    y = np.array([row.value for row in rows()], dtype=float)
    options = ModelOptions(p=1, d=0, q=0, sarima_trend="constant", ets_damped=False)
    fitted = fit_model(y, model, 4, options)
    scaled = fit_model(y * 1e12, model, 4, options)
    np.testing.assert_allclose(scaled.mean / 1e12, fitted.mean, rtol=1e-5)
    np.testing.assert_allclose(scaled.variance / 1e24, fitted.variance, rtol=1e-4)
    assert np.isfinite(fitted.mean).all() and (fitted.variance >= 0).all()
    assert len(fitted.residuals) + fitted.burn == len(y)


def test_sarima_random_walk_matches_naive_forecast() -> None:
    y = np.array([row.value for row in rows()], dtype=float)
    fit = fit_model(y, "sarima", 4, ModelOptions(p=0, d=1, q=0))
    np.testing.assert_allclose(fit.mean, np.repeat(y[-1], 4), atol=1e-7)
    np.testing.assert_allclose(fit.variance / fit.variance[0], [1, 2, 3, 4], rtol=1e-5)


def test_seasonal_models_and_failures() -> None:
    y = np.array([row.value for row in rows(120)], dtype=float)
    options = ModelOptions(
        p=0, d=0, q=0, seasonal_p=1, seasonal_period=12, ets_seasonal=True, ets_damped=False
    )
    for model in ("ets", "sarima"):
        fit = fit_model(y, model, 4, options)
        assert len(fit.mean) == 4
    with pytest.raises(FitError, match="training window"):
        fit_model(y[:20], "seasonal_naive", 4, options)
    with pytest.raises(FitError, match="ARIMA orders"):
        fit_model(y[:20], "sarima", 4, ModelOptions(p=3, q=3))
    with pytest.raises(FitError, match="constant"):
        fit_model(np.ones(30), "ets", 4, ModelOptions())
    constant = [row.model_copy(update={"value": 2.0}) for row in rows(40)]
    result = forecasting.evaluate(constant, "monthly", request(models=["ets"]))
    assert result[0].validation is not None and result[0].validation.mase is None
    assert result[1].status == "failed"
    assert result[0].diagnostics is not None and result[0].diagnostics.ljung_box_pvalue is None


def test_estimation_nonconvergence_and_invalid_variance(monkeypatch: pytest.MonkeyPatch) -> None:
    class BadModel:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def fit(self, **kwargs: Any) -> Any:
            raise ValueError("numerical failure")

    monkeypatch.setattr(forecasting, "ETSModel", BadModel)
    with pytest.raises(FitError, match="could not be estimated"):
        fit_model(np.arange(30.0), "ets", 3, ModelOptions())

    result = SimpleNamespace(
        mle_retvals={"converged": False},
        params=[1.0],
        param_names=["level"],
        resid=np.ones(30),
        predicted_mean=np.ones(3),
        var_pred_mean=np.ones(3),
    )
    result.get_prediction = lambda **kwargs: result
    monkeypatch.setattr(BadModel, "fit", lambda self, **kwargs: result)
    with pytest.raises(FitError, match="did not converge"):
        fit_model(np.arange(30.0), "ets", 3, ModelOptions())
    result.mle_retvals["converged"] = True
    result.var_pred_mean = np.array([-1.0, 1.0, 1.0])
    with pytest.raises(FitError, match="invalid prediction variance"):
        fit_model(np.arange(30.0), "ets", 3, ModelOptions())


@pytest.mark.parametrize(
    "frequency,label,expected",
    [
        ("annual", "2020", "2021-01-01"),
        ("quarterly", "2020Q4", "2021-01-01"),
        ("monthly", "2020M12", "2021-01-01"),
        ("weekly", "2020-12-28", "2021-01-04"),
        ("daily", "2020-02-28", "2020-02-29"),
    ],
)
def test_calendars(frequency: str, label: str, expected: str) -> None:
    assert analysis.next_date(analysis.parse_date(label), frequency).isoformat() == expected


def test_calendar_gaps_duplicates_bounds_and_unknown_frequency() -> None:
    data = [Observation(date="2020-01", value=1), Observation(date="2020-03", value=3)]
    regular, inserted = analysis.calendar_rows(data, "monthly")
    assert inserted == 1 and regular[1].value is None
    assert analysis.resolve_frequency("auto", "Monthly") == "monthly"
    assert analysis.resolve_frequency("weekly", "Unknown") == "weekly"
    with pytest.raises(DataError, match="frequency"):
        analysis.resolve_frequency("auto", "Business daily")
    for invalid in ("abc", "2020-13", "2020-02-30"):
        with pytest.raises(DataError, match="ISO"):
            analysis.parse_date(invalid)
    with pytest.raises(DataError, match="ordered"):
        analysis.calendar_rows([data[0], data[0]], "monthly")
    with pytest.raises(DataError, match="No observations"):
        analysis.calendar_rows(data, "monthly", "2022", "2023")
    with pytest.raises(DataError, match="start date"):
        analysis.calendar_rows(data, "monthly", "2023", "2022")
    with pytest.raises(DataError, match="calendar"):
        analysis.calendar_rows(data, "weekly")
    with pytest.raises(DataError, match="date range"):
        analysis.next_date(date(9999, 12, 1), "annual")


def test_forecast_input_guards_and_trimmed_origin() -> None:
    data = rows(40)
    data[0].value, data[-1].value = None, None
    prepared, notes = forecasting.prepare(data, "monthly", request())
    assert prepared[0].date == data[1].date and prepared[-1].date == data[-2].date
    assert "Trimmed 1 leading and 1 trailing" in notes[0]
    with pytest.raises(DataError, match="Missing periods"):
        forecasting.prepare(data, "monthly", request(missing="reject"))
    data[10].value = None
    with pytest.raises(DataError, match="Missing periods"):
        forecasting.prepare(data, "monthly", request())
    with pytest.raises(DataError, match="no numeric"):
        forecasting.prepare([Observation(date="2020", value=None)], "annual", request())
    with pytest.raises(DataError, match="at least"):
        forecasting.prepare(rows(20), "monthly", request())
    with pytest.raises(DataError, match="only once"):
        forecasting.prepare(rows(), "monthly", request(models=["ets", "ets"]))
    with pytest.raises(DataError, match="seasonal period"):
        forecasting.prepare(rows(), "monthly", request(models=["seasonal_naive"]))
    with pytest.raises(DataError, match="Damping"):
        forecasting.prepare(rows(), "monthly", request(options=ModelOptions(ets_trend=False)))


def test_statistics_transforms_and_nulls() -> None:
    data = [Observation(date=str(2000 + i), value=float(i + 1)) for i in range(5)]
    config = AnalysisRequest(snapshot_id="b" * 64)
    result = analysis.analyze(data, "annual", "Units", config)
    assert result.statistics.mean == 3 and result.statistics.median == 3
    assert result.statistics.std == pytest.approx(np.sqrt(2.5))
    assert result.statistics.q25 == 2 and result.statistics.q75 == 4
    assert result.request == config
    diff = analysis.analyze(
        data, "annual", "Units", config.model_copy(update={"transform": "difference"})
    )
    assert [row.value for row in diff.observations] == [None, 1, 1, 1, 1]
    rolling = analysis.analyze(
        data,
        "annual",
        "Units",
        config.model_copy(update={"transform": "rolling_mean", "window": 3}),
    )
    assert [row.value for row in rolling.observations] == [None, None, 2, 3, 4]
    percent = analysis.analyze(
        data, "annual", "Units", config.model_copy(update={"transform": "pct_change"})
    )
    assert percent.observations[1].value == 100 and percent.units == "% change"
    logged = analysis.analyze(
        data, "annual", "Units", config.model_copy(update={"transform": "log"})
    )
    assert logged.observations[-1].value == pytest.approx(np.log(5))
    data[0].value = 0
    percent = analysis.analyze(
        data, "annual", "Units", config.model_copy(update={"transform": "pct_change"})
    )
    assert percent.observations[1].value is None
    with pytest.raises(DataError, match="positive"):
        analysis.analyze(data, "annual", "Units", config.model_copy(update={"transform": "log"}))
    data[2].value = None
    assert analysis.describe(data)[0].missing == 1
    assert analysis.describe([Observation(date="2020", value=None)])[0].mean is None
    stats, correlations = analysis.describe(rows())
    assert stats.adf_pvalue is not None and correlations[0].lag == 1
    gaps = rows()
    gaps[20].value = None
    assert analysis.describe(gaps)[0].adf_pvalue is None
    with pytest.raises(DataError, match="numerical range"):
        analysis.describe([Observation(date="2020", value=1e200)])


def import_request(**kwargs: Any) -> CsvImportRequest:
    content = "date,value\n" + "\n".join(f"{row.date},{row.value}" for row in rows(48))
    return CsvImportRequest(
        content=content,
        title="Numerical test fixture",
        date_column="date",
        value_column="value",
        frequency="monthly",
        **kwargs,
    )


def test_import_analysis_forecast_api_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("POLICYSIM_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    payload = import_request().model_dump()
    preview = client.post("/api/v1/imports/preview", json={"content": payload["content"]})
    assert preview.status_code == 200 and preview.json()["count"] == 48
    response = client.post("/api/v1/imports", json=payload)
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["series"]["provider"] == "local"
    identifier = snapshot["snapshot_id"]
    assert client.get(f"/api/v1/snapshots/{identifier}").json() == snapshot
    assert "date,value" in client.get(f"/api/v1/snapshots/{identifier}/csv").text
    params = {"snapshot_id": identifier, "transform": "difference"}
    assert client.post("/api/v1/analysis", json=params).json()["statistics"]["missing"] == 1
    assert client.post("/api/v1/analysis/csv", json=params).status_code == 200
    forecast = client.post(
        "/api/v1/forecasts",
        json={"snapshot_id": identifier, "horizon": 3, "folds": 2, "models": ["drift"]},
    )
    assert forecast.status_code == 200, forecast.text
    run = forecast.json()
    assert run["environment"] and run["warnings"] and run["request"]["snapshot_id"] == identifier
    saved = tmp_path / "runs" / f"{run['run_id']}.json"
    assert hashlib.sha256(saved.read_bytes()).hexdigest() == run["run_id"]
    assert client.get(f"/api/v1/forecasts/{run['run_id']}").json() == run
    assert client.get(f"/api/v1/forecasts/{run['run_id']}/download").json() == run
    assert client.get("/api/v1/forecasts").json()[0]["run_id"] == run["run_id"]
    with research_service.RUN_LOCK:
        assert client.post("/api/v1/forecasts", json={"snapshot_id": identifier}).status_code == 409
    assert (
        client.post(
            "/api/v1/forecasts", json={"snapshot_id": identifier, "horizon": 100}
        ).status_code
        == 422
    )
    saved.write_text("{}")
    assert client.get(f"/api/v1/forecasts/{run['run_id']}").status_code == 500
    assert client.get(f"/api/v1/forecasts/{'f' * 64}").status_code == 404
    assert client.get("/api/v1/forecasts/bad").status_code == 422


@pytest.mark.parametrize("content", ["x", "a,a\n1,2", "a,b\n1", 'a,b\n"open,1', "a,\n1,2"])
def test_bad_csv_shape(content: str) -> None:
    with pytest.raises(DataError):
        research_service.preview_csv(content)


def test_csv_values_and_provenance(tmp_path: Path) -> None:
    config = import_request()
    for content, message in (
        ("date,value\n2020,NaN", "finite"),
        ("date,value\n2020,abc", "Row 2"),
        ("date,value\n2020,1\n2020,2", "ordered"),
    ):
        with pytest.raises(DataError, match=message):
            research_service.import_csv(tmp_path, config.model_copy(update={"content": content}))
    for update in ({"date_column": "absent"}, {"value_column": "date"}):
        with pytest.raises(DataError):
            research_service.import_csv(tmp_path, config.model_copy(update=update))
    content = "\ufeffdate,value\n2021,\n2020,2\n"
    snapshot = research_service.import_csv(
        tmp_path, config.model_copy(update={"content": content, "frequency": "annual"})
    )
    assert [row.value for row in snapshot.observations] == [2, None]
    assert (tmp_path / "raw" / f"{snapshot.raw_sha256[0]}.json").read_bytes() == content.encode()
    assert storage.read(tmp_path, snapshot.snapshot_id).observations == snapshot.observations
    assert research_service.list_runs(tmp_path) == []
    bad = json.dumps({"bad": True}).encode()
    identifier = storage.put(tmp_path, bad, "runs")
    with pytest.raises(DataError, match="cannot be read"):
        research_service.read_run(tmp_path, identifier)
