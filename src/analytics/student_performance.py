"""Student-specific academic performance retrieval."""

import pandas as pd

from src.data.schema import STUDENT_REQUIRED_COLUMNS
from src.data.validation import validate_student_data


def get_student_academic_record(
    student_data: pd.DataFrame,
    student_id: str,
) -> pd.DataFrame:
    """Return only academic records matching the requested student ID."""
    if not isinstance(student_id, str) or not student_id.strip():
        raise ValueError("A valid student ID is required.")

    missing_columns = [
        column
        for column in STUDENT_REQUIRED_COLUMNS
        if column not in student_data.columns
    ]
    if missing_columns:
        raise ValueError(
            "Student data is missing required columns: "
            + ", ".join(missing_columns)
        )

    errors = validate_student_data(student_data)
    if errors:
        raise ValueError(
            "Student data validation failed: " + "; ".join(errors)
        )

    return student_data.loc[
        student_data["student_id"] == student_id.strip()
    ].copy(deep=True)
