
"""Tests for EduPulse AI KPI calculations."""

import pandas as pd
import pytest

from src.analytics.kpis import (
    calculate_group_kpis,
    calculate_overall_kpis,
)
from src.data.sample_data import generate_student_data


def test_overall_kpis_return_expected_keys():
    data = generate_student_data(20)

    result = calculate_overall_kpis(data)

    assert result["total_students"] == 20
    assert result["average_academic_score"] >= 0
    assert result["average_academic_score"] <= 100
    assert result["average_attendance"] >= 0
    assert result["average_attendance"] <= 100
    assert 0 <= result["pass_rate"] <= 100
    assert 0 <= result["low_attendance_count"] <= 20


def test_overall_kpis_use_explicit_pass_and_attendance_rules():
    data = pd.DataFrame(
        {
            "student_id": ["A", "B"],
            "student_name": ["Student A", "Student B"],
            "department": ["Science", "Science"],
            "course": ["Course 1", "Course 1"],
            "semester": [1, 1],
            "attendance_percentage": [74, 75],
            "assignment_score": [50, 50],
            "midterm_score": [50, 50],
            "final_score": [39, 40],
        }
    )

    result = calculate_overall_kpis(data)

    assert result["total_students"] == 2
    assert result["low_attendance_count"] == 1
    assert result["passed_students"] == 1
    assert result["pass_rate"] == 50.0
    assert result["average_attendance"] == 74.5
    assert result["average_academic_score"] == 46.5


def test_group_kpis_calculate_department_metrics():
    data = pd.DataFrame(
        {
            "student_id": ["A", "B", "C"],
            "student_name": ["Student A", "Student B", "Student C"],
            "department": ["Science", "Science", "Business"],
            "course": ["Course 1", "Course 1", "Course 2"],
            "semester": [1, 1, 2],
            "attendance_percentage": [80, 60, 90],
            "assignment_score": [60, 70, 80],
            "midterm_score": [60, 70, 80],
            "final_score": [60, 30, 90],
        }
    )

    result = calculate_group_kpis(data, "department")
    science = result.loc[result["department"] == "Science"].iloc[0]

    assert science["total_students"] == 2
    assert science["average_attendance"] == 70.0
    assert science["low_attendance_count"] == 1
    assert science["pass_rate"] == 50.0


def test_unsupported_grouping_is_rejected():
    data = generate_student_data(5)

    with pytest.raises(ValueError, match="group_by"):
        calculate_group_kpis(data, "student_name")


def test_invalid_data_is_rejected():
    data = generate_student_data(5)
    data.loc[0, "final_score"] = 150

    with pytest.raises(ValueError, match="invalid student data"):
        calculate_overall_kpis(data)


def test_kpi_calculations_do_not_modify_input():
    data = generate_student_data(5)
    original = data.copy(deep=True)

    calculate_overall_kpis(data)

    pd.testing.assert_frame_equal(data, original)
