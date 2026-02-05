# Portainer Deployment Guide - Orchestration MCP Platform

## 🎯 Overview

This guide provides comprehensive instructions for deploying the Orchestration MCP Platform using Portainer. **Portainer Agent is MANDATORY** for this deployment to work properly.

### Prerequisites Checklist

- [ ] Portainer Server running and accessible
- [ ] **Portainer Agent installed** on target server (CRITICAL)
- [ ] Docker and Docker Compose available on target server
- [ ] Network connectivity between Portainer Server and Agent
- [ ] GitHub repository access (public or with authentication)
- [ ] API access token for Portainer

## 🔧 Phase 1: Portainer Agent Installation

### Step 1: Install Portainer Agent (MANDATORY)

**On the target server (192.168.0.58):**

```bash
# SSH to target server
ssh root@192.168.0.58

# Install Portainer Agent
docker run -d \
  --name portainer_agent \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/docker/volumes:/var/lib/docker/volumes \
  -p 9001:9001 \
  portainer/agent:latest

# Verify installation
docker ps | grep portainer_agent
```

**Expected Output:**
```
CONTAINER ID   IMAGE                    COMMAND        CREATED         STATUS         PORTS                    NAMES
a1b2c3d4e5f6   portainer/agent:latest   "./agent"      2 minutes ago   Up 2 minutes   0.0.0.0:9001->9001/tcp   portainer_agent
```

### Step 2: Verify Agent Connectivity

```bash
# Test agent health
curl http://localhost:9001/ping

# Expected response:
# {"status":"ok","agent_version":"2.19.1"}

# Test from external network (from Portainer server)
curl http://192.168.0.58:9001/ping
```

### Step 3: Check Network Requirements

```bash
# Verify port 9001 is open
netstat -tlnp | grep :9001

# Check firewall settings (if using UFW)
sudo ufw status
sudo ufw allow 9001  # If needed

# Test external connectivity
nmap -p 9001 192.168.0.58  # Run from Portainer server
```

### Troubleshooting Agent Installation

#### Issue: Agent not responding
```bash
# Check agent logs
docker logs portainer_agent

# Check Docker socket permissions
ls -la /var/run/docker.sock

# Fix permissions if needed
sudo chmod 666 /var/run/docker.sock

# Restart agent
docker restart portainer_agent
```

#### Issue: Port already in use
```bash
# Check what's using port 9001
netstat -tlnp | grep :9001

# Stop conflicting service or use different port
docker run -d \
  --name portainer_agent \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/docker/volumes:/var/lib/docker/volumes \
  -p 9002:9001 \
  portainer/agent:latest
```

## 🌐 Phase 2: Add Environment to Portainer

### Step 1: Add Environment via UI

1. **Login to Portainer UI**
2. **Navigate to Environments**:
   - Click "Environments" in left sidebar
   - Click "Add environment" button

3. **Select Environment Type**:
   - Choose "Docker"
   - Select "Agent" option

4. **Configure Environment**:
   ```
   Name: Orchestration-HAS
   Environment address: 192.168.0.58:9001
   TLS: Disabled (for internal network)
   ```

5. **Test Connection**:
   - Click "Connect"
   - Verify green status indicator

### Step 2: Add Environment via API

```bash
# Get Portainer API token first
export PORTAINER_URL="https://your-portainer-instance.com"
export PORTAINER_USER="admin"
export PORTAINER_PASS="your_password"

# Login and get JWT token
TOKEN=$(curl -s -X POST "$PORTAINER_URL/api/auth" \
  -H "Content-Type: application/json" \
  -d "{\"Username\":\"$PORTAINER_USER\",\"Password\":\"$PORTAINER_PASS\"}" | \
  jq -r '.jwt')

echo "Token: $TOKEN"

# Add environment
curl -X POST "$PORTAINER_URL/api/endpoints" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "Orchestration-HAS",
    "EndpointCreationType": 1,
    "URL": "192.168.0.58:9001",
    "GroupID": 1,
    "TLS": false,
    "Status": 1
  }'
```

### Step 3: Verify Environment

```bash
# List environments
curl -X GET "$PORTAINER_URL/api/endpoints" \
  -H "Authorization: Bearer $TOKEN" | jq

# Get specific environment details
ENDPOINT_ID=2  # Use the ID from the list response
curl -X GET "$PORTAINER_URL/api/endpoints/$ENDPOINT_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 📦 Phase 3: Prepare Stack Configuration

### Step 1: Create Stack Configuration File

Create `portainer_stack_config.json`:

```json
{
  "name": "orchestration-mcp",
  "swarmID": "",
  "endpointId": 2,
  "repositoryURL": "https://github.com/milhy545/orchestration",
  "repositoryReferenceName": "refs/heads/master",
  "repositoryAuthentication": false,
  "composeFile": "docker-compose.yml",
  "env": [
    {
      "name": "POSTGRES_PASSWORD",
      "value": "OrchestrationSecurePass2025!"
    },
    {
      "name": "REDIS_PASSWORD",
      "value": "RedisSecurePass2025!"
    },
    {
      "name": "QDRANT_API_KEY",
      "value": "QdrantSecureKey2025!"
    },
    {
      "name": "JWT_SECRET",
      "value": "JWTSecretKey2025!VerySecure"
    },
    {
      "name": "ENABLE_AUTH",
      "value": "true"
    },
    {
      "name": "API_RATE_LIMIT",
      "value": "100"
    },
    {
      "name": "CORS_ORIGINS",
      "value": "*"
    },
    {
      "name": "ZEN_COORDINATOR_HOST",
      "value": "0.0.0.0"
    },
    {
      "name": "ZEN_COORDINATOR_PORT",
      "value": "7000"
    }
  ]
}
```

### Step 2: Advanced Stack Configuration (Optional)

For production environments with additional security:

```json
{
  "name": "orchestration-mcp-production",
  "swarmID": "",
  "endpointId": 2,
  "repositoryURL": "https://github.com/milhy545/orchestration",
  "repositoryReferenceName": "refs/heads/master",
  "repositoryAuthentication": false,
  "composeFile": "docker-compose.yml",
  "env": [
    {
      "name": "POSTGRES_PASSWORD",
      "value": "{{POSTGRES_PASSWORD}}"
    },
    {
      "name": "REDIS_PASSWORD", 
      "value": "{{REDIS_PASSWORD}}"
    },
    {
      "name": "ANTHROPIC_API_KEY",
      "value": "{{ANTHROPIC_API_KEY}}"
    },
    {
      "name": "PERPLEXITY_API_KEY",
      "value": "{{PERPLEXITY_API_KEY}}"
    },
    {
      "name": "GEMINI_API_KEY",
      "value": "{{GEMINI_API_KEY}}"
    },
    {
      "name": "ENABLE_AUTH",
      "value": "true"
    },
    {
      "name": "JWT_SECRET",
      "value": "{{JWT_SECRET}}"
    },
    {
      "name": "API_RATE_LIMIT",
      "value": "50"
    },
    {
      "name": "CORS_ORIGINS",
      "value": "https://your-allowed-domain.com"
    }
  ]
}
```

## 🚀 Phase 4: Deploy Stack via Portainer

### Method 1: Deploy via Portainer UI

1. **Navigate to Stacks**:
   - Select your environment (Orchestration-HAS)
   - Click "Stacks" in left sidebar
   - Click "Add stack" button

2. **Configure Stack**:
   ```
   Name: orchestration-mcp
   Repository URL: https://github.com/milhy545/orchestration
   Reference: refs/heads/master
   Compose file: docker-compose.yml
   ```

3. **Set Environment Variables**:
   ```
   POSTGRES_PASSWORD=OrchestrationSecurePass2025!
   REDIS_PASSWORD=RedisSecurePass2025!
   QDRANT_API_KEY=QdrantSecureKey2025!
   JWT_SECRET=JWTSecretKey2025!VerySecure
   ENABLE_AUTH=true
   API_RATE_LIMIT=100
   ```

4. **Deploy Stack**:
   - Click "Deploy the stack"
   - Monitor deployment progress
   - Wait for all services to start

### Method 2: Deploy via API

```bash
# Set environment variables
export PORTAINER_URL="https://your-portainer-instance.com"
export PORTAINER_TOKEN="your_jwt_token_here"
export ENDPOINT_ID="2"

# Deploy stack
curl -X POST "$PORTAINER_URL/api/stacks" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d @portainer_stack_config.json

# Monitor deployment
STACK_ID=$(curl -s -X GET "$PORTAINER_URL/api/stacks" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" | \
  jq -r '.[] | select(.Name=="orchestration-mcp") | .Id')

echo "Stack ID: $STACK_ID"

# Check stack status
curl -X GET "$PORTAINER_URL/api/stacks/$STACK_ID" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" | jq
```

### Method 3: Automated Deployment Script

Create `deploy_to_portainer.sh`:

```bash
#!/bin/bash

# Configuration
PORTAINER_URL="${PORTAINER_URL:-https://your-portainer-instance.com}"
PORTAINER_USER="${PORTAINER_USER:-admin}"
PORTAINER_PASS="${PORTAINER_PASS:-your_password}"
ENDPOINT_ID="${ENDPOINT_ID:-2}"
STACK_NAME="orchestration-mcp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to get Portainer token
get_token() {
    log "Getting Portainer authentication token..."
    
    TOKEN=$(curl -s -X POST "$PORTAINER_URL/api/auth" \
        -H "Content-Type: application/json" \
        -d "{\"Username\":\"$PORTAINER_USER\",\"Password\":\"$PORTAINER_PASS\"}" | \
        jq -r '.jwt')
    
    if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
        error "Failed to get authentication token"
        exit 1
    fi
    
    log "Token obtained successfully"
    echo "$TOKEN"
}

# Function to check if stack exists
check_stack_exists() {
    local token="$1"
    local stack_name="$2"
    
    EXISTING_STACK=$(curl -s -X GET "$PORTAINER_URL/api/stacks" \
        -H "Authorization: Bearer $token" | \
        jq -r ".[] | select(.Name==\"$stack_name\") | .Id")
    
    echo "$EXISTING_STACK"
}

# Function to delete existing stack
delete_stack() {
    local token="$1"
    local stack_id="$2"
    
    log "Deleting existing stack with ID: $stack_id"
    
    curl -s -X DELETE "$PORTAINER_URL/api/stacks/$stack_id" \
        -H "Authorization: Bearer $token"
    
    log "Stack deleted, waiting for cleanup..."
    sleep 10
}

# Function to deploy stack
deploy_stack() {
    local token="$1"
    
    log "Deploying orchestration stack..."
    
    # Create stack configuration
    cat > /tmp/stack_config.json << EOF
{
  "name": "$STACK_NAME",
  "swarmID": "",
  "endpointId": $ENDPOINT_ID,
  "repositoryURL": "https://github.com/milhy545/orchestration",
  "repositoryReferenceName": "refs/heads/master",
  "repositoryAuthentication": false,
  "composeFile": "docker-compose.yml",
  "env": [
    {
      "name": "POSTGRES_PASSWORD",
      "value": "OrchestrationSecurePass2025!"
    },
    {
      "name": "REDIS_PASSWORD",
      "value": "RedisSecurePass2025!"
    },
    {
      "name": "QDRANT_API_KEY",
      "value": "QdrantSecureKey2025!"
    },
    {
      "name": "JWT_SECRET",
      "value": "JWTSecretKey2025!VerySecure"
    },
    {
      "name": "ENABLE_AUTH",
      "value": "true"
    },
    {
      "name": "API_RATE_LIMIT",
      "value": "100"
    },
    {
      "name": "ZEN_COORDINATOR_HOST",
      "value": "0.0.0.0"
    },
    {
      "name": "ZEN_COORDINATOR_PORT",
      "value": "7000"
    }
  ]
}
EOF

    # Deploy stack
    RESPONSE=$(curl -s -X POST "$PORTAINER_URL/api/stacks" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d @/tmp/stack_config.json)
    
    # Check for errors
    ERROR=$(echo "$RESPONSE" | jq -r '.message // empty')
    if [ ! -z "$ERROR" ]; then
        error "Deployment failed: $ERROR"
        exit 1
    fi
    
    STACK_ID=$(echo "$RESPONSE" | jq -r '.Id')
    log "Stack deployed successfully with ID: $STACK_ID"
    
    # Clean up
    rm -f /tmp/stack_config.json
    
    echo "$STACK_ID"
}

# Function to monitor stack deployment
monitor_deployment() {
    local token="$1"
    local stack_id="$2"
    
    log "Monitoring deployment progress..."
    
    for i in {1..30}; do
        STATUS=$(curl -s -X GET "$PORTAINER_URL/api/stacks/$stack_id" \
            -H "Authorization: Bearer $token" | \
            jq -r '.Status')
        
        log "Deployment status: $STATUS"
        
        if [ "$STATUS" = "1" ]; then
            log "Stack is running successfully!"
            break
        elif [ "$STATUS" = "2" ]; then
            error "Stack deployment failed!"
            exit 1
        fi
        
        sleep 10
    done
}

# Function to verify services
verify_services() {
    log "Verifying services are running..."
    
    # Wait a bit for services to start
    sleep 30
    
    # Check ZEN Coordinator
    if curl -s -f http://192.168.0.58:7000/health >/dev/null; then
        log "✅ ZEN Coordinator is healthy"
    else
        warn "⚠️ ZEN Coordinator not responding yet"
    fi
    
    # Check service list
    if curl -s -f http://192.168.0.58:7000/services >/dev/null; then
        log "✅ Services endpoint is responding"
        
        # Get service count
        SERVICE_COUNT=$(curl -s http://192.168.0.58:7000/services | jq -r '.total_services // 0')
        log "📊 Running services: $SERVICE_COUNT"
    else
        warn "⚠️ Services endpoint not responding yet"
    fi
}

# Main execution
main() {
    log "Starting Portainer deployment for Orchestration MCP Platform"
    
    # Get authentication token
    TOKEN=$(get_token)
    
    # Check if stack already exists
    EXISTING_STACK=$(check_stack_exists "$TOKEN" "$STACK_NAME")
    
    if [ ! -z "$EXISTING_STACK" ]; then
        warn "Stack '$STACK_NAME' already exists with ID: $EXISTING_STACK"
        read -p "Do you want to redeploy? (y/N): " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            delete_stack "$TOKEN" "$EXISTING_STACK"
        else
            log "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Deploy stack
    STACK_ID=$(deploy_stack "$TOKEN")
    
    # Monitor deployment
    monitor_deployment "$TOKEN" "$STACK_ID"
    
    # Verify services
    verify_services
    
    log "🎉 Deployment completed successfully!"
    log "🌐 ZEN Coordinator available at: http://192.168.0.58:7000"
    log "📋 Health check: curl http://192.168.0.58:7000/health"
    log "🔧 Services list: curl http://192.168.0.58:7000/services"
}

# Run main function
main "$@"
```

Make the script executable and run:

```bash
chmod +x deploy_to_portainer.sh

# Set environment variables
export PORTAINER_URL="https://your-portainer-instance.com"
export PORTAINER_USER="admin"  
export PORTAINER_PASS="your_password"
export ENDPOINT_ID="2"

# Run deployment
./deploy_to_portainer.sh
```

## 🔍 Phase 5: Post-Deployment Verification

### Step 1: Check Stack Status

```bash
# Via Portainer UI
# Navigate to Stacks → orchestration-mcp
# Verify all services show green status

# Via API
curl -X GET "$PORTAINER_URL/api/stacks/$STACK_ID" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" | jq '.Status'

# Status codes:
# 1 = Running
# 2 = Failed
```

### Step 2: Verify Service Health

```bash
# Check ZEN Coordinator
curl http://192.168.0.58:7000/health

# Expected response:
{
  "status": "ok",
  "timestamp": "2025-08-17T03:24:38.371865",
  "coordinator": "running",
  "services_count": 7,
  "tools_count": 28
}

# Check all services
curl http://192.168.0.58:7000/services

# Check available tools
curl http://192.168.0.58:7000/tools/list
```

### Step 3: Test MCP Functionality

```bash
# Test memory storage
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "content": "Portainer deployment test successful",
      "tags": ["portainer", "deployment", "test"]
    }
  }'

# Test file operations
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "system_info",
    "arguments": {
      "details": ["cpu", "memory"]
    }
  }'
```

### Step 4: Performance Verification

```bash
# Check container resources via Portainer UI
# Navigate to Containers → Select container → Stats

# Or via API
curl -X GET "$PORTAINER_URL/api/endpoints/$ENDPOINT_ID/docker/containers/json" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" | jq

# Check logs for any errors
curl -X GET "$PORTAINER_URL/api/endpoints/$ENDPOINT_ID/docker/containers/zen-coordinator/logs?stdout=true&stderr=true&tail=100" \
  -H "Authorization: Bearer $PORTAINER_TOKEN"
```

## 🛠️ Stack Management

### Update Stack

```bash
# Update stack via API
curl -X PUT "$PORTAINER_URL/api/stacks/$STACK_ID" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "env": [
      {
        "name": "API_RATE_LIMIT",
        "value": "200"
      }
    ],
    "prune": true
  }'
```

### Scale Services

```bash
# Scale specific service via Portainer UI
# Navigate to Services → Select service → Scale

# Or via API (for Docker Swarm mode)
curl -X POST "$PORTAINER_URL/api/endpoints/$ENDPOINT_ID/docker/services/$SERVICE_ID/update" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "Mode": {
      "Replicated": {
        "Replicas": 3
      }
    }
  }'
```

### Stack Logs

```bash
# View stack logs via UI
# Navigate to Stacks → orchestration-mcp → Logs

# Or via API for specific container
curl -X GET "$PORTAINER_URL/api/endpoints/$ENDPOINT_ID/docker/containers/$CONTAINER_ID/logs?stdout=true&stderr=true&tail=100&timestamps=true" \
  -H "Authorization: Bearer $PORTAINER_TOKEN"
```

### Delete Stack

```bash
# Delete stack (careful!)
curl -X DELETE "$PORTAINER_URL/api/stacks/$STACK_ID" \
  -H "Authorization: Bearer $PORTAINER_TOKEN"
```

## 🚨 Troubleshooting Portainer Deployment

### Issue: Agent Connection Failed

**Symptoms:**
- Cannot add environment to Portainer
- "Agent endpoint not available" error

**Solutions:**

1. **Verify Agent Installation:**
```bash
# On target server
docker ps | grep portainer_agent
curl http://localhost:9001/ping
```

2. **Check Network Connectivity:**
```bash
# From Portainer server
telnet 192.168.0.58 9001
nmap -p 9001 192.168.0.58
```

3. **Firewall Configuration:**
```bash
# On target server
sudo ufw allow 9001
sudo iptables -A INPUT -p tcp --dport 9001 -j ACCEPT
```

### Issue: Stack Deployment Failed

**Symptoms:**
- Stack status shows "Failed"
- Services not starting

**Solutions:**

1. **Check Stack Logs:**
```bash
# Via Portainer UI: Stacks → orchestration-mcp → Logs
# Look for specific error messages
```

2. **Verify Docker Compose File:**
```bash
# SSH to target server
ssh root@192.168.0.58
cd /tmp
git clone https://github.com/milhy545/orchestration.git
cd orchestration
docker-compose config  # Validate syntax
```

3. **Check Resource Availability:**
```bash
# Check disk space
df -h

# Check memory
free -h

# Check if ports are available
netstat -tlnp | grep -E ":(80[0-9][0-9]|6333)"
```

### Issue: Services Not Responding

**Symptoms:**
- ZEN Coordinator health check fails
- MCP tools return errors

**Solutions:**

1. **Check Service Status:**
```bash
# Via Portainer UI: Containers → Check status of each container

# Or via SSH
ssh root@192.168.0.58
cd /home/orchestration
docker-compose ps
```

2. **Review Service Logs:**
```bash
# Check coordinator logs
docker logs zen-coordinator --tail=50

# Check specific service logs
docker logs mcp-filesystem --tail=20
```

3. **Restart Services:**
```bash
# Restart specific service
docker-compose restart zen-coordinator

# Or restart entire stack via Portainer UI
```

### Issue: Environment Variables Not Applied

**Symptoms:**
- Services using default values instead of custom environment variables
- Authentication not working

**Solutions:**

1. **Verify Environment Variables:**
```bash
# Check container environment
docker exec zen-coordinator env | grep -E "(POSTGRES|REDIS|JWT)"
```

2. **Update Stack Configuration:**
```bash
# Via Portainer UI: Stacks → orchestration-mcp → Editor
# Modify environment variables and redeploy
```

3. **Check Variable Syntax:**
```json
// Correct format in Portainer stack config
"env": [
  {
    "name": "POSTGRES_PASSWORD",
    "value": "your_password"
  }
]
```

## 📈 Monitoring Portainer Deployment

### Automated Health Monitoring

Create `portainer_monitor.sh`:

```bash
#!/bin/bash

PORTAINER_URL="${PORTAINER_URL:-https://your-portainer-instance.com}"
PORTAINER_TOKEN="${PORTAINER_TOKEN:-your_token_here}"
ENDPOINT_ID="${ENDPOINT_ID:-2}"
STACK_NAME="orchestration-mcp"

# Get stack status
STACK_STATUS=$(curl -s -X GET "$PORTAINER_URL/api/stacks" \
  -H "Authorization: Bearer $PORTAINER_TOKEN" | \
  jq -r ".[] | select(.Name==\"$STACK_NAME\") | .Status")

echo "Stack Status: $STACK_STATUS"

# Check service health
SERVICE_HEALTH=$(curl -s http://192.168.0.58:7000/health | jq -r '.status')
echo "Service Health: $SERVICE_HEALTH"

# Alert if unhealthy
if [ "$STACK_STATUS" != "1" ] || [ "$SERVICE_HEALTH" != "ok" ]; then
    echo "ALERT: Orchestration platform is unhealthy!"
    # Send notification (email, Slack, etc.)
fi
```

### Performance Dashboard

Monitor key metrics via Portainer:

1. **Navigate to:** Environments → Orchestration-HAS → Containers
2. **Monitor:**
   - CPU usage per container
   - Memory consumption
   - Network I/O
   - Container restart count

3. **Set up alerts** for:
   - High CPU usage (>80%)
   - High memory usage (>90%)
   - Container restarts
   - Service downtime

---

## 🎉 Successful Deployment Checklist

- [ ] Portainer Agent installed and responding
- [ ] Environment added to Portainer successfully
- [ ] Stack deployed without errors
- [ ] All 28 MCP tools available via `/tools/list`
- [ ] ZEN Coordinator health check passes
- [ ] Sample MCP tool calls work correctly
- [ ] Performance metrics within acceptable ranges
- [ ] Monitoring and alerting configured

**Your Orchestration MCP Platform is now successfully deployed via Portainer!**

Access your platform at: `http://192.168.0.58:7000`