"""Immutable raw response objects and self-contained normalized manifests."""

import hashlib
import os
import tempfile
from pathlib import Path

from policysim.domain import DataError, Snapshot


def put(root: Path, content: bytes, folder: str) -> str:
    digest = hashlib.sha256(content).hexdigest()
    destination = root / folder / f"{digest}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Publish only complete objects. Concurrent readers cannot see a partial write.
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.read_bytes() != content:
                raise DataError("A local snapshot failed its integrity check.", 500) from None
    finally:
        temporary.unlink()
    return digest


def save(root: Path, snapshot: Snapshot, raw: list[bytes]) -> Snapshot:
    try:
        snapshot.raw_sha256 = [put(root, body, "raw") for body in raw]
        content = snapshot.model_dump_json().encode()
        snapshot.snapshot_id = put(root, content, "snapshots")
    except OSError:
        raise DataError(
            "Cannot save the data snapshot. Check local disk permissions/space.", 503
        ) from None
    return snapshot


def read(root: Path, snapshot_id: str) -> Snapshot:
    try:
        content = (root / "snapshots" / f"{snapshot_id}.json").read_bytes()
        if hashlib.sha256(content).hexdigest() != snapshot_id:
            raise DataError("The saved snapshot failed its integrity check.", 500)
        snapshot = Snapshot.model_validate_json(content)
    except FileNotFoundError:
        raise DataError(
            "This local snapshot was not found. Reload the series to save it again.", 404
        ) from None
    except OSError:
        raise DataError(
            "Cannot read this local snapshot. Check storage permissions.", 503
        ) from None
    except ValueError:
        raise DataError("The saved snapshot is invalid.", 500) from None
    snapshot.snapshot_id = snapshot_id
    return snapshot
