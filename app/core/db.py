from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


DATABASE_URL = settings.DATABASE_URL



engine = create_async_engine(DATABASE_URL)



class Base(DeclarativeBase):
    pass



AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)