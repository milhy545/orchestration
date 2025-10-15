# GEMINI Project: Orchestration System

## Language Preference

  Primary language for communication: Czech
  (česky)
  - Use Czech for all explanations,
  discussions, and documentation
  - Code comments and technical documentation
  can remain in English where appropriate
  - Error messages and logs should be explained
   in Czech

## Project Overview

This project is a sophisticated orchestration system designed to manage a suite of microservices, referred to as "MCP" (Model-Context-Protocol) services. The system is built around a central coordinator, the "Zen Coordinator" (or "Mega Coordinator"), which acts as a secure proxy and router for all incoming requests to the various MCP services.

The architecture is highly modular, with each MCP service responsible for a specific domain of tasks, such as file system operations, Git version control, terminal command execution, and more. The system is designed for scalability and extensibility, with placeholders for future services.

The core technologies used in this project include:

*   **Python:** For the Zen Coordinator and many of the MCP services.
*   **Node.js:** For the advanced memory service.
*   **Docker:** For containerizing the services.
*   **Docker Compose:** For orchestrating the deployment of the services.
*   **PostgreSQL:** As the primary database for all services.
*   **Redis:** For caching and session management.
*   **Qdrant:** As a vector database for the advanced memory service.
*   **Prometheus:** For monitoring the health and performance of the services.
*   **MQTT:** For messaging and IoT communication.

## Building and Running

The project is designed to be run using Docker and Docker Compose. The following commands can be used to build and run the system:

*   **Build and start all services:**
    ```bash
    docker-compose up --build -d
    ```
*   **Stop all services:**
    ```bash
    docker-compose down
    ```
*   **View the logs of a specific service:**
    ```bash
    docker-compose logs -f <service_name>
    ```
    (e.g., `docker-compose logs -f zen-coordinator`)

## Development Conventions

*   **Microservices Architecture:** The project follows a microservices architecture, with each service having its own container and API.
*   **Centralized Orchestration:** All requests are routed through the Zen Coordinator, which provides a single point of entry to the system.
*   **Environment Variables:** The services are configured using environment variables, with default values provided in the `docker-compose.yml` file.
*   **MCP Protocol:** The services communicate using a custom JSON-RPC-based protocol called MCP (Model-Context-Protocol).
*   **Database Schema:** The database schema is managed by the services themselves, with each service creating its own tables when it starts up.
*   **Health Checks:** Each service exposes a `/health` endpoint that can be used to monitor its status.