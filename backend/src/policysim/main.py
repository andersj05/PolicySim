"""Versioned HTTP boundary for the local data workspace."""

from datetime import date
from typing import Literal

from fastapi import FastAPI, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ValidationError

from policysim import providers, research_service, storage
from policysim.domain import Country, DataError, Provider, ProviderStatus, SearchResult, Snapshot
from policysim.research_contracts import (
    AnalysisRequest,
    AnalysisResult,
    CsvImportRequest,
    CsvPreview,
    CsvPreviewRequest,
    ForecastRequest,
    ForecastRun,
    RunSummary,
)
from policysim.settings import data_dir, fred_key

app = FastAPI(
    title="PolicySim",
    version="0.1.0",
    description="Local economic data discovery with reproducible source snapshots.",
)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["policysim"]


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Process liveness only; does not imply provider or storage availability."""
    return HealthResponse(status="ok", service="policysim")


@app.exception_handler(DataError)
def data_error(request: Request, exc: DataError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)})


@app.get("/api/v1/providers", response_model=ProviderStatus)
def provider_status() -> ProviderStatus:
    return ProviderStatus(fred_configured=bool(fred_key()))


@app.get("/api/v1/snapshots/{snapshot_id}/download")
def download_snapshot(snapshot_id: str = Path(pattern=r"^[a-f0-9]{64}$")) -> JSONResponse:
    snapshot = storage.read(data_dir(), snapshot_id)
    return JSONResponse(
        content=snapshot.model_dump(),
        headers={
            "Content-Disposition": f'attachment; filename="policysim-{snapshot_id[:12]}.json"',
            "Cache-Control": "no-store",
        },
    )


@app.get("/api/v1/snapshots/{snapshot_id}", response_model=Snapshot)
def saved_snapshot(snapshot_id: str = Path(pattern=r"^[a-f0-9]{64}$")) -> Snapshot:
    return storage.read(data_dir(), snapshot_id)


@app.get("/api/v1/snapshots/{snapshot_id}/csv")
def snapshot_csv(snapshot_id: str = Path(pattern=r"^[a-f0-9]{64}$")) -> Response:
    snapshot = storage.read(data_dir(), snapshot_id)
    return Response(
        content=research_service.observations_csv(snapshot.observations),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="observations.csv"'},
    )


@app.post("/api/v1/imports/preview", response_model=CsvPreview)
def preview_import(request: CsvPreviewRequest) -> CsvPreview:
    return research_service.preview_csv(request.content)


@app.post("/api/v1/imports", response_model=Snapshot)
def import_data(request: CsvImportRequest) -> Snapshot:
    return research_service.import_csv(data_dir(), request)


@app.post("/api/v1/analysis", response_model=AnalysisResult)
def analysis(request: AnalysisRequest) -> AnalysisResult:
    return research_service.analyze_snapshot(data_dir(), request)


@app.post("/api/v1/analysis/csv")
def analysis_csv(request: AnalysisRequest) -> Response:
    result = research_service.analyze_snapshot(data_dir(), request)
    return Response(
        content=research_service.observations_csv(result.observations),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="analysis.csv"'},
    )


@app.post("/api/v1/forecasts", response_model=ForecastRun)
def forecast(request: ForecastRequest) -> ForecastRun:
    return research_service.run_forecast(data_dir(), request)


@app.get("/api/v1/forecasts", response_model=list[RunSummary])
def forecasts() -> list[RunSummary]:
    return research_service.list_runs(data_dir())


@app.get("/api/v1/forecasts/{run_id}", response_model=ForecastRun)
def saved_forecast(run_id: str = Path(pattern=r"^[a-f0-9]{64}$")) -> ForecastRun:
    return research_service.read_run(data_dir(), run_id)


@app.get("/api/v1/forecasts/{run_id}/download")
def download_forecast(run_id: str = Path(pattern=r"^[a-f0-9]{64}$")) -> JSONResponse:
    run = research_service.read_run(data_dir(), run_id)
    return JSONResponse(
        content=run.model_dump(),
        headers={"Content-Disposition": f'attachment; filename="forecast-{run_id[:12]}.json"'},
    )


@app.get("/api/v1/countries", response_model=list[Country])
def countries() -> list[Country]:
    try:
        return providers.countries()
    except (KeyError, TypeError, ValueError):
        raise DataError(
            "World Bank returned unexpected geography metadata. Please retry."
        ) from None


@app.get("/api/v1/series", response_model=SearchResult)
def search(
    provider: Provider,
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1, le=50000),
) -> SearchResult:
    if not q.strip():
        raise DataError("Enter a keyword or series ID.", 422)
    try:
        return providers.search(provider, q.strip(), page)
    except (KeyError, TypeError, ValueError, ValidationError):
        raise DataError(
            "The provider returned unexpected catalog metadata. Please retry."
        ) from None


@app.get("/api/v1/observations", response_model=Snapshot)
def observations(
    provider: Provider,
    series_id: str = Query(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9_.-]+$"),
    country: str = Query(default="USA", pattern=r"^[A-Z0-9]{2,3}$"),
    source_id: str = Query(default="2", pattern=r"^[0-9]{1,5}$"),
    start: date | None = None,
    end: date | None = None,
) -> Snapshot:
    end = end or date.today()
    start = start or (date(max(1, end.year - 9), 1, 1) if provider == "bls" else date(1776, 7, 4))
    if start > end:
        raise DataError("The start date must be on or before the end date.", 422)
    try:
        return providers.load(
            provider, series_id, country, source_id, start.isoformat(), end.isoformat()
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        raise DataError("The provider returned unexpected series data. Please retry.") from None
