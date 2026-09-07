# Project operating instructions

## Read before changing anything

1. Read `docs/memory/STATE.md` and `docs/memory/CONSTRAINTS.md`.
2. Read the latest handoff linked from `docs/memory/README.md`.
3. Read `CONTRIBUTING.md` and relevant ADRs in `docs/decisions/README.md`.
4. Inspect branch, working tree and code. Actual code/check evidence outranks stale
   prose. Reconcile contradictions in memory rather than guessing.

## Delivery rules

- Work on `feat/<short-kebab-case>` from `dev`, never commit directly to `main`
  or `dev`. Make small, coherent conventional commits throughout the work.
- Complete only the requested milestone. Do not invent data or working features.
- Keep calculations in Python and presentation in TypeScript. Research logic must
  remain independent of HTTP, UI and provider-specific data formats.
- Run `python scripts/project.py check` before handoff; use targeted checks during
  development. Report actual results, including failures and unrun checks.
- Update state and a dated handoff for substantive tasks. Put durable decisions in
  ADRs, not buried session history. Follow `docs/memory/README.md`.
- Never commit credentials, private data, generated research output, environment
  files or chat transcripts. No secrets in memory or frontend environment values.
- Add services/dependencies only when the milestone needs them.

## GitHub CLI authentication

- The Windows GitHub CLI account `andersj05` is stored in Windows Credential Manager.
- The workspace sandbox may block outbound GitHub traffic, falsely reporting an
  invalid token. Verify the relevant `gh` command outside the sandbox with the
  narrowest appropriate approval before recommending reauthentication.
- Never recommend `gh auth logout` or `gh auth login` from sandbox checks alone.
