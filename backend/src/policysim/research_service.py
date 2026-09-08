"""Local import, snapshot and run persistence around the pure research engine."""

import csv
import hashlib
import io
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from math import isfinite
from pathlib import Path
from threading import Lock

from policysim import analysis, forecasting, storage
from policysim.domain import DataError, Observation, Series, Snapshot
from policysim.research_contracts import (
    AnalysisRequest,
    AnalysisResult,
    CsvImportRequest,
    CsvPreview,
    ForecastRequest,
    ForecastRun,
    NamedValue,
    RunSummary,
)

ROOT = Path(__file__).resolve().parents[3]
RUN_LOCK = Lock()
if sys.platform == "win32":
    PROCESS_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    PROCESS_FLAGS = 0


def csv_rows(content: str) -> tuple[list[str], list[list[str]]]:
    try:
        parsed = list(csv.reader(io.StringIO(content.lstrip("\ufeff")), strict=True))
    except csv.Error:
        raise DataError("This CSV is not valid. Use a comma-delimited UTF-8 file.", 422) from None
    parsed = [row for row in parsed if row and any(cell.strip() for cell in row)]
    if len(parsed) < 2:
        raise DataError("The CSV needs a header and at least one data row.", 422)
    columns = [column.strip() for column in parsed[0]]
    if (
        len(columns) > 100
        or any(not col or len(col) > 160 for col in columns)
        or len(set(columns)) != len(columns)
    ):
        raise DataError("Use unique, non-empty column names (at most 100 columns).", 422)
    if len(parsed) > 25001 or any(len(row) != len(columns) for row in parsed[1:]):
        raise DataError(
            "Use at most 25,000 rows, with the same number of fields as the header.", 422
        )
    return columns, parsed[1:]


def preview_csv(content: str) -> CsvPreview:
    columns, rows = csv_rows(content)
    return CsvPreview(columns=columns, rows=rows[:5], count=len(rows))


def import_csv(root: Path, request: CsvImportRequest) -> Snapshot:
    columns, rows = csv_rows(request.content)
    if request.date_column == request.value_column:
        raise DataError("Select different date and value columns.", 422)
    try:
        date_index, value_index = (
            columns.index(request.date_column),
            columns.index(request.value_column),
        )
    except ValueError:
        raise DataError("The selected columns are not in this CSV.", 422) from None
    observations = []
    for number, row in enumerate(rows, start=2):
        label, text = row[date_index].strip(), row[value_index].strip()
        analysis.parse_date(label)
        try:
            value = None if text.lower() in ("", "na", "n/a", "null", ".") else float(text)
        except ValueError:
            raise DataError(
                f"Row {number}: use a number or an empty cell for missing data.", 422
            ) from None
        if value is not None and (not isfinite(value) or abs(value) > 1e100):
            raise DataError(f"Row {number}: values must be finite and within ±1e100.", 422)
        observations.append(Observation(date=label, value=value))
    # Sorting is explicit in the import contract; the original CSV remains immutable.
    observations.sort(key=lambda row: analysis.parse_date(row.date))
    analysis.calendar_rows(observations, request.frequency)
    digest = hashlib.sha256(request.content.encode("utf-8")).hexdigest()
    snapshot = Snapshot(
        series=Series(
            provider="local",
            id=f"CSV-{digest[:8]}",
            title=request.title.strip() or "Imported series",
            source_name="Local CSV",
            units=request.units.strip() or "Value",
            frequency=request.frequency.title(),
            seasonal_adjustment="Not specified",
            source_url="",
            license_url="",
            notes=f"Date column: {request.date_column}; value column: {request.value_column}.",
        ),
        country="",
        retrieved_at=datetime.now(UTC).isoformat(),
        snapshot_id="",
        raw_sha256=[],
        vintage="User-supplied CSV; publication times and historical vintages are not verified.",
        transformations=["Selected date/value columns; sorted ascending by observation date."],
        observations=observations,
    )
    return storage.save(root, snapshot, [request.content.encode("utf-8")])


def analyze_snapshot(root: Path, request: AnalysisRequest) -> AnalysisResult:
    snapshot = storage.read(root, request.snapshot_id)
    frequency = analysis.resolve_frequency(request.frequency, snapshot.series.frequency)
    return analysis.analyze(snapshot.observations, frequency, snapshot.series.units, request)


def environment() -> list[NamedValue]:
    values = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "rng": "None; analytical prediction intervals, deterministic estimators",
        "code_commit": "unavailable",
        "code_dirty": "unknown",
    }
    for package in ("numpy", "scipy", "pandas", "statsmodels"):
        values[package] = version(package)
    for filename in ("uv.lock", "frontend/package-lock.json"):
        values[filename + "_sha256"] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for path in sorted((ROOT / "backend/src").rglob("*.py")):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    values["backend_source_sha256"] = digest.hexdigest()
    try:
        for key, args in (
            ("code_commit", ["rev-parse", "HEAD"]),
            ("code_dirty", ["status", "--porcelain"]),
        ):
            result = subprocess.run(
                ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
                creationflags=PROCESS_FLAGS,
            )
            values[key] = (
                str(bool(result.stdout.strip())).lower()
                if key == "code_dirty"
                else result.stdout.strip()
            )
    except (OSError, subprocess.SubprocessError):
        pass
    return [NamedValue(name=name, value=value) for name, value in values.items()]


def run_forecast(root: Path, request: ForecastRequest) -> ForecastRun:
    if not RUN_LOCK.acquire(blocking=False):
        raise DataError("Another forecast is running. Retry when it finishes.", 409)
    try:
        snapshot = storage.read(root, request.snapshot_id)
        frequency = analysis.resolve_frequency(request.frequency, snapshot.series.frequency)
        history, notes = forecasting.prepare(snapshot.observations, frequency, request)
        models = forecasting.evaluate(history, frequency, request)
        run = ForecastRun(
            created_at=datetime.now(UTC).isoformat(),
            engine_version=forecasting.ENGINE_VERSION,
            title=snapshot.series.title,
            units=snapshot.series.units,
            country=snapshot.country,
            request=request,
            frequency=frequency,
            history=history,
            models=models,
            warnings=[
                *notes,
                "Historical evaluation is revision-biased; data vintages are not verified.",
            ],
            assumptions=[
                "Expanding training windows; non-overlapping validation blocks "
                "precede a separate final holdout.",
                "No automatic model selection. Repeated manual tuning on the holdout "
                "compromises its independence.",
                "Future forecasts refit on all selected observations, including evaluation data.",
                "Gaussian prediction intervals condition on fitted parameters, except the "
                "mean baseline includes sample-mean estimation variance. Model and revision "
                "uncertainty are excluded.",
                "Model ranks and RMSE skill use rolling validation only; ties share rank. "
                "Positive skill means lower RMSE than naive. No automatic model selection.",
                "No imputation, resampling, causal effects or future exogenous variables. "
                "Forecasts remain in original units.",
                "MASE uses training-only seasonal naive scale at the configured period, "
                "or naive scale when period is 1; undefined at zero scale.",
                "ETS residual Ljung–Box degrees of freedom use all estimated parameters; "
                "interpret as an approximate diagnostic.",
                "Floating-point results may differ across platforms; "
                "compare with numerical tolerance.",
            ],
            environment=environment(),
        )
        run.run_id = storage.put(root, run.model_dump_json().encode(), "runs")
        return run
    except OSError:
        raise DataError(
            "Cannot save the forecast run. Check local disk permissions and space.", 503
        ) from None
    finally:
        RUN_LOCK.release()


def read_run(root: Path, run_id: str) -> ForecastRun:
    try:
        content = (root / "runs" / f"{run_id}.json").read_bytes()
        if hashlib.sha256(content).hexdigest() != run_id:
            raise DataError("The saved forecast failed its integrity check.", 500)
        run = ForecastRun.model_validate_json(content)
    except FileNotFoundError:
        raise DataError("This saved forecast was not found.", 404) from None
    except (OSError, ValueError):
        raise DataError("This saved forecast cannot be read.", 500) from None
    run.run_id = run_id
    return run


def list_runs(root: Path) -> list[RunSummary]:
    try:
        paths = sorted(
            (root / "runs").glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True
        )
        summaries = []
        for path in paths[:100]:
            run = read_run(root, path.stem)
            summaries.append(
                RunSummary(
                    run_id=run.run_id,
                    created_at=run.created_at,
                    title=run.title,
                    country=run.country,
                    horizon=run.request.horizon,
                    frequency=run.frequency,
                    models=[result.model for result in run.models if result.status == "success"],
                )
            )
        return summaries
    except OSError:
        raise DataError("Cannot read the saved forecasts folder.", 503) from None


def observations_csv(rows: list[Observation]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["date", "value"])
    writer.writerows((row.date, "" if row.value is None else row.value) for row in rows)
    return stream.getvalue()
