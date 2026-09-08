# Project memory

Durable project knowledge travels with Git, works offline and is reviewed in PRs.

## Read order and ownership

1. [STATE.md](STATE.md): current capability, verification, blockers and next action.
2. [CONSTRAINTS.md](CONSTRAINTS.md): durable requirements and scope boundaries.
3. Latest handoff: [2026-09-07 forecasting workspace](sessions/2026-09-07-forecast-workspace.md).
4. [Decision index](../decisions/README.md) and relevant technical guidance.

The contributor owns updating state/handoff in the same PR. The maintainer reviews
accuracy. User instructions and actual code/check evidence outrank stale prose;
ADRs explain intended design. Resolve contradictions instead of following old
notes blindly. Memory is not an automatic recollection of previous conversations.

## Update protocol

- Keep state under 120 lines and this index under 160. Summarize current truth,
  not a transcript. Include concrete paths, commands and outcomes.
- For substantive tasks copy [the template](../templates/HANDOFF.md) to
  `sessions/YYYY-MM-DD-short-topic.md` and update the latest link above.
- Record completed work, checks actually run, unverified claims, blockers and the
  next executable step. Never invent a hash for the commit containing the note.
- Put durable decisions in ADRs and user requirements in constraints.
- Never store secrets, personal data, datasets, long logs or chats.
- After roughly 20 handoffs, consolidate durable lessons in canonical docs; retain
  old sessions as history and add a dated archive index if needed.

## Retrieval and recovery

```sh
rg -n "vintage|storage|forecast" docs
git log --oneline -- docs/memory docs/decisions
git show <commit>:docs/memory/STATE.md
```

Review historical content before restoring with `git restore --source=<commit> --
<path>`, preserving current changes. Commits provide local recovery; pushes provide
off-machine backup. Uncommitted memory has neither guarantee.

The repository checker validates required headings, size bounds, handoff presence
and local Markdown file links. It cannot verify factual truth or force assistants
to read; the contribution rules and PR checklist establish that responsibility.
