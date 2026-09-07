"""Portable project commands: setup, dev, check, format."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def executable(name: str) -> str:
    command = "npm.cmd" if name == "npm" and sys.platform == "win32" else name
    resolved = shutil.which(command)
    if resolved is None:
        raise RuntimeError(f"Missing {name}. Install the prerequisites in docs/DEVELOPMENT.md.")
    return resolved


def run(*args: str) -> None:
    print("+ " + " ".join(args), flush=True)
    subprocess.run([executable(args[0]), *args[1:]], cwd=ROOT, check=True)


def prettier(mode: str) -> None:
    result = subprocess.run(
        [
            executable("git"),
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    suffixes = {".md", ".json", ".yaml", ".yml", ".ts", ".tsx", ".js", ".css", ".html"}
    paths = sorted(
        {
            path.decode("utf-8")
            for path in result.stdout.split(b"\0")
            if path
            and Path(path.decode("utf-8")).suffix in suffixes
            and (ROOT / path.decode("utf-8")).is_file()
        }
    )
    if paths:
        run("node", "frontend/node_modules/prettier/bin/prettier.cjs", mode, *paths)


def setup() -> None:
    run("uv", "sync", "--locked")
    run("npm", "--prefix", "frontend", "ci")
    run("uv", "run", "--locked", "pre-commit", "install")


def check() -> None:
    run("uv", "run", "--locked", "python", "scripts/check_repo.py")
    run("uv", "run", "--locked", "ruff", "check", "backend", "scripts")
    run("uv", "run", "--locked", "ruff", "format", "--check", "backend", "scripts")
    run("uv", "run", "--locked", "mypy")
    run("uv", "run", "--locked", "pytest")
    run("npm", "--prefix", "frontend", "run", "check")
    prettier("--check")


def format_files() -> None:
    run("uv", "run", "--locked", "ruff", "check", "--fix", "backend", "scripts")
    run("uv", "run", "--locked", "ruff", "format", "backend", "scripts")
    prettier("--write")


def require_free_ports() -> None:
    for port in (8000, 5173):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError(
                    f"Port {port} is unavailable. Stop its owner and retry."
                ) from exc


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if sys.platform == "win32":
        if process.poll() is None:
            # Only the process tree started by this launcher is targeted.
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def dev() -> None:
    python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
    if not python.is_file() or not vite.is_file():
        raise RuntimeError("Dependencies missing. Run python scripts/project.py setup first.")
    require_free_ports()
    commands = [
        (
            [
                str(python),
                "-m",
                "uvicorn",
                "policysim.main:app",
                "--reload",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            ROOT,
        ),
        (
            [
                executable("node"),
                str(vite),
                "--host",
                "127.0.0.1",
                "--port",
                "5173",
                "--strictPort",
            ],
            ROOT / "frontend",
        ),
    ]
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for command, cwd in commands:
            processes.append(
                subprocess.Popen(
                    command,
                    cwd=cwd,
                    start_new_session=sys.platform != "win32",
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
            )
        print("UI: http://127.0.0.1:5173 | API: http://127.0.0.1:8000/docs", flush=True)
        print("Press Ctrl+C to stop both servers.", flush=True)
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    raise RuntimeError(
                        f"Development server exited ({code}); stopping both servers."
                    )
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopping development servers.", flush=True)
    finally:
        for process in reversed(processes):
            stop_process(process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "dev", "check", "format"])
    args = parser.parse_args()
    try:
        {"setup": setup, "dev": dev, "check": check, "format": format_files}[args.command]()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
