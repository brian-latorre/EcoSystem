from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Dict, List


@dataclass(frozen=True)
class MaterialSpecFlyweight:
    material_type: str
    bin_color: str
    display_name: str
    category: str
    default_points_per_kg: int
    default_co2_per_kg: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MaterialFlyweightFactory:
    _SPECS: ClassVar[Dict[str, Dict[str, Any]]] = {
        "PLASTICO": {
            "bin_color": "Blanco",
            "display_name": "Plastico PET / HDPE",
            "category": "Aprovechable",
            "default_points_per_kg": 5,
            "default_co2_per_kg": 1.45,
        },
        "PAPEL": {
            "bin_color": "Blanco",
            "display_name": "Papel y Carton",
            "category": "Aprovechable",
            "default_points_per_kg": 3,
            "default_co2_per_kg": 0.95,
        },
        "VIDRIO": {
            "bin_color": "Blanco",
            "display_name": "Vidrio",
            "category": "Aprovechable",
            "default_points_per_kg": 2,
            "default_co2_per_kg": 0.30,
        },
        "METAL": {
            "bin_color": "Blanco",
            "display_name": "Metales y Latas",
            "category": "Aprovechable",
            "default_points_per_kg": 8,
            "default_co2_per_kg": 2.10,
        },
    }
    _pool: ClassVar[Dict[str, MaterialSpecFlyweight]] = {}

    @classmethod
    def get_spec(cls, material_type: str) -> MaterialSpecFlyweight:
        normalized = (material_type or "OTROS").strip().upper()
        if normalized not in cls._pool:
            spec = cls._SPECS.get(
                normalized,
                {
                    "bin_color": "Negro",
                    "display_name": normalized.title(),
                    "category": "General",
                    "default_points_per_kg": 3,
                    "default_co2_per_kg": 1.0,
                },
            )
            cls._pool[normalized] = MaterialSpecFlyweight(
                material_type=normalized,
                bin_color=spec["bin_color"],
                display_name=spec["display_name"],
                category=spec["category"],
                default_points_per_kg=spec["default_points_per_kg"],
                default_co2_per_kg=spec["default_co2_per_kg"],
            )
        return cls._pool[normalized]

    @classmethod
    def pool_size(cls) -> int:
        return len(cls._pool)

    @classmethod
    def list_known_specs(cls) -> List[Dict[str, Any]]:
        return [
            cls.get_spec(material).to_dict()
            for material in ("PLASTICO", "PAPEL", "VIDRIO", "METAL")
        ]

    @classmethod
    def clear_cache(cls) -> None:
        cls._pool.clear()
