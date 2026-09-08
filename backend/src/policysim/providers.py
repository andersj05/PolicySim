"""Read-only provider adapters. Upstream JSON stays at this boundary."""

from __future__ import annotations

import json
import math
import threading
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from policysim.domain import Country, DataError, Observation, SearchResult, Series, Snapshot
from policysim.settings import data_dir, fred_key
from policysim.storage import save

FRED = "https://api.stlouisfed.org/fred/"
WB = "https://api.worldbank.org/v2/"
MAX_PAGES = 100
PAGE_SIZE = 20


def fetch_bytes(base: str, path: str, params: dict[str, str | int]) -> bytes:
    request = Request(
        base + path + "?" + urlencode(params), headers={"User-Agent": "PolicySim/0.1"}
    )
    try:
        with urlopen(request, timeout=30) as response:
            body: bytes = response.read(32 * 1024 * 1024 + 1)
        if len(body) > 32 * 1024 * 1024:
            raise DataError("The provider response is too large. Try a narrower date range.")
        return body
    except HTTPError as exc:
        if exc.code == 429:
            raise DataError(
                "The provider's request limit was reached. Wait a minute and retry.", 429
            ) from None
        if base == FRED and exc.code in (400, 401, 403):
            raise DataError(
                "FRED rejected this request. Check the series ID and backend API key.", 502
            ) from None
        raise DataError(
            "The data provider could not complete this request. Please retry."
        ) from None
    except (URLError, TimeoutError, OSError):
        raise DataError(
            "The data provider is unreachable or timed out. Please retry.", 504
        ) from None


def fetch(base: str, path: str, params: dict[str, str | int]) -> tuple[Any, bytes]:
    body = fetch_bytes(base, path, params)
    try:
        return json.loads(body), body
    except (ValueError, UnicodeDecodeError):
        raise DataError("The data provider returned an unreadable response.") from None


def fred(path: str, **params: str | int) -> tuple[dict[str, Any], bytes]:
    key = fred_key()
    if not key:
        raise DataError("Add FRED_API_KEY to the backend .env file to connect FRED.", 503)
    payload, raw = fetch(FRED, path, {**params, "api_key": key, "file_type": "json"})
    if not isinstance(payload, dict) or "error_code" in payload:
        raise DataError("FRED returned an invalid response.")
    return payload, raw


def wb_pages(
    path: str, *, page_size: int = 5000, expected_source: str = "", **params: str | int
) -> tuple[list[dict[str, Any]], list[bytes]]:
    rows: list[dict[str, Any]] = []
    bodies = []
    expected = None
    for page in range(1, MAX_PAGES + 1):
        query: dict[str, str | int] = {"format": "json", **params}
        if page_size != 50:
            query["per_page"] = page_size
        if page > 1:
            query["page"] = page
        payload, raw = fetch(WB, path, query)
        if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[0], dict):
            raise DataError("World Bank could not find this indicator, database or geography.", 404)
        meta, items = payload
        if expected_source and str(meta.get("sourceid", "")) != expected_source:
            raise DataError("World Bank returned a different database than requested.")
        total = int(meta["total"])
        if expected is not None and expected != total:
            raise DataError("World Bank's catalog changed during retrieval. Please retry.")
        expected = total
        if items is not None and not isinstance(items, list):
            raise DataError("World Bank returned invalid observations.")
        rows.extend(items or [])
        bodies.append(raw)
        if page >= int(meta["pages"]):
            if len(rows) != total:
                raise DataError("World Bank returned incomplete data. Please retry.")
            return rows, bodies
    raise DataError("This dataset exceeds the download limit. Narrow the date range.", 422)


def fred_series(item: dict[str, Any]) -> Series:
    return Series(
        provider="fred",
        id=item["id"],
        title=item["title"],
        source_name="FRED",
        units=item["units"],
        frequency=item["frequency"],
        seasonal_adjustment=item["seasonal_adjustment"],
        notes=item.get("notes", ""),
        source_url="https://fred.stlouisfed.org/series/" + quote(item["id"], safe=""),
        license_url="https://fred.stlouisfed.org/legal/",
        updated=item.get("last_updated", ""),
    )


def wb_series(item: dict[str, Any]) -> Series:
    return Series(
        provider="worldbank",
        id=item["id"],
        title=item["name"],
        source_id=item["source"]["id"],
        source_name=item["source"]["value"],
        units=item.get("unit") or "See indicator title / source notes",
        frequency="Not specified by catalog",
        seasonal_adjustment="Not specified by provider",
        notes="\n\n".join(filter(None, [item.get("sourceNote"), item.get("sourceOrganization")])),
        source_url="https://databank.worldbank.org/source/"
        + item["source"]["id"]
        + "?series="
        + quote(item["id"], safe=""),
        license_url="https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
    )


class Catalog:
    """One-hour cache, published only after every metadata page succeeds."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.expires = 0.0
        self.items: list[Series] = []

    def get(self) -> list[Series]:
        with self.lock:
            if time.monotonic() >= self.expires:
                rows, _ = wb_pages("indicator")
                self.items = [wb_series(row) for row in rows]
                self.expires = time.monotonic() + 3600
            return self.items


catalog = Catalog()


def search(provider: str, query: str, page: int) -> SearchResult:
    if provider in ("bls", "ecb"):
        from policysim.official_providers import search_official

        return search_official(provider, query, page)
    offset = (page - 1) * PAGE_SIZE
    if provider == "fred":
        payload, _ = fred(
            "series/search",
            search_text=query,
            limit=PAGE_SIZE,
            offset=offset,
            order_by="search_rank",
            sort_order="desc",
        )
        items = [fred_series(row) for row in payload["seriess"]]
        total = int(payload["count"])
    else:
        terms = query.casefold().split()
        matches = [
            item
            for item in catalog.get()
            if all(
                term in f"{item.id} {item.title} {item.source_name}".casefold() for term in terms
            )
        ]
        matches.sort(
            key=lambda item: (
                item.id.casefold() != query.casefold(),
                item.source_id != "2",
                item.title,
            )
        )
        total = len(matches)
        items = matches[offset : offset + PAGE_SIZE]
    return SearchResult(items=items, total=total, page=page, page_size=PAGE_SIZE)


def countries() -> list[Country]:
    rows, _ = wb_pages("country", page_size=500)
    return sorted(
        [
            Country(id=row["id"], name=row["name"], aggregate=row["region"]["id"] == "NA")
            for row in rows
        ],
        key=lambda c: c.name,
    )


def number(value: Any) -> float | None:
    if value is None or value == ".":
        return None
    result = float(value)
    if not math.isfinite(result):
        raise DataError("The provider returned a non-finite observation.")
    return result


def load(
    provider: str, series_id: str, country: str, source_id: str, start: str, end: str
) -> Snapshot:
    if provider in ("bls", "ecb"):
        from policysim.official_providers import load_official

        return load_official(provider, series_id, start, end)
    raw: list[bytes] = []
    observations: list[Observation] = []
    if provider == "fred":
        metadata, body = fred("series", series_id=series_id)
        if not metadata["seriess"]:
            raise DataError("This FRED series was not found.", 404)
        series = fred_series(metadata["seriess"][0])
        raw.append(body)
        offset = 0
        for _ in range(MAX_PAGES):
            payload, body = fred(
                "series/observations",
                series_id=series_id,
                observation_start=start,
                observation_end=end,
                limit=100000,
                offset=offset,
                sort_order="asc",
            )
            raw.append(body)
            rows = payload["observations"]
            observations.extend(
                Observation(
                    date=row["date"],
                    value=number(row["value"]),
                    realtime_start=row.get("realtime_start", ""),
                    realtime_end=row.get("realtime_end", ""),
                )
                for row in rows
            )
            offset += len(rows)
            if offset >= int(payload["count"]):
                break
            if not rows:
                raise DataError("FRED returned incomplete observations. Please retry.")
        else:
            raise DataError("This series exceeds the download limit. Narrow the date range.", 422)
        country = ""
        vintage = "Latest available FRED revision; not a historical-vintage dataset."
    else:
        wb_metadata, bodies = wb_pages(
            "indicator/" + quote(series_id, safe=""), page_size=50, source=source_id
        )
        match = next((row for row in wb_metadata if row["source"]["id"] == source_id), None)
        if match is None:
            raise DataError(
                "This indicator was not found in the selected World Bank database.", 404
            )
        series = wb_series(match)
        raw.extend(bodies)
        # Retrieve complete histories: avoid fragile date queries at the provider edge.
        # WDI is the default source; verify its identity on every response page.
        source_params: dict[str, str | int] = {} if source_id == "2" else {"source": source_id}
        rows, bodies = wb_pages(
            "country/" + country + "/indicator/" + quote(series_id, safe=""),
            page_size=100,
            expected_source=source_id,
            **source_params,
        )
        raw.extend(bodies)
        series.updated = str(json.loads(bodies[0])[0].get("lastupdated", ""))
        observations = [
            Observation(date=row["date"], value=number(row["value"]))
            for row in rows
            if start[:4] <= row["date"][:4] <= end[:4]
        ]
        if (
            all(len(item.date) == 4 and item.date.isdigit() for item in observations)
            and observations
        ):
            series.frequency = "Annual"
        vintage = "Latest available World Bank revision; historical vintages are not supplied."
    observations.sort(key=lambda item: item.date)
    if len({item.date for item in observations}) != len(observations):
        raise DataError("The provider returned duplicate observation dates.")
    return save(
        data_dir(),
        Snapshot(
            series=series,
            country=country,
            retrieved_at=datetime.now(UTC).isoformat(),
            snapshot_id="",
            raw_sha256=[],
            vintage=vintage,
            transformations=[],
            requested_start=start,
            requested_end=end,
            observations=observations,
        ),
        raw,
    )
