from app.core.db import AsyncSessionLocal



async def get_async_db_session():
    async with AsyncSessionLocal() as db:
        yield db
