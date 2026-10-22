from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.modules.containers.models import Container
from app.modules.containers.schemas import (ContainerCreate, ContainerResponse)
from app.modules.containers.repository import ContainerRepository


router = APIRouter(
    prefix="/containers",
    tags=["Gestión Geoespacial de Contenedores"]
)


@router.post(
    "/",
    response_model=ContainerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_container(
    payload: ContainerCreate,
    db: Session = Depends(get_db)
):
    repo = ContainerRepository(db)
    return repo.create(payload)


@router.get(
    "/",
    response_model=List[ContainerResponse]
)
def list_containers(
    db: Session = Depends(get_db)
):
    return list(db.scalars(select(Container)).all())


@router.get(
    "/nearby",
    response_model=List[ContainerResponse]
)
def get_nearby_containers(
    lat: float = Query(-12.033, ge=-90.0, le=90.0),
    lon: float = Query(-77.029, ge=-180.0, le=180.0),
    radius_m: float = Query(
        2500.0, ge=100.0, le=10000.0
    ),
    db: Session = Depends(get_db)
):
    repo = ContainerRepository(db)

    return repo.find_nearby(
        lat=lat,
        lon=lon,
        radius_m=radius_m
    )
