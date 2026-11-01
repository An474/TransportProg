from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import MaintenanceRecord, Vehicle, Driver, User
from app.schemas.schemas import MaintenanceOut, MaintenanceCreate, MaintenanceUpdate
from app.services.initial_data import normalize_plate
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/maintenance", tags=["ТО и Ремонты"])

def enrich_maintenance(m: MaintenanceRecord) -> dict:
    driver_obj = getattr(m, 'driver', None)
    vehicle_obj = getattr(m, 'vehicle', None)
    return {
        "id": m.id,
        "vehicle_id": m.vehicle_id,
        "plate_number": vehicle_obj.plate_display if vehicle_obj else "Не указан",
        "driver_id": m.driver_id,
        "driver_name": driver_obj.full_name if driver_obj else None,
        "request_date": m.request_date,
        "appointment_date": m.appointment_date,
        "completion_date": m.completion_date,
        "mileage_at_service": m.mileage_at_service,
        "service_type": m.service_type,
        "contractor": m.contractor,
        "cost": m.cost,
        "document_number": m.document_number,
        "status": m.status,
        "description": m.description,
        "notes": m.notes,
        "created_at": m.created_at
    }

@router.get("", response_model=List[MaintenanceOut])
def get_maintenance_records(
    query: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    service_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(MaintenanceRecord).join(Vehicle)

    if query:
        norm_q = normalize_plate(query)
        q = q.filter(
            or_(
                Vehicle.plate_number.ilike(f"%{norm_q}%"),
                MaintenanceRecord.description.ilike(f"%{query}%"),
                MaintenanceRecord.contractor.ilike(f"%{query}%"),
                MaintenanceRecord.document_number.ilike(f"%{query}%")
            )
        )
    if vehicle_id:
        q = q.filter(MaintenanceRecord.vehicle_id == vehicle_id)
    if service_type:
        q = q.filter(MaintenanceRecord.service_type == service_type)
    if status:
        q = q.filter(MaintenanceRecord.status == status)

    records = q.order_by(MaintenanceRecord.request_date.desc(), MaintenanceRecord.id.desc()).all()
    return [enrich_maintenance(m) for m in records]

@router.post("", response_model=MaintenanceOut)
def create_maintenance_record(
    m_in: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == m_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    maint = MaintenanceRecord(**m_in.model_dump())
    db.add(maint)

    # If status is IN_PROGRESS, set vehicle status to REPAIR
    if maint.status == "IN_PROGRESS" and vehicle.status == "ACTIVE":
        vehicle.status = "REPAIR"

    # Update vehicle mileage if service mileage is higher
    if maint.mileage_at_service > vehicle.current_mileage:
        vehicle.current_mileage = maint.mileage_at_service

    db.commit()
    db.refresh(maint)

    record_audit(db, current_user, "MAINTENANCE", maint.id, "CREATE", {"plate": vehicle.plate_number, "type": maint.service_type})
    return enrich_maintenance(maint)

@router.put("/{record_id}", response_model=MaintenanceOut)
def update_maintenance_record(
    record_id: int,
    m_in: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    maint = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Запись о ТО не найдена")

    update_data = m_in.model_dump(exclude_unset=True)
    changes = {}
    for field, new_val in update_data.items():
        old_val = getattr(maint, field)
        if old_val != new_val:
            changes[field] = {"old": str(old_val), "new": str(new_val)}
            setattr(maint, field, new_val)

    # When repair completes, if vehicle was in REPAIR, restore to ACTIVE
    if maint.status == "COMPLETED" and maint.vehicle and maint.vehicle.status == "REPAIR":
        maint.vehicle.status = "ACTIVE"
        if not maint.completion_date:
            maint.completion_date = date.today()

    db.commit()
    db.refresh(maint)
    if changes:
        record_audit(db, current_user, "MAINTENANCE", maint.id, "UPDATE", changes)
    return enrich_maintenance(maint)

@router.delete("/{record_id}")
def delete_maintenance_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    maint = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    db.delete(maint)
    db.commit()
    record_audit(db, current_user, "MAINTENANCE", record_id, "DELETE", {"type": maint.service_type})
    return {"status": "ok", "message": "Запись удалена"}
