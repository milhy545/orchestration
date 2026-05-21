# Orchestration Audit 2026-05-07

## 0. Scope

- Workspace audited: `/home/milhy777/Develop/orchestration`
- Runtime host sampled: `Milhy-PC`, Debian 13, kernel `6.12.85+deb13-amd64`
- Goal: MCP orchestration, memory transport, transcript loading, semantic memory backend, hardcoded endpoints, HW inventory, deduplicated instruction-file registry

## 1. Files That Define MCP Startup And Memory Connectivity

### 1.1 Primary runtime and compose files

| Path | Purpose | Evidence |
| --- | --- | --- |
| `/home/milhy777/Develop/orchestration/docker-compose.yml` | Main stack definition: `mega-orchestrator`, `memory-mcp`, `advanced-memory-mcp`, DB, Redis, Qdrant, MQTT, monitoring | `docker-compose.yml:5-33`, `127-145`, `242-259` |
| `/home/milhy777/Develop/orchestration/docker-compose.mega.yml` | Alternate expanded compose overlay with same services plus provider envs and monitoring ports | `docker-compose.mega.yml:5-33`, `165-203`, `215-240` |
| `/home/milhy777/Develop/orchestration/.env.example` | Canonical env defaults for DB, Redis, Qdrant, custom model URLs, marketplace URL | `.env.example:5-24`, `37-72` |
| `/home/milhy777/Develop/orchestration/config/Dockerfile` | Build entry for `mega-orchestrator` container | referenced from `docker-compose.yml:6-8`, `docker-compose.mega.yml:166-168` |
| `/home/milhy777/Develop/orchestration/docs/api/mega_orchestrator.md` | Declared HTTP route contract for the orchestrator | `docs/api/mega_orchestrator.md:7-23`, `27-75` |

### 1.2 Orchestrator runtime code

| Path | Purpose | Evidence |
| --- | --- | --- |
| `/home/milhy777/Develop/orchestration/mega_orchestrator/mega_orchestrator_complete.py` | Main HTTP orchestrator, service registry, tool routing, internal transcript recall, semantic memory fallback, service request shaping | service registry `:99-228`; routes `:322-337`; tool routing `:808-924`; per-service HTTP mapping `:1039-1307` |
| `/home/milhy777/Develop/orchestration/mega_orchestrator/mcp_stdio_bridge.py` | stdio JSON-RPC bridge forwarding to `http://127.0.0.1:7000/mcp/rpc` and `.../mcp/schema` | `mcp_stdio_bridge.py:14-17`, `92-170` |
| `/home/milhy777/Develop/orchestration/mega_orchestrator/mcp_tooling.py` | Local MCP tool schema exposed by orchestrator and stdio bridge | `mcp_tooling.py` contains tool definitions including memory and chat recall |
| `/home/milhy777/Develop/orchestration/mega_orchestrator/utils/chat_recall.py` | Exact transcript recall from mounted archive `/home/chat-transcripts` | `chat_recall.py:13-31`, `52-90`, `91-158` |
| `/home/milhy777/Develop/orchestration/mega_orchestrator/utils/conversation_memory.py` | Cross-tool conversation memory persisted in PostgreSQL + Redis | `conversation_memory.py:57-66`, `74-124`, `153-238` |
| `/home/milhy777/Develop/orchestration/mega_orchestrator/utils/hw_detect.py` | Runtime hardware snapshot logic for welcome/bootstrap | `hw_detect.py:20-35`, `47-120` |

### 1.3 Memory services

| Path | Purpose | Evidence |
| --- | --- | --- |
| `/home/milhy777/Develop/orchestration/mcp-servers/memory-mcp/main.py` | Basic memory service backed by PostgreSQL table `unified_memory`; REST API only | `memory-mcp/main.py:17-22`, `25-44`, `90-203`, `255-320` |
| `/home/milhy777/Develop/orchestration/mcp-servers/advanced-memory-mcp/main.py` | Semantic memory service backed by PostgreSQL table `advanced_memories` plus Qdrant collection `advanced_memories`; REST `/tools/*` wrapper | `advanced-memory-mcp/main.py:17-30`, `44-49`, `71-116`, `165-226`, `232-380` |
| `/home/milhy777/Develop/orchestration/mcp-servers/forai-mcp/main.py` | FORAI analysis server; not semantic memory backend, but repo tags it as memory-adjacent workflow | `forai-mcp/main.py:1-18`, `214+` |

## 2. Real Transport Protocols Used For Memory Communication

### 2.1 Implemented

| Layer | Actual transport | Code path |
| --- | --- | --- |
| Client -> Mega Orchestrator | HTTP POST JSON or HTTP POST JSON-RPC 2.0 | `mega_orchestrator_complete.py:322-337`, `400-490`; docs `docs/api/mega_orchestrator.md:7-23` |
| stdio client -> Mega Orchestrator | stdio JSON-RPC bridge, then HTTP POST to `/mcp/rpc` | `mcp_stdio_bridge.py:14-17`, `119-170` |
| Mega Orchestrator -> `memory-mcp` | HTTP REST, not MCP-native; `GET /memory/search`, `GET /memory/list`, `POST /memory/store`, `GET /memory/stats` | `mega_orchestrator_complete.py:1118-1165` |
| Mega Orchestrator -> `advanced-memory-mcp` | HTTP REST wrapper `POST /tools/call` | `mega_orchestrator_complete.py:1288-1300` |
| `advanced-memory-mcp` -> Qdrant | HTTP REST to Qdrant `/collections/...` and `/points/search` | `advanced-memory-mcp/main.py:86-98`, `259-266`, `333-367` |
| `advanced-memory-mcp` -> Gemini embeddings | HTTPS REST to `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent` | `advanced-memory-mcp/main.py:52-68` |
| `conversation_memory` -> PostgreSQL | asyncpg TCP SQL | `conversation_memory.py:15`, `74-124` |
| `conversation_memory` -> Redis | redis async TCP | `conversation_memory.py:16`, `64-66`, `194-238` |

### 2.2 Declared but not materially used for memory runtime in this repo

| Protocol | Status | Evidence |
| --- | --- | --- |
| `streamable_http` | Mentioned in external Codex config guidance, not implemented inside this repo runtime | user/global docs, not repo runtime code |
| `sse` | No active SSE server path found for memory transport in audited runtime files | no matching runtime route in `mega_orchestrator_complete.py`, `memory-mcp`, `advanced-memory-mcp` |

### 2.3 Bottom line

- Memory transport in this workspace is HTTP-first.
- Native stdio exists only as a local compatibility bridge to the HTTP orchestrator.
- No SSE memory path was found in the active runtime implementation.

## 3. Transcript Loading And Semantic Memory Backend

### 3.1 Exact transcript loading

| Component | Behaviour | Evidence |
| --- | --- | --- |
| `CHAT_RECALL_ARCHIVE_ROOT` env | Set to `/home/chat-transcripts` in orchestrator container | `docker-compose.yml:16-21`, `docker-compose.mega.yml:177-187` |
| `ChatRecall` default root | Defaults to `/home/chat-transcripts`, overridable by env | `chat_recall.py:13-31` |
| Transcript file patterns | Reads `transcript.md`, `transcript.part-*.md`, `extracted_text.txt`, `session.jsonl`, `session.part-*.jsonl` under archive dirs | `chat_recall.py:84-90` |
| Manifest loading | Reads sibling `manifest.json` when present | `chat_recall.py:97-110` |
| Query type | Exact substring search over loaded text, with excerpt window | `chat_recall.py:52-82`, `113-134` |
| Exposure in orchestrator | Internal tool `search_chat_history` returns exact hits and optional semantic hits | `mega_orchestrator_complete.py:444-447`, `865-924` |

### 3.2 Semantic memory implementation

#### Basic memory

- Backend table: `unified_memory`
- DB: PostgreSQL only
- Query mode: `ILIKE` substring search
- API surface: `/memory/store`, `/memory/list`, `/memory/search`, `/memory/stats`
- Evidence: `memory-mcp/main.py:25-44`, `120-203`, `255-316`

#### Advanced memory

- Metadata DB table: `advanced_memories`
- Vector DB: Qdrant collection `advanced_memories`
- Embedding generation: Gemini `text-embedding-004` over HTTPS
- Query modes:
  - plain text `ILIKE` over PostgreSQL via `search_memories`
  - vector cosine search via `semantic_similarity`
  - vector search with optional category filter via `vector_search`
- Evidence: `advanced-memory-mcp/main.py:44-45`, `71-98`, `165-205`, `232-380`

### 3.3 Orchestrator semantic fallback chain

1. `search_chat_history` with semantic mode calls `advanced_memory` first as `semantic_search`.
2. Orchestrator rewrites `semantic_search` -> `semantic_similarity`.
3. If advanced memory fails, fallback is `memory-mcp` `search_memories`.

Evidence:

- semantic tool handling: `mega_orchestrator_complete.py:865-924`
- forced routing: `mega_orchestrator_complete.py:810-817`
- alias rewrite: `mega_orchestrator_complete.py:1288-1293`

### 3.4 Separate conversation-context memory

- Distinct from semantic memory.
- Persists request/response thread state in PostgreSQL tables `conversation_contexts` and `file_references`.
- Also mirrors active contexts in Redis with TTL.
- Evidence: `conversation_memory.py:74-124`, `153-238`

## 4. Hardcoded Ports, Hosts, IPs And URLs

### 4.1 Container/service hostnames on internal Docker network

| Hostname | Usage | Evidence |
| --- | --- | --- |
| `postgresql` | primary SQL backend | `docker-compose.yml:13`, `51`, `71`, `98`, `118`, `138`, `214`, `251`; `.env.example:8-9` |
| `redis` | cache/session backend | `docker-compose.yml:14`, `52`, `72`, `99`, `119`, `139`, `215`, `252`; `.env.example:12` |
| `qdrant-vector` | vector DB backend | `docker-compose.yml:253`; `.env.example:24`; `advanced-memory-mcp/main.py:30` |
| `mcp-filesystem`, `mcp-git`, `mcp-terminal`, `mcp-database`, `mcp-memory`, `mcp-research`, `mcp-advanced-memory`, `mcp-marketplace`, `mcp-gmail`, `mcp-forai` | orchestrator service routing | `mega_orchestrator_complete.py:99-228` |
| `mqtt-broker` | MQTT broker host | `docker-compose.mega.yml:233-235` |

### 4.2 Host ports exposed by compose

| Host port | Service |
| --- | --- |
| `7000` | `mega-orchestrator` |
| `7001` | `filesystem-mcp` |
| `7002` | `git-mcp` |
| `7003` | `terminal-mcp` |
| `7004` | `database-mcp` |
| `7005` | `memory-mcp` |
| `7006` | `network-mcp` |
| `7007` | `system-mcp` |
| `7008` | `security-mcp` |
| `7009` | `config-mcp` |
| `7010` | `log-mcp` |
| `7011` | `research-mcp` |
| `7012` | `advanced-memory-mcp` |
| `7015` | `gmail-mcp` |
| `7018` | `mqtt-broker` |
| `7019` | `mqtt-mcp` |
| `7021` | `postgresql` wrapper/db mapping in expanded compose/status artifacts |
| `7022` | `redis` |
| `7023` | `qdrant` HTTP |
| `7024` | `postgresql-mcp-wrapper` |
| `7027` | `qdrant` gRPC/admin |
| `7028` | monitoring |
| `7029` | backup service |
| `7030` | message queue Redis |
| `7031` | Grafana |
| `7032` | Loki |
| `7034` | marketplace |

Evidence: `docker-compose.yml:10-11`, `43-45`, `64-65`, `84-85`, `111-112`, `131-132`, `151-152`, `161-162`, `171-172`, `185-196`, `210-211`, `248-249`; `docker-compose.mega.yml:31-32`, `39-40`, `51-52`, `66-67`, `82-83`, `102-103`, `124-125`, `135-146`, `160-161`, `181-182`, `199-211`, `220-221`, `239-240`

### 4.3 Hardcoded URLs in code/config

| URL | Where | Purpose |
| --- | --- | --- |
| `http://127.0.0.1:7000` | `mcp_stdio_bridge.py:14` | local bridge target |
| `http://127.0.0.1:11434` | `docker-compose.mega.yml:20` | Ollama base URL |
| `https://api.inceptionlabs.ai/v1` | `docker-compose.mega.yml:26` | external model provider |
| `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent` | `advanced-memory-mcp/main.py:58` | Gemini embeddings |
| `http://qdrant-vector:6333` | `docker-compose.yml:253`, `.env.example:24`, `advanced-memory-mcp/main.py:30` | Qdrant vector API |
| `http://localhost:1234/v1` | `.env.example:50` | custom model API default |
| `http://localhost:7034` | `.env.example:57`, `docker-compose.mega.yml:156` | marketplace base URL |
| `http://localhost:7031` | `docker-compose.mega.yml:119` | Grafana root URL |
| `http://loki:3100/loki/api/v1/push` | `monitoring/promtail/promtail-config.yml:9` | log shipping |
| `http://prometheus:9090` | `monitoring/grafana/provisioning/datasources/datasources.yml:8` | Grafana datasource |
| `http://loki:3100` | `monitoring/grafana/provisioning/datasources/datasources.yml:19` | Grafana datasource |

### 4.4 IPs and external endpoints found in adjacent instruction/memory files

These are not runtime literals inside the audited repo codepath, but they are active machine-level connection points discovered during the same audit:

| Endpoint | Source |
| --- | --- |
| `http://192.168.0.58:7000/mcp` | `/home/milhy777/AGENTS.md`, `/home/milhy777/.codex/AGENTS.md`, `/home/milhy777/.gemini/GEMINI.md` |
| `http://home-automat-server.tailb42db0.ts.net:7000/mcp` | same files |
| `http://100.90.137.86:7000/mcp` | same files |

## 5. Deduplicated Registry Of `GEMINI.md`, `AGENTS.md`, `MEMORY.md`

### 5.1 Canonical / non-canonical split

| Canonical group | Canonical file | Additional files in same basename family | Merge result |
| --- | --- | --- | --- |
| `GEMINI.md` | `/home/milhy777/.gemini/GEMINI.md` | `/home/milhy777/Applications/Plasma/plasma-ai-usage-monitor-7.0.0/GEMINI.md`, `/home/milhy777/Develop/orchestration/docs/manuals/GEMINI.md` | Keep `~/.gemini/GEMINI.md` as source of truth; other files are repo/app-local overlays |
| global `AGENTS.md` | `/home/milhy777/AGENTS.md` | `/home/milhy777/.codex/AGENTS.md`, `/home/milhy777/Develop/orchestration/AGENTS.md`, `/home/milhy777/Develop/MyVoiceTranslator/AGENTS.md`, `/home/milhy777/.nvm/AGENTS.md`, `/home/milhy777/Applications/Plasma/plasma-ai-usage-monitor-7.0.0/AGENTS.md` | Split by scope; do not flatten into one file |
| `MEMORY.md` | `/home/milhy777/.codex/memories/MEMORY.md` | no second `MEMORY.md` found within audited depth | single active local registry |

### 5.2 Effective merged rule set

1. System-wide source of truth: `/home/milhy777/.gemini/GEMINI.md`
2. Global agent shim: `/home/milhy777/AGENTS.md`
3. Codex-specific runtime rules: `/home/milhy777/.codex/AGENTS.md`
4. Codex local memory registry: `/home/milhy777/.codex/memories/MEMORY.md`
5. Repo-specific overlays:
   - `/home/milhy777/Develop/orchestration/AGENTS.md`
   - `/home/milhy777/Develop/MyVoiceTranslator/AGENTS.md`
   - app-local files under `/home/milhy777/Applications/...`

## 6. Hardware Inventory

### 6.1 Current host: `Milhy-PC`

| Category | Data |
| --- | --- |
| Hostname | `Milhy-PC` |
| OS | Debian GNU/Linux 13 (trixie) |
| Kernel | `6.12.85+deb13-amd64` |
| Board/Vendor | Gigabyte `Z97P-D3` |
| Firmware | `F9b`, date `2016-03-03` |
| CPU | Intel Core i5-4690K, 4 cores / 4 threads, 3.50 GHz base, 4.40 GHz max |
| RAM | 30 GiB visible (`free -h`), repo detector rounds to ~31.2 GB |
| Swap | 36 GiB |
| GPU 1 | Intel 4th Gen integrated graphics (`00:02.0`) |
| GPU 2 | NVIDIA GP106 GeForce GTX 1060 6GB (`01:00.0`) |
| LAN | Realtek RTL8111/8168/8211/8411 PCIe Gigabit |
| IPv4 LAN | `192.168.0.67/24` on `eth0` |
| Tailscale IPv4 | `100.69.194.108/32` on `tailscale0` |
| Root disk | `sda` CHN 25SATAS3 256, 238.5G; `sda2` mounted `/`, `sda1` `/boot/efi` |
| Secondary SSD | `sdb` Crucial CT1000MX500SSD1, 931.5G; includes `/media/Windows_10` and `/media/Backup` |
| Secondary HDD | `sdc` Seagate ST2000DM001-9YN1, 1.8T |
| Extra HDD | `sdd` Hitachi HDS725050KLA360, 465.8G |
| Extra HDD | `sde` Seagate ST3500312CS, 465.8G |
| USB device | `sdf` Photosmart C4500 |

### 6.2 Additional hardware remembered in memory surfaces

| Node | Memory-derived data | Source |
| --- | --- | --- |
| `KODI-TV` / `RPi` | Raspberry Pi 3B class device, aarch64, Debian 13, LAN `192.168.0.205`, Tailscale `100.88.85.89`, 8 GB SD, Kodi TV node | Mega-Orchestrator `get_context`/`list_memories` result ids `1545`, `1546` |
| `HAS` | endpoint owner for transcript archive and Mega-Orchestrator on `192.168.0.58` | `/home/milhy777/.gemini/GEMINI.md`, `/home/milhy777/AGENTS.md`, `/home/milhy777/.codex/AGENTS.md`, `/home/milhy777/.codex/memories/MEMORY.md` |
| `LLMS`, `Aspire`, `HP-ProBook` | mentioned in memory registry as fleet nodes; no full hardware spec present in retrieved memory sample | `/home/milhy777/.codex/memories/MEMORY.md` |

### 6.3 Memory coverage gap

- Full hardware specs for `HAS`, `LLMS`, `Aspire`, `HP-ProBook` were not returned by the available advanced-memory queries used in this audit.
- Available memory payloads returned detailed specs only for `KODI-TV/RPi`.

## 7. Runtime Design Summary

### 7.1 What is actually running by design

1. `mega-orchestrator` is the single HTTP ingress and routing layer.
2. Basic memory is PostgreSQL-backed `memory-mcp`.
3. Semantic memory is `advanced-memory-mcp` with:
   - embeddings from Gemini HTTPS API
   - vectors in Qdrant
   - metadata rows in PostgreSQL
4. Transcript recall is not vector-native. It is direct file-system exact search over mounted archive text files.
5. Cross-tool session/context memory is a separate PostgreSQL + Redis subsystem inside the orchestrator.

### 7.2 What is not present in the active implementation

- No SSE memory transport path found.
- No direct MCP stdio server in memory services; only the orchestrator bridge speaks stdio, and it immediately forwards to HTTP.
- No evidence that `streamable_http` is a repo runtime primitive; it exists in external client config guidance, not inside the service code.
