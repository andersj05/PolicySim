# Security policy

The foundation is for local loopback development. It has no authentication,
multi-user isolation, rate limiting or production deployment configuration.
Hosting requires a separate reviewed milestone.

Provider keys belong in ignored backend environment files or a deployment secret
store, never browser bundles or `VITE_*` variables. Commit only small explicitly
redistributable test fixtures, not private/licensed datasets.

Report vulnerabilities through GitHub **Security → Report a vulnerability** if
enabled; otherwise arrange private disclosure through an existing maintainer
contact channel. Do not post secrets/exploit details publicly. Revoke leaked keys
first; removing a file does not remove Git history.

Dependency audits run on PRs, protected-branch pushes and weekly. Triage and fix
findings. Any exception needs an owner, expiry, affected versions and written
justification; do not add broad ignores.
