from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.modules.containers.models import (Container, ContainerCitizenReport, ContainerFullEvent)

# Clase de servicio para manejar la lógica de reportes de contenedores
class ContainerThresholdService:

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def report_container_full(self,
        container_id: int,
        citizen_id: int) -> dict:

        if citizen_id <= 0:
            raise HTTPException(
                status_code=422,
                detail="El identificador del ciudadano debe ser positivo"
            )

        # Bloquear el contenedor para evitar condiciones de carrera
        container = self.db.scalar(
            select(Container)
            .where(Container.id == container_id)
            .with_for_update()
        )

        if container is None or container.status == "INACTIVO":
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contenedor no encontrado o inactivo"
            )

        if container.status == "LLENO":
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El contenedor ya se encuentra lleno"
            )

        # Comprobar si el ciudadano ya votó
        duplicate = self.db.scalar(
            select(ContainerCitizenReport).where(
                ContainerCitizenReport.container_id == container_id,
                ContainerCitizenReport.citizen_id == citizen_id
            )
        )

        if duplicate:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El ciudadano ya reportó este contenedor"
            )

        # Registrar el voto y actualizar el contador
        vote = ContainerCitizenReport(
            container_id=container_id,
            citizen_id=citizen_id
        )

        threshold = self.settings.DEFAULT_CONTAINER_REPORT_THRESHOLD

        try:
            self.db.add(vote)

            container.current_reports_count += 1

            if container.current_reports_count >= threshold:
                container.status = "LLENO"

                event = ContainerFullEvent(
                    container_id=container_id,
                    event_type="container.full"
                )
                self.db.add(event)

            self.db.commit()
            self.db.refresh(container)

        except Exception:
            self.db.rollback()
            raise

        return {
            "container_code": container.code,
            "reports_registered": container.current_reports_count,
            "threshold_required": threshold,
            "current_status": container.status,
            "ready_for_tsp_collection": container.status == "LLENO"
        }