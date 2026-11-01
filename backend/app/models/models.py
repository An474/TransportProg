from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Float, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="dispatcher")  # admin, dispatcher, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)

    vehicles = relationship("Vehicle", back_populates="company")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    head_name = Column(String(100), nullable=True)
    head_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

    vehicles = relationship("Vehicle", back_populates="department")
    drivers = relationship("Driver", back_populates="department")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), unique=True, index=True, nullable=False) # Normalized: e.g. "014GI02"
    plate_display = Column(String(30), nullable=False)                         # Display format: e.g. "014 GI 02"
    brand_model = Column(String(100), nullable=False)                         # e.g. "DFSK C 35"
    fuel_type = Column(String(20), default="АИ-92")                            # АИ-92, АИ-95, ДТ, Электро
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    vin = Column(String(50), nullable=True)
    tech_passport_number = Column(String(50), nullable=True)
    tech_passport_date = Column(Date, nullable=True)
    color = Column(String(50), nullable=True)
    fuel_card_number = Column(String(50), nullable=True)
    lease_contract = Column(String(100), nullable=True)
    
    insurance_expiry = Column(Date, nullable=True)
    inspection_expiry = Column(Date, nullable=True)
    inspection_interval_months = Column(Integer, default=12) # 6 months for buses/commercial
    
    has_gps = Column(Boolean, default=False)
    has_branding = Column(Boolean, default=False)
    
    status = Column(String(30), default="ACTIVE") # ACTIVE, REPAIR, WRITE_OFF, RESERVE, SOLD
    current_mileage = Column(Integer, default=0)
    location_notes = Column(String(255), nullable=True) # e.g. "Шымкент Акт №1", "Иссык"
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="vehicles")
    department = relationship("Department", back_populates="vehicles")
    assignments = relationship("DriverAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    waybills = relationship("Waybill", back_populates="vehicle")
    fines = relationship("Fine", back_populates="vehicle")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle")
    fuel_logs = relationship("FuelLog", back_populates="vehicle")

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    position = Column(String(100), default="Водитель") # Бригадир, Инсталлятор, Сварщик, Монтажник etc.
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    status = Column(String(30), default="ACTIVE") # ACTIVE, VACATION, SICK_LEAVE, DISMISSED, SUSPENDED
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="drivers")
    assignments = relationship("DriverAssignment", back_populates="driver")
    waybills = relationship("Waybill", back_populates="driver")
    fines = relationship("Fine", back_populates="driver")

class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=True)
    assignment_type = Column(String(30), default="PRIMARY") # PRIMARY, TEMPORARY, SHIFT
    reason = Column(String(200), nullable=True) # Отпуск, ремонт, замена, перегон
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="assignments")
    driver = relationship("Driver", back_populates="assignments")

class Waybill(Base):
    __tablename__ = "waybills"

    id = Column(Integer, primary_key=True, index=True)
    waybill_number = Column(String(50), index=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    
    period_month = Column(String(20), nullable=True) # e.g. "2026-06", "2026-07"
    issue_date = Column(Date, nullable=False, default=date.today)
    valid_until = Column(Date, nullable=True)
    
    start_odometer = Column(Integer, default=0)
    end_odometer = Column(Integer, default=0)
    total_distance = Column(Integer, default=0)
    
    is_lost = Column(Boolean, default=False)
    weekly_returns = Column(String(255), default='{"w1":false,"w2":false,"w3":false,"w4":false}') # JSON status
    status = Column(String(30), default="ISSUED") # ISSUED, RETURNED, OVERDUE, LOST
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="waybills")
    driver = relationship("Driver", back_populates="waybills")

class Fine(Base):
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    notice_number = Column(String(100), index=True, nullable=False) # № постановления / протокола
    violation_date = Column(Date, nullable=True)
    accounting_date = Column(Date, nullable=True)                  # Дата получения от бухгалтерии
    driver_notified_date = Column(Date, nullable=True)             # Дата оповещения водителя
    payment_date = Column(Date, nullable=True)                     # Дата фактической оплаты
    amount = Column(Float, default=0.0)
    
    status = Column(String(30), default="NEW") # NEW, NOTIFIED, PAID, REFUSED, DISPUTED
    is_not_our_car = Column(Boolean, default=False)
    in_official_memo = Column(Boolean, default=False)              # Включен в служебку СБ
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="fines")
    driver = relationship("Driver", back_populates="fines")

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    request_date = Column(Date, nullable=False, default=date.today)
    appointment_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    mileage_at_service = Column(Integer, default=0)
    
    service_type = Column(String(50), nullable=False) # SCHEDULED_TO, BODY_DAMAGE, TOW_TRUCK, WINDSHIELD, WHEEL_ALIGNMENT, REPAIR
    contractor = Column(String(150), nullable=True)   # СТО Хабаров, ИП Мухраев (эвакуатор)
    cost = Column(Float, default=0.0)
    document_number = Column(String(100), nullable=True) # Номер ЕРП, договора, заказ-наряда
    
    status = Column(String(30), default="REQUESTED") # REQUESTED, SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="maintenance_records")
    driver = relationship("Driver")

class FuelLog(Base):
    __tablename__ = "fuel_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    period_date = Column(Date, nullable=False, default=date.today)
    consumption_rate = Column(Float, default=0.0)      # Норма л/100км
    distance_traveled = Column(Integer, default=0)    # Пробег км
    calculated_liters = Column(Float, default=0.0)    # Расчет по норме
    actual_liters = Column(Float, default=0.0)        # Факт заправки
    deviation_liters = Column(Float, default=0.0)     # Отклонение (+ перерасход, - экономия)
    fuel_card_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="fuel_logs")
    driver = relationship("Driver")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=False)
    entity_name = Column(String(50), nullable=False) # VEHICLE, DRIVER, WAYBILL, FINE, etc.
    entity_id = Column(Integer, nullable=True)
    action = Column(String(20), nullable=False)      # CREATE, UPDATE, DELETE
    changes_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
