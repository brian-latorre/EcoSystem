import json
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine

ROOT = Path(__file__).resolve().parents[1]
GEOJSON_PATH = ROOT / "data" / "geo" / "rimac.geojson"

# Cargar el límite distrital del Rímac desde un archivo GeoJSON
def load_rimac_boundary():
    # Leer el archivo GeoJSON
    with open(GEOJSON_PATH, "r", encoding="utf-8-sig") as file:
        data = json.load(file)

    features = data.get("features", [])

    if len(features) != 1:
        raise ValueError(
            "El GeoJSON debe contener exactamente un distrito."
        )

    feature = features[0]
    properties = feature["properties"]

    # Verificar que corresponda al Rímac
    if (
        properties.get("IDDIST") != "150128"
        or properties.get("NOMBDIST", "").upper() != "RIMAC"
    ):
        raise ValueError(
            "El archivo no corresponde al distrito del Rímac."
        )

    geometry = feature["geometry"]

    # Verificar que la geometría esté presente
    if geometry is None:
        raise ValueError("El distrito no tiene geometría.")

    geometry_json = json.dumps(geometry)

    # Insertar o actualizar el límite distrital
    query = text("""
        INSERT INTO district_boundaries (
            ubigeo,
            name,
            geom
        )
        VALUES (
            :ubigeo,
            :name,
            ST_Multi(
                ST_SetSRID(
                    ST_GeomFromGeoJSON(:geometry),
                    4326
                )
            )
        )
        ON CONFLICT (ubigeo)
        DO UPDATE SET
            name = EXCLUDED.name,
            geom = EXCLUDED.geom
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "ubigeo": "150128",
                "name": "RIMAC",
                "geometry": geometry_json
            }
        )

    print("Límite distrital del Rímac cargado correctamente.")

if __name__ == "__main__":
    load_rimac_boundary()
