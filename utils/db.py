import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

_pool = None

async def init_pool():
    global _pool
    if _pool:
        return
    _pool = await asyncpg.create_pool(DATABASE_URL)

def get_pool():
    if _pool is None:
        raise RuntimeError("init_pool() was not called")
    return _pool

async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

