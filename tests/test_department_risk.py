
"""Tests for department-level student support analytics."""

import pandas as pd
import pytest

from src.analytics.department_risk import calculate_department_risk


def make_student_data() -> pd.DataFrame:
    """Create predictable records for department risk tests."""
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


def test_department_summary_has_expected_columns():
    result = calculate_department_risk(make_student_data())

    expected_columns = {
        "department",
        "total_students",
        "flagged_students",
        "flagged_student_rate",
        "low_attendance_count",
        "low_final_score_count",
        "low_average_score_count",
        "low_attendance_rate",
        "low_final_score_rate",
        "low_average_score_rate",
    }

    assert expected_columns.issubset(result.columns)



def test_department_counts_and_rates_are_correct():
    result = calculate_department_risk(make_student_data())
    departments = result.set_index("department")

    # Science: one of two students is flagged.
    assert departments.loc["Science", "total_students"] == 2
    assert departments.loc["Science", "flagged_students"] == 1
    assert departments.loc["Science", "flagged_student_rate"] == 50.0

    # Arts: neither student triggers a support rule.
    assert departments.loc["Arts", "total_students"] == 2
    assert departments.loc["Arts", "flagged_students"] == 0
    assert departments.loc["Arts", "flagged_student_rate"] == 0.0




def test_indicator_counts_are_correct():
    result = calculate_department_risk(make_student_data())
    departments = result.set_index("department")

    assert departments.loc["Science", "low_attendance_count"] == 1
    assert departments.loc["Science", "low_final_score_count"] == 1
    assert departments.loc["Science", "low_average_score_count"] == 0

    assert departments.loc["Arts", "low_attendance_count"] == 0
    assert departments.loc["Arts", "low_final_score_count"] == 0
    assert departments.loc["Arts", "low_average_score_count"] == 0



def test_departments_are_sorted_by_flagged_rate_descending():
    result = calculate_department_risk(make_student_data())

    assert result["department"].tolist() == ["Science", "Arts"]
    assert result["flagged_student_rate"].is_monotonic_decreasing


def test_invalid_data_is_rejected():
    data = make_student_data().drop(columns=["attendance_percentage"])

    with pytest.raises(ValueError, match="invalid data"):
        calculate_department_risk(data)


def test_empty_data_is_rejected():
    data = make_student_data().iloc[0:0]

    with pytest.raises(ValueError, match="empty data"):
        calculate_department_risk(data)
