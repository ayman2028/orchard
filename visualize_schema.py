import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('scheduling.db')

# Get all table schemas
tables_info = {}
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [table[0] for table in cursor.fetchall()]

print("=== DATABASE SCHEMA VISUALIZATION ===\n")

for table in tables:
    if table == 'sqlite_sequence':
        continue
        
    print(f"📋 TABLE: {table.upper()}")
    print("─" * 40)
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        is_pk = "🔑 PK" if col[5] else ""
        not_null = "❗" if col[3] else ""
        print(f"  {col_name:<20} {col_type:<15} {is_pk} {not_null}")
    
    # Show record count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  📊 Records: {count}")
    
    print()

print("\n=== ENTITY RELATIONSHIPS ===")
print("""
Agent (1:1) AgentSettings
  │
  ├─ (1:N) Appointments  
  │
  └─ (1:N) CalendarEvents

Key: 🔑 = Primary Key, ❗ = Not Null
""")

conn.close()