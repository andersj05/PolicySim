"""Offline provider contract tests. Values are deliberately artificial fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from policysim import official_providers as official
from policysim import providers, storage
from policysim.domain import DataError
from policysim.main import app


def bls_payload() -> dict[str, Any]:
    return {
        "status": "REQUEST_SUCCEEDED",
        "message": [],
        "Results": {
            "series": [
                {
                    "seriesID": "LNS14000000",
                    "data": [
                        {
                            "year": "2024",
                            "period": "M02",
                            "value": "-",
                            "footnotes": [{"text": "Unavailable"}],
                        },
                        {"year": "2024", "period": "M01", "value": "2.5", "footnotes": [{}]},
                        {"year": "2024", "period": "M13", "value": "9"},
                        {"year": "2023", "period": "M12", "value": "1"},
                    ],
                }
            ]
        },
    }


def test_bls_roundtrip_and_month_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POLICYSIM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(official, "data_dir", lambda: tmp_path)
    payload = bls_payload()
    raw = json.dumps(payload).encode()
    monkeypatch.setattr(official, "fetch", lambda *args: (payload, raw))
    result = providers.load("bls", "LNS14000000", "USA", "2", "2024-01-15", "2024-12-31")
    assert [(row.date, row.value) for row in result.observations] == [
        ("2024-01-01", 2.5),
        ("2024-02-01", None),
    ]
    assert "Unavailable" in result.series.notes
    assert storage.read(tmp_path, result.snapshot_id) == result
    assert (tmp_path / "raw" / f"{result.raw_sha256[0]}.json").read_bytes() == raw
    assert result.requested_start == "2024-01-15"


@pytest.mark.parametrize(
    "change, message",
    [
        ("status", "quota"),
        ("warning", "warning"),
        ("identity", "different series"),
        ("period", "monthly period"),
        ("empty", "No observations"),
        ("duplicate", "duplicate"),
    ],
)
def test_bls_rejects_unsafe_responses(
    monkeypatch: pytest.MonkeyPatch, change: str, message: str
) -> None:
    payload = bls_payload()
    series = payload["Results"]["series"][0]
    if change == "status":
        payload["status"] = "REQUEST_NOT_PROCESSED"
    elif change == "warning":
        payload["message"] = ["request truncated"]
    elif change == "identity":
        series["seriesID"] = "OTHER"
    elif change == "period":
        series["data"][0]["period"] = "Q01"
    elif change == "empty":
        series["data"] = []
    else:
        series["data"] *= 2
    monkeypatch.setattr(official, "fetch", lambda *args: (payload, b"fixture"))
    with pytest.raises(DataError, match=message):
        official.load_official("bls", "LNS14000000", "2024-01-01", "2024-12-31")


def test_scoped_catalog_and_limits() -> None:
    assert providers.search("bls", "participation", 1).items[0].id == "LNS11300000"
    assert providers.search("ecb", "yen", 1).items[0].units == "JPY per EUR"
    assert providers.search("ecb", "EXR.M.ISK.EUR.SP00.A", 1).total == 1
    assert providers.search("ecb", "euro", 2).total == len(official.CURRENCIES)
    assert not providers.search("bls", "nonexistent", 1).items
    with pytest.raises(DataError, match="supported BLS"):
        official.bls_series("UNKNOWN")
    with pytest.raises(DataError, match="monthly ECB"):
        official.ecb_series("EXR.D.USD.EUR.SP00.A")
    with pytest.raises(DataError, match="10 calendar years"):
        official.load_bls("LNS14000000", "2000-01-01", "2024-01-01")


ECB_HEADER = "KEY,TIME_PERIOD,OBS_VALUE,UNIT,UNIT_MULT,OBS_STATUS,TITLE\n"
ECB_ROWS = (
    "EXR.M.USD.EUR.SP00.A,2024-01,2.123456789,USD,0,A,Dollar/euro\n"
    "EXR.M.USD.EUR.SP00.A,2024-02,,USD,0,M,Dollar/euro\n"
)


def test_ecb_units_nulls_and_raw_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = (ECB_HEADER + ECB_ROWS).encode()
    monkeypatch.setattr(official, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(official, "fetch_bytes", lambda *args: raw)
    result = providers.load("ecb", "EXR.M.USD.EUR.SP00.A", "USA", "2", "2024-01-01", "2024-12-31")
    assert result.series.units == "USD per EUR" and result.country == ""
    assert result.observations[0].value == 2.123456789
    assert result.observations[1].value is None
    assert "2024-02: M" in result.series.notes
    assert storage.read(tmp_path, result.snapshot_id) == result


@pytest.mark.parametrize(
    "body, message",
    [
        ("OTHER\n1", "columns"),
        (ECB_HEADER + ECB_ROWS.replace("USD,0", "USD,3"), "unit scale"),
        (ECB_HEADER + ECB_ROWS.replace("EXR.M.USD", "EXR.M.GBP"), "different series"),
        (ECB_HEADER + ECB_ROWS.replace("2024-01", "2024-Q1"), "monthly period"),
        (ECB_HEADER + ECB_ROWS.replace("2024-01", "2023-01"), "outside"),
        (ECB_HEADER + ECB_ROWS.replace("2.123456789", "NaN"), "non-finite"),
        (ECB_HEADER, "No observations"),
    ],
)
def test_ecb_rejects_invalid_data(monkeypatch: pytest.MonkeyPatch, body: str, message: str) -> None:
    monkeypatch.setattr(official, "fetch_bytes", lambda *args: body.encode())
    with pytest.raises(DataError, match=message):
        official.load_official("ecb", "EXR.M.USD.EUR.SP00.A", "2024-01-01", "2024-12-31")


def test_bls_http_defaults_and_safe_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = []
    monkeypatch.setattr(official, "data_dir", lambda: tmp_path)

    def response(*args: Any) -> tuple[Any, bytes]:
        seen.append(args[2])
        return bls_payload(), b"fixture"

    monkeypatch.setattr(official, "fetch", response)
    with TestClient(app) as client:
        result = client.get(
            "/api/v1/observations?provider=bls&series_id=LNS14000000&end=2024-12-31"
        )
        assert result.status_code == 200
        assert seen == [{"startyear": "2015", "endyear": "2024"}]
        assert client.get("/api/v1/series?provider=ecb&q=USD").status_code == 200
        monkeypatch.setattr(official, "fetch", lambda *args: ({}, b"bad"))
        assert (
            client.get("/api/v1/observations?provider=bls&series_id=LNS14000000").status_code == 502
        )
