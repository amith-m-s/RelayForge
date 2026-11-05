from types import SimpleNamespace

import pytest

import app.core.security as security
from app.core.security import (
    create_access_token,
    hash_password,
    sign_webhook_payload,
    verify_password,
)


def test_password_hashing_roundtrip() -> None:
    hashed = hash_password("very-strong-password")
    assert verify_password("very-strong-password", hashed)


def test_webhook_signature_is_deterministic() -> None:
    sig1 = sign_webhook_payload(b'{"ok":true}', "1700000000")
    sig2 = sign_webhook_payload(b'{"ok":true}', "1700000000")
    assert sig1 == sig2


@pytest.mark.parametrize(
    "claim_name",
    [
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
    ],
)
def test_access_token_rejects_reserved_extra_claims(claim_name: str) -> None:
    with pytest.raises(ValueError, match="reserved JWT claims"):
        create_access_token(subject="trusted-user", extra_claims={claim_name: "attacker-value"})


def test_access_token_allows_non_reserved_extra_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        security,
        "get_settings",
        lambda: SimpleNamespace(secret_key="test-secret", access_token_expire_minutes=15),
    )

    token = create_access_token(
        subject="trusted-user",
        organization_id="trusted-organization",
        role="member",
        extra_claims={"feature": "beta"},
    )
    payload = security.decode_token(token, expected_type="access")

    assert payload["sub"] == "trusted-user"
    assert payload["organization_id"] == "trusted-organization"
    assert payload["role"] == "member"
    assert payload["feature"] == "beta"
