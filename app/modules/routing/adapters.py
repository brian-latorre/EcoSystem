from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Optional, Tuple


class IExternalDistancePort(ABC):
    @abstractmethod
    def get_driving_distance_km(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> float:
        pass


class OpenRouteServiceGeoJSONClient:
    def __init__(self, api_key: str = "demo_key_protected_by_adapter"):
        self.api_key = api_key

    def fetch_route_metrics(
        self,
        origin_lon_lat: List[float],
        destination_lon_lat: List[float],
    ) -> Dict[str, Any]:
        lon1, lat1 = origin_lon_lat
        lon2, lat2 = destination_lon_lat
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        distance_meters = 6371000.0 * c * 1.28
        duration_seconds = distance_meters / 8.33
        return {
            "routes": [
                {
                    "summary": {
                        "distance": round(distance_meters, 2),
                        "duration": round(duration_seconds, 1),
                    }
                }
            ],
            "metadata": {
                "engine": "OpenRouteServiceGeoJSONClient",
                "coordinate_order": "lon_lat",
            },
        }


class OpenRouteServiceAdapter(IExternalDistancePort):
    def __init__(
        self,
        api_key: str = "demo_key_protected_by_adapter",
        client: Optional[OpenRouteServiceGeoJSONClient] = None,
    ):
        self.api_key = api_key
        self._client = client or OpenRouteServiceGeoJSONClient(api_key=api_key)

    def get_driving_distance_km(
        self, origin: Tuple[float, float], destination: Tuple[float, float]
    ) -> float:
        origin_lon_lat = [origin[1], origin[0]]
        destination_lon_lat = [destination[1], destination[0]]
        payload = self._client.fetch_route_metrics(origin_lon_lat, destination_lon_lat)
        distance_meters = payload["routes"][0]["summary"]["distance"]
        return round(distance_meters / 1000.0, 3)
