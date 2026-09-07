"""Deterministic provider boundary fixtures; values are test-only, not research data."""

import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient
from policysim import providers, settings, storage
from policysim.domain import DataError, Snapshot
from policysim.main import app

FRED_SERIES = {
    "id": "TEST",
    "title": "Test fixture",
    "units": "Percent",
    "frequency": "Monthly",
    "seasonal_adjustment": "Not Seasonally Adjusted",
    "notes": "Fixture metadata",
}
WB_SERIES = {
    "id": "TEST.ID",
    "name": "Fixture indicator",
    "unit": "",
    "source": {"id": "2", "value": "Test database"},
    "sourceNote": "Fixture only",
    "sourceOrganization": "Test source",
}


@pytest.fixture(autouse=True)
def isolate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FRED_API_KEY", "fixture-key")
    monkeypatch.setenv("POLICYSIM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(providers, "catalog", providers.Catalog())


def mock_fetch(monkeypatch: pytest.MonkeyPatch, payloads: list[Any]) -> list[dict[str, str | int]]:
    calls: list[dict[str, str | int]] = []

    def fetch(base: str, path: str, params: dict[str, str | int]) -> tuple[Any, bytes]:
        calls.append(params)
        payload = payloads[len(calls) - 1]
        return payload, json.dumps(payload).encode()

    monkeypatch.setattr(providers, "fetch", fetch)
    return calls


def wb(rows: list[dict[str, Any]] | None, pages: int = 1, total: int | None = None) -> list[Any]:
    return [
        {"sourceid": "2", "pages": pages, "total": len(rows or []) if total is None else total},
        rows,
    ]


def test_fred_pagination_nulls_and_immutable_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = mock_fetch(
        monkeypatch,
        [
            {"seriess": [FRED_SERIES]},
            {
                "count": 2,
                "observations": [
                    {"date": "2020-01-01", "value": ".", "realtime_start": "2021-01-01"}
                ],
            },
            {"count": 2, "observations": [{"date": "2020-02-01", "value": "3.14"}]},
        ],
    )
    result = providers.load("fred", "TEST", "USA", "2", "2020-01-01", "2020-12-31")
    assert [row.value for row in result.observations] == [None, 3.14]
    assert result.observations[0].realtime_start == "2021-01-01"
    assert calls[-1]["offset"] == 1
    assert result.country == "" and result.transformations == []
    for checksum in result.raw_sha256:
        body = (tmp_path / "raw" / f"{checksum}.json").read_bytes()
        assert hashlib.sha256(body).hexdigest() == checksum
        assert b"fixture-key" not in body
    manifest = (tmp_path / "snapshots" / f"{result.snapshot_id}.json").read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == result.snapshot_id
    assert Snapshot.model_validate_json(manifest).observations == result.observations


def test_worldbank_metadata_and_sorted_nulls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = mock_fetch(
        monkeypatch,
        [wb([WB_SERIES]), wb([{"date": "2022", "value": None}, {"date": "2020", "value": 12}])],
    )
    result = providers.load("worldbank", "TEST.ID", "USA", "2", "2020-06-01", "2022-06-01")
    assert result.series.frequency == "Annual"
    assert result.series.units == "See indicator title / source notes"
    assert result.series.source_id == "2" and result.country == "USA"
    assert [row.date for row in result.observations] == ["2020", "2022"]
    assert result.observations[-1].value is None
    assert "date" not in calls[-1] and "source" not in calls[-1]
    assert result.requested_start == "2020-06-01"
    assert result.requested_end == "2022-06-01"


def test_worldbank_validates_database_and_filters_years(monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = {**WB_SERIES, "source": {"id": "3", "value": "Another database"}}
    mock_fetch(monkeypatch, [wb([metadata]), wb([])])
    with pytest.raises(DataError, match="different database"):
        providers.load("worldbank", "TEST.ID", "USA", "3", "2020-01-01", "2022-01-01")
    payload = wb(
        [{"date": "2019", "value": 9}, {"date": "2020", "value": 1}, {"date": "2023", "value": 2}]
    )
    payload[0]["sourceid"] = "3"
    calls = mock_fetch(monkeypatch, [wb([metadata]), payload])
    result = providers.load("worldbank", "TEST.ID", "USA", "3", "2020-01-01", "2022-01-01")
    assert calls[-1]["source"] == "3"
    assert [row.date for row in result.observations] == ["2020"]


def test_catalog_pagination_search_cache_and_source_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    second = {**WB_SERIES, "source": {"id": "3", "value": "Other database"}}
    calls = mock_fetch(monkeypatch, [wb([second], 2, 2), wb([WB_SERIES], 2, 2)])
    result = providers.search("worldbank", "TEST.ID", 1)
    assert result.total == 2 and result.items[0].source_id == "2"
    assert providers.search("worldbank", "unmatched", 1).total == 0
    assert providers.search("worldbank", "fixture", 2).items == []
    assert len(calls) == 2 and calls[1]["page"] == 2


def test_fred_search_and_countries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = mock_fetch(
        monkeypatch,
        [
            {"seriess": [FRED_SERIES], "count": 23},
            wb(
                [
                    {"id": "WLD", "name": "World", "region": {"id": "NA"}},
                    {"id": "USA", "name": "United States", "region": {"id": "NAC"}},
                ]
            ),
        ],
    )
    assert providers.search("fred", "fixture", 2).total == 23
    assert calls[0]["offset"] == 20
    countries = providers.countries()
    assert countries[0].id == "USA" and countries[1].aggregate


@pytest.mark.parametrize(
    "payloads, message",
    [
        ([[{"message": "invalid"}]], "could not find"),
        ([wb([], 1, 1)], "incomplete"),
        ([wb([WB_SERIES], 2, 2), wb([], 2, 3)], "changed"),
        ([[{"pages": 1, "total": 1}, "invalid"]], "invalid observations"),
    ],
)
def test_worldbank_rejects_partial_or_malformed_pages(
    monkeypatch: pytest.MonkeyPatch, payloads: list[Any], message: str
) -> None:
    mock_fetch(monkeypatch, payloads)
    with pytest.raises(DataError, match=message):
        providers.wb_pages("indicator")


def test_bounded_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(providers, "MAX_PAGES", 1)
    mock_fetch(monkeypatch, [wb([WB_SERIES], 2, 2)])
    with pytest.raises(DataError, match="download limit"):
        providers.wb_pages("indicator")
    mock_fetch(
        monkeypatch,
        [
            {"seriess": [FRED_SERIES]},
            {"count": 2, "observations": [{"date": "2020-01-01", "value": "1"}]},
        ],
    )
    with pytest.raises(DataError, match="download limit"):
        providers.load("fred", "TEST", "USA", "2", "2020-01-01", "2022-01-01")


@pytest.mark.parametrize(
    "payloads, message",
    [
        ([{"seriess": []}], "not found"),
        ([{"seriess": [FRED_SERIES]}, {"count": 1, "observations": []}], "incomplete"),
        (
            [
                {"seriess": [FRED_SERIES]},
                {"count": 2, "observations": [{"date": "2020-01-01", "value": "1"}] * 2},
            ],
            "duplicate",
        ),
    ],
)
def test_invalid_fred_observations(
    monkeypatch: pytest.MonkeyPatch, payloads: list[Any], message: str
) -> None:
    mock_fetch(monkeypatch, payloads)
    with pytest.raises(DataError, match=message):
        providers.load("fred", "TEST", "USA", "2", "2020-01-01", "2022-01-01")


def test_worldbank_empty_missing_source_and_nonannual(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_fetch(monkeypatch, [wb([])])
    with pytest.raises(DataError, match="not found"):
        providers.load("worldbank", "TEST", "USA", "2", "2020-01-01", "2022-01-01")
    for rows in ([], [{"date": "2020Q1", "value": 1}]):
        mock_fetch(monkeypatch, [wb([WB_SERIES]), wb(rows)])
        result = providers.load("worldbank", "TEST", "USA", "2", "2020-01-01", "2022-01-01")
        assert result.series.frequency == "Not specified by catalog"


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nonfinite_is_never_a_number(value: str) -> None:
    with pytest.raises(DataError, match="non-finite"):
        providers.number(value)


def test_fred_configuration_and_bad_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRED_API_KEY", "")
    with pytest.raises(DataError, match="FRED_API_KEY"):
        providers.fred("series")
    monkeypatch.setenv("FRED_API_KEY", "fixture-key")
    payloads: list[Any] = [[], {"error_code": 400}]
    for payload in payloads:
        mock_fetch(monkeypatch, [payload])
        with pytest.raises(DataError, match="invalid response"):
            providers.fred("series")


@pytest.mark.parametrize(
    "exception, status",
    [
        (HTTPError("secret-url", 429, "secret", Message(), None), 429),
        (HTTPError("secret-url", 400, "secret", Message(), None), 502),
        (HTTPError("secret-url", 500, "secret", Message(), None), 502),
        (URLError("secret-url"), 504),
        (TimeoutError("secret"), 504),
    ],
)
def test_network_errors_never_leak_provider_url(
    monkeypatch: pytest.MonkeyPatch, exception: Exception, status: int
) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise exception

    monkeypatch.setattr(providers, "urlopen", fail)
    with pytest.raises(DataError) as caught:
        providers.fetch(providers.FRED, "series", {"api_key": "secret"})
    assert caught.value.status == status and "secret" not in str(caught.value)


@pytest.mark.parametrize(
    "body, valid", [(b'{"ok":true}', True), (b"not json", False), (b"\xff", False)]
)
def test_transport_json(monkeypatch: pytest.MonkeyPatch, body: bytes, valid: bool) -> None:
    monkeypatch.setattr(providers, "urlopen", lambda *args, **kwargs: io.BytesIO(body))
    if valid:
        assert providers.fetch(providers.WB, "indicator", {}) == ({"ok": True}, body)
    else:
        with pytest.raises(DataError, match="unreadable"):
            providers.fetch(providers.WB, "indicator", {})


def test_oversized_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers, "urlopen", lambda *args, **kwargs: io.BytesIO(b" " * (32 * 1024 * 1024 + 1))
    )
    with pytest.raises(DataError, match="too large"):
        providers.fetch(providers.WB, "indicator", {})


def test_storage_reuse_corruption_and_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    digest = storage.put(tmp_path, b"fixture", "raw")
    assert storage.put(tmp_path, b"fixture", "raw") == digest
    (tmp_path / "raw" / f"{digest}.json").write_bytes(b"corrupt")
    with pytest.raises(DataError, match="integrity"):
        storage.put(tmp_path, b"fixture", "raw")
    result = Snapshot(
        series=providers.fred_series(FRED_SERIES),
        country="",
        retrieved_at="now",
        snapshot_id="",
        raw_sha256=[],
        vintage="latest",
        transformations=[],
        observations=[],
    )

    def fail(*args: Any) -> str:
        raise PermissionError()

    monkeypatch.setattr(storage, "put", fail)
    with pytest.raises(DataError, match="Cannot save"):
        storage.save(tmp_path, result, [b"fixture"])


def test_settings_precedence_and_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "ROOT", tmp_path)
    monkeypatch.delenv("FRED_API_KEY")
    assert settings.fred_key() == ""
    (tmp_path / ".env").write_text(
        '# test\nOTHER=ignored\nFRED_API_KEY="local-fixture"\n', encoding="utf-8-sig"
    )
    assert settings.fred_key() == "local-fixture"
    monkeypatch.setenv("FRED_API_KEY", "environment-fixture")
    assert settings.fred_key() == "environment-fixture"
    monkeypatch.delenv("FRED_API_KEY")
    (tmp_path / ".env").write_text("OTHER=ignored")
    assert settings.fred_key() == ""


def test_http_validation_and_redaction(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/providers").json() == {"fred_configured": True}
        for query in (
            "provider=invalid&q=a",
            "provider=fred&q=",
            "provider=fred&q=%20",
            "provider=fred&q=a&page=0",
        ):
            assert client.get("/api/v1/series?" + query).status_code == 422
        for query in (
            "provider=fred&series_id=../secret",
            "provider=fred&series_id=X&start=2024-01-01&end=2020-01-01",
            "provider=worldbank&series_id=X&country=all",
        ):
            assert client.get("/api/v1/observations?" + query).status_code == 422
        mock_fetch(monkeypatch, [{"seriess": [FRED_SERIES], "count": 1}])
        assert client.get("/api/v1/series?provider=fred&q=test").json()["total"] == 1
        mock_fetch(monkeypatch, [{}])
        assert client.get("/api/v1/series?provider=fred&q=test").status_code == 502
        mock_fetch(monkeypatch, [{}])
        assert client.get("/api/v1/observations?provider=fred&series_id=TEST").status_code == 502
        mock_fetch(monkeypatch, [{"seriess": [FRED_SERIES]}, {"count": 0, "observations": []}])
        response = client.get("/api/v1/observations?provider=fred&series_id=TEST")
        assert response.status_code == 200 and response.json()["observations"] == []
        assert "fixture-key" not in response.text
        mock_fetch(monkeypatch, [wb([])])
        assert client.get("/api/v1/countries").json() == []
