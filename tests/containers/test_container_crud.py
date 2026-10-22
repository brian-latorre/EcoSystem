import uuid

BASE_URL = "/api/v1/containers/"

# Crear un payload de contenedor con valores predeterminados
def container_payload(
    code=None,
    latitude=-12.0365,
    longitude=-77.0241
):
    return {
        "code": code or f"TEST-{uuid.uuid4().hex[:12]}",
        "name": "Contenedor de prueba",
        "address": "Alameda de los Descalzos, Rímac",
        "latitude": latitude,
        "longitude": longitude,
        "capacity_kg": 150.0
    }

# Crear un payload de actualización con valores predeterminados
def update_payload(
    latitude=-12.0368,
    longitude=-77.0245
):
    return {
        "name": "Contenedor actualizado",
        "address": "Alameda de los Descalzos, Rímac",
        "latitude": latitude,
        "longitude": longitude,
        "capacity_kg": 200.0
    }

# TEST 1: Crear un contenedor válido - HTTP 201
def test_create_container_success(client):
    response = client.post(
        BASE_URL,
        json=container_payload()
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["status"] == "DISPONIBLE"
    assert data["capacity_kg"] == 150.0

# TEST 2: Listar contenedores - HTTP 200
def test_list_containers_success(client):
    client.post(
        BASE_URL,
        json=container_payload()
    )

    response = client.get(BASE_URL)

    assert response.status_code == 200
    assert len(response.json()) == 1

# TEST 3: Rechazar código duplicado - HTTP 409
def test_create_duplicate_code(client):
    payload = container_payload(
        code="TEST-DUPLICADO-01"
    )

    first_response = client.post(
        BASE_URL,
        json=payload
    )

    second_response = client.post(
        BASE_URL,
        json=payload
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

# TEST 4: Rechazar POST fuera del Rímac - HTTP 422
def test_create_outside_rimac(client):
    payload = container_payload(
        latitude=-12.1211,
        longitude=-77.0297
    )

    response = client.post(
        BASE_URL,
        json=payload
    )

    assert response.status_code == 422

# TEST 5: Actualizar contenedor válido - HTTP 200
def test_update_container_success(client):
    created = client.post(
        BASE_URL,
        json=container_payload()
    )

    assert created.status_code == 201
    container_id = created.json()["id"]

    response = client.put(
        f"{BASE_URL}{container_id}",
        json=update_payload()
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Contenedor actualizado"
    assert data["capacity_kg"] == 200.0
    assert data["latitude"] == -12.0368
    assert data["longitude"] == -77.0245


# TEST 6: Actualizar ID inexistente - HTTP 404
def test_update_container_not_found(client):
    response = client.put(
        f"{BASE_URL}999999",
        json=update_payload()
    )

    assert response.status_code == 404

# TEST 7: Rechazar PUT fuera del Rímac - HTTP 422 y sin modificar el registro
def test_update_outside_rimac(client):
    created = client.post(
        BASE_URL,
        json=container_payload()
    )

    assert created.status_code == 201
    container_id = created.json()["id"]

    response = client.put(
        f"{BASE_URL}{container_id}",
        json=update_payload(
            latitude=-12.1211,
            longitude=-77.0297
        )
    )

    assert response.status_code == 422

    # Verificar que el registro original siga intacto
    listing = client.get(BASE_URL)

    assert listing.status_code == 200

    container = next(
        item for item in listing.json()
        if item["id"] == container_id
    )

    assert container["latitude"] == -12.0365
    assert container["longitude"] == -77.0241
    assert container["capacity_kg"] == 150.0

# TEST 8: Desactivar contenedor - HTTP 204 y soft-delete
def test_soft_delete_container(client):
    created = client.post(
        BASE_URL,
        json=container_payload()
    )

    assert created.status_code == 201
    container_id = created.json()["id"]

    response = client.delete(
        f"{BASE_URL}{container_id}"
    )

    assert response.status_code == 204

    listing = client.get(BASE_URL)

    container = next(
        item for item in listing.json()
        if item["id"] == container_id
    )

    assert container["status"] == "INACTIVO"

# TEST 9: Repetir DELETE - HTTP 404
def test_soft_delete_twice(client):
    created = client.post(
        BASE_URL,
        json=container_payload()
    )

    assert created.status_code == 201
    container_id = created.json()["id"]

    first_response = client.delete(
        f"{BASE_URL}{container_id}"
    )

    second_response = client.delete(
        f"{BASE_URL}{container_id}"
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 404