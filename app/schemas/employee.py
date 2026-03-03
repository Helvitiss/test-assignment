from app.schemas.base import ORMModel
from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    hired_at: date | None = None






class EmployeeResponse(ORMModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime
