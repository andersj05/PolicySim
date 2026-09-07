"""Check that workflow guardrails actually reject invalid inputs."""

from pathlib import Path

from scripts.check_repo import REQUIRED, check, route_errors


def memory_tree(tmp_path: Path) -> list[Path]:
    paths = []
    for name, headings in REQUIRED.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(headings) + "\n", encoding="utf-8")
        paths.append(Path(name))
    session = tmp_path / "docs/memory/sessions/2026-09-07-test.md"
    session.parent.mkdir()
    session.write_text(
        "## Context\n## Changes\n## Verification\n## Open issues\n## Next action\n",
        encoding="utf-8",
    )
    index = tmp_path / "docs/memory/README.md"
    with index.open("a", encoding="utf-8") as stream:
        stream.write("[Latest](sessions/2026-09-07-test.md)\n")
    paths.append(session.relative_to(tmp_path))
    return paths


def test_valid_memory(tmp_path: Path) -> None:
    assert check(tmp_path, memory_tree(tmp_path)) == []


def test_missing_state_and_broken_link_fail(tmp_path: Path) -> None:
    paths = memory_tree(tmp_path)
    (tmp_path / "docs/memory/STATE.md").unlink()
    (tmp_path / "AGENTS.md").write_text("[Broken](missing.md)\n", encoding="utf-8")
    errors = check(tmp_path, paths)
    assert any("Missing required memory file" in error for error in errors)
    assert any("broken/outside-repository link" in error for error in errors)


def test_missing_handoff_heading_fails(tmp_path: Path) -> None:
    paths = memory_tree(tmp_path)
    (tmp_path / paths[-1]).write_text("# Empty\n", encoding="utf-8")
    assert any("missing heading ## Verification" in error for error in check(tmp_path, paths))


def test_accidental_env_and_private_key_fail_without_printing_value(tmp_path: Path) -> None:
    paths = memory_tree(tmp_path)
    secret = "-----BEGIN " + "PRIVATE KEY-----"
    (tmp_path / ".env").write_text(secret, encoding="utf-8")
    errors = check(tmp_path, [*paths, Path(".env")])
    assert any("Forbidden" in error for error in errors)
    assert any("possible credential" in error for error in errors)
    assert all(secret not in error for error in errors)


def test_branch_routes() -> None:
    assert route_errors("main", "dev") == []
    assert route_errors("dev", "feat/add-series") == []
    assert route_errors("dev", "dependabot/npm_and_yarn/update") == []
    assert route_errors("main", "feat/add-series")
    assert route_errors("dev", "main")
    assert route_errors("dev", "feat/Bad Name")
