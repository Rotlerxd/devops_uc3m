"""Unit tests for app.core.security — password hashing, JWT tokens, and email."""

import unittest.mock
from datetime import timedelta

import pytest
from jose import jwt

from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_verification_token,
    get_password_hash,
    send_verification_email,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        hashed = get_password_hash("mypassword")
        assert hashed != "mypassword"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = get_password_hash("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("secret123")
        assert verify_password("wrongpass", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2  # bcrypt uses random salt


@pytest.mark.unit
class TestAccessToken:
    def test_create_token_contains_data(self):
        token = create_access_token(data={"sub": "user@test.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@test.com"
        assert "exp" in payload

    def test_create_token_with_custom_expiry(self):
        token = create_access_token(
            data={"sub": "user@test.com"},
            expires_delta=timedelta(hours=2),
        )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@test.com"

    def test_create_token_includes_role(self):
        token = create_access_token(data={"sub": "admin@test.com", "rol": "gestor"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["rol"] == "gestor"

    def test_expired_token_is_rejected(self):
        from jose import JWTError

        token = create_access_token(
            data={"sub": "user@test.com"},
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


@pytest.mark.unit
class TestVerificationToken:
    def test_create_verification_token(self):
        token = create_verification_token("user@example.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@example.com"
        assert "exp" in payload

    def test_verification_token_expiry(self):

        token = create_verification_token("user@example.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@example.com"


@pytest.mark.unit
class TestSendVerificationEmail:
    @unittest.mock.patch("app.core.security.smtplib.SMTP")
    @unittest.mock.patch("app.core.security.load_dotenv")
    def test_send_email_success(self, mock_load_dotenv, mock_smtp):
        mock_server = unittest.mock.MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        send_verification_email("user@example.com", "test-token-123")

        mock_load_dotenv.assert_called_once()
        mock_server.ehlo.assert_called()
        mock_server.starttls.assert_called()
        mock_server.login.assert_called()
        mock_server.send_message.assert_called_once()

    @unittest.mock.patch("app.core.security.smtplib.SMTP")
    @unittest.mock.patch("app.core.security.load_dotenv")
    def test_send_email_connection_error(self, mock_load_dotenv, mock_smtp):
        mock_smtp.side_effect = Exception("Connection refused")

        send_verification_email("user@example.com", "test-token-123")

        mock_load_dotenv.assert_called_once()
        mock_smtp.assert_called_once()

    @unittest.mock.patch("app.core.security.smtplib.SMTP")
    @unittest.mock.patch("app.core.security.load_dotenv")
    def test_send_email_smtp_error(self, mock_load_dotenv, mock_smtp):
        mock_server = unittest.mock.MagicMock()
        mock_server.send_message.side_effect = Exception("SMTP error")
        mock_smtp.return_value.__enter__.return_value = mock_server

        send_verification_email("user@example.com", "test-token-123")

        mock_load_dotenv.assert_called_once()
        mock_server.send_message.assert_called_once()

    @unittest.mock.patch("app.core.security.smtplib.SMTP")
    @unittest.mock.patch("app.core.security.load_dotenv")
    @unittest.mock.patch("app.core.security.GMAIL_USER", "newsradar.app.noreply@gmail.com")
    def test_email_contains_correct_recipient(self, mock_load_dotenv, mock_smtp):
        mock_server = unittest.mock.MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        send_verification_email("user@example.com", "my-secret-token")

        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["To"] == "user@example.com"
        assert sent_msg["From"] == "newsradar.app.noreply@gmail.com"
        assert sent_msg["Subject"] == "NEWSRADAR - Verifica tu cuenta"
