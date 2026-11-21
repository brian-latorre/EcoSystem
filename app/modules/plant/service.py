from typing import List
from app.modules.plant.evaluators import MaterialEvaluatorFactory
from app.modules.plant.models import PlantProcessingRecord
from app.modules.plant.repository import PlantRepository
from app.modules.plant.schemas import PlantProcessInput, PlantProcessResponse


class PlantDomainError(Exception):
    pass


class PackageNotFoundError(PlantDomainError):
    pass


class PackageAlreadyProcessedError(PlantDomainError):
    pass


class InvalidWeightError(PlantDomainError):
    pass


class PlantService:
    def __init__(self, repository: PlantRepository):
        self._repository = repository

    def lookup_package(self, package_code: str):
        package = self._repository.find_package_by_code(package_code)
        if not package:
            raise PackageNotFoundError(f"Paquete {package_code} no encontrado")
        return package

    def list_pending_packages(self) -> List:
        return self._repository.list_pending_packages()

    def list_recent_records(self) -> List[PlantProcessingRecord]:
        return self._repository.list_recent_records()

    def process_package(self, package_code: str, payload: PlantProcessInput) -> PlantProcessResponse:
        package = self._repository.find_package_by_code(package_code)
        if not package:
            raise PackageNotFoundError(f"Paquete {package_code} no encontrado")

        if package.status == "PROCESADO_EN_PLANTA":
            raise PackageAlreadyProcessedError(f"El paquete {package.package_code} ya fue procesado")

        if not payload.is_contaminated and payload.verified_weight_kg <= 0.0:
            raise InvalidWeightError("El peso verificado debe ser mayor a 0 kg para material reciclable")

        verified_mat = payload.verified_material.strip().upper()
        evaluator = MaterialEvaluatorFactory.create(payload.is_contaminated, verified_mat)
        points_per_kg, co2_per_kg = self._repository.get_material_multiplier(verified_mat)
        points_awarded = evaluator.evaluate(payload.verified_weight_kg, points_per_kg)
        co2_saved = 0.0 if points_awarded == 0 else round(payload.verified_weight_kg * co2_per_kg, 2)

        record = PlantProcessingRecord(
            package_code=package.package_code,
            citizen_id=package.citizen_id,
            operator_id=payload.operator_id,
            declared_material=package.material_type,
            verified_material=verified_mat,
            verified_weight_kg=payload.verified_weight_kg,
            points_awarded=points_awarded,
            co2_saved_kg=co2_saved,
            is_contaminated=payload.is_contaminated or points_awarded == 0,
            observations=payload.observations,
        )

        saved_record, new_balance = self._repository.save_processing(record, package, points_awarded)

        return PlantProcessResponse(
            package_code=saved_record.package_code,
            citizen_id=saved_record.citizen_id,
            verified_material=saved_record.verified_material,
            verified_weight_kg=saved_record.verified_weight_kg,
            is_contaminated=saved_record.is_contaminated,
            points_awarded=saved_record.points_awarded,
            co2_saved_kg=saved_record.co2_saved_kg,
            package_status=package.status,
            citizen_new_balance=new_balance,
            evaluator_used=type(evaluator).__name__,
            processed_at=saved_record.processed_at,
        )
