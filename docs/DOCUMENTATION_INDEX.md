# Documentation Index - Orchestration MCP Platform

## 📚 Complete Documentation Suite

This directory contains comprehensive documentation for the **Orchestration MCP Platform** - a production-ready microservices system providing 28 MCP tools across 7 specialized services.

### 🎯 Quick Start

1. **[README.md](README.md)** - Start here for overview and quick setup
2. **[PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md)** - Complete Portainer deployment guide
3. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Full API reference for all 28 tools
4. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions for common issues

---

## 🗂️ Repository Layout Notes

- Operational guides previously in repo root are now under [`docs/manuals/`](manuals/).
- Generated reports and audit summaries are under [`docs/reports/`](reports/).
- Ad-hoc diagnostic scripts are organized in [`scripts/diagnostics/`](../scripts/diagnostics/) and legacy one-offs in [`scripts/legacy/`](../scripts/legacy/).

## 📋 Documentation Contents

### 🏠 Core Documentation

#### [README.md](README.md)
**Complete project overview and getting started guide**
- System architecture overview
- 28 MCP tools summary
- Quick installation guide
- Service ports and status
- Basic configuration
- Health monitoring

**Key Sections:**
- Architecture overview with security model
- Service port mapping (7001-7017, 7000-7022)
- Docker Compose deployment
- Environment configuration
- Performance benchmarks

#### [ARCHITECTURE.md](ARCHITECTURE.md)
**Detailed technical architecture and design decisions**
- Security architecture (Zero Trust model)
- Component relationships
- Data flow diagrams
- Scaling strategies
- Configuration management
- Monitoring & observability

**Key Topics:**
- Network security layers
- MCP protocol implementation
- Database architecture (PostgreSQL, Redis, Qdrant)
- Container orchestration strategy
- Disaster recovery procedures

### 🚀 Deployment Guides

#### [PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md)
**Comprehensive Portainer deployment guide with troubleshooting**
- **Phase 1**: Portainer Agent installation (MANDATORY)
- **Phase 2**: Environment setup in Portainer
- **Phase 3**: Stack configuration
- **Phase 4**: API-based deployment
- **Phase 5**: Post-deployment verification

**Critical Requirements:**
- Portainer Agent on port 9001 (REQUIRED)
- Network connectivity validation
- API token management
- Automated deployment scripts
- Monitoring and maintenance

**Included Scripts:**
- `deploy_to_portainer.sh` - Automated deployment
- `portainer_monitor.sh` - Health monitoring
- Stack configuration templates

#### [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
**Complete API reference for all 28 MCP tools**
- ZEN Coordinator endpoints
- All 7 MCP service APIs
- Request/response examples
- Authentication methods
- Error handling
- Python SDK examples

**Service APIs Covered:**
- **Filesystem MCP** (5 tools): file operations, search, analysis
- **Git MCP** (5 tools): version control, commits, pushes
- **Terminal MCP** (3 tools): command execution, system info
- **Database MCP** (4 tools): queries, connections, backups
- **Memory MCP** (5 tools): storage, search, context
- **Research MCP** (3 tools): web search, Perplexity AI
- **Transcriber MCP** (3 tools): audio/video processing

### 🔧 Technical References

#### [SERVICES_DOCUMENTATION.md](SERVICES_DOCUMENTATION.md)
**Detailed documentation for all 28 MCP tools**
- Individual tool specifications
- Parameter definitions
- Response formats
- Use case examples
- Integration patterns

**Per-Service Details:**
- Tool descriptions and parameters
- Example requests and responses
- Security features
- Performance characteristics
- Integration examples

#### [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
**Comprehensive troubleshooting guide with solutions**
- Emergency procedures
- Common issues and solutions
- Diagnostic commands
- Service-specific debugging
- Performance optimization
- Recovery procedures

**Issue Categories:**
- ZEN Coordinator problems
- MCP service communication errors
- Database connection issues
- Transcriber service debugging
- Memory/performance problems
- Portainer Agent issues
- Git operations failures

---

## 🎯 Documentation Usage Guide

### For New Users
1. **Start with [README.md](README.md)** for system overview
2. **Follow [PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md)** for deployment
3. **Reference [API_DOCUMENTATION.md](API_DOCUMENTATION.md)** for tool usage
4. **Keep [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** handy for issues

### For Developers
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** for system design understanding
2. **[SERVICES_DOCUMENTATION.md](SERVICES_DOCUMENTATION.md)** for detailed tool specs
3. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** for integration examples
4. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for debugging guidance

### For System Administrators
1. **[PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md)** for deployment procedures
2. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for operational issues
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** for monitoring and scaling
4. **[README.md](README.md)** for maintenance commands

### For AI Agents
1. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** for tool integration
2. **[SERVICES_DOCUMENTATION.md](SERVICES_DOCUMENTATION.md)** for detailed tool usage
3. **[README.md](README.md)** for system status and health checks

---

## 🔍 Key Information Quick Reference

### System Status
- **Production Server**: 192.168.0.58 (Home Automation Server)
- **GitHub Repository**: [milhy545/orchestration](https://github.com/milhy545/orchestration)
- **Current Uptime**: 26+ hours
- **Services Running**: 10+ microservices
- **Tools Available**: 28 MCP tools

### Critical Ports
- **7000**: ZEN Coordinator (main entry point)
- **7001-7017**: MCP Services (internal only)
- **7021**: PostgreSQL database
- **7022**: Redis cache
- **6333**: Qdrant vector database
- **9001**: Portainer Agent (required for Portainer)

### API Endpoints
- **Health**: `http://192.168.0.58:7000/health`
- **Services**: `http://192.168.0.58:7000/services`
- **Tools**: `http://192.168.0.58:7000/tools/list`
- **Native MCP JSON-RPC**: `http://192.168.0.58:7000/mcp/rpc` (POST, recommended)
- **Legacy MCP Gateway**: `http://192.168.0.58:7000/mcp` (POST, compatibility mode)

### Quick Health Check
```bash
# Overall system health
curl http://192.168.0.58:7000/health

# List all services
curl http://192.168.0.58:7000/services

# Test native MCP JSON-RPC handshake
curl -X POST http://192.168.0.58:7000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Legacy custom request (compatibility mode)
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool":"system_info","arguments":{}}'
```

---

## 📊 Documentation Metrics

### Documentation Coverage
- **Total Pages**: 6 comprehensive documents
- **Total Content**: ~50,000 words
- **Code Examples**: 100+ practical examples
- **API Endpoints**: 28 tools fully documented
- **Troubleshooting Scenarios**: 20+ common issues covered

### Content Breakdown
- **Setup & Deployment**: 40% (README, Portainer Deployment)
- **API Reference**: 30% (API Documentation, Services Documentation)
- **Architecture & Design**: 20% (Architecture Documentation)
- **Operations & Maintenance**: 10% (Troubleshooting Guide)

### Update Status
- **Created**: 2025-08-17
- **Version**: 1.0
- **Last Updated**: Current
- **Maintenance**: Ongoing with system updates

---

## 🤝 Contributing to Documentation

### Documentation Standards
- **Format**: Markdown with consistent structure
- **Code Examples**: Always include working examples
- **Screenshots**: Include where helpful (UI guides)
- **Updates**: Keep synchronized with system changes

### Feedback and Improvements
- **GitHub Issues**: Report documentation issues at [orchestration/issues](https://github.com/milhy545/orchestration/issues)
- **Pull Requests**: Submit improvements via GitHub
- **Direct Updates**: System administrators can update documentation directly

---

## 📞 Support Resources

### Getting Help
1. **Documentation**: Check relevant documentation first
2. **GitHub Issues**: [orchestration/issues](https://github.com/milhy545/orchestration/issues)
3. **Health Checks**: Use built-in diagnostic tools
4. **Emergency Procedures**: Follow troubleshooting guide

### System Administration
- **Production Server**: `ssh root@192.168.0.58`
- **Log Location**: `/var/log/orchestration/`
- **Backup Location**: `/tmp/orchestration_backup/`
- **Configuration**: `/home/orchestration/.env`

---

**This documentation suite provides complete coverage of the Orchestration MCP Platform, from initial setup through advanced troubleshooting. All documentation is designed to be practical, actionable, and comprehensive.**

## 🏆 Documentation Quality Assurance

✅ **Complete API Coverage**: All 28 MCP tools documented  
✅ **Deployment Procedures**: Step-by-step Portainer deployment  
✅ **Troubleshooting Guide**: Solutions for common issues  
✅ **Architecture Reference**: Technical design documentation  
✅ **Security Guidelines**: Zero Trust implementation details  
✅ **Performance Metrics**: Benchmarks and optimization  
✅ **Maintenance Procedures**: Operational guidelines  
✅ **Integration Examples**: Practical usage scenarios