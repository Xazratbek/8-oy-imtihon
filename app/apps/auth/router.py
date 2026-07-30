from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.apps.auth.models import User
from app.apps.auth.schemas import GoogleLoginRequest, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from app.apps.auth.service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=TokenResponse, summary="Email orqali ro'yxatdan o'tish")
async def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse, summary="Email va parol orqali login")
async def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.login(payload)


@router.post("/token", response_model=TokenResponse, summary="Swagger OAuth2 login")
async def swagger_token(
    form: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.login_with_email_password(form.username, form.password)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh token rotation")
async def refresh(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.refresh(payload)


@router.post("/logout", summary="Refresh tokenni bekor qilish")
async def logout(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> dict:
    return await service.logout(payload)


@router.get("/me", response_model=UserOut, summary="Current user profili")
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/google", response_model=TokenResponse, summary="Google Sign-In")
async def google_login(payload: GoogleLoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return await service.google_login(payload)

