from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import User, AuditLog
from app.schemas.schemas import LoginRequest, Token, UserOut, UserCreate, UserUpdate
from app.api.deps import get_current_user, require_roles, record_audit

router = APIRouter(prefix="/auth", tags=["Аутентификация и Пользователи"])

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учетная запись заблокирована"
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    return db.query(User).order_by(User.id).all()

@router.post("/users", response_model=UserOut)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    new_user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        role=user_in.role,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    record_audit(db, current_user, "USER", new_user.id, "CREATE", {"username": new_user.username, "role": new_user.role})
    return new_user

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    changes = {}
    if user_in.full_name is not None and user_in.full_name != target.full_name:
        changes["full_name"] = {"old": target.full_name, "new": user_in.full_name}
        target.full_name = user_in.full_name
    if user_in.role is not None and user_in.role != target.role:
        changes["role"] = {"old": target.role, "new": user_in.role}
        target.role = user_in.role
    if user_in.is_active is not None and user_in.is_active != target.is_active:
        changes["is_active"] = {"old": target.is_active, "new": user_in.is_active}
        target.is_active = user_in.is_active
    if user_in.password:
        target.hashed_password = get_password_hash(user_in.password)
        changes["password"] = "updated"

    db.commit()
    db.refresh(target)
    if changes:
        record_audit(db, current_user, "USER", target.id, "UPDATE", changes)
    return target

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить собственную учетную запись")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    username = target.username
    # Clear user_id in audit logs before deletion to preserve audit trail without violating foreign keys
    db.query(AuditLog).filter(AuditLog.user_id == user_id).update({AuditLog.user_id: None})
    db.delete(target)
    db.commit()
    record_audit(db, current_user, "USER", user_id, "DELETE", {"username": username})
    return {"status": "ok", "message": f"Пользователь {username} удален"}
