from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.modules.routing.strategies import GeoNode


class RoutingContainerRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_full_stops_or_fallback(self, fallback_nodes: List[GeoNode]) -> List[GeoNode]:
        try:
            from app.modules.containers.models import Container

            total_containers = self._db.scalar(select(func.count()).select_from(Container)) or 0
            stmt = select(Container).where(Container.status == "LLENO")
            full_containers = list(self._db.scalars(stmt).all())
            if full_containers:
                return [
                    GeoNode(c.id, c.code, c.latitude, c.longitude, c.address)
                    for c in full_containers
                ]
            if total_containers > 0:
                return []
        except Exception:
            self._db.rollback()
        return list(fallback_nodes)
