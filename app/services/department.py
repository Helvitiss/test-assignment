from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from collections import deque

from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate,DepartmentDetails
from app.models import DepartmentModel, EmployeeModel
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.schemas.enums import DeleteMode



class DepartmentService:
    def __init__(self, db: AsyncSession, department_repo: DepartmentRepository, employee_repo: EmployeeRepository):
        self.db = db
        self.department_repo = department_repo
        self.employee_repo = employee_repo

    async def create_department(self, payload: DepartmentCreate) -> DepartmentModel:
        if payload.parent_id is not None and await self.department_repo.get(payload.parent_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent department not found")
        if await self.department_repo.is_name_taken_in_parent(parent_id=payload.parent_id, name=payload.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name must be unique in parent")

        try:
            department = await self.department_repo.create(name=payload.name, parent_id=payload.parent_id)
            await self.db.commit()
            return department
        except Exception:
            await self.db.rollback()
            raise

    async def create_employee(self, department_id: int, payload: EmployeeCreate) -> EmployeeModel:
        if await self.department_repo.get(department_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        try:
            employee = await self.employee_repo.create(
                department_id=department_id,
                full_name=payload.full_name,
                position=payload.position,
                hired_at=payload.hired_at
            )
            await self.db.commit()
            return employee
        except Exception:
            await self.db.rollback()
            raise

    async def get_tree(self, department_id: int, depth: int, include_employees: bool) -> DepartmentDetails:
        if depth < 1 or depth > 5:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="depth should be between 1 and 5")

        department = await self.department_repo.get(department_id)
        if department is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        return await self._build_node(department, depth, include_employees)


    async def _build_node(self, department: DepartmentModel, depth: int, include_employees: bool) -> DepartmentDetails:
        employee_models = await self.employee_repo.list_for_department(
            department_id=department.id) if include_employees else []
        employees = [EmployeeResponse.model_validate(employee) for employee in employee_models]
        children_payload: list[DepartmentDetails] = []
        if depth > 0:
            children = await self.department_repo.get_children(department_id=department.id)
            for child in children:
                children_payload.append(await self._build_node(child, depth - 1, include_employees))

        return DepartmentDetails(
            department=DepartmentResponse.model_validate(department),
            employees=employees,
            children=children_payload
        )



    async def update_department(
            self,
            department_id: int,
            payload: DepartmentUpdate
    ) -> DepartmentModel:

        department = await self.department_repo.get(department_id)
        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return department

        new_name = update_data.get("name", department.name)
        new_parent = update_data.get("parent_id", department.parent_id)

        if "parent_id" in update_data:

            if new_parent == department.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department cannot be parent of itself"
                )

            if new_parent is not None:

                parent = await self.department_repo.get(new_parent)
                if parent is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Department not found"
                    )

                if await self._is_descendant(
                        candidate_parent_id=new_parent,
                        source_department_id=department.id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Cannot move department into its subtree"
                    )

        if "name" in update_data or "parent_id" in update_data:
            if await self.department_repo.is_name_taken_in_parent(
                    parent_id=new_parent,
                    name=new_name,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Department name must be unique in parent"
                )

        try:
            department.name = new_name
            department.parent_id = new_parent

            await self.db.commit()
            await self.db.refresh(department)

            return department

        except Exception:
            await self.db.rollback()
            raise

    async def delete_department(
            self,
            department_id: int,
            mode: DeleteMode,
            reassign_to_department_id: int | None
    ) -> None:

        department = await self.department_repo.get(department_id)
        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )

        if mode is DeleteMode.cascade:
            try:
                await self.department_repo.delete(department)
                await self.db.commit()
                return
            except Exception:
                await self.db.rollback()
                raise

        if reassign_to_department_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reassign_to_department_id is required"
            )

        if reassign_to_department_id == department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reassign to deleted department"
            )

        target = await self.department_repo.get(reassign_to_department_id)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )

        descendants = await self._collect_descendant_ids(department_id)
        if reassign_to_department_id in descendants:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot reassign into deleted subtree"
            )

        try:
            await self.employee_repo.reassign_department(
                from_department_id=department_id,
                to_department_id=target.id
            )

            await self.department_repo.new_parent_for_children(
                from_department_id=department_id,
                new_parent_id=department.parent_id
            )

            await self.department_repo.delete(department)

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise


    async def _collect_descendant_ids(self, department_id: int) -> set[int]:
        collected: set[int] = set()
        queue: deque[int] = deque([department_id])

        while queue:
            current = queue.popleft()

            children = await self.department_repo.get_children(current)

            for child in children:
                if child.id in collected:
                    continue

                collected.add(child.id)
                queue.append(child.id)

        return collected

    async def _is_descendant(self, candidate_parent_id: int, source_department_id: int) -> bool:
        return candidate_parent_id in await self._collect_descendant_ids(source_department_id)
