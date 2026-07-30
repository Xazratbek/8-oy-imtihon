from datetime import UTC, datetime, timedelta

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.auth.repository import AuthRepository
from app.apps.auth.schemas import GoogleLoginRequest, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.common.exceptions import ConflictError, UnauthorizedError
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, token_hash, verify_password


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuthRepository(db)

    async def issue_tokens(self, user) -> TokenResponse:
        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id)
        await self.repo.create_refresh_token(
            user.id,
            token_hash(refresh),
            datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        return TokenResponse(access_token=access, refresh_token=refresh)

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        if await self.repo.get_user_by_email(str(payload.email)):
            raise ConflictError("Email allaqachon ro'yxatdan o'tgan")
        user = await self.repo.create_user(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        return await self.issue_tokens(user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        return await self.login_with_email_password(str(payload.email), payload.password)

    async def login_with_email_password(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_user_by_email(email)
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Email yoki parol xato")
        return await self.issue_tokens(user)

    async def refresh(self, payload: RefreshRequest) -> TokenResponse:
        try:
            data = decode_token(payload.refresh_token, "refresh")
        except ValueError as exc:
            raise UnauthorizedError("Refresh token yaroqsiz") from exc
        old = await self.repo.get_refresh_token(token_hash(payload.refresh_token))
        if not old or old.revoked_at or old.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token ishlamaydi")
        old.revoked_at = datetime.now(UTC)
        user = await self.repo.get_user(data["sub"])
        if not user:
            raise UnauthorizedError("User topilmadi")
        return await self.issue_tokens(user)

    async def logout(self, payload: RefreshRequest) -> dict:
        row = await self.repo.get_refresh_token(token_hash(payload.refresh_token))
        if row and not row.revoked_at:
            row.revoked_at = datetime.now(UTC)
            await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"logged_out": True}}

    async def google_login(self, payload: GoogleLoginRequest) -> TokenResponse:
        if not settings.google_client_id:
            raise UnauthorizedError("GOOGLE_CLIENT_ID sozlanmagan")
        info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
        email = info.get("email")
        provider_user_id = info.get("sub")
        if not email or not provider_user_id:
            raise UnauthorizedError("Google token ichida email/sub yo'q")
        user = await self.repo.get_user_by_email(email)
        if not user:
            user = await self.repo.create_user(
                email=email,
                password_hash=None,
                first_name=info.get("given_name", ""),
                last_name=info.get("family_name", ""),
                avatar_url=info.get("picture"),
                email_verified_at=datetime.now(UTC),
            )
        if not await self.repo.get_oauth_account("google", provider_user_id):
            self.repo.add_oauth_account(user.id, "google", provider_user_id, email)
        return await self.issue_tokens(user)

