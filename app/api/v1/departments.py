from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_department_service
from app.schemas.department import DepartmentResponse, DepartmentCreate, DepartmentDetails, DepartmentUpdate
from app.schemas.employee import EmployeeResponse, EmployeeCreate
from app.schemas.enums import DeleteMode
from app.services.department import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post('/', response_model=DepartmentResponse, status_code=201)
async def create_department(
        payload: DepartmentCreate,
        service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponse:
    department = await service.create_department(payload)
    return DepartmentResponse.model_validate(department)


@router.post('/{department_id}/employees', response_model=EmployeeResponse, status_code=201)
async def create_employee(
        department_id: int,
        payload: EmployeeCreate,
        service: DepartmentService = Depends(get_department_service),
) -> EmployeeResponse:
    employee = await service.create_employee(department_id, payload)
    return EmployeeResponse.model_validate(employee)


@router.get('/{department_id}', response_model=DepartmentDetails)
async def get_department(
        department_id: int,
        depth: int = Query(1, ge=1, le=5),
        include_employees: bool = Query(default=True),
        service: DepartmentService = Depends(get_department_service),
) -> DepartmentDetails:
    return await service.get_tree(department_id=department_id, depth=depth, include_employees=include_employees)


@router.patch('/{department_id}', response_model=DepartmentResponse)
async def update_department(
        department_id: int,
        payload: DepartmentUpdate,
        service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponse:
    department = await service.update_department(department_id, payload)
    return DepartmentResponse.model_validate(department)

@router.delete('/{department_id}', status_code=204)
async def delete_department(
        department_id: int,
        mode: DeleteMode,
        reassign_to_department_id: int | None = Query(None, description="department id"),
        service: DepartmentService = Depends(get_department_service)
):
    await service.delete_department(department_id=department_id, mode=mode,
                                    reassign_to_department_id=reassign_to_department_id)
