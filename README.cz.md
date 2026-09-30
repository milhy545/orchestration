# 🧠 Orchestration Platform

[![Platform: Docker](https://img.shields.io/badge/Platform-Docker%20Compose-blue.svg)](https://www.docker.com/)
[![MCP: 14 Services](https://img.shields.io/badge/MCP-14%20Microservices-green.svg)](https://modelcontextprotocol.io/)
[![Storage: Qdrant](https://img.shields.io/badge/Vector%20DB-Qdrant-red.svg)](https://qdrant.tech/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)  
[🇬🇧 English version available here](./README.md)

Komplexní Dockerizovaná multi-agentní platforma pro provoz sítě MCP služeb (Model Context Protocol), perzistentní vektorové paměti a podpůrné infrastruktury. Centrem platformy je brána `mega-orchestrator`, která sjednocuje správu souborů, git, terminál, databáze, sémantickou paměť, bezpečnost (JWT) a správu tajemství (HashiCorp Vault).

---

## 🎯 Hardwarová ironie: Mozek na nejstarším stroji

Zatímco vývojové modely vyžadují silná GPU, **tento centrální mozek celé sítě běží na nejstarším a nejslabším hardware v celém mém labu**.

Důvod je čistě pragmatický:
- MCP servery, API bridge a vektorové indexy nepotřebují gigahertze hrubého procesorového výkonu.
- Potřebují **stabilní RAM, spolehlivou síť (Tailscale mesh) a nepřetržitý běh**.
- Provozování produkční 14-kontejnerové nervové soustavy na starém železe dokazuje, že systémová architektura a optimalizace zdrojů jsou víc než drahý hardware.

---

## 🏗️ Přehled služeb a portů

| Služba | Host Port | Role v ekosystému |
| :--- | :--- | :--- |
| `mega-orchestrator` | `7000` | Centrální brána, JSON-RPC bridge, registr služeb |
| `filesystem-mcp` | `7001` | Práce se soubory, čtení, zápis, analýza |
| `git-mcp` | `7002` | Verzování, status, diff, commity |
| `terminal-mcp` | `7003` | Vzdálené spouštění příkazů a procesů |
| `database-mcp` | `7004` | SQL dotazy, schémata, inspekce tabulek |
| `memory-mcp` | `7005` | CRUD operace nad perzistentní pamětí |
| `network-mcp` | `7006` | Webhooky, HTTP požadavky, síťová diagnostika |
| `system-mcp` | `7007` | Monitoring prostředků, zatížení, disky |
| `security-mcp` | `7008` | Správa JWT tokenů, šifrování, SSL certifikáty |
| `config-mcp` | `7009` | Konfigurace prostředí a validace |
| `log-mcp` | `7010` | Analýza logů a vyhledávání chyb |
| `advanced-memory-mcp` | `7012` | Vektorové vyhledávání v sémantické paměti (Qdrant) |
| `forai-mcp` | `7016` | Injekce a analýza strojově čitelných FORAI hlaviček |
| `marketplace-mcp` | `7034` | Katalog privátních skillů zabezpečený JWT |
| `vault-secrets-ui` | `10000` | UI a API pro správu tajemství (HashiCorp Vault) |

---

## 🏷️ FORAI Tagovací systém & Paměť
Platforma využívá standardizovaný systém strojově čitelných hlaviček **FORAI**. Každý automatizovaný agent při ukládání kontextu injektuje tagy a sémantická metadata, což umožňuje okamžité vyhledávání rozhodnutí v čase bez nutnosti skenovat celé repozitáře.
