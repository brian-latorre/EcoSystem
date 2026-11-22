from sqlalchemy import select
from app.core.database import SessionLocal
from app.modules.auth.models import User, UserRole
from app.modules.auth.security import hash_password


DEMO_USERS = [
    {
        "full_name": "Maria Lopez",
        "email": "ciudadano@rimac.pe",
        "role": UserRole.CIUDADANO,
        "zone_sector": "Rimac Centro",
        "eco_points": 50,
    },
    {
        "full_name": "Carlos Rojas",
        "email": "conductor@rimac.pe",
        "role": UserRole.CONDUCTOR,
        "zone_sector": "Rimac Centro",
        "eco_points": 0,
    },
    {
        "full_name": "Luis Perez",
        "email": "operario@rimac.pe",
        "role": UserRole.OPERARIO,
        "zone_sector": "Planta Rimac",
        "eco_points": 0,
    },
    {
        "full_name": "Juan Admin",
        "email": "admin@rimac.pe",
        "role": UserRole.ADMIN,
        "zone_sector": "Municipalidad",
        "eco_points": 0,
    },
]


def run_seed():
    db = SessionLocal()
    created = 0
    try:
        pwd_hash = hash_password("eco2026")
        for item in DEMO_USERS:
            existing = db.scalar(select(User).where(User.email == item["email"]))
            if existing:
                continue
            db.add(
                User(
                    full_name=item["full_name"],
                    email=item["email"],
                    password_hash=pwd_hash,
                    role=item["role"],
                    zone_sector=item["zone_sector"],
                    eco_points_balance=item["eco_points"],
                    is_active=True,
                )
            )
            created += 1
        db.commit()
        print(f"Usuarios demo creados: {created}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
