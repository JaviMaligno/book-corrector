"""Offline contracts for the existing HS256 and bcrypt authentication API."""

import socket

import pytest
from jose import jwt

from server import auth


@pytest.fixture(autouse=True)
def offline_auth(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "synthetic-offline-test-key-at-least-32-bytes")

    def deny_network(*args, **kwargs):
        raise AssertionError("Authentication contracts must not open network connections")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)


def test_password_hash_and_verify_preserve_bcrypt_contract():
    password_hash = auth.hash_password("synthetic-password")
    assert password_hash.startswith("$2b$")
    assert auth.verify_password("synthetic-password", password_hash)
    assert not auth.verify_password("different-password", password_hash)
    with pytest.raises(ValueError):
        auth.hash_password("a" * 73)


def test_token_subject_expiry_and_algorithm_are_preserved():
    token = auth.create_access_token("synthetic-user")
    claims = jwt.decode(token, auth.get_secret_key(), algorithms=["HS256"])
    assert claims["sub"] == "synthetic-user"
    assert claims["exp"] - claims["iat"] == 3600
    assert auth.verify_token(token) == "synthetic-user"
    assert auth.verify_token(auth.create_access_token("expired", expires_minutes=-1)) is None
    wrong_algorithm = jwt.encode(
        {"sub": "synthetic-user"}, auth.get_secret_key(), algorithm="HS384"
    )
    assert auth.verify_token(wrong_algorithm) is None
    foreign_key = jwt.encode(
        {"sub": "synthetic-user"}, "different-synthetic-key", algorithm="HS256"
    )
    assert auth.verify_token(foreign_key) is None
