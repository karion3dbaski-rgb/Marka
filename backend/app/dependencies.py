from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.middleware.error_handler import AuthenticationError, ForbiddenError
from app.models.user import User
from app.services.auth_service import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = auth_service.decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    try:
        parsed_user_id = UUID(user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationError("Token kullanıcı bilgisi geçersiz.") from exc

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthenticationError("Kullanıcı oturumu geçersiz veya pasif.")
    return user


async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_admin:
        raise ForbiddenError("Bu alan yalnızca yöneticilere açıktır.")
    return current_user
