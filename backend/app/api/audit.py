from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogOut
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/audit", tags=["Журнал аудита"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    entity_name: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    q = db.query(AuditLog)
    if entity_name:
        q = q.filter(AuditLog.entity_name == entity_name)
    if action:
        q = q.filter(AuditLog.action == action)
    
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
