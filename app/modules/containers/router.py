from typing import List
from fastapi import (APIRouter, Depends, Query, HTTPException, status)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.containers.schemas import (ContainerCreate, ContainerResponse, ContainerUpdate)
from app.modules.containers.repository import ContainerRepository

router = APIRouter(
    prefix="/containers",
    tags=["Gestión Geoespacial de Contenedores"]
)

# POST: Registrar un nuevo contenedor
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

# GET: Listar todos los contenedores
@router.get(
    "/",
    response_model=List[ContainerResponse]
)

def list_containers(
    db: Session = Depends(get_db)
):
    repo = ContainerRepository(db)
    return repo.list_all()

# GET: Buscar contenedores cercanos
@router.get(
    "/nearby",
    response_model=List[ContainerResponse]
)

def get_nearby_containers(
    lat: float = Query(-12.033, ge=-90.0, le=90.0),
    lon: float = Query(-77.029, ge=-180.0, le=180.0),
    radius_m: float = Query(
        2500.0,
        ge=100.0,
        le=10000.0
    ),
    db: Session = Depends(get_db)
):
    repo = ContainerRepository(db)

    return repo.find_nearby(
        lat=lat,
        lon=lon,
        radius_m=radius_m
    )

# PUT: Actualizar un contenedor existente
@router.put(
    "/{container_id}",
    response_model=ContainerResponse,
    status_code=status.HTTP_200_OK
)

def update_container(
    container_id: int,
    payload: ContainerUpdate,
    db: Session = Depends(get_db)
):
    repo = ContainerRepository(db)

    container = repo.update(
        container_id=container_id,
        payload=payload
    )

    if container is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contenedor no encontrado o inactivo"
        )

    return container


# DELETE: Desactivar un contenedor
@router.delete(
    "/{container_id}",
    status_code=status.HTTP_204_NO_CONTENT
)

def delete_container(
    container_id: int,
    db: Session = Depends(get_db)
):
    repo = ContainerRepository(db)

    deleted = repo.soft_delete(container_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contenedor no encontrado o ya inactivo"
        )

