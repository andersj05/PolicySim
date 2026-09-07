"""Versioned HTTP boundary for the local data workspace."""

from datetime import date
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from policysim import providers
from policysim.domain import Country, DataError, Provider, ProviderStatus, SearchResult, Snapshot
from policysim.settings import fred_key

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
    start: date = date(1776, 7, 4),
    end: date | None = None,
) -> Snapshot:
    end = end or date.today()
    if start > end:
        raise DataError("The start date must be on or before the end date.", 422)
    try:
        return providers.load(
            provider, series_id, country, source_id, start.isoformat(), end.isoformat()
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        raise DataError("The provider returned unexpected series data. Please retry.") from None
