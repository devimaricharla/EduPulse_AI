
"""Tests for department-level performance analytics."""

import pandas as pd
import pytest

from src.analytics.department_performance import (
    calculate_department_performance,
)


def make_student_data() -> pd.DataFrame:
    """Create predictable student records for testing."""
    return pd.DataFrame(
        {
            "student_id": ["S001", "S002", "S003", "S004"],
            "student_name": ["Asha", "Ravi", "Mina", "Arun"],
            "department": ["Science", "Science", "Arts", "Arts"],
            "course": ["Physics", "Physics", "History", "History"],
            "semester": [1, 1, 2, 2],
            "attendance_percentage": [60, 90, 80, 80],
            "assignment_score": [60, 70, 80, 80],
            "midterm_score": [60, 70, 80, 80],
            "final_score": [35, 70, 80, 80],
        }
    )


def test_department_performance_returns_expected_columns():
    result = calculate_department_performance(make_student_data())

    expected_columns = {
        "department",
        "total_students",
        "average_academic_score",
        "average_attendance",
        "low_attendance_count",
        "pass_rate",
    }

    assert expected_columns.issubset(result.columns)


def test_department_performance_calculates_correct_metrics():
    result = calculate_department_performance(make_student_data())
    departments = result.set_index("department")

    assert departments.loc["Science", "total_students"] == 2
    assert departments.loc["Science", "average_academic_score"] == pytest.approx(
    60.83
)
    assert departments.loc["Science", "average_attendance"] == 75.0
    assert departments.loc["Science", "low_attendance_count"] == 1
    assert departments.loc["Science", "pass_rate"] == 50.0

    assert departments.loc["Arts", "total_students"] == 2
    assert departments.loc["Arts", "average_academic_score"] == 80.0
    assert departments.loc["Arts", "average_attendance"] == 80.0
    assert departments.loc["Arts", "low_attendance_count"] == 0
    assert departments.loc["Arts", "pass_rate"] == 100.0


def test_departments_are_sorted_by_average_score_descending():
    result = calculate_department_performance(make_student_data())

    assert result["department"].tolist() == ["Arts", "Science"]
    assert result["average_academic_score"].is_monotonic_decreasing


def test_invalid_data_is_rejected():
    data = make_student_data().drop(columns=["attendance_percentage"])

    with pytest.raises(ValueError, match="invalid data"):
        calculate_department_performance(data)



def test_empty_data_is_rejected():
    data = make_student_data().iloc[0:0]

    with pytest.raises(ValueError, match="invalid data"):
        calculate_department_performance(data)



def test_input_data_is_not_modified():
    data = make_student_data()
    original = data.copy(deep=True)

    calculate_department_performance(data)

    pd.testing.assert_frame_equal(data, original)
