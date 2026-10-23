from sqlalchemy import text

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

# TEST 4: Respuesta GeoJSON válida
def test_nearby_geojson(client):

    container_id = crear_contenedor(
        client,
        "SPATIAL-GEOJSON-01",
        -12.0365,
        -77.0241
    )

    response = client.get(
        f"{BASE_URL}nearby/geojson",
        params={
            "lat": -12.0365,
            "lon": -77.0241,
            "radius_m": 500
        }
    )

    assert response.status_code == 200

    data = response.json()

    # Comprobar estructura GeoJSON
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)

    # Encontrar el contenedor de prueba
    feature = next(
        item for item in data["features"]
        if item["properties"]["id"] == container_id
    )

    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"

    # GeoJSON utiliza [longitud, latitud]
    assert feature["geometry"]["coordinates"] == [
        -77.0241,
        -12.0365
    ]

    assert (
        feature["properties"]["code"]
        == "SPATIAL-GEOJSON-01"
    )


# TEST 5: Precisión métrica de ST_DWithin
def test_nearby_metric_precision(client):

    # Contenedor de referencia
    container_id = crear_contenedor(
        client,
        "SPATIAL-METRIC-01",
        -12.0365,
        -77.0241
    )

    # A 100 metros debe encontrar el punto
    response_inside = client.get(
        f"{BASE_URL}nearby",
        params={
            "lat": -12.0365,
            "lon": -77.0241,
            "radius_m": 100
        }
    )

    assert response_inside.status_code == 200

    ids_inside = [
        item["id"] for item in response_inside.json()
    ]

    assert container_id in ids_inside

    # Buscar desde una ubicación alejada
    response_outside = client.get(
        f"{BASE_URL}nearby",
        params={
            "lat": -12.0459,
            "lon": -77.0305,
            "radius_m": 100
        }
    )

    assert response_outside.status_code == 200

    ids_outside = [
        item["id"] for item in response_outside.json()
    ]

    assert container_id not in ids_outside

# TEST 6: Precisión cerca del límite de 100 m
def test_nearby_radius_boundary_precision(client, db_engine):

    origin_lat = -12.0365
    origin_lon = -77.0241

    # Calcular coordenadas a 99 y 101 metros usando PostGIS
    with db_engine.connect() as conn:
        coords = conn.execute(
            text("""
                SELECT
                    ST_Y(p99::geometry),
                    ST_X(p99::geometry),
                    ST_Y(p101::geometry),
                    ST_X(p101::geometry)
                FROM (
                    SELECT
                        ST_Project(
                            ST_SetSRID(
                                ST_MakePoint(:lon, :lat),
                                4326
                            )::geography,
                            99,
                            0
                        ) AS p99,
                        ST_Project(
                            ST_SetSRID(
                                ST_MakePoint(:lon, :lat),
                                4326
                            )::geography,
                            101,
                            0
                        ) AS p101
                ) AS points
            """),
            {"lat": origin_lat, "lon": origin_lon}
        ).one()

    lat99, lon99, lat101, lon101 = coords

    id_inside = crear_contenedor(
        client, "SPATIAL-99M", lat99, lon99
    )

    id_outside = crear_contenedor(
        client, "SPATIAL-101M", lat101, lon101
    )

    response = client.get(
        f"{BASE_URL}nearby",
        params={
            "lat": origin_lat,
            "lon": origin_lon,
            "radius_m": 100
        }
    )

    assert response.status_code == 200

    ids = {
        item["id"] for item in response.json()
    }

    assert id_inside in ids
    assert id_outside not in ids