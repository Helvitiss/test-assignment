from fastapi import APIRouter
from .departments import router as department_router


v1_router = APIRouter()


v1_router.include_router(department_router)


__all__ = ['v1_router']
