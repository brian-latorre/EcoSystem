BASE_URL = "/api/v1/containers/"

# Crear un contenedor espacial para pruebas
def crear_contenedor(client, codigo, lat, lon):
    response = client.post(
        BASE_URL,
        json={
            "code": codigo,
            "name": "Contenedor espacial de prueba",
            "address": "Rímac, Lima",
            "latitude": lat,
            "longitude": lon,
            "capacity_kg": 150.0
        }
    )
    assert response.status_code == 201
    return response.json()["id"]


# TEST 1: Un contenedor cercano aparece en la búsqueda
def test_nearby_container(client):
    container_id = crear_contenedor(
        client, "SPATIAL-01", -12.0365, -77.0241
    )

    response = client.get(
        f"{BASE_URL}nearby",
        params={
            "lat": -12.0365,
            "lon": -77.0241,
            "radius_m": 500
        }
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert container_id in ids


# TEST 2: Un contenedor fuera del radio no aparece
def test_container_outside_radius(client):
    container_id = crear_contenedor(
        client, "SPATIAL-02", -12.0365, -77.0241
    )

    response = client.get(
        f"{BASE_URL}nearby",
        params={
            "lat": -12.1211,
            "lon": -77.0297,
            "radius_m": 500
        }
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert container_id not in ids


# TEST 3: Los contenedores inactivos no aparecen
def test_inactive_container_not_nearby(client):
    container_id = crear_contenedor(
        client, "SPATIAL-03", -12.0365, -77.0241
    )

    delete_response = client.delete(
        f"{BASE_URL}{container_id}"
    )
    assert delete_response.status_code == 204

    response = client.get(
        f"{BASE_URL}nearby",
        params={
            "lat": -12.0365,
            "lon": -77.0241,
            "radius_m": 500
        }
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert container_id not in ids
