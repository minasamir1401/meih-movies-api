import asyncpg
import logging
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Movies Table
        await conn.execute("""
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
        await conn.execute("""
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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id SERIAL PRIMARY KEY,
                series_id TEXT,
                episode_number INTEGER,
                title TEXT,
                watch_link TEXT,
                FOREIGN KEY(series_id) REFERENCES series(id)
            )
        """)
    finally:
        await conn.close()

async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)
