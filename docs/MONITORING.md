# MCP Orchestration Monitoring Stack

Complete observability solution for the MCP orchestration platform using Prometheus, Grafana, and Loki.

## 📊 Overview

The monitoring stack provides:
- **Metrics collection** - Prometheus scraping all 16 MCP services
- **Visualization** - Grafana dashboards with real-time metrics
- **Log aggregation** - Loki collecting logs from all Docker containers
- **Alerting capability** - Ready for Alertmanager integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Grafana (7031)                        │
│              Dashboards & Visualization                 │
└────────────┬──────────────────────────┬─────────────────┘
             │                          │
             ▼                          ▼
    ┌────────────────┐         ┌──────────────┐
    │  Prometheus    │         │     Loki     │
    │    (7028)      │         │    (7032)    │
    │   Metrics DB   │         │   Logs DB    │
    └────────┬───────┘         └──────┬───────┘
             │                         │
             │                         │
    ┌────────▼─────────────────────────▼────────┐
    │              Promtail                      │
    │         Log Collection Agent               │
    └────────┬───────────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────────────┐
    │     16 MCP Services (7001-7026)            │
    │  - /metrics endpoints (Prometheus)         │
    │  - Docker logs (Promtail → Loki)           │
    │                                             │
    │  Core: terminal, filesystem, database,     │
    │        git, memory, system, config, log,   │
    │        network, security                    │
    │  AI: research, transcriber                 │
    │  DB Wrappers: postgresql, redis, qdrant    │
    │  Messaging: mqtt                           │
    └────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
# Start all monitoring services
docker-compose up -d prometheus grafana loki promtail

# Or start entire platform including monitoring
docker-compose up -d
```

### 2. Access Dashboards

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Grafana** | http://localhost:7031 | admin / admin |
| **Prometheus** | http://localhost:7028 | - |
| **Loki API** | http://localhost:7032 | - |

### 3. View Metrics

1. Open Grafana: http://localhost:7031
2. Login with `admin/admin` (you'll be prompted to change password)
3. Navigate to **Dashboards** → **MCP** → **MCP Orchestration - Overview**

## 📈 Available Metrics

### Service Health
- **up{job=~"mcp-.*"}** - Service availability (1=up, 0=down)
- **process_resident_memory_bytes** - Memory usage per service
- **process_cpu_seconds_total** - CPU time consumed

### HTTP Metrics (FastAPI)
- **http_requests_total** - Total HTTP requests (by status, method, path)
- **http_request_duration_seconds** - Request latency histogram
- **http_requests_created** - Request creation timestamp

### Database Metrics
- **pg_stat_activity_count** - PostgreSQL active connections
- **redis_connected_clients** - Redis client connections

### MQTT Metrics
- **mqtt_messages_received_total** - Messages received by broker
- **mqtt_messages_sent_total** - Messages sent by broker

## 🎯 Pre-configured Dashboards

### MCP Orchestration - Overview
Default dashboard showing:

1. **Service Health Status**
   - Green/red indicators for all 16 services
   - Last heartbeat timestamp

2. **Request Rate**
   - Requests per second by service
   - 5-minute rolling average

3. **Response Time (p95)**
   - 95th percentile latency
   - By service and endpoint

4. **Error Rate**
   - 5xx errors per second
   - Stacked by service

5. **Infrastructure Metrics**
   - PostgreSQL active connections gauge
   - Redis connected clients gauge

6. **MQTT Activity**
   - Message rate (sent/received)
   - Real-time throughput

7. **Live Error Logs**
   - Recent errors from all services
   - Searchable and filterable

## 🔍 Querying Metrics

### Prometheus Query Examples

```promql
# Request rate for all services
rate(http_requests_total[5m])

# 99th percentile latency for filesystem-mcp
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="filesystem-mcp"}[5m]))

# Error rate percentage
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# Memory usage by service
sum(process_resident_memory_bytes) by (service)

# Services currently down
up{job=~"mcp-.*"} == 0
```

### Loki Query Examples (LogQL)

```logql
# All errors from any service
{service=~".*mcp.*"} |= "ERROR"

# Errors from specific service
{service="terminal-mcp"} |~ "(?i)error|exception|failed"

# High latency requests (>1s)
{service=~".*mcp.*"} |~ "duration.*[1-9][0-9]{3,}ms"

# Database connection errors
{service=~".*mcp.*"} |~ "(?i)database.*error|connection.*failed"

# Filter by service group
{service_group="core"} |= "ERROR"
```

## ⚙️ Configuration Files

### Directory Structure
```
monitoring/
├── prometheus/
│   └── prometheus.yml          # Scrape configuration
├── loki/
│   └── loki-config.yml         # Log aggregation config
├── promtail/
│   └── promtail-config.yml     # Log collection config
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasources.yml # Auto-provisioned datasources
        └── dashboards/
            ├── dashboards.yml  # Dashboard provisioning
            └── mcp-overview.json # MCP dashboard definition
```

### Prometheus Configuration

**Scrape interval:** 15 seconds
**Retention:** Default (15 days)
**Storage:** Docker volume `prometheus-data`

**Scrape jobs:**
- `prometheus` - Prometheus self-monitoring
- `zen-coordinator` - Master controller
- `mcp-core-services` - 10 core services
- `mcp-ai-services` - AI/enhanced services
- `mcp-db-wrappers` - Database wrapper services
- `mcp-mqtt` - MQTT service
- `infrastructure` - PostgreSQL, Redis, Qdrant
- `loki` - Loki self-monitoring

### Loki Configuration

**Retention:** 7 days (168 hours)
**Storage:** Docker volume `loki-data`
**Max ingestion rate:** 16MB/s
**Query parallelism:** 32

### Promtail Configuration

**Log sources:**
- Docker containers (via /var/run/docker.sock)
- System logs (/var/log/)

**Label extraction:**
- `container` - Container name
- `service` - Service name from compose
- `service_group` - Service category (core, ai, infrastructure, etc.)

## 🛠️ Maintenance

### Health Check

Run the monitoring health check script:

```bash
./scripts/monitoring-health-check.sh
```

This validates:
- All configuration files exist and are valid YAML/JSON
- All required scrape jobs are configured
- All 16 MCP services are instrumented
- Docker compose services are properly defined
- Port mappings are correct

### Viewing Logs

```bash
# Grafana logs
docker logs mcp-grafana -f

# Prometheus logs
docker logs mcp-prometheus -f

# Loki logs
docker logs mcp-loki -f

# Promtail logs
docker logs mcp-promtail -f
```

### Reloading Configuration

```bash
# Reload Prometheus config without restart
curl -X POST http://localhost:7028/-/reload

# Restart individual service
docker-compose restart prometheus
docker-compose restart grafana
docker-compose restart loki
```

### Data Persistence

All monitoring data is stored in Docker volumes:

```bash
# List monitoring volumes
docker volume ls | grep -E "prometheus|grafana|loki"

# Backup Grafana dashboards
docker run --rm -v orchestration_grafana-data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/grafana-$(date +%Y%m%d).tar.gz /data

# Backup Prometheus data
docker run --rm -v orchestration_prometheus-data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /data
```

## 📊 Adding Custom Dashboards

### Method 1: Through UI
1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `monitoring/grafana/provisioning/dashboards/`
4. Restart Grafana: `docker-compose restart grafana`

### Method 2: Programmatically
```bash
# Export existing dashboard
curl -H "Authorization: Bearer <api-key>" \
  http://localhost:7031/api/dashboards/uid/mcp-overview \
  > my-dashboard.json

# Place in provisioning directory
mv my-dashboard.json monitoring/grafana/provisioning/dashboards/
```

## 🚨 Setting Up Alerts (Optional)

### 1. Add Alertmanager

Edit `docker-compose.yml`:

```yaml
alertmanager:
  image: prom/alertmanager:latest
  container_name: mcp-alertmanager
  ports:
    - "7033:9093"
  volumes:
    - ./monitoring/alertmanager/config.yml:/etc/alertmanager/config.yml
    - alertmanager-data:/alertmanager
  restart: unless-stopped
  networks:
    - mcp-network
```

### 2. Configure Alert Rules

Create `monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: mcp_services
    interval: 30s
    rules:
      - alert: ServiceDown
        expr: up{job=~"mcp-.*"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MCP Service {{ $labels.service }} is down"

      - alert: HighErrorRate
        expr: (rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.service }}"
```

Update `prometheus.yml`:

```yaml
rule_files:
  - '/etc/prometheus/alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

## 🔐 Security Considerations

### Production Recommendations

1. **Change default Grafana password** immediately
2. **Enable HTTPS** for Grafana and Prometheus
3. **Restrict access** with firewall rules or reverse proxy
4. **Use authentication** for Prometheus (basic auth via reverse proxy)
5. **Limit retention** to manage disk space
6. **Regular backups** of Grafana dashboards and Prometheus data

### Access Control

```yaml
# Example Grafana environment variables for production
environment:
  - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
  - GF_USERS_ALLOW_SIGN_UP=false
  - GF_AUTH_ANONYMOUS_ENABLED=false
  - GF_SERVER_ENFORCE_DOMAIN=true
  - GF_SERVER_ROOT_URL=https://grafana.yourdomain.com
```

## 📝 Troubleshooting

### Prometheus can't scrape services

**Problem:** Targets show as "down" in Prometheus
**Solution:**
1. Check service is running: `docker ps | grep mcp-`
2. Verify /metrics endpoint: `curl http://localhost:7001/metrics`
3. Check network connectivity: `docker exec mcp-prometheus ping filesystem-mcp`

### Grafana shows "No data"

**Problem:** Dashboard panels show no data
**Solution:**
1. Verify datasource configuration: Settings → Data Sources
2. Test Prometheus connection: Click "Test" button
3. Check time range in dashboard (top right)
4. Verify Prometheus has scraped data: http://localhost:7028/targets

### Loki logs not appearing

**Problem:** No logs in Grafana Explore
**Solution:**
1. Check Promtail is running: `docker ps | grep promtail`
2. Verify Promtail config: `docker logs mcp-promtail`
3. Check label filters in LogQL query
4. Test Loki API: `curl http://localhost:7032/ready`

### High disk usage

**Problem:** Monitoring volumes consuming too much space
**Solution:**
1. Reduce Prometheus retention: Add `--storage.tsdb.retention.time=7d` to command
2. Reduce Loki retention: Edit `loki-config.yml` → `limits_config.retention_period`
3. Clean old data: `docker volume prune`

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [LogQL Cheat Sheet](https://megamorf.gitlab.io/cheat-sheets/loki/)

## 🤝 Contributing

To improve monitoring:

1. Add new metrics in FastAPI services using custom Prometheus metrics
2. Create additional Grafana dashboards for specific use cases
3. Extend Prometheus scrape jobs for new services
4. Add alerting rules for critical scenarios

Example custom metric:

```python
from prometheus_client import Counter

api_calls = Counter('api_calls_total', 'Total API calls', ['endpoint', 'method'])

@app.get("/some-endpoint")
def endpoint():
    api_calls.labels(endpoint='/some-endpoint', method='GET').inc()
    # ... your code
```

## 📄 License

Part of the MCP Orchestration Platform.
