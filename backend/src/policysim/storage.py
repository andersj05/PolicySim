"""Immutable raw response objects and self-contained normalized manifests."""

import hashlib
from pathlib import Path

from policysim.domain import DataError, Snapshot


def put(root: Path, content: bytes, folder: str) -> str:
    digest = hashlib.sha256(content).hexdigest()
    destination = root / folder / f"{digest}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        if destination.read_bytes() != content:
            raise DataError("A local snapshot failed its integrity check.", 500) from None
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
