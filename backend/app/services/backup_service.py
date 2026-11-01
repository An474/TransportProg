import os
import json
import base64
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings

def get_backup_settings() -> Dict[str, Any]:
    """Retrieves backup and cloud integration settings."""
    default_settings = {
        "google_drive_webhook_url": os.getenv("GOOGLE_DRIVE_WEBHOOK_URL", ""),
        "google_drive_enabled": False,
        "last_google_drive_backup": None,
        "last_google_drive_status": None,
        "last_google_drive_file_id": None
    }
    if os.path.exists(settings.SETTINGS_FILE):
        try:
            with open(settings.SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_settings.update(saved)
        except Exception:
            pass
    return default_settings

def save_backup_settings(new_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Saves updated backup and cloud integration settings."""
    current = get_backup_settings()
    current.update(new_settings)
    os.makedirs(os.path.dirname(settings.SETTINGS_FILE), exist_ok=True)
    with open(settings.SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    return current

def upload_backup_to_google_drive(backup_path: str) -> Dict[str, Any]:
    """
    Sends the zip backup file to the Google Apps Script Webhook.
    Returns status and response details.
    """
    conf = get_backup_settings()
    webhook_url = conf.get("google_drive_webhook_url", "").strip()
    if not webhook_url:
        return {"status": "skipped", "message": "Google Drive Webhook URL не указан"}

    if not os.path.exists(backup_path):
        return {"status": "error", "message": f"Файл бэкапа не найден: {backup_path}"}

    filename = os.path.basename(backup_path)
    try:
        with open(backup_path, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "filename": filename,
            "content": encoded_content
        }

        # Follow redirects because Google Apps Script 302s to script.googleusercontent.com
        with httpx.Client(timeout=90.0, follow_redirects=True) as client:
            resp = client.post(webhook_url, json=payload)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if resp.status_code == 200:
            try:
                res_data = resp.json()
            except Exception:
                res_data = {"status": "ok", "raw": resp.text}

            if res_data.get("status") == "ok":
                status_msg = f"Успешно выгружено на Google Диск ({filename})"
                save_backup_settings({
                    "last_google_drive_backup": now_str,
                    "last_google_drive_status": status_msg,
                    "last_google_drive_file_id": res_data.get("fileId")
                })
                return {
                    "status": "ok",
                    "message": status_msg,
                    "file_id": res_data.get("fileId"),
                    "file_url": res_data.get("url")
                }
            else:
                err_msg = res_data.get("message", "Неизвестная ошибка скрипта Google Apps Script")
                save_backup_settings({
                    "last_google_drive_backup": now_str,
                    "last_google_drive_status": f"Ошибка: {err_msg}"
                })
                return {"status": "error", "message": err_msg}
        else:
            err_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
            save_backup_settings({
                "last_google_drive_backup": now_str,
                "last_google_drive_status": f"Ошибка {err_msg}"
            })
            return {"status": "error", "message": err_msg}

    except Exception as e:
        err_msg = f"Исключение при отправке на Google Диск: {str(e)}"
        save_backup_settings({
            "last_google_drive_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_google_drive_status": f"Ошибка: {str(e)}"
        })
        return {"status": "error", "message": err_msg}

def create_database_backup(upload_to_gdrive: bool = True) -> Dict[str, Any]:
    """
    Creates a timestamped backup copy of the database and optionally
    uploads it to Google Drive if configured.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
    
    # Resolve SQLite file path
    db_file = settings.DATABASE_URL.replace("sqlite:///", "")
    backup_filename = f"backup_transport_{timestamp}.zip"
    backup_path = os.path.join(settings.BACKUP_DIR, backup_filename)

    if not os.path.exists(db_file):
        return {"status": "error", "message": f"Файл базы данных не найден: {db_file}"}

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(db_file, arcname="transport.db")

    result = {
        "status": "ok",
        "filename": backup_filename,
        "path": backup_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Upload to Google Drive if enabled
    conf = get_backup_settings()
    if upload_to_gdrive and conf.get("google_drive_enabled") and conf.get("google_drive_webhook_url"):
        gdrive_res = upload_backup_to_google_drive(backup_path)
        result["google_drive"] = gdrive_res
    else:
        result["google_drive"] = {"status": "skipped", "message": "Выгрузка в облако отключена в настройках"}

    return result

def list_backups() -> List[dict]:
    """Lists available local backups."""
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
    files = []
    for f in os.listdir(settings.BACKUP_DIR):
        if f.endswith(".zip") or f.endswith(".db"):
            fp = os.path.join(settings.BACKUP_DIR, f)
            stat = os.stat(fp)
            files.append({
                "filename": f,
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            })
    files.sort(key=lambda x: x["created_at"], reverse=True)
    return files
