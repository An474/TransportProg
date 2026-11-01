from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import Driver, Department, DriverAssignment, Vehicle, User
from app.schemas.schemas import DriverOut, DriverCreate, DriverUpdate
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/drivers", tags=["Водители"])

def enrich_driver(d: Driver, db: Session) -> dict:
    active_assign = db.query(DriverAssignment).filter(
        DriverAssignment.driver_id == d.id,
        DriverAssignment.is_active == True
    ).order_by(DriverAssignment.id.desc()).first()

    plate = active_assign.vehicle.plate_display if active_assign and active_assign.vehicle else None

    return {
        "id": d.id,
        "full_name": d.full_name,
        "phone": d.phone,
        "position": d.position,
        "department_id": d.department_id,
        "department_name": d.department.name if d.department else None,
        "status": d.status,
        "notes": d.notes,
        "current_vehicle_plate": plate,
        "created_at": d.created_at
    }

@router.get("", response_model=List[DriverOut])
def get_drivers(
    query: Optional[str] = None,
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Driver)

    if query:
        q = q.filter(
            or_(
                Driver.full_name.ilike(f"%{query}%"),
                Driver.phone.ilike(f"%{query}%"),
                Driver.position.ilike(f"%{query}%")
            )
        )
    if department_id:
        q = q.filter(Driver.department_id == department_id)
    if status:
        q = q.filter(Driver.status == status)

    drivers = q.order_by(Driver.full_name).all()
    return [enrich_driver(d, db) for d in drivers]

@router.get("/{driver_id}", response_model=DriverOut)
def get_driver(driver_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = db.query(Driver).filter(Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    return enrich_driver(d, db)

@router.post("", response_model=DriverOut)
def create_driver(
    d_in: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    driver = Driver(**d_in.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    record_audit(db, current_user, "DRIVER", driver.id, "CREATE", {"name": driver.full_name})
    return enrich_driver(driver, db)

@router.put("/{driver_id}", response_model=DriverOut)
def update_driver(
    driver_id: int,
    d_in: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    
    update_data = d_in.model_dump(exclude_unset=True)
    changes = {}
    for field, new_val in update_data.items():
        old_val = getattr(driver, field)
        if old_val != new_val:
            changes[field] = {"old": str(old_val), "new": str(new_val)}
            setattr(driver, field, new_val)

    db.commit()
    db.refresh(driver)
    if changes:
        record_audit(db, current_user, "DRIVER", driver.id, "UPDATE", changes)
    return enrich_driver(driver, db)

@router.delete("/{driver_id}")
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")
    
    name = driver.full_name
    db.delete(driver)
    db.commit()
    record_audit(db, current_user, "DRIVER", driver_id, "DELETE", {"name": name})
    return {"status": "ok", "message": f"Водитель {name} удален"}
