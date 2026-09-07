# PolicySim

A local research workspace for economic data, reproducible simulations and forecasting.
Current milestone: engineering foundation. Providers, models and research screens
are future work.

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
Ctrl+C stops both servers. No API keys or external services are required.
The screen is a foundation placeholder, not a research application.

```sh
python scripts/project.py check
```

This runs CI's offline quality checks. Dependency audits are a separate networked
CI gate. On Windows, `py -3.12` can replace `python` if needed.

## Layout

```text
backend/src/policysim/  Python API; future data and research modules
backend/tests/         API contract tests
frontend/              React + strict TypeScript + Vite
scripts/               Cross-platform development and repository checks
docs/decisions/        Architecture decision records (ADRs)
docs/memory/           Current state, constraints and dated handoffs
.github/               CI, dependency updates, templates and rules
```

Branch flow: `feat/* → dev → main`. Commit both dependency lockfiles.
