from fastapi import APIRouter, HTTPException
from app.models import UserCreate, UserLogin, TokenResponse
from app.services.firebase_service import create_user, login_user

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    try:
        result = await create_user(user.email, user.password, user.name)
        return TokenResponse(
            token=result["token"],
            user_id=result["user_id"],
            email=user.email,
            name=user.name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    try:
        result = await login_user(credentials.email, credentials.password)
        return TokenResponse(
            token=result["token"],
            user_id=result["user_id"],
            email=credentials.email,
            name=result["name"]
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
