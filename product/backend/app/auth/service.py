from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import create_access_token, hash_password, verify_password


class AuthError(Exception):
    pass


def authenticate(db: Session, username: str, password: str) -> tuple[User, str]:
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Identifiants invalides")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user, create_access_token(user.username, user.role)


def create_user(db: Session, *, username: str, email: str, password: str, role: str = "analyst") -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()
