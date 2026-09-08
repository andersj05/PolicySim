"""Small local configuration surface. Environment takes precedence over .env."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def fred_key() -> str:
    if "FRED_API_KEY" in os.environ:
        return os.environ["FRED_API_KEY"].strip()
    path = ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() == "FRED_API_KEY":
                return value.strip().strip("\"'")
    return ""


def data_dir() -> Path:
    return Path(os.environ.get("POLICYSIM_DATA_DIR", str(ROOT / "data")))
