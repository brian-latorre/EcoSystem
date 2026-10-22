from abc import ABC, abstractmethod
import math
from typing import Tuple


class IExternalDistancePort(ABC):
    @abstractmethod
    def get_driving_distance_km(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> float:
        pass


class OpenRouteServiceAdapter(IExternalDistancePort):
    def __init__(self, api_key: str = "demo_key_protected_by_adapter"):
        self.api_key = api_key

    def get_driving_distance_km(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> float:
        lat1, lon1 = origin
        lat2, lon2 = destination
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        straight_km = 6371.0 * c
        return round(straight_km * 1.28, 3)
