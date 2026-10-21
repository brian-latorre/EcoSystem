from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "EcoSystem API - Municipalidad Distrital del Rímac"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://ecosystem_user:ecosystem_pass_2026@localhost:5432/ecosystem_rimac_db"
    DEFAULT_CONTAINER_REPORT_THRESHOLD: int = 3
    MUNICIPAL_DEPOT_LAT: float = -12.0298
    MUNICIPAL_DEPOT_LON: float = -77.0285
    OPENROUTESERVICE_API_KEY: str = "demo_key_protected_by_adapter"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()