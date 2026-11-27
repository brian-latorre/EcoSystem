from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.plant.flyweight import MaterialFlyweightFactory
from app.modules.plant.repository import PlantRepository
from app.modules.plant.schemas import (
    PlantHistoryItem,
    PlantPackageLookupResponse,
    PlantProcessInput,
    PlantProcessResponse,
)
from app.modules.plant.service import (
    InvalidWeightError,
    PackageAlreadyProcessedError,
    PackageNotFoundError,
    PlantService,
)

router = APIRouter(
    prefix="/plant",
    tags=["Planta de Reciclaje y Recompensas (HU-014 / HU-015 / HU-016)"],
)


def get_plant_service(db: Session = Depends(get_db)) -> PlantService:
    return PlantService(PlantRepository(db))


@router.get("/material-specs")
def get_material_specs():
    specs = MaterialFlyweightFactory.list_known_specs()
    return {
        "pattern": "Flyweight",
        "pool_size": MaterialFlyweightFactory.pool_size(),
        "specs": specs,
    }


@router.get("/packages/pending", response_model=List[PlantPackageLookupResponse])
def list_pending_packages(service: PlantService = Depends(get_plant_service)):
    return service.list_pending_packages()


@router.get("/packages/{package_code}", response_model=PlantPackageLookupResponse)
def lookup_package(package_code: str, service: PlantService = Depends(get_plant_service)):
    try:
        return service.lookup_package(package_code)
    except PackageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/packages/{package_code}/process", response_model=PlantProcessResponse)
def process_package(
    package_code: str,
    payload: PlantProcessInput,
    service: PlantService = Depends(get_plant_service),
):
    try:
        return service.process_package(package_code, payload)
    except PackageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PackageAlreadyProcessedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidWeightError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/history", response_model=List[PlantHistoryItem])
def get_processing_history(service: PlantService = Depends(get_plant_service)):
    return service.list_recent_records()
