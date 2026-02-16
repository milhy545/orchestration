# Orchestration Project

## Description

This project is a microservices-based system for orchestrating and managing a collection of services using Docker. It acts as a central hub for various functionalities, including file operations, version control, command execution, AI-powered tasks, and more. The system is designed to be modular and extensible, with services communicating over a shared network.

## Architecture

The core of the project is the **Mega-Orchestrator**, a Python-based HTTP server that acts as a secure proxy to the various MCP (Master Control Program) services. The coordinator is responsible for:

-   **Routing:** It routes incoming requests to the appropriate MCP service based on the requested tool.
-   **Health Checks:** It monitors the health of the MCP services.
-   **Logging:** It logs all MCP requests to a PostgreSQL database.
-   **Caching:** It caches responses from the MCP services using Redis.
-   **API Abstraction:** It provides a unified API for interacting with the MCP services.

The MCP services themselves are a collection of microservices, each responsible for a specific set of tasks. They are designed to be lightweight and independent, and they communicate with the coordinator over a shared Docker network.

## Getting Started

To get started with this project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    ```
2.  **Set up the environment:**
    - Copy `.env.example` to `.env` and customize credentials/API keys.
    - Confirm path variables used by `docker-compose.yml`:
      - `PROJECT_ROOT` (repo path visible to Docker daemon)
      - `DATA_ROOT` (persistent data directory)
      - `MONITORING_ROOT` (base path containing `monitoring/`)
      - `HOST_HOME_PATH` (host `/home` mount used by `filesystem-mcp`)
      - `ZEN_MCP_SERVER_PATH` (build context for `zen-mcp-server`)
3.  **Run the services:**
    ```bash
    docker compose up -d
    ```

### Portable path notes (Coder/remote Docker daemon)

If your Docker daemon cannot access your workspace path directly (common in Coder or remote-Docker setups), set path variables to daemon-visible locations before starting services.

```bash
export PROJECT_ROOT=/absolute/path/visible/to/docker-daemon
export DATA_ROOT=/absolute/path/visible/to/docker-daemon/data
export MONITORING_ROOT=/absolute/path/visible/to/docker-daemon

docker compose up -d prometheus grafana loki promtail
```

If monitoring files live only in your workspace filesystem, copy `monitoring/` to a daemon-visible path first, then point `MONITORING_ROOT` there.

## Services

The `docker-compose.yml` file defines the following services, which are organized into logical groups:

### Master Controller

-   **`mega-orchestrator` (Port 7000):** The master controller that acts as an HTTP to MCP (Master Control Program) bridge.

### Core MCP Services

-   **`filesystem-mcp` (Port 7001):** Handles file operations.
-   **`git-mcp` (Port 7002):** Provides version control functionalities.
-   **`terminal-mcp` (Port 7003):** Allows for command execution.
-   **`database-mcp` (Port 7004):** Manages data operations.
-   **`memory-mcp` (Port 7005):** Offers simple storage capabilities.
-   **`network-mcp` (Port 7006):** (Placeholder) Intended for network operations.
-   **`system-mcp` (Port 7007):** (Placeholder) Intended for system information.
-   **`security-mcp` (Port 7008):** (Placeholder) Intended for security operations.
-   **`config-mcp` (Port 7009):** (Placeholder) Intended for configuration management.
-   **`log-mcp` (Port 7010):** (Placeholder) Intended for logging operations.

### AI/Enhanced Services

-   **`research-mcp` (Port 7011):** Facilitates AI research tasks.
-   **`advanced-memory-mcp` (Port 7012):** Provides AI-powered memory with vector search and semantic similarity.
-   **`transcriber-mcp` (Port 7013):** Handles audio processing and transcription.
-   **`vision-mcp` (Port 7014):** (Placeholder) Intended for vision-related tasks.
-   **`zen-mcp-server` (Port 7017):** MCP tool orchestration gateway for multi-model usage.

### Service Wrappers

-   **`postgresql-mcp-wrapper` (Port 7024):** A wrapper for database operations.
-   **`redis-mcp-wrapper` (Port 7025):** A wrapper for cache and session management.
-   **`qdrant-mcp-wrapper` (Port 7026):** A wrapper for vector database operations.

### Support Services

-   **`postgresql` (Port 7021):** The primary database for the system.
-   **`redis` (Port 7022):** Used for caching and session management.
-   **`qdrant-vector` (Port 7023):** A vector database for AI-related tasks.

### Management & Monitoring Services

-   **`prometheus` (Port 7028):** Metrics collection and storage for all MCP services.
-   **`grafana` (Port 7031):** Dashboards and visualization platform with pre-configured MCP overview dashboard.
-   **`loki` (Port 7032):** Log aggregation system collecting logs from all Docker containers.
-   **`promtail`:** Log collection agent (no external port, internal service).
-   **`backup-service` (Port 7029):** Performs automated backups.
-   **`message-queue` (Port 7030):** A Redis-based message queue for task queuing.

**📊 Full observability stack** - See [MONITORING.md](docs/MONITORING.md) for complete monitoring documentation.

### MQTT Services

-   **`mqtt-broker` (Port 7018):** A Mosquitto message broker for IoT communication.
-   **`mqtt-mcp` (Port 7019):** Handles MQTT operations via the MCP protocol.

## API Endpoints

The Mega-Orchestrator exposes the following endpoints:

-   **`GET /services`**: Lists the available MCP services and their status.
-   **`GET /health`**: Provides a health check of the coordinator and its database/cache connections.
-   **`GET /tools/list`**: Lists all available tools from the MCP services.
-   **`GET /stats`**: Shows usage statistics from the PostgreSQL database.
-   **`POST /mcp`**: A proxy endpoint for MCP tool requests.
-   **`POST /tools/call`**: Another endpoint for calling MCP tools.

## Usage

To start all the services in detached mode, run:

```bash
docker-compose up -d
```

To stop the services, run:

```bash
docker-compose down
```

You can view the logs of a specific service using:

```bash
docker-compose logs -f <service-name>
```

## Monitoring & Observability

The platform includes a comprehensive monitoring stack for full visibility into all services:

### Quick Start

```bash
# Access Grafana dashboards
http://localhost:7031  (admin/admin)

# View Prometheus metrics
http://localhost:7028

# Query logs via Loki
http://localhost:7032
```

### Available Dashboards

- **MCP Orchestration - Overview**: Real-time service health, request rates, latency, errors, and infrastructure metrics
- **Service Health Status**: Up/down status for all 16 MCP services
- **Performance Metrics**: Request rate, response time (p95), error rates
- **Infrastructure**: PostgreSQL connections, Redis clients, MQTT message rates
- **Live Logs**: Real-time error streaming from all containers

### Health Check

Validate monitoring stack configuration (requires `python3` + `PyYAML`):

```bash
./scripts/monitoring-health-check.sh
```

**📊 For detailed monitoring documentation, see [MONITORING.md](docs/MONITORING.md)**

## Contributing

Please refer to the existing coding style and conventions. Before submitting a pull request, ensure that your changes are well-tested.
