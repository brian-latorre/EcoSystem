from typing import Any, Dict, Iterable, List
from app.modules.containers.flyweight import ContainerFlyweightFactory


class GeoJsonContainerAdapter:
    @staticmethod
    def to_feature(container: Any) -> Dict[str, Any]:
        flyweight = ContainerFlyweightFactory.get_flyweight(container.status)
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    container.longitude,
                    container.latitude,
                ],
            },
            "properties": {
                "id": container.id,
                "code": container.code,
                "name": container.name,
                "address": container.address,
                "status": container.status,
                "capacity_kg": container.capacity_kg,
                "current_reports_count": container.current_reports_count,
                "marker_color": flyweight.marker_color,
                "priority_label": flyweight.priority_label,
                "dispatch_eligible": flyweight.dispatch_eligible,
                "icon_name": flyweight.icon_name,
            },
        }

    @classmethod
    def to_feature_collection(cls, containers: Iterable[Any]) -> Dict[str, Any]:
        features: List[Dict[str, Any]] = [
            cls.to_feature(container) for container in containers
        ]
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_features": len(features),
                "flyweight_instances_in_ram": ContainerFlyweightFactory.pool_size(),
            },
        }
