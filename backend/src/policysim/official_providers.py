"""Explicitly scoped, credential-free BLS and ECB adapters."""

import csv
import io
import re
from datetime import UTC, datetime

from policysim.domain import DataError, Observation, SearchResult, Series, Snapshot
from policysim.providers import PAGE_SIZE, fetch, fetch_bytes, number
from policysim.settings import data_dir
from policysim.storage import save

BLS = "https://api.bls.gov/publicAPI/v2/"
ECB = "https://data-api.ecb.europa.eu/service/"
BLS_CATALOG = [
    ("LNS14000000", "Unemployment rate", "Percent"),
    ("CES0000000001", "Total nonfarm payrolls", "Thousands of persons"),
    ("CUSR0000SA0", "Consumer price index · all items", "Index 1982–1984=100"),
    ("CUSR0000SA0L1E", "Core CPI · excluding food and energy", "Index 1982–1984=100"),
    ("CES0500000003", "Average hourly earnings · private sector", "Dollars per hour"),
    ("LNS11300000", "Labor force participation rate", "Percent"),
    ("LNS12300000", "Employment–population ratio", "Percent"),
    ("LNS12000000", "Civilian employment", "Thousands of persons"),
    ("CES3000000001", "Manufacturing employment", "Thousands of persons"),
    ("CES0500000001", "Total private employment", "Thousands of persons"),
]
CURRENCIES = {
    "USD": "US dollar",
    "GBP": "Pound sterling",
    "JPY": "Japanese yen",
    "CHF": "Swiss franc",
    "CAD": "Canadian dollar",
    "AUD": "Australian dollar",
    "CNY": "Chinese yuan",
    "SEK": "Swedish krona",
    "NOK": "Norwegian krone",
    "DKK": "Danish krone",
    "NZD": "New Zealand dollar",
    "INR": "Indian rupee",
    "BRL": "Brazilian real",
    "MXN": "Mexican peso",
    "ZAR": "South African rand",
    "KRW": "South Korean won",
    "SGD": "Singapore dollar",
    "HKD": "Hong Kong dollar",
    "PLN": "Polish zloty",
    "CZK": "Czech koruna",
    "HUF": "Hungarian forint",
}


def bls_series(series_id: str) -> Series:
    item = next((item for item in BLS_CATALOG if item[0] == series_id), None)
    if item is None:
        raise DataError("Choose a series from the supported BLS labor and prices catalog.", 422)
    return Series(
        provider="bls",
        id=series_id,
        title=item[1],
        source_name="U.S. Bureau of Labor Statistics",
        units=item[2],
        frequency="Monthly",
        seasonal_adjustment="Seasonally adjusted",
        source_url="https://data.bls.gov/timeseries/" + series_id,
        license_url="https://www.bls.gov/bls/linksite.htm",
        notes="Direct BLS monthly data. Annual averages are excluded. "
        "Unregistered API access supports 10 calendar years per request and 25 requests per day. "
        "Source metadata is maintained for the supported catalog; response footnotes follow.",
    )


def ecb_series(series_id: str) -> Series:
    match = re.fullmatch(r"EXR\.M\.([A-Z]{3})\.EUR\.SP00\.A", series_id)
    if not match:
        raise DataError("Use a monthly ECB reference-rate key, e.g. EXR.M.USD.EUR.SP00.A.", 422)
    currency = match[1]
    return Series(
        provider="ecb",
        id=series_id,
        title=f"{CURRENCIES.get(currency, currency)} / euro",
        source_name="European Central Bank",
        units=f"{currency} per EUR",
        frequency="Monthly",
        seasonal_adjustment="Not seasonally adjusted",
        source_url="https://data.ecb.europa.eu/data/datasets/EXR/" + series_id,
        license_url="https://www.ecb.europa.eu/services/disclaimer/html/index.en.html",
        notes="ECB reference exchange rate, monthly average. Units of foreign currency "
        "per euro; this is not an executable trading price. Observation status flags "
        "are retained below and in the original response.",
    )


def search_official(provider: str, query: str, page: int) -> SearchResult:
    items = (
        [bls_series(item[0]) for item in BLS_CATALOG]
        if provider == "bls"
        else [ecb_series(f"EXR.M.{currency}.EUR.SP00.A") for currency in CURRENCIES]
    )
    if provider == "ecb" and re.fullmatch(r"EXR\.M\.[A-Z]{3}\.EUR\.SP00\.A", query.upper()):
        items = [ecb_series(query.upper())]
    terms = query.casefold().split()
    matches = [
        item
        for item in items
        if all(term in f"{item.id} {item.title} {item.units}".casefold() for term in terms)
    ]
    offset = (page - 1) * PAGE_SIZE
    return SearchResult(
        items=matches[offset : offset + PAGE_SIZE],
        total=len(matches),
        page=page,
        page_size=PAGE_SIZE,
    )


def load_bls(series_id: str, start: str, end: str) -> tuple[Series, list[Observation], bytes]:
    series = bls_series(series_id)
    if int(end[:4]) - int(start[:4]) > 9:
        raise DataError(
            "BLS supports at most 10 calendar years per unregistered request. "
            "Set a shorter source range.",
            422,
        )
    payload, raw = fetch(
        BLS, "timeseries/data/" + series_id, {"startyear": start[:4], "endyear": end[:4]}
    )
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise DataError(
            "BLS could not complete the request. Its daily quota may be exhausted; "
            "retry later or use the equivalent FRED series."
        )
    # A successful envelope can still report ignored dates or partial data.
    if payload.get("message"):
        raise DataError(
            "BLS reported a data availability or request warning. "
            "The response was not saved; try a narrower date range."
        )
    result = payload["Results"]["series"]
    if len(result) != 1 or result[0]["seriesID"] != series_id:
        raise DataError("BLS returned a different series than requested.")
    observations = []
    footnotes = []
    for row in result[0]["data"]:
        period = row["period"]
        if period == "M13":
            continue
        if not re.fullmatch(r"M(0[1-9]|1[0-2])", period):
            raise DataError("BLS returned an unexpected monthly period.")
        label = f"{int(row['year']):04d}-{period[1:]}-01"
        if not start[:7] <= label[:7] <= end[:7]:
            continue
        value = row["value"].strip()
        observations.append(
            Observation(date=label, value=number(None if value in ("", "-", "–") else value))
        )
        for note in row.get("footnotes", []):
            if note.get("text"):
                footnotes.append(f"{label}: {note['text']}")
    if footnotes:
        series.notes += "\n\n" + "\n".join(dict.fromkeys(footnotes))
    return series, observations, raw


def load_ecb(series_id: str, start: str, end: str) -> tuple[Series, list[Observation], bytes]:
    series = ecb_series(series_id)
    raw = fetch_bytes(
        ECB,
        "data/EXR/" + series_id.removeprefix("EXR."),
        {"startPeriod": start[:7], "endPeriod": end[:7], "format": "csvdata"},
    )
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    required = {"KEY", "TIME_PERIOD", "OBS_VALUE", "UNIT", "UNIT_MULT", "OBS_STATUS"}
    if not required.issubset(reader.fieldnames or []):
        raise DataError("ECB returned unexpected CSV columns.")
    observations = []
    flags = []
    for row in reader:
        if (
            row["KEY"] != series_id
            or row["UNIT"] != series_id.split(".")[2]
            or row["UNIT_MULT"] != "0"
        ):
            raise DataError("ECB returned a different series or unit scale than requested.")
        label = row["TIME_PERIOD"]
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", label):
            raise DataError("ECB returned an unexpected monthly period.")
        if not start[:7] <= label <= end[:7]:
            raise DataError("ECB returned observations outside the requested range.")
        observations.append(Observation(date=label + "-01", value=number(row["OBS_VALUE"] or None)))
        if row["OBS_STATUS"] and row["OBS_STATUS"] != "A":
            flags.append(f"{label}: {row['OBS_STATUS']}")
        if row.get("TITLE"):
            series.title = row["TITLE"]
    if flags:
        series.notes += "\n\nObservation status: " + "; ".join(flags)
    return series, observations, raw


def load_official(provider: str, series_id: str, start: str, end: str) -> Snapshot:
    series, observations, raw = (load_bls if provider == "bls" else load_ecb)(series_id, start, end)
    if not observations:
        raise DataError("No observations were returned for this series and date range.", 404)
    observations.sort(key=lambda item: item.date)
    if len({item.date for item in observations}) != len(observations):
        raise DataError("The provider returned duplicate observation dates.")
    return save(
        data_dir(),
        Snapshot(
            series=series,
            country="USA" if provider == "bls" else "",
            retrieved_at=datetime.now(UTC).isoformat(),
            snapshot_id="",
            raw_sha256=[],
            vintage="Latest available revision; historical vintages are not supplied.",
            transformations=[],
            requested_start=start,
            requested_end=end,
            observations=observations,
        ),
        [raw],
    )
