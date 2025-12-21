import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def test_conn():
    url = os.getenv("DATABASE_URL")
    if not url or "your_supabase" in url:
        print("Error: DATABASE_URL not set correctly in .env file.")
        return
    
    try:
        conn = await asyncpg.connect(url)
        print("Connected to Supabase!")
        
        # Test table creation
        print("Testing table creation...")
        from database import init_db
        await init_db()
        print("Database initialized successfully!")
        
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
