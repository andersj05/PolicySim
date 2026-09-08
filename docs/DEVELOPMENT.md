# Development

## Prerequisites

Git, Node 24 with npm 10 or 11, Python 3.12+ to run the launcher, and
[uv 0.12.5](https://docs.astral.sh/uv/getting-started/installation/).
The project's interpreter is Python 3.12; uv downloads a current patch if needed.
Run all commands from the repository root.

```sh
python scripts/project.py setup
python scripts/project.py dev
```

Setup uses locked Python dependencies, npm ci, and installs local pre-commit hooks.
No virtual-environment activation, Docker or database is needed. World Bank needs
no key. Copy `.env.example` to ignored root `.env` and set `FRED_API_KEY` for FRED.
The Python backend reads that key directly; an environment variable takes precedence.
Restart after environment changes; edits to `.env` apply on the next request.
On Windows use `py -3.12` instead of `python` when necessary. The launcher resolves
`npm.cmd` internally, avoiding PowerShell npm.ps1 execution-policy issues.

The frontend uses 127.0.0.1:5173; backend uses 127.0.0.1:8000. Both bind loopback.
Ctrl+C stops the two owned process trees. An early server exit stops its sibling
and returns a failure. Free either occupied port rather than accepting a silent
port change. Use two terminals to debug servers individually:

```sh
uv run --locked uvicorn policysim.main:app --reload --host 127.0.0.1 --port 8000
npm --prefix frontend run dev
```

## Quality commands

```sh
python scripts/project.py check
python scripts/project.py format
uv run --locked pytest
uv run --locked mypy
npm --prefix frontend run check
uv run --locked pre-commit run --all-files
```

Check validates memory/links/repository hygiene, Ruff lint/format, mypy, tests
and branch coverage, generated API contract drift, frontend lint/types/build,
and repository Prettier formatting. Regenerate changed domain contracts with
`uv run --locked python scripts/generate_contracts.py`.
Format modifies files; check does not. Build output and caches are ignored.

Hooks run repository hygiene, Ruff and Prettier plus a protected-branch commit
guard. They are not a substitute for the full check. Install hooks in each clone;
CI enforces checks even without hooks.

CI adds networked dependency audits and validates PR branch routing. It runs on
Linux and Windows, and reports one required `quality-gate`. See
[repository administration](REPOSITORY.md) for remote settings.

## Dependency maintenance

```sh
uv lock --upgrade
uv sync --locked
npm --prefix frontend update
python scripts/project.py check
```

Use a feature branch and inspect lock changes. For newly added JS dependencies,
use `npm --prefix frontend install --save-exact <package>`. Dependabot opens weekly
updates for uv, npm and CI actions against dev.

## Troubleshooting

- Lock mismatch: intentional manifest edits need lock regeneration and review;
  otherwise restore the matching manifest/lock pair. Do not bypass locked CI.
- Missing dependencies: rerun setup. A failed setup returns nonzero; do not assume
  later steps completed.
- uv/network permissions: use the approved network environment to install; check
  commands should then run offline (dependency audits are explicitly networked).
- Git dubious ownership in Codex's sandbox: use a per-command safe.directory for
  this known workspace or execute Git as the owning user, not a wildcard exception.
- GitHub auth: follow AGENTS.md; a sandbox network error is not proof of a bad token.
- Only `FRED_API_KEY` is read from root `.env`; it is never sent to the frontend.
- World Bank may return transient gateway errors. Retry the request; no synthetic
  data is substituted. The first search indexes the full indicator catalog.
- Snapshots live in ignored `data/raw` and `data/snapshots`. Set the environment
  variable `POLICYSIM_DATA_DIR` to relocate them. Retention cleanup is manual.

## Release and recovery

Promote dev to main only through a passing PR; tag a version when a meaningful
releasable milestone exists. No automatic deploy or release is configured.
Revert a defective change with a feature PR to dev, promote the repair, and sync
main ancestry back to dev. Do not reset or force-push published protected history.
