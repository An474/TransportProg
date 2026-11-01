import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.services.import_service import init_db_data
from app.services.backup_service import create_database_backup

# Routers
from app.api.auth import router as auth_router
from app.api.references import router as ref_router
from app.api.vehicles import router as vehicles_router
from app.api.drivers import router as drivers_router
from app.api.assignments import router as assignments_router
from app.api.waybills import router as waybills_router
from app.api.fines import router as fines_router
from app.api.maintenance import router as maint_router
from app.api.fuel import router as fuel_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router
from app.api.backup import router as backup_router
from app.api.system import router as system_router

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure all database tables exist
    Base.metadata.create_all(bind=engine)
    
    # 2. Seed initial data (vehicles, drivers, companies, departments, fines)
    db = SessionLocal()
    try:
        init_db_data(db)
    finally:
        db.close()

    # 3. Setup daily automated backup at 00:00
    scheduler.add_job(create_database_backup, 'cron', hour=0, minute=0, id="daily_backup")
    scheduler.start()
    
    yield
    
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Единая автоматизированная информационная система транспортного отдела",
    lifespan=lifespan
)

# Enable CORS for local network access (allow other computers in the office to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(ref_router, prefix=settings.API_V1_STR)
app.include_router(vehicles_router, prefix=settings.API_V1_STR)
app.include_router(drivers_router, prefix=settings.API_V1_STR)
app.include_router(assignments_router, prefix=settings.API_V1_STR)
app.include_router(waybills_router, prefix=settings.API_V1_STR)
app.include_router(fines_router, prefix=settings.API_V1_STR)
app.include_router(maint_router, prefix=settings.API_V1_STR)
app.include_router(fuel_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(backup_router, prefix=settings.API_V1_STR)
app.include_router(system_router, prefix=settings.API_V1_STR)

# Mount static frontend build if it exists
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/dist"))
if not os.path.exists(frontend_dist):
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API and Swagger docs through
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Маршрут не найден")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": settings.PROJECT_NAME,
            "docs_url": "/docs",
            "api_prefix": settings.API_V1_STR
        }
