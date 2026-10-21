"""Tests for student-specific academic performance retrieval."""

import pandas as pd
import pytest

from src.analytics.student_performance import get_student_academic_record
from src.data.loader import load_sample_student_data


def test_returns_only_requested_student_record():
    student_data = load_sample_student_data(num_students=10)
    target_id = student_data.iloc[0]["student_id"]

    result = get_student_academic_record(student_data, target_id)

    assert len(result) == 1
    assert result.iloc[0]["student_id"] == target_id


def test_unknown_student_returns_empty_dataframe():
    student_data = load_sample_student_data(num_students=10)

    result = get_student_academic_record(student_data, "UNKNOWN001")

    assert result.empty
    assert list(result.columns) == list(student_data.columns)


@pytest.mark.parametrize("student_id", ["", "   ", None, 123])
def test_rejects_invalid_student_id(student_id):
    student_data = load_sample_student_data(num_students=10)

    with pytest.raises(ValueError, match="valid student ID"):
        get_student_academic_record(student_data, student_id)


def test_rejects_missing_required_columns():
    student_data = pd.DataFrame({"student_id": ["STU00001"]})

    with pytest.raises(ValueError, match="missing required columns"):
        get_student_academic_record(student_data, "STU00001")


def test_does_not_modify_original_data():
    student_data = load_sample_student_data(num_students=10)
    original = student_data.copy(deep=True)

    get_student_academic_record(
        student_data,
        student_data.iloc[0]["student_id"],
    )

    pd.testing.assert_frame_equal(student_data, original)


def test_rejects_invalid_academic_data():
    student_data = load_sample_student_data(num_students=10)
    student_data.loc[0, "attendance_percentage"] = 150

    with pytest.raises(ValueError, match="validation failed"):
        get_student_academic_record(
            student_data,
            student_data.iloc[0]["student_id"],
        )
