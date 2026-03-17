#!/usr/bin/env python3
"""
Simple migration script: SQLite databases -> PostgreSQL
"""

import sqlite3
import psycopg2
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
    """Create unified tables in PostgreSQL"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unified_memory (
            id SERIAL PRIMARY KEY,
            source_db VARCHAR(50),
            content TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL tables created")

def migrate_database(db_name, db_path):
    """Migrate single SQLite database"""
    if not os.path.exists(db_path):
        print(f"⚠️ Database not found: {db_path}")
        return 0
    
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cursor = pg_conn.cursor()
    
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = sqlite_cursor.fetchall()
    
    total_records = 0
    for (table_name,) in tables:
        print(f"  📋 Migrating {table_name}")

        # Get data
        # lgtm[py/sql-injection] - Safe: table_name comes from sqlite_master, not user input
        sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = sqlite_cursor.fetchall()
        
        for row in rows:
            content = json.dumps(list(row), default=str)
            metadata = json.dumps({"table": table_name, "source": db_name})
            
            pg_cursor.execute("""
                INSERT INTO unified_memory (source_db, content, metadata)
                VALUES (%s, %s, %s)
            """, (f"{db_name}_{table_name}", content, metadata))
            total_records += 1
    
    pg_conn.commit()
    pg_cursor.close()
    pg_conn.close()
    sqlite_conn.close()
    
    return total_records

if __name__ == "__main__":
    print("🚀 Starting migration...")
    create_postgres_tables()
    
    total = 0
    total += migrate_database("cldmemory", "/home/orchestration/data/databases/cldmemory.db")
    total += migrate_database("unified_memory", "/home/orchestration/data/databases/unified_memory_forai.db")
    
    print(f"✅ Migration completed! Total: {total} records")