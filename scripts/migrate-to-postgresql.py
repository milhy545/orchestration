#\!/usr/bin/env python3
"""
Migration script: SQLite databases -> PostgreSQL
Migrates existing SQLite databases to unified PostgreSQL database
"""

import sqlite3
import psycopg2
import json
import os
from datetime import datetime

# Database configurations
SQLITE_DATABASES = {
    "cldmemory": "/home/orchestration/data/databases/cldmemory.db",
    "unified_memory": "/home/orchestration/data/databases/unified_memory_forai.db"
}

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mcp_unified",
    "user": "mcp_admin",
    "password": "mcp_secure_2024"
}

def create_postgres_tables():
    """Create unified tables in PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Unified memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unified_memory (
                id SERIAL PRIMARY KEY,
                source_db VARCHAR(50),
                content TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Index for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unified_memory_source 
            ON unified_memory(source_db);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unified_memory_metadata 
            ON unified_memory USING GIN(metadata);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL tables created successfully")
        
    except Exception as e:
        print(f"❌ Error creating PostgreSQL tables: {e}")

def migrate_sqlite_to_postgres():
    """Migrate data from SQLite databases to PostgreSQL"""
    try:
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        pg_cursor = pg_conn.cursor()
        
        total_migrated = 0
        
        for db_name, db_path in SQLITE_DATABASES.items():
            if not os.path.exists(db_path):
                print(f"⚠️  SQLite database not found: {db_path}")
                continue
            
            print(f"📂 Migrating {db_name} from {db_path}...")
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(db_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Get all tables
            sqlite_cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type=table AND name NOT LIKE sqlite_%
            """)
            tables = sqlite_cursor.fetchall()
            
            for (table_name,) in tables:
                print(f"  📋 Migrating table: {table_name}")
                
                # Get all data from table
                # lgtm[py/sql-injection] - Safe: table_name comes from sqlite_master, not user input
                sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                rows = sqlite_cursor.fetchall()

                # Get column names
                # lgtm[py/sql-injection] - Safe: table_name comes from sqlite_master, not user input
                sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in sqlite_cursor.fetchall()]
                
                # Migrate rows
                for row in rows:
                    # Prepare metadata
                    row_dict = dict(zip(columns, row))
                    metadata = {
                        "original_table": table_name,
                        "original_columns": columns,
                        "migrated_at": datetime.now().isoformat()
                    }
                    
                    # Convert row to text content
                    content = json.dumps(row_dict, default=str, indent=2)
                    
                    # Insert into PostgreSQL
                    pg_cursor.execute("""
                        INSERT INTO unified_memory (source_db, content, metadata)
                        VALUES (%s, %s, %s)
                    """, (f"{db_name}_{table_name}", content, json.dumps(metadata)))
                    
                    total_migrated += 1
                
                print(f"    ✅ Migrated {len(rows)} rows from {table_name}")
            
            sqlite_conn.close()
        
        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()
        
        print(f"🎉 Migration completed\! Total records migrated: {total_migrated}")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

def verify_migration():
    """Verify migration success"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT source_db, COUNT(*) FROM unified_memory GROUP BY source_db")
        results = cursor.fetchall()
        
        print("\n📊 Migration verification:")
        for source_db, count in results:
            print(f"  {source_db}: {count} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification error: {e}")

if __name__ == "__main__":
    print("🚀 Starting SQLite to PostgreSQL migration...")
    
    create_postgres_tables()
    migrate_sqlite_to_postgres()
    verify_migration()
    
    print("✅ Migration process completed\!")
