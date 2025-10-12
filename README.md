# Orchestration Project

## Description

This project is a microservices-based system for orchestrating and managing a collection of services using Docker. It acts as a central hub for various functionalities, including file operations, version control, command execution, AI-powered tasks, and more. The system is designed to be modular and extensible, with services communicating over a shared network.

## Architecture

The core of the project is the **ZEN Coordinator**, a Python-based HTTP server that acts as a secure proxy to the various MCP (Master Control Program) services. The coordinator is responsible for:

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
    - Copy the `.env.example` file to `.env` and customize the environment variables as needed.
3.  **Run the services:**
    ```bash
    docker-compose up -d
    ```

## Services

The `docker-compose.yml` file defines the following services, which are organized into logical groups:

### Master Controller

-   **`zen-coordinator` (Port 8020):** The master controller that acts as an HTTP to MCP (Master Control Program) bridge.

### Core MCP Services

-   **`filesystem-mcp` (Port 8001):** Handles file operations.
-   **`git-mcp` (Port 8002):** Provides version control functionalities.
-   **`terminal-mcp` (Port 8003):** Allows for command execution.
-   **`database-mcp` (Port 8004):** Manages data operations.
-   **`memory-mcp` (Port 8005):** Offers simple storage capabilities.
-   **`network-mcp` (Port 8006):** (Placeholder) Intended for network operations.
-   **`system-mcp` (Port 8007):** (Placeholder) Intended for system information.
-   **`security-mcp` (Port 8008):** (Placeholder) Intended for security operations.
-   **`config-mcp` (Port 8009):** (Placeholder) Intended for configuration management.
-   **`log-mcp` (Port 8010):** (Placeholder) Intended for logging operations.

### AI/Enhanced Services

-   **`research-mcp` (Port 8011):** Facilitates AI research tasks.
-   **`advanced-memory-mcp` (Port 8012):** Provides AI-powered memory with vector search and semantic similarity.
-   **`transcriber-mcp` (Port 8013):** Handles audio processing and transcription.
-   **`vision-mcp` (Port 8014):** (Placeholder) Intended for vision-related tasks.

### Service Wrappers

-   **`postgresql-mcp-wrapper` (Port 8024):** A wrapper for database operations.
-   **`redis-mcp-wrapper` (Port 8025):** A wrapper for cache and session management.
-   **`qdrant-mcp-wrapper` (Port 8026):** A wrapper for vector database operations.

### Support Services

-   **`postgresql` (Port 8021):** The primary database for the system.
-   **`redis` (Port 8022):** Used for caching and session management.
-   **`qdrant-vector` (Port 8023):** A vector database for AI-related tasks.

### Management Services

-   **`monitoring` (Port 8028):** A Prometheus instance for health checks and metrics.
-   **`backup-service` (Port 8029):** Performs automated backups.
-   **`message-queue` (Port 8030):** A Redis-based message queue for task queuing.

### MQTT Services

-   **`mqtt-broker` (Port 8018):** A Mosquitto message broker for IoT communication.
-   **`mqtt-mcp` (Port 8019):** Handles MQTT operations via the MCP protocol.

## API Endpoints

The ZEN Coordinator exposes the following endpoints:

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

## Contributing

Please refer to the existing coding style and conventions. Before submitting a pull request, ensure that your changes are well-tested.
