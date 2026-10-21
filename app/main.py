from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import Base, engine, init_postgis_extension

settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0-Sprint1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODULES = ["auth", "containers", "routing", "drop_and_go", "governance", "waste_reports"]

@app.on_event("startup")
def on_startup():
    init_postgis_extension()
    for mod in MODULES:
        try:
            __import__(f"app.modules.{mod}.models")
        except ImportError:
            pass
    Base.metadata.create_all(bind=engine)

for mod in MODULES:
    try:
        module = __import__(f"app.modules.{mod}.router", fromlist=["router"])
        app.include_router(module.router, prefix=settings.API_V1_STR)
    except (ImportError, AttributeError):
        pass