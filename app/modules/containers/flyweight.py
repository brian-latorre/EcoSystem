from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Dict, List


@dataclass(frozen=True)
class ContainerVisualFlyweight:
    status: str
    marker_color: str
    priority_label: str
    dispatch_eligible: bool
    icon_name: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContainerFlyweightFactory:
    _SPECS: ClassVar[Dict[str, Dict[str, Any]]] = {
        "DISPONIBLE": {
            "marker_color": "#059669",
            "priority_label": "Operativo",
            "dispatch_eligible": False,
            "icon_name": "container-green",
        },
        "LLENO": {
            "marker_color": "#e11d48",
            "priority_label": "Recoleccion prioritaria",
            "dispatch_eligible": True,
            "icon_name": "container-red",
        },
        "INACTIVO": {
            "marker_color": "#64748b",
            "priority_label": "Fuera de servicio",
            "dispatch_eligible": False,
            "icon_name": "container-gray",
        },
    }
    _pool: ClassVar[Dict[str, ContainerVisualFlyweight]] = {}

    @classmethod
    def get_flyweight(cls, status: str) -> ContainerVisualFlyweight:
        normalized = (status or "INACTIVO").strip().upper()
        if normalized not in cls._pool:
            spec = cls._SPECS.get(normalized, cls._SPECS["INACTIVO"])
            cls._pool[normalized] = ContainerVisualFlyweight(
                status=normalized,
                marker_color=spec["marker_color"],
                priority_label=spec["priority_label"],
                dispatch_eligible=spec["dispatch_eligible"],
                icon_name=spec["icon_name"],
            )
        return cls._pool[normalized]

    @classmethod
    def pool_size(cls) -> int:
        return len(cls._pool)

    @classmethod
    def list_known_specs(cls) -> List[Dict[str, Any]]:
        return [
            cls.get_flyweight(state).to_dict()
            for state in ("DISPONIBLE", "LLENO", "INACTIVO")
        ]

    @classmethod
    def clear_cache(cls) -> None:
        cls._pool.clear()
