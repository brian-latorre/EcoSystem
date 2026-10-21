from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from app.modules.containers.models import Container
from app.modules.containers.schemas import ContainerCreate
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError


class ContainerRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ContainerCreate) -> Container:
        wkt_point = WKTElement(
            f"POINT({payload.longitude} {payload.latitude})",
            srid=4326
        )

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

    def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: float = 2500.0
    ) -> List[Container]:

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
