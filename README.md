# PolicySim

A local research workspace for economic data, reproducible simulations and forecasting.
Current milestone: a live FRED and World Bank data explorer. Search catalogs,
inspect charts and tables, choose countries and dates, and download observations
with source provenance. Simulations and forecasting are future milestones.

## Start here

- [Current state](docs/memory/STATE.md) and [roadmap](docs/ROADMAP.md)
- [Development commands](docs/DEVELOPMENT.md) and [contributing](CONTRIBUTING.md)
- [Architecture](docs/ARCHITECTURE.md), [design](docs/DESIGN.md), [research standards](docs/RESEARCH.md)
- [Persistent memory](docs/memory/README.md) and [agent instructions](AGENTS.md)

## Quick start

Install Git, Node.js 24 (with npm), Python 3.12+, and uv 0.12.5. uv installs the
project's Python 3.12 runtime if necessary. From the repository root:

```sh
python scripts/project.py setup
python scripts/project.py dev
```

Open <http://127.0.0.1:5173>. API docs: <http://127.0.0.1:8000/docs>.
Ctrl+C stops both servers. World Bank works without credentials. For FRED, copy
`.env.example` to `.env` and add `FRED_API_KEY` on the backend. Never use frontend
environment variables for keys. Both data providers need internet access.

Search by keyword or series ID, or choose one of the suggested starting points.
World Bank supports country/aggregate selection across its Indicators API catalog.
Downloads contain untransformed values, missing observations and source metadata.
Exact provider responses are saved under ignored `data/` with SHA-256 checksums.
Latest revisions are not historical vintages for backtesting.

```sh
python scripts/project.py check
```

This runs CI's offline quality checks. Dependency audits are a separate networked
CI gate. On Windows, `py -3.12` can replace `python` if needed.

## Layout

```text
backend/src/policysim/  Python API, provider adapters and source snapshots
backend/tests/         Offline provider and API contract tests
frontend/              React + strict TypeScript + Vite
scripts/               Cross-platform development and repository checks
docs/decisions/        Architecture decision records (ADRs)
docs/memory/           Current state, constraints and dated handoffs
.github/               CI, dependency updates, templates and rules
```

Branch flow: `feat/* → dev → main`. Commit both dependency lockfiles.
