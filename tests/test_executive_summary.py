
"""Tests for executive summary analytics."""

import pandas as pd
import pytest

from src.analytics.executive_summary import calculate_executive_summary


def make_student_data() -> pd.DataFrame:
    """Create predictable student records for executive summary tests."""
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


def test_executive_summary_contains_expected_metrics():
    result = calculate_executive_summary(make_student_data())

    expected_keys = {
        "total_students",
        "average_academic_score",
        "average_attendance",
        "pass_rate",
        "low_attendance_count",
        "flagged_students",
        "flagged_student_rate",
        "multiple_indicator_students",
        "highest_performing_department",
        "highest_support_rate_department",
    }

    assert expected_keys.issubset(result.keys())


def test_executive_summary_calculates_support_counts():
    result = calculate_executive_summary(make_student_data())

    assert result["total_students"] == 4
    assert result["flagged_students"] == 1
    assert result["flagged_student_rate"] == 25.0
    assert result["multiple_indicator_students"] == 1


def test_executive_summary_identifies_departments():
    result = calculate_executive_summary(make_student_data())

    assert result["highest_performing_department"] == "Arts"
    assert result["highest_support_rate_department"] == "Science"


def test_executive_summary_rejects_invalid_data():
    data = make_student_data().drop(columns=["attendance_percentage"])

    with pytest.raises(ValueError):
        calculate_executive_summary(data)


def test_executive_summary_does_not_modify_input():
    data = make_student_data()
    original = data.copy(deep=True)

    calculate_executive_summary(data)

    pd.testing.assert_frame_equal(data, original)
