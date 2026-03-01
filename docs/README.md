# Orchestration Documentation

## Purpose

This directory contains the maintained documentation for the Orchestration MCP platform, grouped by function instead of historical file order.

Use this directory as the documentation front door for:
- current architecture and design notes
- operational runbooks
- API and service references
- security summaries
- generated reports
- archived historical planning docs

## Documentation Map

### Architecture
- [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- [architecture/MEGA_MCP_COMPATIBILITY.md](architecture/MEGA_MCP_COMPATIBILITY.md)
- [architecture/VAULT_VARIANT_B.md](architecture/VAULT_VARIANT_B.md)

### Operations
- [operations/DEPLOYMENT.md](operations/DEPLOYMENT.md)
- [operations/MONITORING.md](operations/MONITORING.md)
- [operations/PORTAINER_DEPLOYMENT.md](operations/PORTAINER_DEPLOYMENT.md)
- [operations/TROUBLESHOOTING.md](operations/TROUBLESHOOTING.md)

### API and Integrations
- [api/API_DOCUMENTATION.md](api/API_DOCUMENTATION.md)
- [api/API_REFERENCE.md](api/API_REFERENCE.md)
- [api/SERVICES_DOCUMENTATION.md](api/SERVICES_DOCUMENTATION.md)

### Security
- [security/SECURITY_SCAN_SUMMARY.md](security/SECURITY_SCAN_SUMMARY.md)

### Manuals
- [manuals/](manuals/)

### Reports
- [reports/](reports/)

### Historical Documentation
- [archive/](archive/)

### Index
- [index/DOCUMENTATION_INDEX.md](index/DOCUMENTATION_INDEX.md)

## By Audience

- Operators: start with [operations/](operations/) and then [security/](security/).
- Contributors: start with [architecture/](architecture/) and [api/](api/).
- Integrators and MCP client authors: start with [api/](api/) and [architecture/MEGA_MCP_COMPATIBILITY.md](architecture/MEGA_MCP_COMPATIBILITY.md).
- Auditors: start with [security/](security/) and [reports/](reports/).
- Historical research: use [archive/](archive/).

## Archive Distinction

- `docs/archive/` contains archived documentation, superseded plans, and historical migration notes.
- Top-level [`../archive/`](../archive/) contains retained project artifacts such as backups, legacy configs, and scratch material.

These two archive areas are intentionally separate.
