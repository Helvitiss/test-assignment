from app.core.db import AsyncSessionLocal





def get_async_session():
    with AsyncSessionLocal as db:
        yield db
