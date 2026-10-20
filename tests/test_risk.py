
"""Tests for explainable student support indicators."""

import pandas as pd
import pytest

from src.analytics.risk import identify_student_risks
from src.data.sample_data import generate_student_data


def test_risk_analysis_returns_expected_columns():
    result = identify_student_risks(generate_student_data(10))

    expected_columns = {
        "average_academic_score",
        "low_attendance",
        "low_final_score",
        "low_average_score",
        "risk_indicator_count",
        "support_priority",
        "support_reasons",
    }

    assert expected_columns.issubset(result.columns)


def test_all_support_indicators_are_triggered():
    data = pd.DataFrame(
        {
            "student_id": ["STU00001"],
            "student_name": ["Alex Morgan"],
            "department": ["Computer Science"],
            "course": ["BCA"],
            "semester": [1],
            "attendance_percentage": [60],
            "assignment_score": [30],
            "midterm_score": [35],
            "final_score": [20],
        }
    )

    result = identify_student_risks(data)
    student = result.iloc[0]

    assert student["low_attendance"]
    assert student["low_final_score"]
    assert student["low_average_score"]
    assert student["risk_indicator_count"] == 3
    assert student["support_priority"] == "Multiple support indicators"
    assert "Attendance below 75%" in student["support_reasons"]
    assert "Final score below 40" in student["support_reasons"]


def test_no_support_indicators_are_triggered():
    data = pd.DataFrame(
        {
            "student_id": ["STU00002"],
            "student_name": ["Jordan Taylor"],
            "department": ["Business"],
            "course": ["BBA"],
            "semester": [2],
            "attendance_percentage": [90],
            "assignment_score": [80],
            "midterm_score": [75],
            "final_score": [85],
        }
    )

    student = identify_student_risks(data).iloc[0]

    assert student["risk_indicator_count"] == 0
    assert student["support_priority"] == "No rule-based flag"
    assert student["support_reasons"] == (
        "No configured support indicators triggered."
    )


def test_threshold_boundaries_are_not_flagged():
    data = pd.DataFrame(
        {
            "student_id": ["STU00003"],
            "student_name": ["Casey Parker"],
            "department": ["Electronics"],
            "course": ["BTech Electronics"],
            "semester": [3],
            "attendance_percentage": [75],
            "assignment_score": [60],
            "midterm_score": [60],
            "final_score": [40],
        }
    )

    student = identify_student_risks(data).iloc[0]

    assert not student["low_attendance"]
    assert not student["low_final_score"]
    assert not student["low_average_score"]
    assert student["risk_indicator_count"] == 0


def test_invalid_data_is_rejected():
    data = generate_student_data(5)
    data.loc[0, "final_score"] = 150

    with pytest.raises(ValueError, match="invalid data"):
        identify_student_risks(data)


def test_risk_analysis_does_not_modify_input():
    data = generate_student_data(5)
    original = data.copy(deep=True)

    identify_student_risks(data)

    pd.testing.assert_frame_equal(data, original)
