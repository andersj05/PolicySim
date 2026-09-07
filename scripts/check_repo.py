"""Repository policy checks. Standard library only; safe to run before setup."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "AGENTS.md": ["## Read before changing anything", "## GitHub CLI authentication"],
    "docs/memory/STATE.md": [
        "## Updated", "## Implemented", "## Verified", "## Open issues", "## Next action",
    ],
    "docs/memory/README.md": ["## Read order and ownership", "## Update protocol"],
    "docs/memory/CONSTRAINTS.md": ["# Durable constraints"],
    "docs/decisions/README.md": ["# Decision index"],
}
HANDOFF_HEADINGS = ["## Context", "## Changes", "## Verification", "## Open issues", "## Next action"]
LINK = re.compile(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
GITHUB_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")


def repository_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "ls-files",
         "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, check=True, capture_output=True,
    )
    return sorted({Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p})


def route_errors(base: str, head: str) -> list[str]:
    if base == "main" and head == "dev":
        return []
    if base == "dev" and (
        re.fullmatch(r"feat/[a-z0-9]+(?:-[a-z0-9]+)*", head)
        or head.startswith("dependabot/")
    ):
        return []
    return [f"Invalid PR route {head!r} -> {base!r}; use feat/* -> dev -> main."]


def check(root: Path, paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for name, headings in REQUIRED.items():
        path = root / name
        if not path.is_file():
            errors.append(f"Missing required memory file: {name}")
            continue
        content = path.read_text(encoding="utf-8")
        for heading in headings:
            if heading not in content.splitlines():
                errors.append(f"{name}: missing heading {heading}")
    for name, limit in [("STATE.md", 120), ("README.md", 160)]:
        path = root / "docs/memory" / name
        if path.is_file() and len(path.read_text(encoding="utf-8").splitlines()) > limit:
            errors.append(f"{path.relative_to(root)} exceeds {limit} lines; compact current memory.")
    index = root / "docs/memory/README.md"
    if index.is_file():
        links = LINK.findall(index.read_text(encoding="utf-8"))
        if not any(link.startswith("sessions/") for link in links):
            errors.append("Memory index must link the latest session handoff.")
    for relative in paths:
        path = root / relative
        if not path.is_file():
            continue  # Deleted files are checked by required-file validation above.
        parts = relative.parts
        if (
            relative.name.startswith(".env") and relative.name != ".env.example"
            or parts[0] in {"data", "artifacts", "outputs", ".venv", ".tmp"}
            or any(p in {"node_modules", "__pycache__", "dist"} for p in parts)
            or path.suffix.lower() in {".pem", ".key", ".p12", ".sqlite", ".db", ".parquet"}
        ):
            errors.append(f"Forbidden source-control path: {relative}")
        if path.stat().st_size > 2 * 1024 * 1024:
            errors.append(f"{relative}: exceeds 2 MiB; review data/artifact storage.")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if PRIVATE_KEY.search(content) or GITHUB_TOKEN.search(content):
            errors.append(f"{relative}: possible credential; remove/rotate it (value withheld).")
        if path.suffix != ".md":
            continue
        if relative.as_posix().startswith("docs/memory/sessions/"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md", relative.name):
                errors.append(f"{relative}: use YYYY-MM-DD-topic.md.")
            for heading in HANDOFF_HEADINGS:
                if heading not in content.splitlines():
                    errors.append(f"{relative}: missing heading {heading}")
        for target in LINK.findall(content):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                errors.append(f"{relative}: broken/outside-repository link {target}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--commit-guard", action="store_true")
    args = parser.parse_args()
    if args.commit_guard:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "branch", "--show-current"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        branch = result.stdout.strip()
        if branch in {"main", "dev"}:
            print("Direct commits to main/dev are blocked. Create feat/<topic> from dev.")
            return 1
        return 0
    errors = check(ROOT, repository_files(ROOT))
    if args.base is not None or args.head is not None:
        errors.extend(route_errors(args.base or "", args.head or ""))
    for error in errors:
        print(error)
    if not errors:
        print("Repository and memory checks passed.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
