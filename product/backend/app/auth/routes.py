from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, TokenResponse, UserResponse
from app.auth.service import AuthError, authenticate
from app.core.deps import get_current_user, get_db

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Authentification utilisateur")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        _, token = authenticate(db, payload.username, payload.password)
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Informations utilisateur courant")
def me(current_user=Depends(get_current_user)):
    return current_user
