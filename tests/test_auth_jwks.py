import base64
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from app.core import auth
from app.core.config import settings


def _b64url_uint(value: int) -> str:
    data = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@pytest.fixture
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()
    public_jwk = {
        "kty": "RSA",
        "use": "sig",
        "kid": "test-key",
        "alg": "RS256",
        "n": _b64url_uint(public_numbers.n),
        "e": _b64url_uint(public_numbers.e),
    }
    return private_pem, public_jwk


@pytest.fixture(autouse=True)
def auth0_settings(monkeypatch):
    monkeypatch.setattr(settings, "auth0_domain", "tenant.example.auth0.com")
    monkeypatch.setattr(settings, "auth0_audience", "https://api.smartinvoice.test")
    auth.clear_jwks_cache()
    yield
    auth.clear_jwks_cache()


def _cache_signing_key(public_jwk: dict) -> None:
    auth._JWKS_CACHE["keys_by_kid"] = {public_jwk["kid"]: public_jwk}
    auth._JWKS_CACHE["expires_at"] = time.monotonic() + auth.JWKS_CACHE_TTL_SECONDS


def _encode_token(private_pem: bytes, claims: dict, kid: str = "test-key") -> str:
    return jwt.encode(
        claims,
        private_pem,
        algorithm="RS256",
        headers={"kid": kid},
    )


def _valid_claims(**overrides) -> dict:
    claims = {
        "sub": "auth0|user123",
        "aud": settings.auth0_audience,
        "iss": f"https://{settings.auth0_domain}/",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return claims


@pytest.mark.asyncio
async def test_verify_jwt_accepts_valid_auth0_rs256_token(rsa_keypair):
    private_pem, public_jwk = rsa_keypair
    _cache_signing_key(public_jwk)

    token = _encode_token(private_pem, _valid_claims())

    payload = await auth.verify_jwt(token)

    assert payload["sub"] == "auth0|user123"


@pytest.mark.asyncio
async def test_verify_jwt_fetches_and_caches_auth0_jwks(monkeypatch, rsa_keypair):
    private_pem, public_jwk = rsa_keypair
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"keys": [public_jwk]}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url):
            calls.append(url)
            return FakeResponse()

    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)
    token = _encode_token(private_pem, _valid_claims())

    assert (await auth.verify_jwt(token))["sub"] == "auth0|user123"
    assert (await auth.verify_jwt(token))["sub"] == "auth0|user123"

    assert calls == ["https://tenant.example.auth0.com/.well-known/jwks.json"]


@pytest.mark.asyncio
async def test_verify_jwt_rejects_expired_token(rsa_keypair):
    private_pem, public_jwk = rsa_keypair
    _cache_signing_key(public_jwk)
    token = _encode_token(private_pem, _valid_claims(exp=int(time.time()) - 1))

    with pytest.raises(auth.AuthError, match="Token has expired"):
        await auth.verify_jwt(token)


@pytest.mark.asyncio
async def test_verify_jwt_rejects_wrong_audience(rsa_keypair):
    private_pem, public_jwk = rsa_keypair
    _cache_signing_key(public_jwk)
    token = _encode_token(private_pem, _valid_claims(aud="https://wrong.example"))

    with pytest.raises(auth.AuthError, match="Invalid token claims"):
        await auth.verify_jwt(token)


@pytest.mark.asyncio
async def test_verify_jwt_rejects_wrong_issuer(rsa_keypair):
    private_pem, public_jwk = rsa_keypair
    _cache_signing_key(public_jwk)
    token = _encode_token(private_pem, _valid_claims(iss="https://evil.example/"))

    with pytest.raises(auth.AuthError, match="Invalid token claims"):
        await auth.verify_jwt(token)


@pytest.mark.asyncio
async def test_verify_jwt_rejects_malformed_token():
    with pytest.raises(auth.AuthError, match="Invalid token"):
        await auth.verify_jwt("not-a-valid-jwt")


@pytest.mark.asyncio
async def test_verify_jwt_rejects_non_rs256_token(rsa_keypair):
    private_pem, public_jwk = rsa_keypair
    _cache_signing_key(public_jwk)
    token = jwt.encode(
        _valid_claims(),
        "shared-secret",
        algorithm="HS256",
        headers={"kid": "test-key"},
    )

    with pytest.raises(auth.AuthError, match="Invalid token signing algorithm"):
        await auth.verify_jwt(token)
