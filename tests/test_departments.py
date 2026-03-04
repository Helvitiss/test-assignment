import pytest


@pytest.mark.asyncio
async def test_create_department_success(client):
    response = await client.post("/departments/", json={"name": "Engineering"})

    assert response.status_code in {200, 201}
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Engineering"
    assert data["parent_id"] is None
    assert data["created_at"]


@pytest.mark.asyncio
async def test_create_department_duplicate_name_same_parent(client):
    first = await client.post("/departments/", json={"name": "Back Office"})
    assert first.status_code in {200, 201}

    second = await client.post("/departments/", json={"name": "Back Office"})
    assert second.status_code in {400, 409}


@pytest.mark.asyncio
async def test_get_department_with_depth(client):
    root = await client.post("/departments/", json={"name": "A"})
    root_id = root.json()["id"]

    child = await client.post("/departments/", json={"name": "B", "parent_id": root_id})
    child_id = child.json()["id"]

    await client.post("/departments/", json={"name": "C", "parent_id": child_id})

    depth_1 = await client.get(f"/departments/{root_id}", params={"depth": 1, "include_employees": False})
    assert depth_1.status_code == 200
    depth_1_data = depth_1.json()
    assert len(depth_1_data["children"]) == 1
    assert depth_1_data["children"][0]["department"]["name"] == "B"
    assert depth_1_data["children"][0]["children"] == []

    depth_2 = await client.get(f"/departments/{root_id}", params={"depth": 2, "include_employees": False})
    assert depth_2.status_code == 200
    depth_2_data = depth_2.json()
    assert len(depth_2_data["children"]) == 1
    assert len(depth_2_data["children"][0]["children"]) == 1
    assert depth_2_data["children"][0]["children"][0]["department"]["name"] == "C"


@pytest.mark.asyncio
async def test_prevent_cycle(client):
    dep_a = await client.post("/departments/", json={"name": "A"})
    dep_a_id = dep_a.json()["id"]

    dep_b = await client.post("/departments/", json={"name": "B", "parent_id": dep_a_id})
    dep_b_id = dep_b.json()["id"]

    dep_c = await client.post("/departments/", json={"name": "C", "parent_id": dep_b_id})
    dep_c_id = dep_c.json()["id"]

    cycle_attempt = await client.patch(f"/departments/{dep_a_id}", json={"parent_id": dep_c_id})
    assert cycle_attempt.status_code in {400, 409}


@pytest.mark.asyncio
async def test_delete_department_cascade(client):
    parent = await client.post("/departments/", json={"name": "Parent"})
    parent_id = parent.json()["id"]

    child = await client.post("/departments/", json={"name": "Child", "parent_id": parent_id})
    child_id = child.json()["id"]

    await client.post(
        f"/departments/{parent_id}/employees/",
        json={"full_name": "Alice Johnson", "position": "Lead"},
    )
    await client.post(
        f"/departments/{child_id}/employees/",
        json={"full_name": "Bob Smith", "position": "Engineer"},
    )

    delete_response = await client.delete(f"/departments/{parent_id}", params={"mode": "cascade"})
    assert delete_response.status_code == 204

    parent_after_delete = await client.get(f"/departments/{parent_id}")
    child_after_delete = await client.get(f"/departments/{child_id}")
    assert parent_after_delete.status_code == 404
    assert child_after_delete.status_code == 404


@pytest.mark.asyncio
async def test_delete_department_reassign(client):
    source = await client.post("/departments/", json={"name": "Source"})
    source_id = source.json()["id"]

    target = await client.post("/departments/", json={"name": "Target"})
    target_id = target.json()["id"]

    created_employee = await client.post(
        f"/departments/{source_id}/employees/",
        json={"full_name": "Jane Doe", "position": "Analyst"},
    )
    assert created_employee.status_code in {200, 201}

    delete_response = await client.delete(
        f"/departments/{source_id}",
        params={"mode": "reassign", "reassign_to_department_id": target_id},
    )
    assert delete_response.status_code == 204

    target_state = await client.get(f"/departments/{target_id}", params={"depth": 1, "include_employees": True})
    assert target_state.status_code == 200
    target_data = target_state.json()
    assert len(target_data["employees"]) == 1
    assert target_data["employees"][0]["full_name"] == "Jane Doe"
    assert target_data["employees"][0]["department_id"] == target_id

