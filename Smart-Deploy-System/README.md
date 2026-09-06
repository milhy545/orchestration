# Smart Deploy System v2.0

Unified, modular and "smart" deployment system with **Centralized Source of Truth on HAS**.

## Core Mandates
- **Master Data:** All canonical files reside on `HAS:/home/orchestration/Smart-Deploy-System/unified-truth/`.
- **Sync Engine:** Automatic bidirectional synchronization with user approval.
- **Priority Network:** Local SSH (port 2222) with Unified Key 2026.

## Key Features
1. **Zero-Touch Onboarding:** New agents sync automatically from HAS.
2. **Sync Wizard:** Welcome Dashboard checks and repairs your context files (`AGENTS.md`, `MEMORY.md`, `GEMINI.md`).
3. **Universal Installer:** Agnostic AI skill deployment.

## Usage
Run the dashboard to check your synchronization status:
```bash
welcome_dashboard
```

## Setup for new machines
```bash
ssh HAS 'cat /home/orchestration/Smart-Deploy-System/bootstrap.sh' | bash
```
