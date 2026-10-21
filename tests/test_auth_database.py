
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

def test_create_student_profile(isolated_database):
    user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    profile_id = database.create_student_profile(
        user_id=user_id,
        student_id="STU001",
        student_name="Test Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    with database.get_connection() as connection:
        profile = connection.execute(
            "SELECT * FROM student_profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()

    assert profile is not None
    assert profile["user_id"] == user_id
    assert profile["student_id"] == "STU001"
    assert profile["student_name"] == "Test Student"
    assert profile["department_id"] == department_id
    assert profile["course_id"] == course_id
    assert profile["semester"] == 3


def test_student_profile_rejects_non_student_account(isolated_database):
    user_id = database.create_user(
        "faculty01",
        "Password123!",
        "faculty",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    with pytest.raises(ValueError, match="active student account"):
        database.create_student_profile(
            user_id=user_id,
            student_id="STU001",
            student_name="Test Student",
            department_id=department_id,
            course_id=course_id,
            semester=3,
        )


def test_student_profile_rejects_course_from_another_department(
    isolated_database,
):
    user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_a = database.create_department("Computer Science")
    department_b = database.create_department("Mathematics")
    course_id = database.create_course(department_b, "Mathematics")

    with pytest.raises(ValueError, match="selected department"):
        database.create_student_profile(
            user_id=user_id,
            student_id="STU001",
            student_name="Test Student",
            department_id=department_a,
            course_id=course_id,
            semester=3,
        )


@pytest.mark.parametrize("semester", [0, 9, -1, 1.5, True])
def test_student_profile_rejects_invalid_semester(
    isolated_database,
    semester,
):
    user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    with pytest.raises(ValueError, match="Semester must be"):
        database.create_student_profile(
            user_id=user_id,
            student_id="STU001",
            student_name="Test Student",
            department_id=department_id,
            course_id=course_id,
            semester=semester,
        )

def test_link_parent_to_student(isolated_database):
    parent_id = database.create_user(
        "parent01",
        "Password123!",
        "parent",
    )
    student_user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    profile_id = database.create_student_profile(
        user_id=student_user_id,
        student_id="STU001",
        student_name="Test Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    database.link_parent_to_student(parent_id, profile_id)

    with database.get_connection() as connection:
        link = connection.execute(
            """
            SELECT parent_user_id, student_profile_id
            FROM parent_student_links
            WHERE parent_user_id = ? AND student_profile_id = ?
            """,
            (parent_id, profile_id),
        ).fetchone()

    assert link is not None
    assert link["parent_user_id"] == parent_id
    assert link["student_profile_id"] == profile_id


def test_parent_link_rejects_non_parent_account(isolated_database):
    student_user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    profile_id = database.create_student_profile(
        user_id=student_user_id,
        student_id="STU001",
        student_name="Test Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    with pytest.raises(ValueError, match="active parent account"):
        database.link_parent_to_student(student_user_id, profile_id)


def test_parent_link_rejects_missing_student_profile(isolated_database):
    parent_id = database.create_user(
        "parent01",
        "Password123!",
        "parent",
    )

    with pytest.raises(ValueError, match="Student profile was not found"):
        database.link_parent_to_student(parent_id, 999)

def test_assign_faculty_to_course(isolated_database):
    faculty_id = database.create_user(
        "faculty01",
        "Password123!",
        "faculty",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    database.assign_faculty_to_course(faculty_id, course_id)

    with database.get_connection() as connection:
        assignment = connection.execute(
            """
            SELECT faculty_user_id, course_id
            FROM faculty_course_assignments
            WHERE faculty_user_id = ? AND course_id = ?
            """,
            (faculty_id, course_id),
        ).fetchone()

    assert assignment is not None
    assert assignment["faculty_user_id"] == faculty_id
    assert assignment["course_id"] == course_id


def test_faculty_assignment_rejects_wrong_role(isolated_database):
    student_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    with pytest.raises(ValueError, match="active faculty account"):
        database.assign_faculty_to_course(student_id, course_id)


def test_assign_hod_to_department(isolated_database):
    hod_id = database.create_user(
        "hod01",
        "Password123!",
        "hod",
    )
    department_id = database.create_department("Computer Science")

    database.assign_hod_to_department(hod_id, department_id)

    with database.get_connection() as connection:
        assignment = connection.execute(
            """
            SELECT hod_user_id, department_id
            FROM hod_department_assignments
            WHERE hod_user_id = ? AND department_id = ?
            """,
            (hod_id, department_id),
        ).fetchone()

    assert assignment is not None
    assert assignment["hod_user_id"] == hod_id
    assert assignment["department_id"] == department_id


def test_hod_assignment_rejects_wrong_role(isolated_database):
    student_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")

    with pytest.raises(ValueError, match="active HOD account"):
        database.assign_hod_to_department(student_id, department_id)

def test_student_can_retrieve_own_profile(isolated_database):
    user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    database.create_student_profile(
        user_id=user_id,
        student_id="STU001",
        student_name="Test Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    profile = database.get_student_profile_for_user(user_id)

    assert profile is not None
    assert profile["student_id"] == "STU001"
    assert profile["student_name"] == "Test Student"
    assert profile["department_name"] == "Computer Science"
    assert profile["course_name"] == "Computer Science"
    assert profile["semester"] == 3
    assert "password_hash" not in profile


def test_student_profile_query_rejects_inactive_account(
    isolated_database,
):
    user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    database.create_student_profile(
        user_id=user_id,
        student_id="STU001",
        student_name="Test Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    database.set_user_active(user_id, False)

    assert database.get_student_profile_for_user(user_id) is None

def test_parent_can_retrieve_only_linked_students(isolated_database):
    parent_id = database.create_user(
        "parent01",
        "Password123!",
        "parent",
    )

    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    linked_user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    linked_profile_id = database.create_student_profile(
        user_id=linked_user_id,
        student_id="STU001",
        student_name="Linked Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    database.link_parent_to_student(parent_id, linked_profile_id)

    unlinked_user_id = database.create_user(
        "student02",
        "Password123!",
        "student",
    )
    database.create_student_profile(
        user_id=unlinked_user_id,
        student_id="STU002",
        student_name="Unlinked Student",
        department_id=department_id,
        course_id=course_id,
        semester=2,
    )

    students = database.get_linked_students_for_parent(parent_id)

    assert len(students) == 1
    assert students[0]["student_id"] == "STU001"
    assert students[0]["student_name"] == "Linked Student"


def test_parent_query_returns_no_students_when_parent_is_inactive(
    isolated_database,
):
    parent_id = database.create_user(
        "parent01",
        "Password123!",
        "parent",
    )

    database.set_user_active(parent_id, False)

    assert database.get_linked_students_for_parent(parent_id) == []


def test_parent_query_rejects_invalid_user_id(isolated_database):
    with pytest.raises(ValueError, match="positive integer"):
        database.get_linked_students_for_parent(0)

def test_faculty_can_retrieve_students_in_assigned_course(
    isolated_database,
):
    faculty_id = database.create_user(
        "faculty01",
        "Password123!",
        "faculty",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    database.assign_faculty_to_course(faculty_id, course_id)

    student_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    database.create_student_profile(
        user_id=student_id,
        student_id="STU001",
        student_name="Assigned Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    students = database.get_students_for_faculty(faculty_id)

    assert len(students) == 1
    assert students[0]["student_id"] == "STU001"


def test_faculty_cannot_retrieve_students_in_unassigned_course(
    isolated_database,
):
    faculty_id = database.create_user(
        "faculty01",
        "Password123!",
        "faculty",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )

    student_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    database.create_student_profile(
        user_id=student_id,
        student_id="STU001",
        student_name="Unassigned Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    assert database.get_students_for_faculty(faculty_id) == []


def test_faculty_query_returns_no_students_when_account_is_inactive(
    isolated_database,
):
    faculty_id = database.create_user(
        "faculty01",
        "Password123!",
        "faculty",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    database.assign_faculty_to_course(faculty_id, course_id)

    database.set_user_active(faculty_id, False)

    assert database.get_students_for_faculty(faculty_id) == []

def test_hod_can_retrieve_students_in_assigned_department(
    isolated_database,
):
    hod_id = database.create_user(
        "hod01",
        "Password123!",
        "hod",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    database.assign_hod_to_department(hod_id, department_id)

    student_user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    database.create_student_profile(
        user_id=student_user_id,
        student_id="STU001",
        student_name="Assigned Department Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    students = database.get_students_for_hod(hod_id)

    assert len(students) == 1
    assert students[0]["student_id"] == "STU001"


def test_hod_cannot_retrieve_students_from_unassigned_department(
    isolated_database,
):
    hod_id = database.create_user(
        "hod01",
        "Password123!",
        "hod",
    )
    assigned_department = database.create_department("Computer Science")
    database.assign_hod_to_department(hod_id, assigned_department)

    other_department = database.create_department("Mathematics")
    other_course = database.create_course(
        other_department,
        "Mathematics",
    )
    student_user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    database.create_student_profile(
        user_id=student_user_id,
        student_id="STU002",
        student_name="Other Department Student",
        department_id=other_department,
        course_id=other_course,
        semester=2,
    )

    assert database.get_students_for_hod(hod_id) == []


def test_hod_query_returns_no_students_when_account_is_inactive(
    isolated_database,
):
    hod_id = database.create_user(
        "hod01",
        "Password123!",
        "hod",
    )
    department_id = database.create_department("Computer Science")
    course_id = database.create_course(
        department_id,
        "Computer Science",
    )
    database.assign_hod_to_department(hod_id, department_id)

    student_user_id = database.create_user(
        "student01",
        "Password123!",
        "student",
    )
    database.create_student_profile(
        user_id=student_user_id,
        student_id="STU001",
        student_name="Test Student",
        department_id=department_id,
        course_id=course_id,
        semester=3,
    )

    database.set_user_active(hod_id, False)

    assert database.get_students_for_hod(hod_id) == []
