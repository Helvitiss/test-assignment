import pytest


@pytest.mark.asyncio
async def test_create_employee_success(client):
    department = await client.post("/departments/", json={"name": "People Ops"})
    department_id = department.json()["id"]

    response = await client.post(
        f"/departments/{department_id}/employees/",
        json={"full_name": "John Doe", "position": "HR Manager"},
    )

    assert response.status_code in {200, 201}
    data = response.json()
    assert data["id"] > 0
    assert data["department_id"] == department_id
    assert data["full_name"] == "John Doe"
    assert data["position"] == "HR Manager"


@pytest.mark.asyncio
async def test_create_employee_invalid_department(client):
    response = await client.post(
        "/departments/999999/employees/",
        json={"full_name": "Ghost Person", "position": "Unknown"},
    )

    assert response.status_code == 404
