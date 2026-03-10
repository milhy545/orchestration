# Security Policy

## Supported Branch

Security fixes are applied to the current `master` branch. Historical snapshots, archived plans, and old generated artifacts are retained for reference only and should not be treated as supported releases.

## Security Posture

- The stack is designed for controlled LAN or development environments by default.
- Many service ports are exposed directly by `docker-compose.yml`; do not publish them to the public internet without adding a reverse proxy, authentication, network policy, and secret rotation.
- Marketplace access is gated by JWT bearer tokens when `JWT_SECRET` is configured.
- Vault-based runtime secret injection is available through `docker-compose.vault.yml` and `services/vault-secrets-ui/`.

## Reporting a Vulnerability

Report security issues privately to the repository maintainer and include:

- the affected service or endpoint
- a minimal reproduction or proof of concept
- impact assessment
- any logs or configuration needed to reproduce the issue safely

Do not open public issues for unpatched vulnerabilities that expose credentials, authentication bypasses, remote execution paths, or data exfiltration risks.
