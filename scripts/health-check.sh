#\!/bin/bash
echo "=== ORCHESTRACE HEALTH CHECK ===" 
echo "Date: $(date)"
echo

echo "=== CONTAINERS STATUS ===" 
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep mcp

echo
echo "=== DATABASE FILES ===" 
ls -la /tmp/*.db 2>/dev/null || echo "No DB in /tmp"
ls -la /home/orchestration/data/databases/

echo  
echo "=== COORDINATOR STATUS ===" 
curl -s http://localhost:7000/health 2>/dev/null || echo "Coordinator not responding"

echo
echo "=== DISK USAGE ===" 
df -h /home /tmp
