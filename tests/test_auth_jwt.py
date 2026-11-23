import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import get_db
from app.main import app
from app.modules.auth.models import User, UserRole
from app.modules.auth.security import create_access_token, decode_access_token, hash_password


def _setup_auth_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    User.__table__.create(bind=engine)

    db = TestingSession()
    db.add(
        User(
            full_name="Carlos Rojas",
            email="conductor@rimac.pe",
            password_hash=hash_password("eco2026"),
            role=UserRole.CONDUCTOR,
            zone_sector="Rimac Centro",
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_jwt_create_and_decode_roundtrip():
    token = create_access_token(7, "CIUDADANO", "vecino@rimac.pe")
    claims = decode_access_token(token)
    assert claims["sub"] == "7"
    assert claims["role"] == "CIUDADANO"
    assert claims["email"] == "vecino@rimac.pe"

    with pytest.raises(ValueError):
        decode_access_token(token + "tampered")


def test_login_returns_valid_jwt_and_enforces_role():
    client = _setup_auth_client()
    try:
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Maria Lopez",
                "email": "maria@rimac.pe",
                "password": "secret",
                "zone_sector": "Rimac Centro",
            },
        )
        assert reg.status_code == 201

        ok_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "conductor@rimac.pe",
                "password": "eco2026",
                "expected_role": "CONDUCTOR",
            },
        )
        assert ok_login.status_code == 200
        body = ok_login.json()
        assert body["token_type"] == "bearer"
        claims = decode_access_token(body["access_token"])
        assert claims["role"] == "CONDUCTOR"

        wrong_role = client.post(
            "/api/v1/auth/login",
            json={
                "email": "conductor@rimac.pe",
                "password": "eco2026",
                "expected_role": "ADMIN",
            },
        )
        assert wrong_role.status_code == 403

        me_ok = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert me_ok.status_code == 200
        assert me_ok.json()["role"] == "CONDUCTOR"

        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    finally:
        app.dependency_overrides.clear()
