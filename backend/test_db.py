import asyncio
from app.db import engine
from sqlalchemy import text

async def test_db():
    try:
        print("Intentando INSERT a DB con asyncpg...")
        async with engine.begin() as conn:
            await conn.execute(
                text("INSERT INTO tasks (title, status, priority, created_at, updated_at) VALUES ('test_script', 'PENDING', 'MEDIUM', NOW(), NOW())"), 
            )
            print('Insert exitoso a Neon DB')
    except Exception as e:
        print(f'=== Error de conexion / insert ===\n{type(e).__name__}: {e}')

asyncio.run(test_db())
