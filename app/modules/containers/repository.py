from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from app.modules.containers.models import (Container, DistrictBoundary)
from app.modules.containers.schemas import (ContainerCreate ,ContainerUpdate )
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


class ContainerRepository:

    # Inicializar el repositorio con la sesión de base de datos
    def __init__(self, db: Session):
        self.db = db

    # Ubicación dentro del Rímac
    def is_within_rimac(self, 
        latitude: float,
        longitude: float ) -> bool:

        point = func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude), 4326
        )

        stmt = (
            select(
                func.ST_Covers(DistrictBoundary.geom, point)
            )
            .where(DistrictBoundary.ubigeo == "150128")
        )

        result = self.db.scalar(stmt)

        if result is None:
            raise RuntimeError(
                "No se encontró el límite distrital del Rímac."
            )

        return bool(result)


    # Crear un nuevo contenedor
    def create(self, payload: ContainerCreate) -> Container:

        # Validar que las coordenadas estén dentro del distrito del Rímac
        if not self.is_within_rimac(
            payload.latitude,
            payload.longitude
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "El contenedor debe ubicarse dentro "
                    "del distrito del Rímac"
                )
            )

        # Formato WKT para la ubicación geográfica del contenedor
        wkt_point = WKTElement(
            f"POINT({payload.longitude} {payload.latitude})",
            srid=4326
        )

        # Crear la entidad del contenedor con los datos proporcionados
        entity = Container(
            code=payload.code,
            name=payload.name,
            address=payload.address,
            latitude=payload.latitude,
            longitude=payload.longitude,
            geom=wkt_point,
            status="DISPONIBLE",
            current_reports_count=0,
            capacity_kg=payload.capacity_kg
        )

        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El código del contenedor ya está registrado"
            )
        
        return entity
    
    # Listar todos los contenedores
    def list_all(self) -> List[Container]:

        stmt = select(Container).order_by(Container.id)

        return list(self.db.scalars(stmt).all())

    # Buscar contenedores cercanos a una ubicación geográfica
    def find_nearby(self,
        lat: float,
        lon: float,
        radius_m: float = 2500.0) -> List[Container]:

        ref_point = func.ST_SetSRID(
            func.ST_MakePoint(lon, lat),
            4326
        )

        stmt = select(Container).where(
            Container.status != "INACTIVO",
            func.ST_DWithin(
                Container.geom,
                ref_point,
                radius_m
            )
        )

        return list(self.db.scalars(stmt).all())

    # Actualizar un contenedor existente
    def update(self,
        container_id: int,
        payload: ContainerUpdate ) -> Container | None:

        # Buscar el contenedor
        container = self.db.get(Container, container_id)

        if container is None or container.status == "INACTIVO":
            return None

        # Validar la ubicación geográfica
        if not self.is_within_rimac(
            payload.latitude,
            payload.longitude
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Las nuevas coordenadas deben estar "
                    "dentro del distrito del Rímac"
                )
            )

        # Actualizar los datos del contenedor
        container.name = payload.name
        container.address = payload.address
        container.latitude = payload.latitude
        container.longitude = payload.longitude
        container.capacity_kg = payload.capacity_kg

        # Sincronizar las coordenadas con PostGIS
        container.geom = WKTElement(
            f"POINT({payload.longitude} {payload.latitude})",
            srid=4326
        )

        # Guardar los cambios
        try:
            self.db.commit()
            self.db.refresh(container)

        except Exception:
            self.db.rollback()
            raise

        return container

    # Desactivar un contenedor
    def soft_delete(self, container_id: int) -> bool:

        container = self.db.get(Container, container_id)

        # No existe o ya está desactivado
        if container is None or container.status == "INACTIVO":
            return False

        container.status = "INACTIVO"

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return True
