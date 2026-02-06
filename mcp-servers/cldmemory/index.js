const fastify = require("fastify")({ logger: true });
const rateLimit = require("@fastify/rate-limit");
const { Client } = require("pg");
const Redis = require("ioredis");

// Configuration
const config = {
  port: process.env.MCP_SERVER_PORT || 8000,
  postgres: {
    connectionString: process.env.MCP_DATABASE_URL || "postgresql://mcp_admin:mcp_secure_2024@postgresql:5432/mcp_unified"
  },
  redis: {
    url: process.env.REDIS_URL || "redis://redis:6379"
  }
};

// Global rate limiting
fastify.register(rateLimit, {
  max: 60,
  timeWindow: "1 minute"
});

// Initialize clients
let pgClient, redisClient;

// Initialize database schema
async function initializeDatabase() {
  try {
    await pgClient.query(`
      CREATE TABLE IF NOT EXISTS cldmemory_records (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        content TEXT NOT NULL,
        metadata JSONB DEFAULT '{}',
        importance FLOAT DEFAULT 0.5,
        created_at TIMESTAMP DEFAULT NOW()
      );
    `);
    
    await pgClient.query(`
      CREATE INDEX IF NOT EXISTS idx_cldmemory_importance 
      ON cldmemory_records(importance);
    `);
    
    console.log("✅ PostgreSQL schema initialized for CLDMEMORY");
  } catch (error) {
    console.error("❌ Database initialization failed:", error);
  }
}

// Store memory
async function storeMemory(content, metadata = {}, importance = 0.5) {
  try {
    const result = await pgClient.query(`
      INSERT INTO cldmemory_records (content, metadata, importance)
      VALUES ($1, $2, $3)
      RETURNING id, created_at
    `, [content, JSON.stringify(metadata), importance]);
    
    const record = result.rows[0];
    
    // Cache recent record
    await redisClient.setex(`memory:${record.id}`, 3600, JSON.stringify({
      id: record.id,
      content,
      metadata,
      importance
    }));
    
    return {
      success: true,
      id: record.id,
      created_at: record.created_at,
      message: "Memory stored successfully"
    };
    
  } catch (error) {
    console.error("Store memory error:", error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Search memories
async function searchMemories(query, limit = 10) {
  try {
    const results = await pgClient.query(`
      SELECT id, content, metadata, importance, created_at
      FROM cldmemory_records
      WHERE content ILIKE $1
      ORDER BY importance DESC, created_at DESC
      LIMIT $2
    `, [`%${query}%`, limit]);
    
    return {
      success: true,
      results: results.rows,
      total_found: results.rows.length,
      source: "postgresql_search"
    };
    
  } catch (error) {
    console.error("Search memories error:", error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Get memory statistics
async function getMemoryStats() {
  try {
    const stats = await pgClient.query(`
      SELECT 
        COUNT(*) as total_memories,
        AVG(importance) as avg_importance,
        MAX(created_at) as latest_memory,
        MIN(created_at) as oldest_memory
      FROM cldmemory_records
    `);
    
    return {
      success: true,
      postgresql: stats.rows[0]
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Health check endpoint
fastify.get("/health", async (request, reply) => {
  const health = {
    status: "healthy",
    service: "CLDMEMORY MCP (PostgreSQL)",
    port: config.port,
    timestamp: new Date().toISOString(),
    components: {}
  };
  
  // Test PostgreSQL
  try {
    await pgClient.query("SELECT 1");
    health.components.postgresql = "healthy";
  } catch (error) {
    health.components.postgresql = "unhealthy: " + error.message;
    health.status = "degraded";
  }
  
  // Test Redis
  try {
    await redisClient.ping();
    health.components.redis = "healthy";
  } catch (error) {
    health.components.redis = "unhealthy: " + error.message;
    health.status = "degraded";
  }
  
  return health;
});

// MCP endpoints
fastify.post("/mcp", async (request, reply) => {
  const { jsonrpc, id, method, params } = request.body;
  
  try {
    let result;
    
    switch (method) {
      case "tools/list":
        result = {
          tools: [
            {
              name: "store_memory",
              description: "Store content in advanced memory system with PostgreSQL"
            },
            {
              name: "search_memories", 
              description: "Search through stored memories"
            },
            {
              name: "get_context",
              description: "Retrieve contextual memories for given topic"
            },
            {
              name: "memory_stats",
              description: "Get statistics about the memory system"
            }
          ]
        };
        break;
        
      case "tools/call":
        const toolName = params.name;
        const toolArgs = params.arguments || {};
        
        switch (toolName) {
          case "store_memory":
            result = await storeMemory(
              toolArgs.content,
              toolArgs.metadata || {},
              toolArgs.importance || 0.5
            );
            break;
            
          case "search_memories":
            result = await searchMemories(
              toolArgs.query,
              toolArgs.limit || 10
            );
            break;
            
          case "get_context":
            result = await searchMemories(
              toolArgs.topic,
              5 // Limit for context
            );
            break;
            
          case "memory_stats":
            result = await getMemoryStats();
            break;
            
          default:
            throw new Error(`Unknown tool: ${toolName}`);
        }
        break;
        
      default:
        throw new Error(`Unknown method: ${method}`);
    }
    
    return {
      jsonrpc: "2.0",
      id,
      result: {
        content: [{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }]
      }
    };
    
  } catch (error) {
    return {
      jsonrpc: "2.0",
      id,
      error: {
        code: -1,
        message: error.message
      }
    };
  }
});

// Initialize and start server
async function start() {
  try {
    // Initialize clients
    pgClient = new Client(config.postgres);
    await pgClient.connect();
    console.log("✅ Connected to PostgreSQL");
    
    redisClient = new Redis(config.redis.url);
    console.log("✅ Connected to Redis");
    
    // Initialize database
    await initializeDatabase();
    
    // Start server
    await fastify.listen({
      port: config.port,
      host: "0.0.0.0"
    });
    
    console.log(`🚀 CLDMEMORY MCP Server running on port ${config.port}`);
    console.log("📊 Features: PostgreSQL + Redis");
    
  } catch (error) {
    console.error("❌ Server startup failed:", error);
    process.exit(1);
  }
}

start();
