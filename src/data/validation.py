
"""Validation utilities for EduPulse AI student records."""

import pandas as pd

from src.data.schema import (
    ATTENDANCE_MAX,
    ATTENDANCE_MIN,
    SCORE_COLUMNS,
    SCORE_MAX,
    SCORE_MIN,
    STUDENT_NUMERIC_COLUMNS,
    STUDENT_REQUIRED_COLUMNS,
)


def validate_student_data(data: pd.DataFrame) -> list[str]:
    """Return validation errors found in a student dataset.

    An empty list means no validation errors were detected.
    The input DataFrame is never modified.
    """
    errors: list[str] = []

    if not isinstance(data, pd.DataFrame):
        return ["Input must be a pandas DataFrame."]

    missing_columns = [
        column
        for column in STUDENT_REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        return [f"Missing required columns: {', '.join(missing_columns)}"]

    if data.empty:
        return ["Dataset must contain at least one student record."]

    if data["student_id"].isna().any():
        errors.append("student_id must not contain missing values.")
    elif data["student_id"].astype(str).str.strip().eq("").any():
        errors.append("student_id must not contain blank values.")

    if data["student_id"].duplicated().any():
        errors.append("student_id values must be unique.")

    for column in ("student_name", "department", "course"):
        if data[column].isna().any():
            errors.append(f"{column} must not contain missing values.")
        elif data[column].astype(str).str.strip().eq("").any():
            errors.append(f"{column} must not contain blank values.")

    for column in STUDENT_NUMERIC_COLUMNS:
        values = pd.to_numeric(data[column], errors="coerce")

        if values.isna().any():
            errors.append(f"{column} must contain valid numeric values.")
            continue

        if column == "semester":
            if ((values < 1) | (values > 8) | (values % 1 != 0)).any():
                errors.append("semester must be an integer from 1 to 8.")

        elif column == "attendance_percentage":
            if (
                (values < ATTENDANCE_MIN)
                | (values > ATTENDANCE_MAX)
            ).any():
                errors.append(
                    "attendance_percentage must be between 0 and 100."
                )

        elif column in SCORE_COLUMNS:
            if ((values < SCORE_MIN) | (values > SCORE_MAX)).any():
                errors.append(f"{column} must be between 0 and 100.")

    return errors
