#!/usr/bin/env python3
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json
import os
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database configurations
SQLITE_DATABASES = {
    "cldmemory": os.getenv("SQLITE_CLDMEMORY_PATH", "/home/orchestration/data/databases/cldmemory.db"),
    "unified_memory": os.getenv("SQLITE_UNIFIED_MEMORY_PATH", "/home/orchestration/data/databases/unified_memory_forai.db")
}

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "mcp_unified"),
    "user": os.getenv("POSTGRES_USER", "mcp_admin"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

def create_postgres_tables():
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()
    
    # Unified memory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            category VARCHAR(100),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT__TIMESTAMP
        )
    """)
    
    # CLD memory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cld_memories (
            id SERIAL PRIMARY KEY,
            memory_key VARCHAR(255) UNIQUE,
            memory_value TEXT,
            tags TEXT[],
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def migrate_data():
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cur = pg_conn.cursor()

    # Migrate Unified Memory
    if os.path.exists(SQLITE_DATABASES["unified_memory"]):
        sl_conn = sqlite3.connect(SQLITE_DATABASES["unified_memory"])
        sl_cur = sl_conn.cursor()
        
        sl_cur.execute("SELECT content, category, metadata, created_at FROM memories")
        rows = sl_cur.fetchall()
        
        execute_values(pg_cur, 
            "INSERT INTO memories (content, category, metadata, created_at) VALUES %s",
            rows)
        
        print(f"Migrated {len(rows)} memories from unified_memory")
        sl_conn.close()

    # Migrate CLD Memory
    if os.path.exists(SQLITE_DATABASES["cldmemory"]):
        sl_conn = sqlite3.connect(SQLITE_DATABASES["cldmemory"])
        sl_cur = sl_conn.cursor()
        
        sl_cur.execute("SELECT memory_key, memory_value, tags, last_accessed FROM memories")
        rows = sl_cur.fetchall()
        
        # Convert tags string to list
        processed_rows = []
        for r in rows:
            tags = r[2].split(',') if r[2] else []
            processed_rows.append((r[0], r[1], tags, r[3]))

        execute_values(pg_cur,
            "INSERT INTO cld_memories (memory_key, memory_value, tags, last_accessed) VALUES %s ON CONFLICT (memory_key) DO NOTHING",
            processed_rows)
            
        print(f"Migrated {len(rows)} memories from cldmemory")
        sl_conn.close()

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

if __name__ == "__main__":
    print("Starting migration...")
    try:
        create_postgres_tables()
        migrate_data()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
