# 🚀 Deployment Guide

## Production Deployment

### Prerequisites
- **Docker Engine**: 20.10+ 
- **Docker Compose**: 2.0+
- **Minimum RAM**: 4GB
- **Minimum Storage**: 10GB free
- **Network**: Internet access for initial setup

### Environment Setup

1. **Clone Repository**
```bash
git clone https://github.com/milhy545/orchestration.git
cd orchestration
```

2. **Configure Environment**
```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

3. **Required Environment Variables**
```bash
# Database Configuration
POSTGRES_DB=mcp_unified
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password_here

# Database URLs
MCP_DATABASE_URL=postgresql://your_db_user:your_secure_password_here@postgresql:5432/mcp_unified
DEFAULT_POSTGRES_URL=postgresql://your_db_user:your_secure_password_here@postgresql:5432/mcp_unified

# Redis
REDIS_URL=redis://redis:6379

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Service Configuration
MCP_SERVER_PORT=8000
QDRANT_URL=http://qdrant-vector:6333
```

### Production Deployment Steps

1. **Start Infrastructure Services First**
```bash
# Start databases first
docker-compose up -d postgresql redis qdrant-vector

# Wait for databases to be ready
./scripts/health-check.sh
```

2. **Start MCP Services**
```bash
# Start all MCP services
docker-compose up -d

# Verify all services are running
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

3. **Run Health Checks**
```bash
# Comprehensive health check
./scripts/health-check.sh

# Run integration tests
./tests/unit/orchestration_workflow_test.sh
```

### Production Configuration

#### Docker Compose Overrides
Create `docker-compose.prod.yml`:
```yaml
version: "3.8"

services:
  zen-coordinator:
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  postgresql:
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    volumes:
      - /opt/orchestration/data/postgresql:/var/lib/postgresql/data
      - /opt/orchestration/backups:/backups

  redis:
    restart: always
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'
```

#### Reverse Proxy Setup (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:7000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS Configuration

#### Using Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal crontab
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### Monitoring & Logging

#### Log Management
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/orchestration

/opt/orchestration/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

#### Health Monitoring Cron
```bash
# Add to crontab
*/5 * * * * /opt/orchestration/scripts/health-check.sh >> /var/log/orchestration-health.log 2>&1
```

### Backup Strategy

#### Database Backup
```bash
# Setup automated backup cron
0 2 * * * /opt/orchestration/scripts/backup-databases.sh
```

#### Volume Backup
```bash
#!/bin/bash
# backup-volumes.sh
BACKUP_DIR="/backup/orchestration/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup data volumes
tar -czf "$BACKUP_DIR/postgresql.tar.gz" -C /opt/orchestration/data postgresql/
tar -czf "$BACKUP_DIR/redis.tar.gz" -C /opt/orchestration/data redis/
tar -czf "$BACKUP_DIR/qdrant.tar.gz" -C /opt/orchestration/data qdrant/
```

### Security Hardening

#### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 7000/tcp  # Only allow via reverse proxy
ufw enable
```

#### Docker Security
```bash
# Run Docker rootless mode
systemctl --user enable docker
systemctl --user start docker

# Limit container capabilities
# Add to docker-compose.yml:
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - CHOWN
  - SETGID
  - SETUID
```

### Performance Optimization

#### PostgreSQL Tuning
```sql
-- /opt/orchestration/config/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
```

#### Redis Optimization
```bash
# /opt/orchestration/config/redis.conf
maxmemory 128mb
maxmemory-policy allkeys-lru
save 300 10
```

### Scaling Considerations

#### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: "3.8"

services:
  zen-coordinator:
    deploy:
      replicas: 3
    ports:
      - "7050-7052:8020"
```

#### Load Balancer (HAProxy)
```
backend orchestration
    balance roundrobin
    server coord1 localhost:7050 check
    server coord2 localhost:7051 check
    server coord3 localhost:7052 check
```

### Troubleshooting

#### Common Issues
```bash
# Check service logs
docker-compose logs zen-coordinator

# Database connection issues
docker exec -it mcp-postgresql psql -U $POSTGRES_USER -d $POSTGRES_DB

# Redis connection test
docker exec -it mcp-redis redis-cli ping

# Container resource usage
docker stats --no-stream
```

#### Recovery Procedures
```bash
# Service recovery
docker-compose restart <service-name>

# Database recovery from backup
./scripts/restore-database.sh /backup/path/backup.sql

# Full system restart
docker-compose down && docker-compose up -d
```

### Monitoring Endpoints

```bash
# Service health
curl http://localhost:7000/health

# System metrics
curl http://localhost:7000/metrics

# Database status
curl http://localhost:7000/status/database

# All services status
./scripts/monitor-services.sh
```

### Update Procedure

```bash
# 1. Backup current state
./scripts/backup-databases.sh

# 2. Pull latest code
git pull origin main

# 3. Update services
docker-compose pull
docker-compose up -d

# 4. Run health checks
./scripts/health-check.sh
```

This deployment guide ensures **high availability**, **security**, and **scalability** for production environments.
