from utils.db import get_pool

async def save_role(guild_id, role_id):
    pool = get_pool()
    await pool.execute(
        'INSERT INTO guild_config (guild_id, role_id) '
        'VALUES ($1, $2) '
        'ON CONFLICT (guild_id) DO UPDATE SET role_id = EXCLUDED.role_id',
        guild_id, role_id,
    )

