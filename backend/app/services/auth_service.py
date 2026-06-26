import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as redis
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.middleware.error_handler import AuthenticationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self) -> None:
        self._redis_client: redis.Redis | None | bool = None
        self._memory_blacklist: set[str] = set()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, subject: str) -> str:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        return self._create_token(subject=subject, token_type="access", expires_delta=expires_delta)

    def create_refresh_token(self, subject: str) -> str:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
        return self._create_token(subject=subject, token_type="refresh", expires_delta=expires_delta)

    def _create_token(self, subject: str, token_type: str, expires_delta: timedelta) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    def decode_token(self, token: str, expected_type: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except JWTError as exc:
            raise AuthenticationError("Oturum doğrulanamadı.") from exc

        if payload.get("type") != expected_type:
            raise AuthenticationError("Geçersiz token türü.")
        if not payload.get("sub"):
            raise AuthenticationError("Token içeriği geçersiz.")
        return payload

    async def _get_redis_client(self) -> redis.Redis | None:
        if not settings.redis_url:
            return None
        if self._redis_client is False:
            return None
        if self._redis_client is None:
            try:
                client = redis.from_url(settings.redis_url, decode_responses=True)
                await client.ping()
                self._redis_client = client
            except Exception:
                self._redis_client = False
                return None
        return self._redis_client if isinstance(self._redis_client, redis.Redis) else None

    async def blacklist_refresh_token(self, token: str) -> None:
        payload = self.decode_token(token, expected_type="refresh")
        jti = payload.get("jti")
        exp = int(payload.get("exp", 0))
        ttl = max(exp - int(datetime.now(UTC).timestamp()), 1)
        if not jti:
            return
        client = await self._get_redis_client()
        if client is not None:
            await client.setex(f"refresh_blacklist:{jti}", ttl, "1")
        else:
            self._memory_blacklist.add(jti)

    async def is_refresh_token_blacklisted(self, jti: str | None) -> bool:
        if not jti:
            return True
        client = await self._get_redis_client()
        if client is not None:
            return bool(await client.get(f"refresh_blacklist:{jti}"))
        return jti in self._memory_blacklist


auth_service = AuthService()
