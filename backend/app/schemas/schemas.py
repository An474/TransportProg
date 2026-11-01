from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ----------------- User Schemas -----------------
class UserBase(BaseModel):
    username: str
    full_name: str
    role: str = "dispatcher"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class LoginRequest(BaseModel):
    username: str
    password: str

# ----------------- Reference Schemas -----------------
class CompanyBase(BaseModel):
    name: str
    code: Optional[str] = None
    is_active: bool = True

class CompanyOut(CompanyBase):
    id: int
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str
    head_name: Optional[str] = None
    head_phone: Optional[str] = None
    is_active: bool = True

class DepartmentOut(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

# ----------------- Driver Schemas -----------------
class DriverBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    position: Optional[str] = "Водитель"
    department_id: Optional[int] = None
    status: Optional[str] = "ACTIVE"
    notes: Optional[str] = None

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class DriverOut(DriverBase):
    id: int
    department_name: Optional[str] = None
    current_vehicle_plate: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Assignment Schemas -----------------
class AssignmentCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    assignment_type: str = "PRIMARY" # PRIMARY, TEMPORARY, SHIFT
    reason: Optional[str] = None
    notes: Optional[str] = None

class AssignmentOut(BaseModel):
    id: int
    vehicle_id: int
    driver_id: int
    driver_name: str
    driver_phone: Optional[str] = None
    plate_number: str
    start_date: date
    end_date: Optional[date] = None
    assignment_type: str
    reason: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Vehicle Schemas -----------------
class VehicleBase(BaseModel):
    plate_number: str
    plate_display: Optional[str] = None
    brand_model: str
    fuel_type: str = "АИ-92"
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    vin: Optional[str] = None
    tech_passport_number: Optional[str] = None
    tech_passport_date: Optional[date] = None
    color: Optional[str] = None
    fuel_card_number: Optional[str] = None
    lease_contract: Optional[str] = None
    insurance_expiry: Optional[date] = None
    inspection_expiry: Optional[date] = None
    inspection_interval_months: int = 12
    has_gps: bool = False
    has_branding: bool = False
    status: str = "ACTIVE"
    current_mileage: int = 0
    location_notes: Optional[str] = None
    notes: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    plate_number: Optional[str] = None
    plate_display: Optional[str] = None
    brand_model: Optional[str] = None
    fuel_type: Optional[str] = None
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    vin: Optional[str] = None
    tech_passport_number: Optional[str] = None
    tech_passport_date: Optional[date] = None
    color: Optional[str] = None
    fuel_card_number: Optional[str] = None
    lease_contract: Optional[str] = None
    insurance_expiry: Optional[date] = None
    inspection_expiry: Optional[date] = None
    inspection_interval_months: Optional[int] = None
    has_gps: Optional[bool] = None
    has_branding: Optional[bool] = None
    status: Optional[str] = None
    current_mileage: Optional[int] = None
    location_notes: Optional[str] = None
    notes: Optional[str] = None

class VehicleOut(VehicleBase):
    id: int
    company_name: Optional[str] = None
    department_name: Optional[str] = None
    current_driver_name: Optional[str] = None
    current_driver_phone: Optional[str] = None
    
    # Calculated fields
    days_to_insurance: Optional[int] = None
    days_to_inspection: Optional[int] = None
    insurance_state: str = "OK"   # OK, WARNING (<30 days), EXPIRED (<0 days), UNSET
    inspection_state: str = "OK"  # OK, WARNING (<30 days), EXPIRED (<0 days), UNSET
    
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Waybill Schemas -----------------
class WaybillBase(BaseModel):
    waybill_number: str
    vehicle_id: int
    driver_id: int
    period_month: Optional[str] = None
    issue_date: date = Field(default_factory=date.today)
    valid_until: Optional[date] = None
    start_odometer: int = 0
    end_odometer: int = 0
    total_distance: int = 0
    is_lost: bool = False
    weekly_returns: Optional[str] = '{"w1":false,"w2":false,"w3":false,"w4":false}'
    status: str = "ISSUED"
    notes: Optional[str] = None

class WaybillCreate(WaybillBase):
    pass

class WaybillUpdate(BaseModel):
    waybill_number: Optional[str] = None
    driver_id: Optional[int] = None
    issue_date: Optional[date] = None
    valid_until: Optional[date] = None
    start_odometer: Optional[int] = None
    end_odometer: Optional[int] = None
    total_distance: Optional[int] = None
    is_lost: Optional[bool] = None
    weekly_returns: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class WaybillOut(WaybillBase):
    id: int
    plate_number: str
    driver_name: str
    driver_phone: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Fine Schemas -----------------
class FineBase(BaseModel):
    vehicle_id: int
    driver_id: Optional[int] = None
    notice_number: str
    violation_date: Optional[date] = None
    accounting_date: Optional[date] = None
    driver_notified_date: Optional[date] = None
    payment_date: Optional[date] = None
    amount: float = 0.0
    status: str = "NEW"
    is_not_our_car: bool = False
    in_official_memo: bool = False
    notes: Optional[str] = None

class FineCreate(FineBase):
    pass

class FineUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    notice_number: Optional[str] = None
    violation_date: Optional[date] = None
    accounting_date: Optional[date] = None
    driver_notified_date: Optional[date] = None
    payment_date: Optional[date] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    is_not_our_car: Optional[bool] = None
    in_official_memo: Optional[bool] = None
    notes: Optional[str] = None

class FineOut(FineBase):
    id: int
    plate_number: str
    company_name: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    department_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Maintenance Schemas -----------------
class MaintenanceBase(BaseModel):
    vehicle_id: int
    driver_id: Optional[int] = None
    request_date: date = Field(default_factory=date.today)
    appointment_date: Optional[date] = None
    completion_date: Optional[date] = None
    mileage_at_service: int = 0
    service_type: str = "SCHEDULED_TO"
    contractor: Optional[str] = None
    cost: float = 0.0
    document_number: Optional[str] = None
    status: str = "REQUESTED"
    description: Optional[str] = None
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    driver_id: Optional[int] = None
    request_date: Optional[date] = None
    appointment_date: Optional[date] = None
    completion_date: Optional[date] = None
    mileage_at_service: Optional[int] = None
    service_type: Optional[str] = None
    contractor: Optional[str] = None
    cost: Optional[float] = None
    document_number: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class MaintenanceOut(MaintenanceBase):
    id: int
    plate_number: str
    driver_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Fuel Schemas -----------------
class FuelLogBase(BaseModel):
    vehicle_id: int
    driver_id: Optional[int] = None
    period_date: date = Field(default_factory=date.today)
    consumption_rate: float = 0.0
    distance_traveled: int = 0
    calculated_liters: float = 0.0
    actual_liters: float = 0.0
    deviation_liters: float = 0.0
    fuel_card_number: Optional[str] = None
    notes: Optional[str] = None

class FuelLogCreate(FuelLogBase):
    pass

class FuelLogOut(FuelLogBase):
    id: int
    plate_number: str
    driver_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Audit Schema -----------------
class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str
    entity_name: str
    entity_id: Optional[int] = None
    action: str
    changes_json: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ----------------- Dashboard Stats -----------------
class DashboardStats(BaseModel):
    total_vehicles: int
    active_vehicles: int
    repair_vehicles: int
    reserve_vehicles: int
    insurance_expired: int
    insurance_warning: int
    inspection_expired: int
    inspection_warning: int
    total_fines: int
    unpaid_fines: int
    active_drivers: int
    active_waybills: int
