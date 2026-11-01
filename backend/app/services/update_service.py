import os
import re
import shutil
import zipfile
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from app.services.backup_service import create_database_backup

def parse_version(v_str: str) -> tuple:
    """Parses 'v1.2.3' or '1.2' into a comparable tuple of integers."""
    clean = re.sub(r'^[vV]', '', str(v_str).strip())
    parts = []
    for p in clean.split('.'):
        digits = re.findall(r'\d+', p)
        if digits:
            parts.append(int(digits[0]))
        else:
            parts.append(0)
    return tuple(parts)

def check_for_updates() -> Dict[str, Any]:
    """
    Checks GitHub Releases for a newer version of the application.
    Repository: An474/TransportProg
    """
    repo = settings.GITHUB_REPO
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "TransportApp-Updater"
    }

    current_ver = settings.APP_VERSION

    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)

        if resp.status_code == 404:
            return {
                "has_update": False,
                "current_version": current_ver,
                "latest_version": current_ver,
                "release_name": "Актуальная версия",
                "release_notes": "На GitHub пока не опубликовано официальных релизов.",
                "published_at": None,
                "download_url": None
            }

        if resp.status_code != 200:
            return {
                "has_update": False,
                "current_version": current_ver,
                "latest_version": current_ver,
                "error": f"Ошибка GitHub API ({resp.status_code}): {resp.text[:150]}"
            }

        data = resp.json()
        tag_name = data.get("tag_name", "").lstrip("vV")
        release_notes = data.get("body", "Нет описания изменений.")
        published_at = data.get("published_at")
        release_name = data.get("name") or f"Версия {tag_name}"

        # Find update.zip asset or fallback to zipball
        download_url = None
        for asset in data.get("assets", []):
            if asset.get("name") in ["update.zip", "LocalLogistic_Update.zip"]:
                download_url = asset.get("browser_download_url")
                break

        if not download_url:
            download_url = data.get("zipball_url")

        has_update = parse_version(tag_name) > parse_version(current_ver)

        return {
            "has_update": has_update,
            "current_version": current_ver,
            "latest_version": tag_name,
            "release_name": release_name,
            "release_notes": release_notes,
            "published_at": published_at,
            "download_url": download_url
        }

    except Exception as e:
        return {
            "has_update": False,
            "current_version": current_ver,
            "latest_version": current_ver,
            "error": f"Не удалось подключиться к GitHub: {str(e)}"
        }

def perform_update(download_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Downloads the update package from GitHub, backs up the database,
    and updates backend/app and frontend/dist without touching backend/data.
    """
    # 1. Determine download URL
    if not download_url:
        check = check_for_updates()
        if not check.get("has_update") and not download_url:
            return {"status": "error", "message": "Нет доступных обновлений на GitHub"}
        download_url = check.get("download_url")

    if not download_url:
        return {"status": "error", "message": "Файл обновления update.zip не найден в релизе"}

    # 2. Make an automatic pre-update backup of the database
    backup_res = create_database_backup(upload_to_gdrive=True)
    if backup_res.get("status") != "ok":
        return {"status": "error", "message": "Не удалось создать резервную копию перед обновлением"}

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    updates_dir = os.path.join(root_dir, "backend", "data", "updates")
    os.makedirs(updates_dir, exist_ok=True)
    temp_zip = os.path.join(updates_dir, "incoming_update.zip")
    extract_dir = os.path.join(updates_dir, "extracted")

    try:
        # 3. Download the update zip
        headers = {"User-Agent": "TransportApp-Updater"}
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            with open(temp_zip, "wb") as f:
                with client.stream("GET", download_url, headers=headers) as resp:
                    if resp.status_code != 200:
                        return {"status": "error", "message": f"Ошибка скачивания ({resp.status_code})"}
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)

        # 4. Extract update package
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(temp_zip, "r") as zipf:
            zipf.extractall(extract_dir)

        # 5. Look for backend/app and frontend/dist inside the extracted folder
        # (Could be in root or in a subfolder like TransportProg-v1.0.1/)
        source_app = None
        source_dist = None

        for root, dirs, files in os.walk(extract_dir):
            if "app" in dirs and os.path.exists(os.path.join(root, "app", "main.py")):
                source_app = os.path.join(root, "app")
            if "dist" in dirs and os.path.exists(os.path.join(root, "dist", "index.html")):
                source_dist = os.path.join(root, "dist")

        target_app = os.path.join(root_dir, "backend", "app")
        target_dist = os.path.join(root_dir, "frontend", "dist")

        updated_components = []

        # Replace backend/app
        if source_app:
            shutil.copytree(source_app, target_app, dirs_exist_ok=True)
            updated_components.append("Бэкенд (backend/app)")

        # Replace frontend/dist
        if source_dist:
            os.makedirs(target_dist, exist_ok=True)
            shutil.copytree(source_dist, target_dist, dirs_exist_ok=True)
            updated_components.append("Интерфейс (frontend/dist)")

        # Clean up temporary update files
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

        return {
            "status": "ok",
            "message": "Обновление успешно загружено и установлено!",
            "updated_components": updated_components,
            "backup_created": backup_res.get("filename"),
            "restart_required": True
        }

    except Exception as e:
        return {"status": "error", "message": f"Сбой при установке обновления: {str(e)}"}
