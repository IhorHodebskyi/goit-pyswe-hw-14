from unittest.mock import Mock, patch

import pytest
from sqlalchemy import select

from src.entity.models import User
from src.services.auth import auth_service
from tests.conftest import client, TestingSessionLocal
from src.conf import messages


user_mock = {"username": "Jon Snow", "email": "7ySd1@example.com", "password": "123456789", "confirmed": True,
             "role": "user"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_mock)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "password" not in data
    assert "id" in data
    assert "avatar" in data
    assert data["username"] == user_mock["username"]
    assert data["email"] == user_mock["email"]
    assert mock_send_email.calld


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_mock)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXISTS

    assert mock_send_email.calld


def test_not_confirmed_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_mock["email"], "password": user_mock["password"]})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.EMAIL_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter_by(email=user_mock.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post("api/auth/login",
                           data={"username": user_mock["email"], "password": user_mock["password"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password(client):
    response = client.post("api/auth/login",
                           data={"username": user_mock["email"], "password": "wrong_password"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.CREDENTIALS_EXCEPTION


def test_wrong_email(client):
    response = client.post("api/auth/login",
                           data={"username": "wrong_email", "password": user_mock["password"]})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.CREDENTIALS_EXCEPTION


def test_validation_error(client):
    response = client.post("api/auth/login",
                           data={"password": user_mock["password"]})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_refresh_token_success(client):
    async with TestingSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == user_mock["email"]))).scalar_one_or_none()
        user.confirmed = True
        await session.commit()

    response = client.post("api/auth/login",
                           data={"username": user_mock["email"], "password": user_mock["password"]})
    tokens = response.json()

    headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    response = client.get("api/auth/refresh_token", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid_token(client):
    headers = {"Authorization": "Bearer invalid.token.string"}
    response = client.get("api/auth/refresh_token", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_confirmed_email(client, get_token):
    with patch.object(auth_service, "cache") as redis_mok:
        redis_mok.get.return_value = None
        tokens = get_token
        response = client.get(f"/api/auth/confirmed_email/{tokens}")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED


@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(client, get_token):
    with patch.object(auth_service, "cache") as redis_mok:
        redis_mok.get.return_value = None
        tokens = get_token
        client.get(f"/api/auth/confirmed_email/{tokens}")

        response = client.get(f"/api/auth/confirmed_email/{tokens}")
        data = response.json()
        assert response.status_code == 200
        assert data["message"] == messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED


@pytest.mark.asyncio
async def test_confirmed_email_invalid_token(client):
    response = client.get("/api/auth/confirmed_email/invalid.token.string")
    data = response.json()
    assert response.status_code == 422
    assert "detail" in data



def test_request_email_send(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/request_email", json={"email": user_mock["email"]})
    data = response.json()
    print(f"response: {response}")
    assert response.status_code == 200
    assert "message" in data



def test_request_email_already_confirmed(client):
    response = client.post("api/auth/request_email", json={"email": user_mock["email"]})
    data = response.json()
    assert response.status_code == 200
    assert data["message"] == messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED


def test_request_email_invalid(client):
    response = client.post("api/auth/request_email", json={"email": "nonexistent@example.com"})
    data = response.json()
    assert response.status_code == 404
    assert data["detail"] == messages.USER_NOT_FOUND
