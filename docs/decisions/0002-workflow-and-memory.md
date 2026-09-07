# ADR 0002: Workflow and memory

- Status: Accepted
- Date: 2026-09-07

## Context

Durable continuity between human/agent sessions, frequent commits and stable main.

## Decision

Use `feat/* → dev → main`, PR merge commits and required checks. Keep memory in
versioned Markdown: short current state, durable ADRs and indexed dated handoffs.
Validate structure/links automatically; review factual accuracy in PRs.

Require PRs, up-to-date green checks and resolved discussions, with no bypass
actors. Start with zero mandatory approvals for a sole maintainer; increase to
one when another maintainer joins. Bootstrap once before enabling protection.
Sync release merge ancestry back into dev through a feature PR.

## Consequences

Memory is portable, diffable, recoverable and offline, with no external service or
assistant dependency. Future sessions must explicitly read it. CI cannot know
whether prose is true; reconcile it against code and actual verification.
