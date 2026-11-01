from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import Vehicle, Company, Department, Driver, DriverAssignment, Fine, MaintenanceRecord, Waybill, User
from app.schemas.schemas import VehicleOut, VehicleCreate, VehicleUpdate
from app.services.initial_data import normalize_plate, format_plate_display
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/vehicles", tags=["Автопарк"])

def enrich_vehicle(v: Vehicle, db: Session) -> dict:
    today = date.today()
    
    # Calculate insurance state
    days_ins = None
    ins_state = "UNSET"
    if v.insurance_expiry:
        days_ins = (v.insurance_expiry - today).days
        if days_ins < 0:
            ins_state = "EXPIRED"
        elif days_ins <= 30:
            ins_state = "WARNING"
        else:
            ins_state = "OK"

    # Calculate inspection state
    days_insp = None
    insp_state = "UNSET"
    if v.inspection_expiry:
        days_insp = (v.inspection_expiry - today).days
        if days_insp < 0:
            insp_state = "EXPIRED"
        elif days_insp <= 30:
            insp_state = "WARNING"
        else:
            insp_state = "OK"

    # Current active driver
    active_assign = db.query(DriverAssignment).filter(
        DriverAssignment.vehicle_id == v.id,
        DriverAssignment.is_active == True
    ).order_by(DriverAssignment.id.desc()).first()

    driver_name = active_assign.driver.full_name if active_assign and active_assign.driver else None
    driver_phone = active_assign.driver.phone if active_assign and active_assign.driver else None

    return {
        "id": v.id,
        "plate_number": v.plate_number,
        "plate_display": v.plate_display,
        "brand_model": v.brand_model,
        "fuel_type": v.fuel_type,
        "company_id": v.company_id,
        "company_name": v.company.name if v.company else None,
        "department_id": v.department_id,
        "department_name": v.department.name if v.department else None,
        "vin": v.vin,
        "tech_passport_number": v.tech_passport_number,
        "tech_passport_date": v.tech_passport_date,
        "color": v.color,
        "fuel_card_number": v.fuel_card_number,
        "lease_contract": v.lease_contract,
        "insurance_expiry": v.insurance_expiry,
        "inspection_expiry": v.inspection_expiry,
        "inspection_interval_months": v.inspection_interval_months,
        "has_gps": v.has_gps,
        "has_branding": v.has_branding,
        "status": v.status,
        "current_mileage": v.current_mileage,
        "location_notes": v.location_notes,
        "notes": v.notes,
        "current_driver_name": driver_name,
        "current_driver_phone": driver_phone,
        "days_to_insurance": days_ins,
        "days_to_inspection": days_insp,
        "insurance_state": ins_state,
        "inspection_state": insp_state,
        "created_at": v.created_at
    }

@router.get("", response_model=List[VehicleOut])
def get_vehicles(
    query: Optional[str] = None,
    company_id: Optional[int] = None,
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    insurance_state: Optional[str] = None,
    inspection_state: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Vehicle)

    if query:
        norm_q = normalize_plate(query)
        q = q.filter(
            or_(
                Vehicle.plate_number.ilike(f"%{norm_q}%"),
                Vehicle.brand_model.ilike(f"%{query}%"),
                Vehicle.vin.ilike(f"%{query}%"),
                Vehicle.notes.ilike(f"%{query}%"),
                Vehicle.location_notes.ilike(f"%{query}%"),
            )
        )
    if company_id:
        q = q.filter(Vehicle.company_id == company_id)
    if department_id:
        q = q.filter(Vehicle.department_id == department_id)
    if status:
        q = q.filter(Vehicle.status == status)

    vehicles = q.order_by(Vehicle.plate_number).all()
    results = [enrich_vehicle(v, db) for v in vehicles]

    # Filter by calculated states if requested
    if insurance_state:
        results = [r for r in results if r["insurance_state"] == insurance_state]
    if inspection_state:
        results = [r for r in results if r["inspection_state"] == inspection_state]

    return results

@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    return enrich_vehicle(v, db)

@router.get("/{vehicle_id}/history")
def get_vehicle_history(vehicle_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    # Driver assignments history
    assignments = db.query(DriverAssignment).filter(
        DriverAssignment.vehicle_id == vehicle_id
    ).order_by(DriverAssignment.start_date.desc()).all()
    
    assign_list = [{
        "id": a.id,
        "driver_id": a.driver_id,
        "driver_name": a.driver.full_name if a.driver else None,
        "driver_phone": a.driver.phone if a.driver else None,
        "start_date": a.start_date,
        "end_date": a.end_date,
        "assignment_type": a.assignment_type,
        "reason": a.reason,
        "is_active": a.is_active,
        "notes": a.notes
    } for a in assignments]

    # Fines history
    fines = db.query(Fine).filter(Fine.vehicle_id == vehicle_id).order_by(Fine.violation_date.desc()).all()
    fine_list = [{
        "id": f.id,
        "notice_number": f.notice_number,
        "violation_date": f.violation_date,
        "driver_name": f.driver.full_name if f.driver else None,
        "amount": f.amount,
        "status": f.status,
        "payment_date": f.payment_date,
        "in_official_memo": f.in_official_memo,
        "notes": f.notes
    } for f in fines]

    # Maintenance history
    maint = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.vehicle_id == vehicle_id
    ).order_by(MaintenanceRecord.request_date.desc()).all()
    maint_list = [{
        "id": m.id,
        "request_date": m.request_date,
        "service_type": m.service_type,
        "mileage_at_service": m.mileage_at_service,
        "contractor": m.contractor,
        "cost": m.cost,
        "status": m.status,
        "description": m.description
    } for m in maint]

    return {
        "vehicle": enrich_vehicle(v, db),
        "assignments": assign_list,
        "fines": fine_list,
        "maintenance": maint_list
    }

@router.post("", response_model=VehicleOut)
def create_vehicle(
    v_in: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    norm_plate = normalize_plate(v_in.plate_number)
    disp_plate = format_plate_display(v_in.plate_number) if not v_in.plate_display else v_in.plate_display

    existing = db.query(Vehicle).filter(Vehicle.plate_number == norm_plate).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Автомобиль с госномером {norm_plate} уже зарегистрирован")

    v_data = v_in.model_dump()
    v_data["plate_number"] = norm_plate
    v_data["plate_display"] = disp_plate

    vehicle = Vehicle(**v_data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    record_audit(db, current_user, "VEHICLE", vehicle.id, "CREATE", {"plate": vehicle.plate_number, "brand": vehicle.brand_model})
    return enrich_vehicle(vehicle, db)

@router.put("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    v_in: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    update_data = v_in.model_dump(exclude_unset=True)
    if "plate_number" in update_data and update_data["plate_number"]:
        norm = normalize_plate(update_data["plate_number"])
        update_data["plate_number"] = norm
        if "plate_display" not in update_data or not update_data["plate_display"]:
            update_data["plate_display"] = format_plate_display(norm)

    changes = {}
    for field, new_val in update_data.items():
        old_val = getattr(vehicle, field)
        if old_val != new_val:
            changes[field] = {"old": str(old_val), "new": str(new_val)}
            setattr(vehicle, field, new_val)

    db.commit()
    db.refresh(vehicle)
    if changes:
        record_audit(db, current_user, "VEHICLE", vehicle.id, "UPDATE", changes)
    return enrich_vehicle(vehicle, db)

@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    
    plate = vehicle.plate_number
    db.delete(vehicle)
    db.commit()
    record_audit(db, current_user, "VEHICLE", vehicle_id, "DELETE", {"plate": plate})
    return {"status": "ok", "message": f"Автомобиль {plate} удален"}
