from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.auth import LoginRequest, TokenResponse
from app.core.config.database import get_db
from app.services.auth_service import AuthService
from app.core.config.settings import Settings

settings = Settings()

auth_router = APIRouter(tags=["auth"], prefix="/auth")

@auth_router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    login_response = AuthService(db).login(
        email=data.email,
        password=data.password
    )

    return login_response
