"""Typed, provider-independent inputs and outputs for numerical research."""

from typing import Literal

from pydantic import ConfigDict, Field

from policysim.domain import Contract, Observation

Frequency = Literal["auto", "annual", "quarterly", "monthly", "weekly", "daily"]
Transform = Literal["level", "difference", "pct_change", "log", "rolling_mean"]
ModelName = Literal["naive", "mean", "drift", "seasonal_naive", "ets", "sarima", "autoreg"]


class ResearchRequest(Contract):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class AnalysisRequest(ResearchRequest):
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    start: str = ""
    end: str = ""
    frequency: Frequency = "auto"
    transform: Transform = "level"
    lag: int = Field(default=1, ge=1, le=60)
    window: int = Field(default=12, ge=2, le=120)


class Statistics(Contract):
    count: int
    missing: int
    mean: float | None
    median: float | None
    std: float | None
    minimum: float | None
    maximum: float | None
    q25: float | None
    q75: float | None
    adf_statistic: float | None
    adf_pvalue: float | None
    adf_lags: int | None


class Correlation(Contract):
    lag: int
    value: float


class AnalysisResult(Contract):
    snapshot_id: str
    request: AnalysisRequest
    frequency: str
    transform: Transform
    units: str
    observations: list[Observation]
    statistics: Statistics
    autocorrelation: list[Correlation]
    warnings: list[str]


class ModelOptions(ResearchRequest):
    ar_lags: int = Field(default=3, ge=1, le=24)
    ar_trend: Literal["constant", "linear"] = "constant"
    p: int = Field(default=1, ge=0, le=3)
    d: int = Field(default=1, ge=0, le=2)
    q: int = Field(default=1, ge=0, le=3)
    seasonal_p: int = Field(default=0, ge=0, le=1)
    seasonal_d: int = Field(default=0, ge=0, le=1)
    seasonal_q: int = Field(default=0, ge=0, le=1)
    seasonal_period: int = Field(default=1, ge=1, le=24)
    sarima_trend: Literal["none", "constant"] = "none"
    ets_trend: bool = True
    ets_damped: bool = True
    ets_seasonal: bool = False


class ForecastRequest(ResearchRequest):
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    start: str = ""
    end: str = ""
    frequency: Frequency = "auto"
    missing: Literal["reject", "trim_edges"] = "trim_edges"
    horizon: int = Field(default=12, ge=1, le=36)
    folds: int = Field(default=3, ge=2, le=5)
    interval: Literal[80, 95] = 95
    models: list[ModelName] = Field(default=["naive", "ets", "sarima"], min_length=1, max_length=7)
    options: ModelOptions = Field(default_factory=ModelOptions)


class ForecastReadiness(Contract):
    ready: bool
    message: str
    periods: int
    required_periods: int
    missing_periods: int
    suggested_start: str = ""
    suggested_end: str = ""


class ForecastPoint(Contract):
    date: str
    value: float
    lower: float
    upper: float


class EvaluationPoint(ForecastPoint):
    origin: str
    horizon: int
    actual: float
    scale: float | None


class Accuracy(Contract):
    count: int
    mae: float
    rmse: float
    mase: float | None
    coverage: float
    bias: float | None = None


class HorizonAccuracy(Accuracy):
    horizon: int


class NamedValue(Contract):
    name: str
    value: str


class ResidualDiagnostics(Contract):
    count: int
    mean: float
    ljung_box_lag: int
    ljung_box_pvalue: float | None
    degrees_of_freedom: int


class ModelResult(Contract):
    model: ModelName
    status: Literal["success", "failed"]
    error: str = ""
    validation_rank: int | None = None
    rmse_skill: float | None = None
    forecast: list[ForecastPoint] = Field(default_factory=list)
    validation: Accuracy | None = None
    holdout: Accuracy | None = None
    by_horizon: list[HorizonAccuracy] = Field(default_factory=list)
    validation_points: list[EvaluationPoint] = Field(default_factory=list)
    holdout_points: list[EvaluationPoint] = Field(default_factory=list)
    residuals: list[Observation] = Field(default_factory=list)
    diagnostics: ResidualDiagnostics | None = None
    parameters: list[NamedValue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ForecastRun(Contract):
    run_id: str = ""
    created_at: str
    engine_version: str
    title: str
    units: str
    country: str
    request: ForecastRequest
    frequency: str
    history: list[Observation]
    models: list[ModelResult]
    warnings: list[str]
    assumptions: list[str]
    environment: list[NamedValue]


class RunSummary(Contract):
    run_id: str
    created_at: str
    title: str
    country: str
    horizon: int
    frequency: str
    models: list[str]


class CsvPreviewRequest(ResearchRequest):
    content: str = Field(min_length=1, max_length=2_000_000)


class CsvPreview(Contract):
    columns: list[str]
    rows: list[list[str]]
    count: int


class CsvImportRequest(CsvPreviewRequest):
    title: str = Field(min_length=1, max_length=160)
    date_column: str = Field(min_length=1, max_length=160)
    value_column: str = Field(min_length=1, max_length=160)
    units: str = Field(default="Value", min_length=1, max_length=160)
    frequency: Literal["annual", "quarterly", "monthly", "weekly", "daily"]
