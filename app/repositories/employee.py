from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmployeeModel


class EmployeeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_department(self, department_id: int, sorting: bool = True) -> list[EmployeeModel]:
        """
        Возвращает сотрудников подразделения.

        По умолчанию сортирует по created_at (ASC), затем по full_name (ASC).
        """

        stmt = (
            select(EmployeeModel)
            .where(EmployeeModel.department_id == department_id)

        )
        if sorting:
            stmt = stmt.order_by(EmployeeModel.created_at.asc(), EmployeeModel.full_name.asc())

        result = await self.db.scalars(stmt)
        return result.all()

    async def create(self,
                     *,
                     department_id: int,
                     full_name: str,
                     position: str,
                     hired_at: date | None
                     ) -> EmployeeModel:
        employee = EmployeeModel(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at
        )
        self.db.add(employee)
        await self.db.flush()
        return employee

    async def reassign_department(self, *, from_department_id: int, to_department_id: int) -> None:
        stmt = (
            update(EmployeeModel)
            .where(EmployeeModel.department_id == from_department_id)
            .values(department_id=to_department_id)
        )
        await self.db.execute(stmt)
        await self.db.flush()