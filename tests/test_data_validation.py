
"""Tests for student data validation."""

import pandas as pd
import pytest

from src.data.sample_data import generate_student_data
from src.data.validation import validate_student_data


def test_generated_data_is_valid():
    data = generate_student_data(20)
    assert validate_student_data(data) == []


def test_missing_required_column_is_reported():
    data = generate_student_data(5).drop(columns=["final_score"])
    errors = validate_student_data(data)
    assert any("final_score" in error for error in errors)


def test_duplicate_student_ids_are_reported():
    data = generate_student_data(5)
    data.loc[1, "student_id"] = data.loc[0, "student_id"]
    errors = validate_student_data(data)
    assert any("unique" in error for error in errors)


@pytest.mark.parametrize(
    "column,value",
    [
        ("attendance_percentage", 101),
        ("assignment_score", -1),
        ("midterm_score", 101),
        ("final_score", -5),
        ("semester", 9),
    ],
)
def test_out_of_range_values_are_reported(column, value):
    data = generate_student_data(5)
    data.loc[0, column] = value
    assert validate_student_data(data)


def test_empty_dataset_is_rejected():
    data = generate_student_data(5).iloc[0:0]
    errors = validate_student_data(data)
    assert any("at least one" in error for error in errors)


def test_input_data_is_not_modified():
    data = generate_student_data(5)
    original = data.copy(deep=True)

    validate_student_data(data)

    pd.testing.assert_frame_equal(data, original)

