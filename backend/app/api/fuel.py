from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import FuelLog, Vehicle, Driver, User
from app.schemas.schemas import FuelLogOut, FuelLogCreate
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/fuel", tags=["ГСМ и Топливо"])

def enrich_fuel(f: FuelLog) -> dict:
    driver_obj = getattr(f, 'driver', None)
    vehicle_obj = getattr(f, 'vehicle', None)
    return {
        "id": f.id,
        "vehicle_id": f.vehicle_id,
        "plate_number": vehicle_obj.plate_display if vehicle_obj else "Не указан",
        "driver_id": f.driver_id,
        "driver_name": driver_obj.full_name if driver_obj else None,
        "period_date": f.period_date,
        "consumption_rate": f.consumption_rate,
        "distance_traveled": f.distance_traveled,
        "calculated_liters": round(f.calculated_liters, 2),
        "actual_liters": round(f.actual_liters, 2),
        "deviation_liters": round(f.deviation_liters, 2),
        "fuel_card_number": f.fuel_card_number,
        "notes": f.notes,
        "created_at": f.created_at
    }

@router.get("", response_model=List[FuelLogOut])
def get_fuel_logs(
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(FuelLog).join(Vehicle)
    if vehicle_id:
        q = q.filter(FuelLog.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(FuelLog.driver_id == driver_id)

    logs = q.order_by(FuelLog.period_date.desc(), FuelLog.id.desc()).all()
    return [enrich_fuel(f) for f in logs]

@router.post("", response_model=FuelLogOut)
def create_fuel_log(
    f_in: FuelLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == f_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    # Auto calculate if rate and distance provided
    calc_liters = f_in.calculated_liters
    if calc_liters == 0.0 and f_in.consumption_rate > 0 and f_in.distance_traveled > 0:
        calc_liters = (f_in.distance_traveled * f_in.consumption_rate) / 100.0

    deviation = f_in.actual_liters - calc_liters

    card_num = f_in.fuel_card_number or vehicle.fuel_card_number

    fuel = FuelLog(
        vehicle_id=f_in.vehicle_id,
        driver_id=f_in.driver_id,
        period_date=f_in.period_date,
        consumption_rate=f_in.consumption_rate,
        distance_traveled=f_in.distance_traveled,
        calculated_liters=calc_liters,
        actual_liters=f_in.actual_liters,
        deviation_liters=deviation,
        fuel_card_number=card_num,
        notes=f_in.notes
    )
    db.add(fuel)
    db.commit()
    db.refresh(fuel)

    record_audit(db, current_user, "FUEL", fuel.id, "CREATE", {"plate": vehicle.plate_number, "actual_liters": fuel.actual_liters})
    return enrich_fuel(fuel)

@router.delete("/{fuel_id}")
def delete_fuel_log(
    fuel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    f = db.query(FuelLog).filter(FuelLog.id == fuel_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    db.delete(f)
    db.commit()
    return {"status": "ok", "message": "Запись удалена"}
