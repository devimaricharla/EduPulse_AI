
"""Tests for EduPulse AI account storage and authentication."""

import pytest

from src.auth import database


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Give each test its own temporary database."""
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "test_users.db",
    )
    database.initialize_database()


def test_database_initializes(isolated_database):
    assert database.DATABASE_PATH.exists()


def test_create_and_authenticate_user(isolated_database):
    user_id = database.create_user(
        "student01",
        "SecureTestPassword123!",
        "student",
    )

    user = database.authenticate_user(
        "student01",
        "SecureTestPassword123!",
    )

    assert user["id"] == user_id
    assert user["username"] == "student01"
    assert user["role"] == "student"
    assert "password_hash" not in user


def test_username_is_case_insensitive(isolated_database):
    database.create_user("student01", "Password123!", "student")

    user = database.authenticate_user("STUDENT01", "Password123!")

    assert user is not None
    assert user["role"] == "student"


def test_wrong_password_is_rejected(isolated_database):
    database.create_user("student01", "Password123!", "student")

    assert database.authenticate_user(
        "student01",
        "WrongPassword123!",
    ) is None


def test_unknown_user_is_rejected(isolated_database):
    assert database.authenticate_user(
        "unknown",
        "Password123!",
    ) is None


def test_invalid_role_is_rejected(isolated_database):
    with pytest.raises(ValueError, match="Invalid user role"):
        database.create_user("user01", "Password123!", "superadmin")


def test_duplicate_username_is_rejected(isolated_database):
    database.create_user("student01", "Password123!", "student")

    with pytest.raises(Exception):
        database.create_user("STUDENT01", "Password456!", "student")


def test_empty_password_is_rejected(isolated_database):
    with pytest.raises(ValueError, match="non-empty"):
        database.create_user("student01", "", "student")


def test_oversized_password_is_rejected(isolated_database):
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        database.create_user("student01", "a" * 73, "student")


def test_inactive_user_cannot_log_in(isolated_database):
    user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )

    database.set_user_active(user_id, False)

    assert database.authenticate_user(
        "student01",
        "Password123!",
    ) is None


def test_password_hash_is_not_plain_text(isolated_database):
    database.create_user("student01", "Password123!", "student")

    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            ("student01",),
        ).fetchone()

    assert row["password_hash"] != b"Password123!"
    assert b"Password123!" not in row["password_hash"]
