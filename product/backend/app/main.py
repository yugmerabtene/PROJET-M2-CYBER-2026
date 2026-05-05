from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth.routes import router as auth_router
from app.auth.service import create_user, get_by_username
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Outil de supervision réseau orienté SOC — DevinciWatch MVP",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/auth", tags=["auth"])

    @app.get("/health", tags=["system"], summary="Santé applicative")
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
