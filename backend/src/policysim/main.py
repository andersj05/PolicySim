"""Minimal HTTP boundary. Research capabilities are a later milestone."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="PolicySim",
    version="0.1.0",
    description="Economic research workspace. Foundation health API only.",
)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["policysim"]


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Process liveness only; does not imply provider or storage availability."""
    return HealthResponse(status="ok", service="policysim")
