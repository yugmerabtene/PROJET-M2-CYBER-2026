from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token

bearer = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
    db: Session = Depends(get_db),
):
    from app.auth.models import User

    try:
        payload = decode_token(credentials.credentials)
        username: str = payload.get("sub")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rôle admin requis")
    return current_user


def require_agent(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
):
    from app.core.config import settings

    if credentials.credentials != settings.agent_ingest_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clé agent invalide")
