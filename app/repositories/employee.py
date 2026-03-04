from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmployeeModel


class EmployeeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_departments(self, department_ids: set[int]) -> list[EmployeeModel]:
        if not department_ids:
            return []

        stmt = (
            select(EmployeeModel)
            .where(EmployeeModel.department_id.in_(department_ids))
            .order_by(EmployeeModel.department_id.asc(),
                      EmployeeModel.created_at.asc(),
                      EmployeeModel.full_name.asc()
                      )
        )

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

    async def reassign_department(self, *, from_department_ids: set[int], to_department_id: int) -> None:
        stmt = (
            update(EmployeeModel)
            .where(EmployeeModel.department_id.in_(from_department_ids))
            .values(department_id=to_department_id)
        )
        await self.db.execute(stmt)
