from sqlalchemy import select
from geoalchemy2.elements import WKTElement
from app.core.database import SessionLocal
from app.modules.containers.models import Container

# Datos de semilla para contenedores en RIMAC
RIMAC_SEED_CONTAINERS = [
    {
        "code": "CONT-RIMAC-01",
        "name": "Acopio Alameda de los Descalzos",
        "address": "Alameda de los Descalzos cdra. 1",
        "lat": -12.0365,
        "lon": -77.0241,
        "status": "LLENO",
        "reports": 3
    },
    {
        "code": "CONT-RIMAC-02",
        "name": "Punto Verde Jr. Trujillo",
        "address": "Jr. Trujillo cdra. 4",
        "lat": -12.0392,
        "lon": -77.0289,
        "status": "LLENO",
        "reports": 4
    },
    {
        "code": "CONT-RIMAC-03",
        "name": "Acopio Parque del Maestro",
        "address": "Av. Samuel Alcázar cdra. 6",
        "lat": -12.0271,
        "lon": -77.0315,
        "status": "LLENO",
        "reports": 3
    },
    {
        "code": "CONT-RIMAC-04",
        "name": "Contenedor Paseo de Aguas",
        "address": "Jr. Hualgayoc cdra. 3",
        "lat": -12.0348,
        "lon": -77.0232,
        "status": "DISPONIBLE",
        "reports": 1
    },
    {
        "code": "CONT-RIMAC-05",
        "name": "Punto Limpio Av. Tarapacá",
        "address": "Av. Tarapacá cdra. 8",
        "lat": -12.0294,
        "lon": -77.0342,
        "status": "DISPONIBLE",
        "reports": 0
    },
    {
        "code": "CONT-RIMAC-06",
        "name": "Acopio Caquetá - Próceres",
        "address": "Av. Caquetá cdra. 2",
        "lat": -12.0322,
        "lon": -77.0381,
        "status": "LLENO",
        "reports": 5
    }
]

# Función para ejecutar la semilla de contenedores en la base de datos
def run_seed():
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for item in RIMAC_SEED_CONTAINERS:
            existing = db.scalar(
                select(Container).where(
                    Container.code == item["code"]
                )
            )

            if existing:
                skipped += 1
                print(f"Omitido: {item['code']}")
                continue

            container = Container(
                code=item["code"],
                name=item["name"],
                address=item["address"],
                latitude=item["lat"],
                longitude=item["lon"],
                geom=WKTElement(
                    f"POINT({item['lon']} {item['lat']})",
                    srid=4326
                ),
                status=item["status"],
                current_reports_count=item["reports"],
                capacity_kg=150.0
            )

            db.add(container)
            created += 1

        db.commit()

        print(f"Contenedores creados: {created}")
        print(f"Contenedores existentes: {skipped}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    run_seed()