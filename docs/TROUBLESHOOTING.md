# Troubleshooting Guide - Orchestration MCP Platform

## 🚨 Emergency Procedures

### Quick Emergency Recovery
```bash
# Complete system restart (use with caution)
cd /home/orchestration
docker-compose down
docker-compose up -d

# Wait for services to stabilize
sleep 30

# Verify all services are running
curl http://localhost:7000/health
curl http://localhost:7000/services
```

### Emergency Service Health Check
```bash
#!/bin/bash
# emergency_check.sh

echo "=== EMERGENCY HEALTH CHECK ==="
echo "Current time: $(date)"

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo "❌ CRITICAL: Docker daemon not running!"
    echo "Fix: sudo systemctl start docker"
    exit 1
fi

# Check ZEN Coordinator
if curl -s http://localhost:7000/health >/dev/null; then
    echo "✅ ZEN Coordinator: Running"
else
    echo "❌ ZEN Coordinator: Failed"
    echo "Fix: docker-compose restart zen-coordinator"
fi

# Check critical services
services=(7001 7002 7003 7004 7005 7000 7021 7022)
for port in "${services[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ Port $port: Open"
    else
        echo "❌ Port $port: Closed"
    fi
done

echo "=== END HEALTH CHECK ==="
```

## 🔍 Diagnostic Commands

### System Overview
```bash
# Check all container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check container resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check Docker compose services
cd /home/orchestration
docker-compose ps

# Check system resources
df -h                    # Disk space
free -h                  # Memory usage
uptime                   # System load
```

### Network Diagnostics
```bash
# Check port bindings
netstat -tlnp | grep -E ":(70[0-9][0-9]|6333|9001)"

# Test internal connectivity
curl http://localhost:7000/health    # ZEN Coordinator
curl http://localhost:7001/health    # Filesystem MCP
curl http://localhost:7021/         # PostgreSQL (should return error page)

# Check Docker networks
docker network ls
docker network inspect orchestration_default
```

### Service-Specific Diagnostics
```bash
# ZEN Coordinator logs
docker logs zen-coordinator --tail=50

# All MCP service logs
docker logs mcp-filesystem --tail=20
docker logs mcp-git --tail=20
docker logs mcp-terminal --tail=20
docker logs mcp-database --tail=20
docker logs mcp-memory --tail=20
docker logs mcp-research --tail=20
docker logs mcp-transcriber --tail=20

# Database logs
docker logs mcp-postgresql --tail=30
docker logs mcp-redis --tail=30
```

## 🛠️ Common Issues & Solutions

### 1. ZEN Coordinator Not Responding

**Symptoms:**
- `curl http://localhost:7000/health` returns connection refused
- Portainer shows coordinator container as stopped

**Diagnosis:**
```bash
# Check coordinator status
docker ps | grep zen-coordinator

# Check coordinator logs
docker logs zen-coordinator --tail=100

# Check if port is in use
netstat -tlnp | grep :7000
```

**Solutions:**

**Solution A: Simple Restart**
```bash
docker-compose restart zen-coordinator
sleep 10
curl http://localhost:7000/health
```

**Solution B: Full Rebuild**
```bash
# Stop and remove coordinator
docker-compose stop zen-coordinator
docker-compose rm -f zen-coordinator

# Rebuild and start
docker-compose up -d zen-coordinator

# Verify startup
docker logs zen-coordinator -f
```

**Solution C: Check Dependencies**
```bash
# Ensure MCP services are running first
for port in 7001 7002 7003 7004 7005 7011 7012; do
    if ! nc -z localhost $port; then
        echo "Service on port $port is down"
        docker-compose restart mcp-$([ $port -eq 7001 ] && echo "filesystem" || 
                                        [ $port -eq 7002 ] && echo "git" ||
                                        [ $port -eq 7003 ] && echo "terminal" ||
                                        [ $port -eq 7004 ] && echo "database" ||
                                        [ $port -eq 7005 ] && echo "memory" ||
                                        [ $port -eq 7011 ] && echo "research" ||
                                        [ $port -eq 7012 ] && echo "advanced-memory")
    fi
done

# Start coordinator after services are up
docker-compose restart zen-coordinator
```

### 2. MCP Service Communication Errors

**Symptoms:**
- ZEN Coordinator returns "Service on port XXXX requires MCP protocol adaptation"
- HTTP 502 errors when calling MCP tools

**Diagnosis:**
```bash
# Test direct service communication
curl http://localhost:7001/health    # Should return {"status":"ok"}
curl http://localhost:7002/health    
curl http://localhost:7003/health

# Check if services are actually MCP compliant
docker logs mcp-filesystem | grep -i "mcp\|protocol\|error"
```

**Solutions:**

**Solution A: Restart Problematic Service**
```bash
# Identify which service is failing from ZEN Coordinator logs
docker logs zen-coordinator | grep -i "error\|failed"

# Restart specific service (example for filesystem)
docker-compose restart mcp-filesystem
sleep 5

# Test service directly
curl http://localhost:7001/health
```

**Solution B: Check Service Configuration**
```bash
# Verify environment variables
docker exec mcp-filesystem env | grep -E "(PORT|HOST|MCP)"

# Check if service is binding to correct port
docker exec mcp-filesystem netstat -tlnp
```

**Solution C: Protocol Debugging**
```bash
# Enable debug mode in coordinator
docker-compose stop zen-coordinator

# Edit docker-compose.yml to add debug environment
# Then restart with debug logging
docker-compose up -d zen-coordinator

# Monitor debug logs
docker logs zen-coordinator -f
```

### 3. Database Connection Issues

**Symptoms:**
- Database MCP tools fail with connection errors
- "password authentication failed" errors

**Diagnosis:**
```bash
# Test PostgreSQL connectivity
docker exec mcp-postgresql pg_isready -U mcp_admin

# Test connection from another container
docker exec mcp-database psql -h mcp-postgresql -U mcp_admin -d mcp_unified -c "SELECT 1;"

# Check Redis connectivity
docker exec mcp-redis redis-cli ping
```

**Solutions:**

**Solution A: Reset Database Passwords**
```bash
# Check current password in environment
grep POSTGRES_PASSWORD .env

# Reset PostgreSQL password
docker exec -it mcp-postgresql psql -U postgres -c "ALTER USER mcp_admin PASSWORD 'new_password';"

# Update .env file
sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=new_password/' .env

# Restart database services
docker-compose restart mcp-database mcp-postgresql
```

**Solution B: Reinitialize Database**
```bash
# Backup existing data (if important)
docker exec mcp-postgresql pg_dump -U mcp_admin mcp_unified > backup.sql

# Stop and remove database
docker-compose stop mcp-postgresql
docker volume rm orchestration_postgres_data

# Start fresh database
docker-compose up -d mcp-postgresql
sleep 10

# Restore data if needed
docker exec -i mcp-postgresql psql -U mcp_admin mcp_unified < backup.sql
```

**Solution C: Network Connectivity Issues**
```bash
# Check if services can reach each other
docker exec mcp-database nslookup mcp-postgresql
docker exec mcp-database telnet mcp-postgresql 5432

# If network issues, recreate network
docker-compose down
docker network prune -f
docker-compose up -d
```

### 4. Transcriber Service Unhealthy

**Symptoms:**
- Service shows as "unhealthy" in `/services` endpoint
- Audio transcription tools fail

**Diagnosis:**
```bash
# Check transcriber status
curl http://localhost:7013/health

# Check transcriber logs
docker logs mcp-transcriber --tail=100

# Check if required dependencies are installed
docker exec mcp-transcriber which ffmpeg
docker exec mcp-transcriber python -c "import whisper"
```

**Solutions:**

**Solution A: Restart and Rebuild**
```bash
# Simple restart first
docker-compose restart mcp-transcriber
sleep 15
curl http://localhost:7013/health

# If still failing, rebuild
docker-compose stop mcp-transcriber
docker-compose build mcp-transcriber
docker-compose up -d mcp-transcriber
```

**Solution B: Check Dependencies**
```bash
# Check if audio processing libraries are installed
docker exec mcp-transcriber pip list | grep -E "(whisper|ffmpeg|pydub)"

# If missing, rebuild with proper dependencies
# Edit Dockerfile for transcriber service and rebuild
docker-compose build --no-cache mcp-transcriber
docker-compose up -d mcp-transcriber
```

**Solution C: Resource Issues**
```bash
# Check if system has enough resources for AI processing
free -h
df -h

# Transcriber needs significant memory and CPU
# Consider running on more powerful hardware or reduce concurrency
```

### 5. Memory/Performance Issues

**Symptoms:**
- Services running slowly
- Out of memory errors
- High CPU usage

**Diagnosis:**
```bash
# Check system resources
free -h
df -h
top -p $(docker inspect --format='{{.State.Pid}}' $(docker ps -q))

# Check container resource usage
docker stats --no-stream

# Check disk space usage by containers
docker system df
```

**Solutions:**

**Solution A: Resource Cleanup**
```bash
# Clean up Docker resources
docker system prune -f
docker volume prune -f
docker image prune -f

# Clean up logs
docker-compose down
truncate -s 0 /var/lib/docker/containers/*/*.log

# Restart services
docker-compose up -d
```

**Solution B: Memory Optimization**
```bash
# Add memory limits to docker-compose.yml
version: '3.8'
services:
  zen-coordinator:
    mem_limit: 512m
  mcp-filesystem:
    mem_limit: 256m
  mcp-memory:
    mem_limit: 1g

# Restart with new limits
docker-compose down
docker-compose up -d
```

**Solution C: Performance Tuning**
```bash
# Optimize PostgreSQL settings
docker exec mcp-postgresql psql -U postgres -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET max_connections = '100';
SELECT pg_reload_conf();
"

# Restart database
docker-compose restart mcp-postgresql
```

### 6. Portainer Agent Issues

**Symptoms:**
- Cannot add environment to Portainer
- "Agent not responding" errors
- Stack deployment fails

**Diagnosis:**
```bash
# Check if Portainer Agent is running
docker ps | grep portainer_agent

# Test agent connectivity
curl http://localhost:9001/ping

# Check agent logs
docker logs portainer_agent

# Test from external network
curl http://192.168.0.58:9001/ping
```

**Solutions:**

**Solution A: Reinstall Portainer Agent**
```bash
# Remove existing agent
docker stop portainer_agent
docker rm portainer_agent

# Install fresh agent
docker run -d \
  --name portainer_agent \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/docker/volumes:/var/lib/docker/volumes \
  -p 9001:9001 \
  portainer/agent:latest

# Verify installation
sleep 5
curl http://localhost:9001/ping
```

**Solution B: Network/Firewall Issues**
```bash
# Check if port 9001 is open
netstat -tlnp | grep :9001

# Check firewall settings (if using UFW)
sudo ufw status
sudo ufw allow 9001

# Test external connectivity
nmap -p 9001 192.168.0.58
```

**Solution C: Docker Socket Permissions**
```bash
# Check Docker socket permissions
ls -la /var/run/docker.sock

# Fix permissions if needed
sudo chmod 666 /var/run/docker.sock

# Restart agent
docker restart portainer_agent
```

### 7. Git Operations Failing

**Symptoms:**
- Git MCP tools return authentication errors
- Cannot push to repository

**Diagnosis:**
```bash
# Test git operations manually
docker exec mcp-git git status /home/orchestration
docker exec mcp-git git remote -v

# Check SSH keys or tokens
docker exec mcp-git ls -la ~/.ssh/
docker exec mcp-git cat ~/.gitconfig
```

**Solutions:**

**Solution A: Configure Git Credentials**
```bash
# Set git configuration
docker exec mcp-git git config --global user.name "Orchestration Bot"
docker exec mcp-git git config --global user.email "bot@orchestration.local"

# If using SSH, copy keys
docker cp ~/.ssh/id_rsa mcp-git:/root/.ssh/
docker cp ~/.ssh/id_rsa.pub mcp-git:/root/.ssh/
docker exec mcp-git chmod 600 /root/.ssh/id_rsa
```

**Solution B: Use HTTPS with Token**
```bash
# Configure remote URL with token
docker exec mcp-git git remote set-url origin https://username:token@github.com/milhy545/orchestration.git

# Test authentication
docker exec mcp-git git ls-remote origin
```

## 📊 Monitoring & Alerting

### Automated Health Monitoring Script
```bash
#!/bin/bash
# monitoring.sh - Run via cron every 5 minutes

LOG_FILE="/var/log/orchestration-health.log"
ALERT_EMAIL="admin@yourdomain.com"

echo "$(date): Starting health check" >> $LOG_FILE

# Check critical services
critical_services=(
    "http://localhost:7000/health"  # ZEN Coordinator
    "http://localhost:7021/"        # PostgreSQL (expect connection)
    "http://localhost:7022/"        # Redis  
)

failed_services=()

for service in "${critical_services[@]}"; do
    if ! curl -s -f "$service" >/dev/null 2>&1; then
        failed_services+=("$service")
        echo "$(date): FAILED - $service" >> $LOG_FILE
    fi
done

# Check Portainer Agent
if ! curl -s -f "http://localhost:9001/ping" >/dev/null 2>&1; then
    failed_services+=("Portainer Agent")
    echo "$(date): FAILED - Portainer Agent" >> $LOG_FILE
fi

# Send alert if any services failed
if [ ${#failed_services[@]} -gt 0 ]; then
    echo "ALERT: The following services are down:" | mail -s "Orchestration Platform Alert" $ALERT_EMAIL
    printf '%s\n' "${failed_services[@]}" | mail -s "Failed Services" $ALERT_EMAIL
    
    # Attempt automatic recovery
    echo "$(date): Attempting automatic recovery" >> $LOG_FILE
    cd /home/orchestration
    docker-compose restart
fi

echo "$(date): Health check completed" >> $LOG_FILE
```

### Performance Monitoring
```bash
#!/bin/bash
# performance_monitor.sh

# Check container performance
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" > /tmp/performance.log

# Check for high resource usage
high_cpu=$(docker stats --no-stream --format "{{.Container}} {{.CPUPerc}}" | awk '$2+0 > 80 {print $1}')
high_mem=$(docker stats --no-stream --format "{{.Container}} {{.MemUsage}}" | awk -F'/' '$1+0 > 1000000000 {print $1}' | awk '{print $1}')

if [ -n "$high_cpu" ]; then
    echo "High CPU usage detected: $high_cpu"
    # Consider restarting or investigating
fi

if [ -n "$high_mem" ]; then
    echo "High memory usage detected: $high_mem"
    # Consider memory cleanup
fi
```

## 🔧 Maintenance Procedures

### Regular Maintenance Checklist

**Weekly Tasks:**
```bash
# 1. Update containers
docker-compose pull
docker-compose up -d

# 2. Clean up resources
docker system prune -f

# 3. Backup database
docker exec mcp-postgresql pg_dump -U mcp_admin mcp_unified > "backup_$(date +%Y%m%d).sql"

# 4. Check log sizes
du -sh /var/lib/docker/containers/*/*.log

# 5. Verify all services
./health-check.sh
```

**Monthly Tasks:**
```bash
# 1. Full system backup
tar -czf "orchestration_backup_$(date +%Y%m%d).tar.gz" /home/orchestration

# 2. Security updates
apt update && apt upgrade -y

# 3. Review performance metrics
docker stats --no-stream > "performance_$(date +%Y%m%d).log"

# 4. Test disaster recovery
# (Run on test environment)
```

### Log Management
```bash
# Rotate logs to prevent disk space issues
#!/bin/bash
# log_rotate.sh

LOG_DIR="/var/lib/docker/containers"
MAX_SIZE="100M"

find $LOG_DIR -name "*.log" -size +$MAX_SIZE -exec truncate -s 0 {} \;

# Or use logrotate configuration
cat > /etc/logrotate.d/docker-containers << EOF
/var/lib/docker/containers/*/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    copytruncate
    size 100M
}
EOF
```

## 🆘 When All Else Fails

### Nuclear Option: Complete Reset
```bash
#!/bin/bash
# nuclear_reset.sh - USE WITH EXTREME CAUTION

echo "WARNING: This will destroy all data!"
read -p "Are you sure? Type 'YES' to continue: " confirm

if [ "$confirm" != "YES" ]; then
    echo "Aborted."
    exit 1
fi

# Backup first
mkdir -p /tmp/orchestration_backup
docker exec mcp-postgresql pg_dump -U mcp_admin mcp_unified > /tmp/orchestration_backup/database_backup.sql
cp -r /home/orchestration /tmp/orchestration_backup/

# Nuclear reset
cd /home/orchestration
docker-compose down -v
docker system prune -af
docker volume prune -f
docker network prune -f

# Rebuild everything
docker-compose build --no-cache
docker-compose up -d

# Wait for services
sleep 60

# Restore data if needed
# docker exec -i mcp-postgresql psql -U mcp_admin mcp_unified < /tmp/orchestration_backup/database_backup.sql

echo "Nuclear reset completed. Check service status:"
curl http://localhost:7000/health
```

### Emergency Contact Information
```
System Administrator: root@192.168.0.58
GitHub Repository: https://github.com/milhy545/orchestration/issues
Documentation: /home/orchestration/docs/
Emergency Procedures: This document - TROUBLESHOOTING.md
```

---

## 📞 Getting Help

1. **Check this troubleshooting guide first**
2. **Review service logs**: `docker-compose logs service-name`
3. **Test basic connectivity**: Use curl commands provided
4. **Check GitHub issues**: [orchestration/issues](https://github.com/milhy545/orchestration/issues)
5. **Emergency reset**: Use nuclear option as last resort

Remember: Most issues can be resolved with a service restart. Start simple before attempting complex solutions.
