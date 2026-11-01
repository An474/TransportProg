import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = (BASE_BACKEND_DIR / "data" / "transport.db").as_posix()
DEFAULT_BACKUP_PATH = (BASE_BACKEND_DIR / "data" / "backups").as_posix()
DEFAULT_UPLOAD_PATH = (BASE_BACKEND_DIR / "data" / "uploads").as_posix()
SETTINGS_FILE_PATH = (BASE_BACKEND_DIR / "data" / "settings.json").as_posix()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Информационная система транспортного отдела"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-transport-department-key-2026-safe")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Versioning & GitHub
    APP_VERSION: str = "1.0.0"
    GITHUB_REPO: str = "An474/TransportProg"

    # SQLite default, or postgresql+psycopg2://user:password@localhost/transport_db in cloud
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", DEFAULT_BACKUP_PATH)
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", DEFAULT_UPLOAD_PATH)
    SETTINGS_FILE: str = SETTINGS_FILE_PATH

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
