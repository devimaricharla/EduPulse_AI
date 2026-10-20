
"""Tests for the EduPulse AI data-loading utilities."""

from io import StringIO

import pandas as pd
import pytest

from src.data.loader import (
    load_sample_student_data,
    load_student_csv,
)


def test_sample_loader_returns_valid_data():
    data = load_sample_student_data(num_students=10, seed=42)

    assert data.shape == (10, 9)
    assert data["student_id"].is_unique


def test_sample_loader_is_reproducible():
    first = load_sample_student_data(num_students=10, seed=42)
    second = load_sample_student_data(num_students=10, seed=42)

    pd.testing.assert_frame_equal(first, second)


def test_csv_loader_accepts_valid_csv():
    csv_content = StringIO(
        "student_id,student_name,department,course,semester,"
        "attendance_percentage,assignment_score,midterm_score,final_score\n"
        "STU00001,Alex Morgan,Computer Science,BCA,1,85,70,75,80\n"
    )

    data = load_student_csv(csv_content)

    assert data.shape == (1, 9)
    assert data.loc[0, "student_id"] == "STU00001"


def test_csv_loader_trims_column_name_whitespace():
    csv_content = StringIO(
        " student_id ,student_name,department,course,semester,"
        "attendance_percentage,assignment_score,midterm_score,final_score\n"
        "STU00001,Alex Morgan,Computer Science,BCA,1,85,70,75,80\n"
    )

    data = load_student_csv(csv_content)

    assert "student_id" in data.columns


def test_csv_loader_rejects_missing_required_columns():
    csv_content = StringIO(
        "student_id,student_name\nSTU00001,Alex Morgan\n"
    )

    with pytest.raises(ValueError, match="validation failed"):
        load_student_csv(csv_content)


def test_csv_loader_rejects_invalid_scores():
    csv_content = StringIO(
        "student_id,student_name,department,course,semester,"
        "attendance_percentage,assignment_score,midterm_score,final_score\n"
        "STU00001,Alex Morgan,Computer Science,BCA,1,85,70,75,150\n"
    )

    with pytest.raises(ValueError, match="validation failed"):
        load_student_csv(csv_content)




def test_csv_loader_does_not_modify_source_dataframe():
    csv_content = StringIO(
        "student_id,student_name,department,course,semester,"
        "attendance_percentage,assignment_score,midterm_score,final_score\n"
        "STU00001,Alex Morgan,Computer Science,BCA,1,85,70,75,80\n"
    )

    data = load_student_csv(csv_content)
    original = data.copy(deep=True)

    data.loc[0, "final_score"] = 100

    assert original.loc[0, "final_score"] == 80
    assert data.loc[0, "final_score"] == 100
