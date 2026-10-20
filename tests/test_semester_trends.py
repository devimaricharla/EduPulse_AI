
"""Tests for semester-wise performance trend analytics."""

import pandas as pd
import pytest

from src.analytics.semester_trends import calculate_semester_trends


def make_student_data() -> pd.DataFrame:
    """Create predictable records across three semesters."""
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002", "S003", "S004"],
            "student_name": ["Asha", "Ravi", "Mina", "Arun"],
            "department": ["Science", "Science", "Arts", "Arts"],
            "course": ["Physics", "Physics", "History", "History"],
            "semester": [2, 1, 3, 1],
            "attendance_percentage": [60, 90, 80, 70],
            "assignment_score": [60, 70, 80, 90],
            "midterm_score": [60, 70, 80, 90],
            "final_score": [35, 70, 80, 90],
        }
    )


def test_semester_trends_return_expected_columns():
    result = calculate_semester_trends(make_student_data())

    expected_columns = {
        "semester",
        "total_students",
        "average_academic_score",
        "average_attendance",
        "low_attendance_count",
        "pass_rate",
    }

    assert expected_columns.issubset(result.columns)


def test_semester_trends_calculate_correct_metrics():
    result = calculate_semester_trends(make_student_data())
    semesters = result.set_index("semester")

    # Semester 1: scores 70, 70, 70 and 90, 90, 90.
    assert semesters.loc[1, "total_students"] == 2
    assert semesters.loc[1, "average_academic_score"] == pytest.approx(80.0)
    assert semesters.loc[1, "average_attendance"] == 80.0
    assert semesters.loc[1, "low_attendance_count"] == 1
    assert semesters.loc[1, "pass_rate"] == 100.0

    # Semester 2: one student with scores 60, 60, and 35.
    assert semesters.loc[2, "total_students"] == 1
    assert semesters.loc[2, "average_academic_score"] == pytest.approx(
        51.67, abs=0.01
    )
    assert semesters.loc[2, "average_attendance"] == 60.0
    assert semesters.loc[2, "low_attendance_count"] == 1
    assert semesters.loc[2, "pass_rate"] == 0.0


def test_semesters_are_sorted_numerically():
    result = calculate_semester_trends(make_student_data())

    assert result["semester"].tolist() == [1, 2, 3]
    assert result["semester"].is_monotonic_increasing


def test_invalid_data_is_rejected():
    data = make_student_data().drop(columns=["attendance_percentage"])

    with pytest.raises(ValueError, match="invalid data"):
        calculate_semester_trends(data)


def test_empty_data_is_rejected():
    data = make_student_data().iloc[0:0]

    with pytest.raises(ValueError, match="invalid data"):
        calculate_semester_trends(data)


def test_input_data_is_not_modified():
    data = make_student_data()
    original = data.copy(deep=True)

    calculate_semester_trends(data)

    pd.testing.assert_frame_equal(data, original)
