from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DepartmentModel


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, department_id: int) -> DepartmentModel | None:
        return await self.db.get(DepartmentModel, department_id)

    async def get_children(self, department_id: int) -> list[DepartmentModel]:
        stmt = (select(DepartmentModel)
                .where(DepartmentModel.parent_id == department_id)
                .order_by(DepartmentModel.id))

        result = await self.db.scalars(stmt)
        return result.all()

    async def get_children_for_parents(self, parent_ids: set[int]) -> list[DepartmentModel]:
        if not parent_ids:
            return []

        stmt = (
            select(DepartmentModel)
            .where(DepartmentModel.parent_id.in_(parent_ids))
            .order_by(DepartmentModel.parent_id.asc(), DepartmentModel.id.asc())
        )
        result = await self.db.scalars(stmt)
        return result.all()

    async def is_name_taken_in_parent(self, *, parent_id: int | None, name: str, exclude_id: int | None = None) -> bool:
        stmt = select(DepartmentModel.id).where(
            DepartmentModel.name == name,
        )
        if exclude_id is not None:
            stmt = stmt.where(DepartmentModel.id != exclude_id)


        if parent_id is None:
            stmt = stmt.where(DepartmentModel.parent_id.is_(None))
        else:
            stmt = stmt.where(DepartmentModel.parent_id == parent_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, *, name: str, parent_id: int | None) -> DepartmentModel:
        department = DepartmentModel(name=name, parent_id=parent_id)
        self.db.add(department)
        await self.db.flush()
        return department

    async def new_parent_for_children(self, *, from_department_id: int, new_parent_id: int | None) -> None:
        children = await self.get_children(from_department_id)
        for child in children:
            child.parent_id = new_parent_id
        await self.db.flush()

    async def delete(self, department: DepartmentModel) -> None:
        await self.db.delete(department)
        await self.db.flush()
