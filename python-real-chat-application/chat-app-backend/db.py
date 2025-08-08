import os
from typing import Optional
from datetime import datetime, timezone

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "root")
DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")
DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA", "real_chat")

_pool: Optional[asyncpg.Pool] = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS online_users (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    connected BOOLEAN NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL
);
"""


async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
            min_size=1,
            max_size=10,
        )
        # ensure table
        async with _pool.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)
    return _pool


async def close_db_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# helper db ops
async def set_user_connected(user_id, name, connected=True):
    pool = await init_db_pool()
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        # upsert
        await conn.execute(
            """
            INSERT INTO online_users (id, name, connected, last_seen)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                connected = EXCLUDED.connected,
                last_seen = EXCLUDED.last_seen
            """,
            user_id, name, connected, now
        )


async def set_user_disconnected(user_id):
    pool = await init_db_pool()
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE online_users
            SET connected = FALSE,
                last_seen = $2
            WHERE id = $1
            """,
            user_id, now
        )


async def get_online_users_from_db():
    pool = await init_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM public.online_users ORDER BY id ASC"
        )
        result = []
        for row in rows:
            row_dict = dict(row)
            row_dict["id"] = str(row_dict["id"])  # convert UUID → string
            result.append(row_dict)
        return result
