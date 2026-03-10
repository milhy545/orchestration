# Security Summary

## Current Posture

The current stack relies on a combination of compose-network isolation, service-specific validation, Vault-backed runtime secret management, and token-gated marketplace access.

## Key Security Controls

- runtime secrets can be managed through Vault and surfaced through generated env files
- marketplace APIs enforce token scope checks
- security-mcp exposes dedicated JWT, password, encryption, and SSL helper routes
- services run behind compose networking and are monitored through health checks
- several containers use `no-new-privileges` or similar runtime hardening settings

## Sensitive Interfaces

- `mega-orchestrator` `7000`
- `marketplace-mcp` `7034`
- `vault-secrets-ui`
- service wrappers on `7024-7026`
- persistence backends on PostgreSQL, Redis, Qdrant, and Neo4j

## Review Priorities

- verify that secret-bearing environment variables are not committed
- confirm marketplace tokens and JWT secrets are set in production
- keep Vault token handling and runtime env generation restricted to operators
- review direct-service exposure before placing the stack on an untrusted network

## Documentation Rule

When a security-sensitive route, secret namespace, or auth dependency changes, update the API docs, architecture docs, and public-surface inventory in the same change set.
