from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Company, Department, User
from app.schemas.schemas import CompanyOut, CompanyBase, DepartmentOut, DepartmentBase
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/ref", tags=["Справочники"])

@router.get("/companies", response_model=List[CompanyOut])
def get_companies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Company).filter(Company.is_active == True).order_by(Company.name).all()

@router.post("/companies", response_model=CompanyOut)
def create_company(
    comp_in: CompanyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    comp = Company(**comp_in.model_dump())
    db.add(comp)
    db.commit()
    db.refresh(comp)
    record_audit(db, current_user, "COMPANY", comp.id, "CREATE", {"name": comp.name})
    return comp

@router.get("/departments", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Department).filter(Department.is_active == True).order_by(Department.name).all()

@router.post("/departments", response_model=DepartmentOut)
def create_department(
    dept_in: DepartmentBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "dispatcher"]))
):
    dept = Department(**dept_in.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    record_audit(db, current_user, "DEPARTMENT", dept.id, "CREATE", {"name": dept.name})
    return dept
