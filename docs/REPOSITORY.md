# Repository administration

The source of the intended GitHub policy is
[branch-rules.json](../.github/branch-rules.json). It applies to main and dev,
requires PRs, up-to-date `quality-gate` from GitHub Actions (app ID 15368),
resolved conversations, and prevents deletion and force pushes. No bypass actors.
Zero required approvals supports the sole maintainer; set one when the team grows.

The bootstrap procedure applies and reads back this policy after publishing checked
branches. See [current state](memory/STATE.md) for actual remote verification.
A checked-in JSON file alone does not enforce GitHub settings.

An administrator can inspect/reapply using GitHub CLI:

```sh
gh api repos/andersj05/PolicySim/rulesets
gh api --method POST repos/andersj05/PolicySim/rulesets --input .github/branch-rules.json
```

Do not POST duplicates: for an existing matching ruleset, inspect its ID and
use PUT to `repos/andersj05/PolicySim/rulesets/<id>` with the same input file.
Read back enforcement, branch conditions and required checks after any update.

Keep main as default branch; allow merge commits, disable squash/rebase merging
to preserve branch ancestry, and disable automatic deletion of head branches so
dev survives promotion. Delete merged feat branches manually when no longer needed.
Enable repository vulnerability alerts and private vulnerability reporting.

CI workflows use read-only repository permissions and immutable action SHAs.
Never replace pull_request with pull_request_target to run untrusted PR code.
No deployment credentials are required. Weekly audits also run on main to catch
new advisories without a code change. Review and triage failed audit results.
