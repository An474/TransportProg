from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.models.models import Fine, Vehicle, Driver, DriverAssignment, Waybill, User
from app.schemas.schemas import FineOut, FineCreate, FineUpdate
from app.services.initial_data import normalize_plate
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/fines", tags=["Штрафы"])

def enrich_fine(f: Fine) -> dict:
    return {
        "id": f.id,
        "vehicle_id": f.vehicle_id,
        "plate_number": f.vehicle.plate_display if f.vehicle else "Не указан",
        "company_name": f.vehicle.company.name if f.vehicle and f.vehicle.company else None,
        "department_name": f.vehicle.department.name if f.vehicle and f.vehicle.department else None,
        "driver_id": f.driver_id,
        "driver_name": f.driver.full_name if f.driver else "Не определен",
        "driver_phone": f.driver.phone if f.driver else None,
        "notice_number": f.notice_number,
        "violation_date": f.violation_date,
        "accounting_date": f.accounting_date,
        "driver_notified_date": f.driver_notified_date,
        "payment_date": f.payment_date,
        "amount": f.amount,
        "status": f.status,
        "is_not_our_car": f.is_not_our_car,
        "in_official_memo": f.in_official_memo,
        "notes": f.notes,
        "created_at": f.created_at
    }

@router.get("", response_model=List[FineOut])
def get_fines(
    query: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    status: Optional[str] = None,
    in_official_memo: Optional[bool] = None,
    is_not_our_car: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Fine).join(Vehicle)

    if query:
        norm_q = normalize_plate(query)
        q = q.outerjoin(Driver).filter(
            or_(
                Fine.notice_number.ilike(f"%{query}%"),
                Vehicle.plate_number.ilike(f"%{norm_q}%"),
                Driver.full_name.ilike(f"%{query}%"),
                Fine.notes.ilike(f"%{query}%")
            )
        )
    if vehicle_id:
        q = q.filter(Fine.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(Fine.driver_id == driver_id)
    if status:
        q = q.filter(Fine.status == status)
    if in_official_memo is not None:
        q = q.filter(Fine.in_official_memo == in_official_memo)
    if is_not_our_car is not None:
        q = q.filter(Fine.is_not_our_car == is_not_our_car)

    fines = q.order_by(Fine.accounting_date.desc(), Fine.id.desc()).all()
    return [enrich_fine(f) for f in fines]

@router.get("/auto-detect-driver")
def auto_detect_driver(
    vehicle_id: int,
    violation_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Automatically detects which driver was driving the vehicle on the violation date
    by checking assignments and waybills active on that date.
    """
    # 1. Check temporary assignments first (transfers/reassignments on that date)
    temp_assign = db.query(DriverAssignment).filter(
        DriverAssignment.vehicle_id == vehicle_id,
        DriverAssignment.assignment_type.in_(["TEMPORARY", "SHIFT"]),
        DriverAssignment.start_date <= violation_date,
        or_(DriverAssignment.end_date >= violation_date, DriverAssignment.end_date == None)
    ).first()
    if temp_assign and temp_assign.driver:
        return {
            "driver_id": temp_assign.driver.id,
            "driver_name": temp_assign.driver.full_name,
            "driver_phone": temp_assign.driver.phone,
            "source": "Временная пересадка (замена)",
            "reason": temp_assign.reason
        }

    # 2. Check waybill issued covering this date
    waybill = db.query(Waybill).filter(
        Waybill.vehicle_id == vehicle_id,
        Waybill.issue_date <= violation_date,
        or_(Waybill.valid_until >= violation_date, Waybill.valid_until == None)
    ).first()
    if waybill and waybill.driver:
        return {
            "driver_id": waybill.driver.id,
            "driver_name": waybill.driver.full_name,
            "driver_phone": waybill.driver.phone,
            "source": f"Путевой лист №{waybill.waybill_number}",
            "reason": "Выписан путевой лист"
        }

    # 3. Check primary assignment
    prim_assign = db.query(DriverAssignment).filter(
        DriverAssignment.vehicle_id == vehicle_id,
        DriverAssignment.start_date <= violation_date,
        or_(DriverAssignment.end_date >= violation_date, DriverAssignment.end_date == None)
    ).first()
    if prim_assign and prim_assign.driver:
        return {
            "driver_id": prim_assign.driver.id,
            "driver_name": prim_assign.driver.full_name,
            "driver_phone": prim_assign.driver.phone,
            "source": "Основное закрепление",
            "reason": prim_assign.reason
        }

    return {"driver_id": None, "driver_name": None, "source": "Не удалось автоматически определить", "reason": None}

@router.get("/memo-candidates", response_model=List[FineOut])
def get_memo_candidates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns fines marked for official memo or where driver refused to pay."""
    fines = db.query(Fine).filter(
        or_(Fine.status == "REFUSED", Fine.in_official_memo == True)
    ).order_by(Fine.violation_date.desc()).all()
    return [enrich_fine(f) for f in fines]

@router.post("", response_model=FineOut)
def create_fine(
    f_in: FineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == f_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    # If driver not explicitly provided and violation_date is known, try auto-detect
    driver_id = f_in.driver_id
    if not driver_id and f_in.violation_date:
        detect = auto_detect_driver(f_in.vehicle_id, f_in.violation_date, db, current_user)
        driver_id = detect.get("driver_id")

    fine = Fine(
        vehicle_id=f_in.vehicle_id,
        driver_id=driver_id,
        notice_number=f_in.notice_number,
        violation_date=f_in.violation_date,
        accounting_date=f_in.accounting_date,
        driver_notified_date=f_in.driver_notified_date,
        payment_date=f_in.payment_date,
        amount=f_in.amount,
        status=f_in.status,
        is_not_our_car=f_in.is_not_our_car,
        in_official_memo=f_in.in_official_memo,
        notes=f_in.notes
    )
    db.add(fine)
    db.commit()
    db.refresh(fine)

    record_audit(db, current_user, "FINE", fine.id, "CREATE", {"notice": fine.notice_number, "plate": vehicle.plate_number})
    return enrich_fine(fine)

@router.put("/{fine_id}", response_model=FineOut)
def update_fine(
    fine_id: int,
    f_in: FineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    fine = db.query(Fine).filter(Fine.id == fine_id).first()
    if not fine:
        raise HTTPException(status_code=404, detail="Штраф не найден")
    
    update_data = f_in.model_dump(exclude_unset=True)
    changes = {}

    for field, new_val in update_data.items():
        old_val = getattr(fine, field)
        if old_val != new_val:
            changes[field] = {"old": str(old_val), "new": str(new_val)}
            setattr(fine, field, new_val)

    # Auto set status to PAID if payment_date is set
    if fine.payment_date and fine.status != "PAID":
        fine.status = "PAID"
        changes["status"] = {"old": "not paid", "new": "PAID"}

    db.commit()
    db.refresh(fine)
    if changes:
        record_audit(db, current_user, "FINE", fine.id, "UPDATE", changes)
    return enrich_fine(fine)

@router.delete("/{fine_id}")
def delete_fine(
    fine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    fine = db.query(Fine).filter(Fine.id == fine_id).first()
    if not fine:
        raise HTTPException(status_code=404, detail="Штраф не найден")
    
    notice = fine.notice_number
    db.delete(fine)
    db.commit()
    record_audit(db, current_user, "FINE", fine_id, "DELETE", {"notice": notice})
    return {"status": "ok", "message": f"Штраф {notice} удален"}
