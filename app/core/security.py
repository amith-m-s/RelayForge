from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Final, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from cryptography.fernet import Fernet

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
ALGORITHM = "HS256"

_RESERVED_JWT_CLAIMS: Final[frozenset[str]] = frozenset(
    {
        "aud",
        "exp",
        "iat",
        "iss",
        "jti",
        "nbf",
        "organization_id",
        "role",
        "sub",
        "tenant_id",
        "token_id",
        "type",
    }
)


class TokenError(ValueError):
    pass


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(password: str, hashed: str) -> bool:
    return cast(bool, pwd_context.verify(password, hashed))


def _utc_now() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    subject: str,
    organization_id: str | None = None,
    role: str | None = None,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create an access token without allowing extensions to replace security claims."""
    if extra_claims:
        reserved_claims = _RESERVED_JWT_CLAIMS.intersection(extra_claims)
        if reserved_claims:
            names = ", ".join(sorted(reserved_claims))
            raise ValueError(f"extra_claims cannot override reserved JWT claims: {names}")

    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "exp": int(
            (
                _utc_now()
                + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
            ).timestamp()
        ),
        "iat": int(_utc_now().timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if organization_id is not None:
        payload["organization_id"] = organization_id
    if role is not None:
        payload["role"] = role
    if extra_claims:
        payload.update(extra_claims)
    return cast(str, jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM))


def create_refresh_token(subject: str, token_id: str, expires_days: int | None = None) -> str:
    settings = get_settings()
    payload = {
        "sub": subject,
        "token_id": token_id,
        "type": "refresh",
        "exp": int(
            (
                _utc_now() + timedelta(days=expires_days or settings.refresh_token_expire_days)
            ).timestamp()
        ),
        "iat": int(_utc_now().timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    return cast(str, jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM))


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = cast(dict[str, Any], jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM]))
    except JWTError as exc:
        raise TokenError("Invalid token") from exc
    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError("Unexpected token type")
    return payload


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def sign_webhook_payload(raw_body: bytes, timestamp: str, secret: str | None = None) -> str:
    settings = get_settings()
    key = secret if secret is not None else settings.webhook_signing_secret
    msg = timestamp.encode("utf-8") + b"." + raw_body
    return hmac.new(key.encode("utf-8"), msg, sha256).hexdigest()


def verify_webhook_signature(raw_body: bytes, timestamp: str, signature: str, secret: str | None = None) -> bool:
    expected = sign_webhook_payload(raw_body, timestamp, secret)
    return hmac.compare_digest(expected, signature)


def encrypt_webhook_secret(secret: str) -> str:
    key = get_settings().webhook_encryption_key.encode("utf-8")
    return Fernet(key).encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_webhook_secret(ciphertext: str) -> str:
    key = get_settings().webhook_encryption_key.encode("utf-8")
    return Fernet(key).decrypt(ciphertext.encode("utf-8")).decode("utf-8")
