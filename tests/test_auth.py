import pytest
from fastapi import HTTPException
from api.auth import hash_password, verify_password, create_token, decode_token


def test_hash_is_not_plaintext():
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"


def test_verify_correct_password():
    hashed = hash_password("correctpassword")
    assert verify_password("correctpassword", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_token_returns_string():
    token = create_token(user_id=1)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token_recovers_user_id():
    token = create_token(user_id=42)
    payload = decode_token(token)
    assert payload["user_id"] == 42


def test_decode_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("this.is.not.a.valid.token")
    assert exc_info.value.status_code == 401


def test_decode_tampered_token_raises_401():
    token = create_token(user_id=1)
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401
