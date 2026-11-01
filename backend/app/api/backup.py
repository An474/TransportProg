from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from app.models.models import User
from app.services.backup_service import (
    create_database_backup,
    list_backups,
    get_backup_settings,
    save_backup_settings,
    upload_backup_to_google_drive
)
from app.api.deps import require_roles
from app.core.config import settings

router = APIRouter(prefix="/backup", tags=["Резервное копирование"])

class BackupSettingsUpdate(BaseModel):
    google_drive_webhook_url: str = ""
    google_drive_enabled: bool = False

@router.get("", response_model=List[dict])
def get_backups(current_user: User = Depends(require_roles(["admin"]))):
    return list_backups()

@router.post("/create")
def make_backup(current_user: User = Depends(require_roles(["admin"]))):
    res = create_database_backup(upload_to_gdrive=True)
    if res.get("status") != "ok":
        raise HTTPException(status_code=500, detail=res.get("message", "Ошибка при создании резервной копии"))
    return res

@router.get("/settings")
def read_settings(current_user: User = Depends(require_roles(["admin"]))):
    return get_backup_settings()

@router.post("/settings")
def update_settings(payload: BackupSettingsUpdate, current_user: User = Depends(require_roles(["admin"]))):
    updated = save_backup_settings(payload.dict())
    return {"status": "ok", "settings": updated}

@router.post("/test-google-drive")
def test_google_drive(current_user: User = Depends(require_roles(["admin"]))):
    # 1. Create a quick backup
    res = create_database_backup(upload_to_gdrive=False)
    if res.get("status") != "ok":
        raise HTTPException(status_code=500, detail="Не удалось создать резервную копию для теста")
    
    # 2. Upload to Google Drive
    upload_res = upload_backup_to_google_drive(res["path"])
    if upload_res.get("status") != "ok":
        raise HTTPException(status_code=400, detail=upload_res.get("message", "Ошибка загрузки на Google Диск"))
    
    return {
        "status": "ok",
        "message": f"Тестовый бэкап успешно отправлен на ваш Google Диск!",
        "details": upload_res
    }
