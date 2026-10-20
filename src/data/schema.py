
"""Canonical schema definitions for EduPulse AI."""

from typing import Final

STUDENT_REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "student_id",
    "student_name",
    "department",
    "course",
    "semester",
    "attendance_percentage",
    "assignment_score",
    "midterm_score",
    "final_score",
)

STUDENT_NUMERIC_COLUMNS: Final[tuple[str, ...]] = (
    "semester",
    "attendance_percentage",
    "assignment_score",
    "midterm_score",
    "final_score",
)

SCORE_COLUMNS: Final[tuple[str, ...]] = (
    "assignment_score",
    "midterm_score",
    "final_score",
)

SCORE_MIN: Final[float] = 0.0
SCORE_MAX: Final[float] = 100.0
ATTENDANCE_MIN: Final[float] = 0.0
ATTENDANCE_MAX: Final[float] = 100.0

PASS_MARK: Final[float] = 40.0
ATTENDANCE_WARNING_THRESHOLD: Final[float] = 75.0
