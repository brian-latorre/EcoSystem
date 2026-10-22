from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.modules.governance.models import SystemParameterPolicy, MaterialPointMultiplier
from app.modules.governance.schemas import ParameterUpdateInput, MultiplierCreateInput, StaffCreateInput
from app.modules.governance.repository import GovernanceStaffRepository

router = APIRouter(prefix="/governance", tags=["Gobernanza y Politicas de Negocio (HU-017 / HU-018)"])

@router.get("/policies")
def list_business_policies(db: Session = Depends(get_db)):
    params = list(db.scalars(select(SystemParameterPolicy)).all())
    multipliers = list(db.scalars(select(MaterialPointMultiplier)).all())
    return {"system_parameters": params, "material_multipliers": multipliers}

@router.put("/policies/parameters/{param_key}")
def update_system_parameter(param_key: str, payload: ParameterUpdateInput, db: Session = 
Depends(get_db)):
    policy = db.scalar(select(SystemParameterPolicy).where(SystemParameterPolicy.param_key == 
param_key))
    if not policy:
        policy = SystemParameterPolicy(
            param_key=param_key,
            param_value=payload.param_value,
            description=payload.description
        )
        db.add(policy)
    else:
        policy.param_value = payload.param_value
        policy.description = payload.description
    db.commit()
    db.refresh(policy)
    return policy

@router.post("/policies/multipliers", status_code=status.HTTP_201_CREATED)
def upsert_material_multiplier(payload: MultiplierCreateInput, db: Session = Depends(get_db)):
    mat_key = payload.material_type.upper()
    existing = db.scalar(select(MaterialPointMultiplier).where(MaterialPointMultiplier.material_type 
== mat_key))
    if existing:
        existing.points_per_kg = payload.points_per_kg
        existing.co2_saved_per_kg = payload.co2_saved_per_kg
        db.commit()
        return existing
    new_mult = MaterialPointMultiplier(
        material_type=mat_key,
        points_per_kg=payload.points_per_kg,
        co2_saved_per_kg=payload.co2_saved_per_kg
    )
    db.add(new_mult)
    db.commit()
    db.refresh(new_mult)
    return new_mult

@router.post("/staff", status_code=status.HTTP_201_CREATED)
def register_operational_staff(payload: StaffCreateInput, db: Session = Depends(get_db)):
    repo = GovernanceStaffRepository(db)
    return repo.create_staff(payload)

@router.get("/staff")
def list_staff(db: Session = Depends(get_db)):
    repo = GovernanceStaffRepository(db)
    return repo.list_staff()

@router.delete("/staff/{user_id}")
def deactivate_staff_member(user_id: int, db: Session = Depends(get_db)):
    repo = GovernanceStaffRepository(db)
    success = repo.deactivate_staff(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"status": "success", "message": f"Usuario {user_id} desactivado correctamente"}