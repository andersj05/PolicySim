"""Provider-independent data contracts. No HTTP or research transformations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

Provider = Literal["fred", "worldbank"]


class Contract(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class Series(Contract):
    provider: Literal["fred", "worldbank", "local"]
    id: str
    title: str
    source_id: str = ""
    source_name: str
    units: str
    frequency: str
    seasonal_adjustment: str
    notes: str = ""
    source_url: str
    license_url: str
    updated: str = ""


class Observation(Contract):
    date: str
    value: float | None
    realtime_start: str = ""
    realtime_end: str = ""


class SearchResult(Contract):
    items: list[Series]
    total: int
    page: int
    page_size: int


class Country(Contract):
    id: str
    name: str
    aggregate: bool


class ProviderStatus(Contract):
    fred_configured: bool


class Snapshot(Contract):
    series: Series
    country: str
    retrieved_at: str
    snapshot_id: str
    raw_sha256: list[str]
    vintage: str
    transformations: list[str]
    requested_start: str = ""
    requested_end: str = ""
    observations: list[Observation]


class DataError(Exception):
    """Safe user-facing message; never expose upstream URLs or credentials."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status
