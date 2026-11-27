from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.core.config import get_settings
from app.core.database import Base, engine, init_postgis_extension


settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME, version="2.0.0-Sprint2")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODULES = ["auth", "containers", "routing", "drop_and_go", "governance", "waste_reports", "plant"]

@app.on_event("startup")
def on_startup():
    init_postgis_extension()
    for mod in MODULES:
        try:
            __import__(f"app.modules.{mod}.models")
        except ImportError:
            pass
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE abandoned_waste_reports "
                    "ALTER COLUMN photo_evidence_url TYPE TEXT;"
                )
            )
    except Exception:
        pass
    try:
        from app.modules.auth.seed import run_seed as seed_auth
        from app.modules.containers.seed import run_seed as seed_containers
        from app.modules.governance.seed import run_seed as seed_governance

        seed_auth()
        seed_containers()
        seed_governance()
    except Exception:
        pass

for mod in MODULES:
    try:
        module = __import__(f"app.modules.{mod}.router", fromlist=["router"])
        app.include_router(module.router, prefix=settings.API_V1_STR)
    except (ImportError, AttributeError):
        pass


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/app/index.html")


app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
