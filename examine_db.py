import sqlite3

# Connect to the database
conn = sqlite3.connect('scheduling.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables found:", [table[0] for table in tables])

# For each table, show its structure and sample data
for table in tables:
    table_name = table[0]
    print(f"\n=== {table_name} ===")
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get sample data (first 3 rows)
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    print("Sample data:")
    for row in rows:
        print(f"  {row}")

conn.close()