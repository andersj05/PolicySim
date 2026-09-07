"""Check launcher failure and cleanup boundaries using owned local processes."""

import socket
import subprocess
import sys

import pytest

from scripts.project import PROCESS_FLAGS, require_free_ports, stop_process


def test_occupied_api_port_fails_clearly() -> None:
    with socket.socket() as owner:
        try:
            owner.bind(("127.0.0.1", 8000))
        except OSError:
            pytest.skip("Port 8000 already occupied by an unrelated process.")
        owner.listen()
        with pytest.raises(RuntimeError, match="Port 8000 is unavailable"):
            require_free_ports()


def test_cleanup_stops_owned_process() -> None:
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=sys.platform != "win32",
        creationflags=PROCESS_FLAGS,
    )
    try:
        stop_process(child)
        assert child.poll() is not None
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
