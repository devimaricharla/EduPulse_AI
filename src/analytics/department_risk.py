
"""Department-level student support analytics for EduPulse AI."""

import pandas as pd

from src.analytics.risk import identify_student_risks


def calculate_department_risk(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize rule-based student support indicators by department.

    Returns one row per department with student counts, flagged student
    counts, flag rates, and counts for each support indicator.
    """
    if data.empty:
        raise ValueError("Cannot calculate department risk for empty data.")

    risk_data = identify_student_risks(data)

    summary = (
        risk_data.groupby("department", as_index=False)
        .agg(
            total_students=("student_id", "count"),
            flagged_students=(
                "risk_indicator_count",
                lambda values: int((values > 0).sum()),
            ),
            low_attendance_count=("low_attendance", "sum"),
            low_final_score_count=("low_final_score", "sum"),
            low_average_score_count=("low_average_score", "sum"),
        )
    )

    summary["flagged_student_rate"] = (
        summary["flagged_students"] / summary["total_students"] * 100
    )

    summary["low_attendance_rate"] = (
        summary["low_attendance_count"] / summary["total_students"] * 100
    )

    summary["low_final_score_rate"] = (
        summary["low_final_score_count"] / summary["total_students"] * 100
    )

    summary["low_average_score_rate"] = (
        summary["low_average_score_count"] / summary["total_students"] * 100
    )

    return summary.sort_values(
        "flagged_student_rate",
        ascending=False,
    ).reset_index(drop=True)
