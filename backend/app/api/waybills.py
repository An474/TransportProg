import json
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import Waybill, Vehicle, Driver, User
from app.schemas.schemas import WaybillOut, WaybillCreate, WaybillUpdate
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/waybills", tags=["Путевые листы"])

def enrich_waybill(w: Waybill) -> dict:
    return {
        "id": w.id,
        "waybill_number": w.waybill_number,
        "vehicle_id": w.vehicle_id,
        "plate_number": w.vehicle.plate_display if w.vehicle else "Не указан",
        "driver_id": w.driver_id,
        "driver_name": w.driver.full_name if w.driver else "Не указан",
        "driver_phone": w.driver.phone if w.driver else None,
        "period_month": w.period_month,
        "issue_date": w.issue_date,
        "valid_until": w.valid_until,
        "start_odometer": w.start_odometer,
        "end_odometer": w.end_odometer,
        "total_distance": w.total_distance,
        "is_lost": w.is_lost,
        "weekly_returns": w.weekly_returns,
        "status": w.status,
        "notes": w.notes,
        "created_at": w.created_at
    }

@router.get("", response_model=List[WaybillOut])
def get_waybills(
    query: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    status: Optional[str] = None,
    is_lost: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Waybill)

    if query:
        q = q.join(Vehicle).join(Driver).filter(
            or_(
                Waybill.waybill_number.ilike(f"%{query}%"),
                Vehicle.plate_number.ilike(f"%{query}%"),
                Driver.full_name.ilike(f"%{query}%")
            )
        )
    if vehicle_id:
        q = q.filter(Waybill.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(Waybill.driver_id == driver_id)
    if status:
        q = q.filter(Waybill.status == status)
    if is_lost is not None:
        q = q.filter(Waybill.is_lost == is_lost)

    waybills = q.order_by(Waybill.issue_date.desc(), Waybill.id.desc()).all()
    return [enrich_waybill(w) for w in waybills]

@router.post("", response_model=WaybillOut)
def create_waybill(
    w_in: WaybillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == w_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    driver = db.query(Driver).filter(Driver.id == w_in.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")

    # If start odometer is not provided, use vehicle current mileage
    start_odo = w_in.start_odometer if w_in.start_odometer > 0 else vehicle.current_mileage
    total_dist = (w_in.end_odometer - start_odo) if w_in.end_odometer > start_odo else 0

    waybill = Waybill(
        waybill_number=w_in.waybill_number,
        vehicle_id=w_in.vehicle_id,
        driver_id=w_in.driver_id,
        period_month=w_in.period_month or date.today().strftime("%Y-%m"),
        issue_date=w_in.issue_date,
        valid_until=w_in.valid_until,
        start_odometer=start_odo,
        end_odometer=w_in.end_odometer,
        total_distance=total_dist,
        is_lost=w_in.is_lost,
        weekly_returns=w_in.weekly_returns or '{"w1":false,"w2":false,"w3":false,"w4":false}',
        status=w_in.status,
        notes=w_in.notes
    )
    db.add(waybill)

    # If completed and has end odometer, update vehicle mileage
    if w_in.end_odometer > vehicle.current_mileage:
        vehicle.current_mileage = w_in.end_odometer

    db.commit()
    db.refresh(waybill)

    record_audit(db, current_user, "WAYBILL", waybill.id, "CREATE", {"number": waybill.waybill_number, "plate": vehicle.plate_number, "driver": driver.full_name})
    return enrich_waybill(waybill)

@router.put("/{waybill_id}", response_model=WaybillOut)
def update_waybill(
    waybill_id: int,
    w_in: WaybillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    waybill = db.query(Waybill).filter(Waybill.id == waybill_id).first()
    if not waybill:
        raise HTTPException(status_code=404, detail="Путевой лист не найден")
    
    update_data = w_in.model_dump(exclude_unset=True)
    changes = {}

    for field, new_val in update_data.items():
        old_val = getattr(waybill, field)
        if old_val != new_val:
            changes[field] = {"old": str(old_val), "new": str(new_val)}
            setattr(waybill, field, new_val)

    # Recalculate total distance
    if waybill.end_odometer > waybill.start_odometer:
        waybill.total_distance = waybill.end_odometer - waybill.start_odometer
        if waybill.vehicle and waybill.end_odometer > waybill.vehicle.current_mileage:
            waybill.vehicle.current_mileage = waybill.end_odometer

    db.commit()
    db.refresh(waybill)
    if changes:
        record_audit(db, current_user, "WAYBILL", waybill.id, "UPDATE", changes)
    return enrich_waybill(waybill)

@router.delete("/{waybill_id}")
def delete_waybill(
    waybill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    waybill = db.query(Waybill).filter(Waybill.id == waybill_id).first()
    if not waybill:
        raise HTTPException(status_code=404, detail="Путевой лист не найден")
    
    num = waybill.waybill_number
    db.delete(waybill)
    db.commit()
    record_audit(db, current_user, "WAYBILL", waybill_id, "DELETE", {"number": num})
    return {"status": "ok", "message": f"Путевой лист {num} удален"}
