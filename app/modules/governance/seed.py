from app.core.database import SessionLocal
from app.modules.governance.models import SystemParameterPolicy, MaterialPointMultiplier

INITIAL_MULTIPLIERS = [
    {"material_type": "PLASTICO", "points_per_kg": 5, "co2": 1.45},
    {"material_type": "PAPEL", "points_per_kg": 3, "co2": 0.95},
    {"material_type": "VIDRIO", "points_per_kg": 2, "co2": 0.30},
    {"material_type": "METAL", "points_per_kg": 8, "co2": 2.10},
]

def run_seed():
    db = SessionLocal()
    try:
        for m in INITIAL_MULTIPLIERS:
            exists = db.query(MaterialPointMultiplier).filter(MaterialPointMultiplier.material_type
== m["material_type"]).first()
            if not exists:
                db.add(MaterialPointMultiplier(
                    material_type=m["material_type"],
                    points_per_kg=m["points_per_kg"],
                    co2_saved_per_kg=m["co2"]
                ))
        thresh = db.query(SystemParameterPolicy).filter(SystemParameterPolicy.param_key ==
"DEFAULT_CONTAINER_REPORT_THRESHOLD").first()
        if not thresh:
            db.add(SystemParameterPolicy(
                param_key="DEFAULT_CONTAINER_REPORT_THRESHOLD",
                param_value=3.0,
                unit="reportes",
                description="Número mínimo de reportes ciudadanos distintos para activar estado LLENO"
            ))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()