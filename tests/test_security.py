from app.core.security import hash_password, sign_webhook_payload, verify_password


def test_password_hashing_roundtrip() -> None:
    hashed = hash_password("very-strong-password")
    assert verify_password("very-strong-password", hashed)


def test_webhook_signature_is_deterministic() -> None:
    sig1 = sign_webhook_payload(b'{"ok":true}', "1700000000")
    sig2 = sign_webhook_payload(b'{"ok":true}', "1700000000")
    assert sig1 == sig2
