
"""Semester-wise performance trend analytics for EduPulse AI."""

import pandas as pd

from src.analytics.kpis import calculate_group_kpis
from src.data.validation import validate_student_data


def calculate_semester_trends(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate performance metrics for each semester.

    Returns one row per semester, ordered from lowest to highest semester
    number. Metrics use the existing project KPI definitions.
    """
    errors = validate_student_data(data)

    if errors:
        raise ValueError(
            "Cannot calculate semester trends from invalid data: "
            + "; ".join(errors)
        )

    summary = calculate_group_kpis(data, group_by="semester")

    if summary.empty:
        return summary

    return summary.sort_values(
        "semester",
        ascending=True,
    ).reset_index(drop=True)
