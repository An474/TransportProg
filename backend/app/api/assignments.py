from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import DriverAssignment, Vehicle, Driver, User
from app.schemas.schemas import AssignmentCreate, AssignmentOut
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/assignments", tags=["Пересадки и Закрепления"])

@router.get("", response_model=List[AssignmentOut])
def get_assignments(
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(DriverAssignment)
    if vehicle_id:
        q = q.filter(DriverAssignment.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(DriverAssignment.driver_id == driver_id)
    if active_only:
        q = q.filter(DriverAssignment.is_active == True)

    assignments = q.order_by(DriverAssignment.start_date.desc(), DriverAssignment.id.desc()).all()
    
    results = []
    for a in assignments:
        results.append({
            "id": a.id,
            "vehicle_id": a.vehicle_id,
            "driver_id": a.driver_id,
            "driver_name": a.driver.full_name if a.driver else "Не указан",
            "driver_phone": a.driver.phone if a.driver else None,
            "plate_number": a.vehicle.plate_display if a.vehicle else "Не указан",
            "start_date": a.start_date,
            "end_date": a.end_date,
            "assignment_type": a.assignment_type,
            "reason": a.reason,
            "is_active": a.is_active,
            "notes": a.notes,
            "created_at": a.created_at
        })
    return results

@router.post("", response_model=AssignmentOut)
def create_assignment(
    assign_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == assign_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    driver = db.query(Driver).filter(Driver.id == assign_in.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")

    # If new assignment is PRIMARY or replacing active one, close previous active assignments on this car
    if assign_in.assignment_type == "PRIMARY":
        prev_active = db.query(DriverAssignment).filter(
            DriverAssignment.vehicle_id == vehicle.id,
            DriverAssignment.is_active == True
        ).all()
        for p in prev_active:
            p.is_active = False
            if not p.end_date:
                p.end_date = assign_in.start_date

    new_assign = DriverAssignment(
        vehicle_id=assign_in.vehicle_id,
        driver_id=assign_in.driver_id,
        start_date=assign_in.start_date,
        end_date=assign_in.end_date,
        assignment_type=assign_in.assignment_type,
        reason=assign_in.reason,
        is_active=True,
        notes=assign_in.notes
    )
    db.add(new_assign)
    db.commit()
    db.refresh(new_assign)

    record_audit(
        db, current_user, "ASSIGNMENT", new_assign.id, "CREATE",
        {"plate": vehicle.plate_number, "driver": driver.full_name, "type": new_assign.assignment_type, "reason": new_assign.reason}
    )

    return {
        "id": new_assign.id,
        "vehicle_id": new_assign.vehicle_id,
        "driver_id": new_assign.driver_id,
        "driver_name": driver.full_name,
        "driver_phone": driver.phone,
        "plate_number": vehicle.plate_display,
        "start_date": new_assign.start_date,
        "end_date": new_assign.end_date,
        "assignment_type": new_assign.assignment_type,
        "reason": new_assign.reason,
        "is_active": new_assign.is_active,
        "notes": new_assign.notes,
        "created_at": new_assign.created_at
    }

@router.put("/{assignment_id}/deactivate")
def deactivate_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    a = db.query(DriverAssignment).filter(DriverAssignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    
    a.is_active = False
    if not a.end_date:
        a.end_date = date.today()
    db.commit()
    record_audit(db, current_user, "ASSIGNMENT", a.id, "DEACTIVATE", {"plate": a.vehicle.plate_number, "driver": a.driver.full_name})
    return {"status": "ok", "message": "Назначение деактивировано"}
