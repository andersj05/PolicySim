# Contributing

## Branches and commits

- `main`: stable checked milestones; default branch.
- `dev`: integration for the next milestone.
- `feat/<short-kebab-case>`: focused work, including docs, fixes and chores.
- Dependabot's generated branches may target `dev` for dependency maintenance.

```sh
git fetch origin
git switch dev
git pull --ff-only origin dev
git switch -c feat/describe-the-change
```

Use `docs:`, `chore:`, `feat:`, `fix:`, `test:` or `refactor:` commits. Commit
coherent steps frequently. Do not rewrite shared history or force-push protected
branches. Feature PRs target `dev`; milestone promotions target `main` from `dev`.
Use merge commits to retain the small commits and release ancestry.

After promotion, merge `origin/main` into a new `feat/sync-main-<milestone>` branch
based on `dev`, then PR it into `dev`. This preserves ancestry without direct
protected-branch pushes. Do not delete `dev`.

Initial empty-repository bootstrap is a one-time exception: after local checks
pass, fast-forward `dev` and `main` to the foundation, publish the branches, then
activate protections. Record the exception in the bootstrap handoff.

## Required gates

Every PR runs repository policy, formatting, lint, strict types, backend tests with
branch coverage, frontend build and dependency audits. Quality checks run on Linux
and Windows. No path filters may skip required gates. `quality-gate` is the stable
required status; it fails if any dependency fails, is cancelled or is skipped.

Protections require a PR, green up-to-date checks and resolved conversations, and
prohibit force-pushes/deletion on `main` and `dev`. Start with zero required approvals
so the sole maintainer can merge. Require one independent approval when a second
maintainer joins. CODEOWNERS identifies stewardship; it is not automatic approval.
No automatic merge is configured.

## Definition of done

- Scope, acceptance criteria, behavior and errors are clear.
- Checks pass; test real boundaries and failure modes, not static markup repetition.
- Update state/handoff for substantive work and ADRs for durable decisions.
- Data/model changes meet [research standards](docs/RESEARCH.md).
- No secrets, private data, fabricated results or generated output.
- PR describes outcome, rationale, verification and remaining limitations.

## Dependencies

Use `uv add` / `uv add --dev` and frontend `npm install --save-exact`. Commit
manifests and locks together. Ordinary installs use `uv sync --locked` and `npm ci`;
CI must not regenerate locks. Dependabot opens weekly update PRs to `dev`.
Hooks give fast feedback; CI is authoritative. See [SECURITY.md](SECURITY.md).
