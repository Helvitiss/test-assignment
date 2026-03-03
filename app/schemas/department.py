from  datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.base import ORMModel


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None



class DepartmentResponse(ORMModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime


class DepartmentDetails(ORMModel):
    department: DepartmentResponse
    employees: list["EmployeeResponse"] | None = None
    children: list["DepartmentDetails"] = Field(default_factory=list)

from app.schemas.employee import EmployeeResponse  # noqa: E402

DepartmentDetails.model_rebuild()
