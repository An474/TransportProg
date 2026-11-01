from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.models.models import User
from app.api.deps import require_roles
from app.services.update_service import check_for_updates, perform_update

router = APIRouter(prefix="/system", tags=["Система и обновления"])

class UpdateRequest(BaseModel):
    download_url: Optional[str] = None

@router.get("/updates")
def get_updates_info(current_user: User = Depends(require_roles(["admin"]))):
    """Checks GitHub for application updates."""
    return check_for_updates()

@router.post("/update")
def execute_update(payload: UpdateRequest = UpdateRequest(), current_user: User = Depends(require_roles(["admin"]))):
    """Downloads and applies the latest update."""
    res = perform_update(download_url=payload.download_url)
    if res.get("status") != "ok":
        raise HTTPException(status_code=400, detail=res.get("message", "Ошибка обновления"))
    return res
