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
    
    # Simple table for generic memory migration
    cur.execute("""
        CREATE TABLE IF NOT EXISTS unified_memories (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def migrate_sqlite_file(sqlite_path):
    if not os.path.exists(sqlite_path):
        print(f"File not found: {sqlite_path}")
        return

    print(f"Migrating {sqlite_path}...")
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cur = pg_conn.cursor()
    
    sl_conn = sqlite3.connect(sqlite_path)
    sl_cur = sl_conn.cursor()
    
    try:
        sl_cur.execute("SELECT content, metadata, created_at FROM memories")
        rows = sl_cur.fetchall()
        
        execute_values(pg_cur, 
            "INSERT INTO unified_memories (content, metadata, created_at) VALUES %s",
            rows)
        
        pg_conn.commit()
        print(f"Successfully migrated {len(rows)} rows")
    except Exception as e:
        print(f"Error migrating {sqlite_path}: {e}")
    finally:
        sl_conn.close()
        pg_cur.close()
        pg_conn.close()

if __name__ == "__main__":
    create_postgres_tables()
    # Example usage:
    # migrate_sqlite_file("data/databases/cldmemory.db")
