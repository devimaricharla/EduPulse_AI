
"""Data-loading utilities for EduPulse AI."""

from pathlib import Path
from typing import IO

import pandas as pd

from src.data.sample_data import generate_student_data
from src.data.validation import validate_student_data


def load_student_csv(
    source: str | Path | IO[str],
) -> pd.DataFrame:
    """Load and validate student records from a CSV source.

    Args:
        source: A file path or a text file-like object containing CSV data.

    Returns:
        A validated DataFrame with the canonical student records.

    Raises:
        ValueError: If the CSV cannot be read or its data is invalid.
    """
    try:
        data = pd.read_csv(source)
    except (OSError, UnicodeError, pd.errors.ParserError, ValueError) as exc:
        raise ValueError(f"Could not read student CSV: {exc}") from exc

    # Ignore accidental whitespace around column names.
    data.columns = data.columns.astype(str).str.strip()

    errors = validate_student_data(data)
    if errors:
        raise ValueError(
            "Student CSV validation failed: " + "; ".join(errors)
        )

    # Return a copy so callers can work without modifying the loaded object.
    return data.copy(deep=True)


def load_sample_student_data(
    num_students: int = 200,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate and validate synthetic student records."""
    data = generate_student_data(num_students=num_students, seed=seed)

    errors = validate_student_data(data)
    if errors:
        raise ValueError(
            "Generated sample data failed validation: "
            + "; ".join(errors)
        )

    return data
