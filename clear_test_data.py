import sqlite3
import os

def clear_db():
    db_path = 'netflix_clone.db'
    if not os.path.exists(db_path):
        print(f"File {db_path} not found.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                print(f"Clearing table: {table_name}")
                cursor.execute(f"DELETE FROM {table_name}")
        
        conn.commit()
        conn.close()
        print("✅ Database cleared successfully.")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

if __name__ == "__main__":
    clear_db()
