from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.services.department import DepartmentService


async def get_async_db_session():
    async with AsyncSessionLocal() as db:
        yield db


def get_employee_repository(db: AsyncSession = Depends(get_async_db_session)) -> EmployeeRepository:
    return EmployeeRepository(db)


def get_department_repository(db: AsyncSession = Depends(get_async_db_session)) -> DepartmentRepository:
    return DepartmentRepository(db)


def get_department_service(
        db: AsyncSession = Depends(get_async_db_session),
        department_repository: DepartmentRepository = Depends(get_department_repository),
        employee_repository: EmployeeRepository = Depends(get_employee_repository),
) -> DepartmentService:
    return DepartmentService(db, department_repository, employee_repository)