
"""Explainable, rule-based student support indicators for EduPulse AI."""

import pandas as pd

from src.data.schema import (
    ATTENDANCE_WARNING_THRESHOLD,
    PASS_MARK,
    SCORE_COLUMNS,
)
from src.data.validation import validate_student_data


LOW_AVERAGE_SCORE_THRESHOLD = 50.0


def identify_student_risks(data: pd.DataFrame) -> pd.DataFrame:
    """Add transparent support indicators to validated student records.

    Rules:
    - Low attendance: attendance below the configured warning threshold.
    - Low final score: final score below the configured pass mark.
    - Low average score: mean of the three assessment scores below 50.

    This function flags possible support needs; it does not predict future
    outcomes or make decisions about students.
    """
    errors = validate_student_data(data)

    if errors:
        raise ValueError(
            "Cannot identify student risks from invalid data: "
            + "; ".join(errors)
        )

    result = data.copy(deep=True)

    result["average_academic_score"] = result[
        list(SCORE_COLUMNS)
    ].mean(axis=1)

    result["low_attendance"] = (
        result["attendance_percentage"] < ATTENDANCE_WARNING_THRESHOLD
    )

    result["low_final_score"] = result["final_score"] < PASS_MARK

    result["low_average_score"] = (
        result["average_academic_score"] < LOW_AVERAGE_SCORE_THRESHOLD
    )

    risk_columns = [
        "low_attendance",
        "low_final_score",
        "low_average_score",
    ]

    result["risk_indicator_count"] = result[risk_columns].sum(axis=1)

    result["support_priority"] = result["risk_indicator_count"].map(
        {
            0: "No rule-based flag",
            1: "Consider support",
            2: "Support recommended",
            3: "Multiple support indicators",
        }
    )

    result["support_reasons"] = result.apply(
        _build_support_reasons,
        axis=1,
    )

    return result


def _build_support_reasons(student: pd.Series) -> str:
    """Explain which rules were triggered for one student."""
    reasons: list[str] = []

    if student["low_attendance"]:
        reasons.append(
            f"Attendance below {ATTENDANCE_WARNING_THRESHOLD:.0f}%"
        )

    if student["low_final_score"]:
        reasons.append(f"Final score below {PASS_MARK:.0f}")

    if student["low_average_score"]:
        reasons.append(
            "Average academic score below "
            f"{LOW_AVERAGE_SCORE_THRESHOLD:.0f}"
        )

    if not reasons:
        return "No configured support indicators triggered."

    return "; ".join(reasons)
