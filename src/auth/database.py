
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
    """Create the user and institutional relationship tables if needed."""
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL
                    REFERENCES departments(id),
                name TEXT NOT NULL COLLATE NOCASE,
                UNIQUE (department_id, name)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE
                    REFERENCES users(id),
                student_id TEXT NOT NULL UNIQUE,
                student_name TEXT NOT NULL,
                department_id INTEGER NOT NULL
                    REFERENCES departments(id),
                course_id INTEGER NOT NULL
                    REFERENCES courses(id),
                semester INTEGER NOT NULL
                    CHECK (semester BETWEEN 1 AND 8)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parent_student_links (
                parent_user_id INTEGER NOT NULL
                    REFERENCES users(id),
                student_profile_id INTEGER NOT NULL
                    REFERENCES student_profiles(id),
                PRIMARY KEY (parent_user_id, student_profile_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS faculty_course_assignments (
                faculty_user_id INTEGER NOT NULL
                    REFERENCES users(id),
                course_id INTEGER NOT NULL
                    REFERENCES courses(id),
                PRIMARY KEY (faculty_user_id, course_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hod_department_assignments (
                hod_user_id INTEGER NOT NULL
                    REFERENCES users(id),
                department_id INTEGER NOT NULL
                    REFERENCES departments(id),
                PRIMARY KEY (hod_user_id, department_id)
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

def create_department(name: str) -> int:
    """Create a department and return its ID."""
    if not isinstance(name, str):
        raise ValueError("Department name must be a string.")

    name = name.strip()
    if not name or len(name) > 100:
        raise ValueError("Department name must contain 1–100 characters.")

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO departments (name) VALUES (?)",
            (name,),
        )
        return cursor.lastrowid


def create_course(department_id: int, name: str) -> int:
    """Create a course within a department and return its ID."""
    if (
        isinstance(department_id, bool)
        or not isinstance(department_id, int)
        or department_id <= 0
    ):
        raise ValueError("A valid department ID is required.")

    if not isinstance(name, str):
        raise ValueError("Course name must be a string.")

    name = name.strip()
    if not name or len(name) > 100:
        raise ValueError("Course name must contain 1–100 characters.")

    initialize_database()

    with get_connection() as connection:
        department = connection.execute(
            "SELECT id FROM departments WHERE id = ?",
            (department_id,),
        ).fetchone()

        if department is None:
            raise ValueError("Department was not found.")

        cursor = connection.execute(
            """
            INSERT INTO courses (department_id, name)
            VALUES (?, ?)
            """,
            (department_id, name),
        )
        return cursor.lastrowid

def create_student_profile(
    user_id: int,
    student_id: str,
    student_name: str,
    department_id: int,
    course_id: int,
    semester: int,
) -> int:
    """Create a student profile for a valid student account."""
    for value, label in (
        (user_id, "User ID"),
        (department_id, "Department ID"),
        (course_id, "Course ID"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")

    if not isinstance(student_id, str):
        raise ValueError("Student ID must be a string.")
    student_id = student_id.strip()
    if not student_id or len(student_id) > 100:
        raise ValueError("Student ID must contain 1–100 characters.")

    if not isinstance(student_name, str):
        raise ValueError("Student name must be a string.")
    student_name = student_name.strip()
    if not student_name or len(student_name) > 200:
        raise ValueError("Student name must contain 1–200 characters.")

    if (
        isinstance(semester, bool)
        or not isinstance(semester, int)
        or not 1 <= semester <= 8
    ):
        raise ValueError("Semester must be an integer between 1 and 8.")

    initialize_database()

    with get_connection() as connection:
        user = connection.execute(
            "SELECT role FROM users WHERE id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()

        if user is None or user["role"] != "student":
            raise ValueError("An active student account is required.")

        course = connection.execute(
            """
            SELECT id
            FROM courses
            WHERE id = ? AND department_id = ?
            """,
            (course_id, department_id),
        ).fetchone()

        if course is None:
            raise ValueError(
                "The course must belong to the selected department."
            )

        cursor = connection.execute(
            """
            INSERT INTO student_profiles (
                user_id,
                student_id,
                student_name,
                department_id,
                course_id,
                semester
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                student_id,
                student_name,
                department_id,
                course_id,
                semester,
            ),
        )
        return cursor.lastrowid

def link_parent_to_student(
    parent_user_id: int,
    student_profile_id: int,
) -> None:
    """Link an active parent account to a student profile."""
    for value, label in (
        (parent_user_id, "Parent user ID"),
        (student_profile_id, "Student profile ID"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        parent = connection.execute(
            """
            SELECT role
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (parent_user_id,),
        ).fetchone()

        if parent is None or parent["role"] != "parent":
            raise ValueError("An active parent account is required.")

        student = connection.execute(
            "SELECT id FROM student_profiles WHERE id = ?",
            (student_profile_id,),
        ).fetchone()

        if student is None:
            raise ValueError("Student profile was not found.")

        connection.execute(
            """
            INSERT INTO parent_student_links (
                parent_user_id,
                student_profile_id
            )
            VALUES (?, ?)
            """,
            (parent_user_id, student_profile_id),
        )

def assign_faculty_to_course(
    faculty_user_id: int,
    course_id: int,
) -> None:
    """Assign an active faculty account to a course."""
    for value, label in (
        (faculty_user_id, "Faculty user ID"),
        (course_id, "Course ID"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        faculty = connection.execute(
            """
            SELECT role
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (faculty_user_id,),
        ).fetchone()

        if faculty is None or faculty["role"] != "faculty":
            raise ValueError("An active faculty account is required.")

        course = connection.execute(
            "SELECT id FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()

        if course is None:
            raise ValueError("Course was not found.")

        connection.execute(
            """
            INSERT INTO faculty_course_assignments (
                faculty_user_id,
                course_id
            )
            VALUES (?, ?)
            """,
            (faculty_user_id, course_id),
        )


def assign_hod_to_department(
    hod_user_id: int,
    department_id: int,
) -> None:
    """Assign an active HOD account to a department."""
    for value, label in (
        (hod_user_id, "HOD user ID"),
        (department_id, "Department ID"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        hod = connection.execute(
            """
            SELECT role
            FROM users
            WHERE id = ? AND is_active = 1
            """,
            (hod_user_id,),
        ).fetchone()

        if hod is None or hod["role"] != "hod":
            raise ValueError("An active HOD account is required.")

        department = connection.execute(
            "SELECT id FROM departments WHERE id = ?",
            (department_id,),
        ).fetchone()

        if department is None:
            raise ValueError("Department was not found.")

        connection.execute(
            """
            INSERT INTO hod_department_assignments (
                hod_user_id,
                department_id
            )
            VALUES (?, ?)
            """,
            (hod_user_id, department_id),
        )

def get_student_profile_for_user(user_id: int):
    """Return the profile for an active student account, or None."""
    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or user_id <= 0
    ):
        raise ValueError("User ID must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        profile = connection.execute(
            """
            SELECT
                sp.id AS profile_id,
                sp.student_id,
                sp.student_name,
                sp.department_id,
                d.name AS department_name,
                sp.course_id,
                c.name AS course_name,
                sp.semester
            FROM student_profiles AS sp
            JOIN users AS u ON u.id = sp.user_id
            JOIN departments AS d ON d.id = sp.department_id
            JOIN courses AS c ON c.id = sp.course_id
            WHERE sp.user_id = ?
              AND u.role = 'student'
              AND u.is_active = 1
            """,
            (user_id,),
        ).fetchone()

    return dict(profile) if profile is not None else None

def get_linked_students_for_parent(parent_user_id: int) -> list[dict]:
    """Return only student profiles linked to an active parent account."""
    if (
        isinstance(parent_user_id, bool)
        or not isinstance(parent_user_id, int)
        or parent_user_id <= 0
    ):
        raise ValueError("Parent user ID must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                sp.id AS profile_id,
                sp.student_id,
                sp.student_name,
                d.name AS department_name,
                c.name AS course_name,
                sp.semester
            FROM parent_student_links AS psl
            JOIN users AS u ON u.id = psl.parent_user_id
            JOIN student_profiles AS sp
                ON sp.id = psl.student_profile_id
            JOIN departments AS d ON d.id = sp.department_id
            JOIN courses AS c ON c.id = sp.course_id
            WHERE psl.parent_user_id = ?
              AND u.role = 'parent'
              AND u.is_active = 1
            ORDER BY sp.student_name COLLATE NOCASE
            """,
            (parent_user_id,),
        ).fetchall()

    return [dict(row) for row in rows]

def get_students_for_faculty(faculty_user_id: int) -> list[dict]:
    """Return students in courses assigned to an active faculty member."""
    if (
        isinstance(faculty_user_id, bool)
        or not isinstance(faculty_user_id, int)
        or faculty_user_id <= 0
    ):
        raise ValueError("Faculty user ID must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT
                sp.id AS profile_id,
                sp.student_id,
                sp.student_name,
                d.name AS department_name,
                c.name AS course_name,
                sp.semester
            FROM faculty_course_assignments AS fca
            JOIN users AS u ON u.id = fca.faculty_user_id
            JOIN courses AS c ON c.id = fca.course_id
            JOIN student_profiles AS sp ON sp.course_id = c.id
            JOIN departments AS d ON d.id = sp.department_id
            WHERE fca.faculty_user_id = ?
              AND u.role = 'faculty'
              AND u.is_active = 1
            ORDER BY sp.student_name COLLATE NOCASE
            """,
            (faculty_user_id,),
        ).fetchall()

    return [dict(row) for row in rows]

def get_students_for_hod(hod_user_id: int) -> list[dict]:
    """Return students in departments assigned to an active HOD."""
    if (
        isinstance(hod_user_id, bool)
        or not isinstance(hod_user_id, int)
        or hod_user_id <= 0
    ):
        raise ValueError("HOD user ID must be a positive integer.")

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                sp.id AS profile_id,
                sp.student_id,
                sp.student_name,
                d.name AS department_name,
                c.name AS course_name,
                sp.semester
            FROM hod_department_assignments AS hda
            JOIN users AS u ON u.id = hda.hod_user_id
            JOIN departments AS d ON d.id = hda.department_id
            JOIN student_profiles AS sp
                ON sp.department_id = d.id
            JOIN courses AS c ON c.id = sp.course_id
            WHERE hda.hod_user_id = ?
              AND u.role = 'hod'
              AND u.is_active = 1
            ORDER BY sp.student_name COLLATE NOCASE
            """,
            (hod_user_id,),
        ).fetchall()

    return [dict(row) for row in rows]
