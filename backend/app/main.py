import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal, get_db
from backend.app.seeds.sources import seed_database_if_empty
from backend.app.services.scheduler import start_scheduler, shutdown_scheduler

from backend.app.api.routes_radar import router as radar_router, record_radar_interaction
from backend.app.api.routes_stories import router as stories_router
from backend.app.api.routes_feed import router as feed_router
from backend.app.api.routes_sources import router as sources_router
from backend.app.api.routes_preferences import router as preferences_router
from backend.app.api.routes_stats import router as stats_router

from backend.app.schemas.interaction import InteractionCreate, RadarInteractResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CLIVE")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables, seed DB, start scheduler
    logger.info("Initializing CLIVE Database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
        logger.info("CLIVE Database seeded with default sources and intelligence stories.")
    finally:
        db.close()
        
    start_scheduler()
    logger.info("CLIVE Engine is LIVE and operational.")
    yield
    # Shutdown: Stop scheduler
    shutdown_scheduler()
    logger.info("CLIVE Engine shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=f"{settings.APP_NAME} — {settings.TAGLINE}",
    lifespan=lifespan
)

# Setup CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(feed_router)
app.include_router(radar_router)
app.include_router(stories_router)
app.include_router(sources_router)
app.include_router(preferences_router)
app.include_router(stats_router)

@app.post("/api/interactions", response_model=RadarInteractResponse, tags=["Radar"])
def record_general_interaction(
    payload: InteractionCreate,
    db: Session = Depends(get_db)
):
    return record_radar_interaction(payload=payload, db=db)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Web Application Frontend SPA Serving
DIST_DIR = os.path.abspath("frontend/dist") if os.path.exists("frontend/dist") else os.path.abspath("dist")

if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json"]:
            raise HTTPException(status_code=404, detail="Not Found")
        
        file_path = os.path.join(DIST_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
            
        index_path = os.path.join(DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "online"}
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "tagline": settings.TAGLINE,
            "status": "online"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

