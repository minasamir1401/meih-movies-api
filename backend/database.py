import aiosqlite
import logging

DB_NAME = "netflix_clone.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Movies Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id TEXT PRIMARY KEY,
                title TEXT,
                poster TEXT,
                year TEXT,
                rating TEXT,
                description TEXT,
                category TEXT
            )
        """)
        # Series Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS series (
                id TEXT PRIMARY KEY,
                title TEXT,
                poster TEXT,
                year TEXT,
                rating TEXT,
                description TEXT,
                category TEXT
            )
        """)
        # Episodes Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT,
                episode_number INTEGER,
                title TEXT,
                watch_link TEXT,
                FOREIGN KEY(series_id) REFERENCES series(id)
            )
        """)
        await db.commit()

async def get_db_connection():
    db = await aiosqlite.connect(DB_NAME)
    db.row_factory = aiosqlite.Row
    return db
