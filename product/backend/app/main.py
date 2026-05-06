from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.alerts.routes import router as alerts_router
from app.assets.routes import router as assets_router
from app.auth.routes import router as auth_router
from app.auth.service import create_user, get_by_username
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.correlation.routes import router as correlation_router
from app.reports.routes import router as reports_router
from app.telemetry.routes import router as telemetry_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.3.0",
        description="Outil de supervision reseau oriente SOC - DevinciWatch MVP",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
    app.include_router(assets_router, prefix="/assets", tags=["assets"])
    app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
    app.include_router(correlation_router, prefix="/correlation", tags=["correlation"])
    app.include_router(reports_router, prefix="/reports", tags=["reports"])

    @app.get("/health", tags=["system"], summary="Sante applicative")
    def health() -> dict:
        db_status = "ok"
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"
        return {"status": "ok", "env": settings.app_env, "database": db_status}

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            if get_by_username(db, settings.default_admin_username) is None:
                create_user(
                    db,
                    username=settings.default_admin_username,
                    email="admin@devinciwatch.local",
                    password=settings.default_admin_password,
                    role="admin",
                )
        finally:
            db.close()

    return app


app = create_app()
