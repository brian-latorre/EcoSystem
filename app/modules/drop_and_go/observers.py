
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import unicodedata

from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.modules.drop_and_go.models import (
    DropAndGoRequest,
    CitizenAlertNotification,
)


class ICollectionObserver(ABC):
    @abstractmethod
    def update(self, db: Session, event: Dict[str, Any]) -> None:
        pass


class ContainerCounterResetObserver(ICollectionObserver):
    def update(self, db: Session, event: Dict[str, Any]) -> None:
        if event.get("event_type") == "CONTAINER_EMPTIED":
            code = event.get("container_code")

            try:
                with db.begin_nested():
                    db.execute(
                        text(
                            "DELETE FROM container_citizen_reports "
                            "WHERE container_id IN ("
                            "SELECT id FROM containers WHERE code = :c"
                            ")"
                        ),
                        {"c": code},
                    )
                    db.execute(
                        text(
                            "UPDATE containers "
                            "SET status = 'DISPONIBLE', "
                            "current_reports_count = 0 "
                            "WHERE code = :c"
                        ),
                        {"c": code},
                    )
            except Exception:
                pass


class PackageStatusCollectedObserver(ICollectionObserver):
    def update(self, db: Session, event: Dict[str, Any]) -> None:
        if event.get("event_type") == "CONTAINER_EMPTIED":
            code = event.get("container_code")

            pkgs = db.scalars(
                select(DropAndGoRequest).where(
                    DropAndGoRequest.container_code == code,
                    DropAndGoRequest.status == "REGISTRADA",
                )
            ).all()

            for pkg in pkgs:
                pkg.status = "RECOLECTADA"


def _normalize_sector(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value or "")
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.strip().lower()


class CitizenSectorAlertObserver(ICollectionObserver):
    def update(self, db: Session, event: Dict[str, Any]) -> None:
        sector = event.get("zone_sector", "Rímac Centro")
        target_sector = _normalize_sector(sector)

        candidates = db.scalars(
            select(DropAndGoRequest).where(
                DropAndGoRequest.status == "REGISTRADA",
            )
        ).all()

        reqs = [
            req for req in candidates
            if _normalize_sector(req.zone_sector) == target_sector
        ]

        seen_users = set()

        for r in reqs:
            if r.citizen_id not in seen_users:
                db.add(
                    CitizenAlertNotification(
                        citizen_id=r.citizen_id,
                        title="Camión de Reciclaje en Proximidad",
                        message=(
                            f"El camión recolector está en camino a "
                            f"{sector}. Saca tu paquete {r.package_code}."
                        ),
                        channel="PUSH_NOTIFICATION",
                    )
                )
                seen_users.add(r.citizen_id)


class CollectionEventSubject:
    def __init__(self):
        self._observers: List[ICollectionObserver] = []

    def attach(self, observer: ICollectionObserver) -> None:
        self._observers.append(observer)

    def notify(self, db: Session, event: Dict[str, Any]) -> None:
        for obs in self._observers:
            obs.update(db, event)

        db.commit()
