#!/bin/bash
echo "=== PRODUCTION MONITORING Sun Aug 17 09:59:31 BST 2025 ==="

# Health status
curl -s http://127.0.0.1:7000/health

# Service count
echo "Services running: 0"

# Resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Log any issues
docker ps --filter "health=unhealthy" --format "{{.Names}}"
