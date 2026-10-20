
"""Department-level academic performance analytics for EduPulse AI."""

import pandas as pd

from src.analytics.kpis import calculate_group_kpis
from src.data.validation import validate_student_data


def calculate_department_performance(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate academic performance, attendance, and pass rate by department.

    Returns one row per department, sorted by average academic score
    from highest to lowest.
    """
    errors = validate_student_data(data)

    if errors:
        raise ValueError(
            "Cannot calculate department performance from invalid data: "
            + "; ".join(errors)
        )

    summary = calculate_group_kpis(data, group_by="department")

    if summary.empty:
        return summary

    return summary.sort_values(
        "average_academic_score",
        ascending=False,
    ).reset_index(drop=True)
