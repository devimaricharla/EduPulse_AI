
"""SQLite account management and authentication for EduPulse AI."""

import sqlite3
from pathlib import Path

import bcrypt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "edupulse_users.db"

ALLOWED_ROLES = {
    "student",
    "faculty",
    "parent",
    "hod",
    "admin",
}


def get_connection():
    """Open a connection to the EduPulse AI account database."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the users table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('student', 'faculty', 'parent', 'hod', 'admin')
                ),
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def hash_password(password: str) -> bytes:
    """Return a secure bcrypt hash for a password."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    password_bytes = password.encode("utf-8")

    # bcrypt accepts at most 72 password bytes.
    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes.")

    return bcrypt.hashpw(password_bytes, bcrypt.gensalt())


def create_user(
    username: str,
    password: str,
    role: str,
) -> int:
    """Create an account and return its user ID.

    Account creation is an administrative operation. Do not expose this
    function directly through an unrestricted public registration form.
    """
    initialize_database()

    if not isinstance(username, str):
        raise ValueError("Username must be a string.")

    username = username.strip()
    if not username or len(username) > 100:
        raise ValueError("Username must contain 1–100 characters.")

    if not isinstance(role, str) or role not in ALLOWED_ROLES:
        raise ValueError("Invalid user role.")

    password_hash = hash_password(password)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (username, password_hash, role),
        )
        return cursor.lastrowid


def authenticate_user(username: str, password: str):
    """Return safe account details for valid credentials, or None."""
    if (
        not isinstance(username, str)
        or not isinstance(password, str)
        or not username.strip()
        or not password
    ):
        return None

    # bcrypt only verifies up to 72 password bytes.
    if len(password.encode("utf-8")) > 72:
        return None

    initialize_database()

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, username, password_hash, role, is_active
            FROM users
            WHERE username = ? COLLATE NOCASE
            """,
            (username.strip(),),
        ).fetchone()

    if user is None or user["is_active"] != 1:
        return None

    try:
        valid_password = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"],
        )
    except (ValueError, TypeError):
        return None

    if not valid_password:
        return None

    # Never return the password hash to the calling application.
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }


def set_user_active(user_id: int, is_active: bool) -> None:
    """Activate or deactivate an account."""
    if not isinstance(is_active, bool):
        raise ValueError("is_active must be True or False.")

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (int(is_active), user_id),
        )

        if cursor.rowcount == 0:
            raise ValueError("User account was not found.")
