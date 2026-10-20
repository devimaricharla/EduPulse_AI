
"""Reusable student-performance KPI calculations for EduPulse AI."""

import pandas as pd

from src.data.schema import (
    ATTENDANCE_WARNING_THRESHOLD,
    PASS_MARK,
    SCORE_COLUMNS,
    STUDENT_REQUIRED_COLUMNS,
)
from src.data.validation import validate_student_data


def _prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    """Validate student records and return a safe numeric working copy."""
    errors = validate_student_data(data)

    if errors:
        raise ValueError(
            "Cannot calculate KPIs from invalid student data: "
            + "; ".join(errors)
        )

    result = data.copy(deep=True)

    for column in SCORE_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="raise")

    result["attendance_percentage"] = pd.to_numeric(
        result["attendance_percentage"], errors="raise"
    )

    return result


def calculate_overall_kpis(data: pd.DataFrame) -> dict[str, int | float]:
    """Calculate high-level performance metrics for a student cohort.

    Passing rule: final_score >= PASS_MARK.
    Low-attendance rule: attendance_percentage <
    ATTENDANCE_WARNING_THRESHOLD.

    The input DataFrame is not modified.
    """
    prepared = _prepare_data(data)

    # Average the three assessment scores for each student first.
    student_average = prepared.loc[:, list(SCORE_COLUMNS)].mean(axis=1)

    total_students = int(prepared["student_id"].nunique())
    average_academic_score = float(student_average.mean())
    average_attendance = float(prepared["attendance_percentage"].mean())

    low_attendance_count = int(
        (
            prepared["attendance_percentage"]
            < ATTENDANCE_WARNING_THRESHOLD
        ).sum()
    )

    passed_count = int((prepared["final_score"] >= PASS_MARK).sum())
    pass_rate = float((passed_count / total_students) * 100)

    return {
        "total_students": total_students,
        "average_academic_score": round(average_academic_score, 2),
        "average_attendance": round(average_attendance, 2),
        "low_attendance_count": low_attendance_count,
        "passed_students": passed_count,
        "pass_rate": round(pass_rate, 2),
    }


def calculate_group_kpis(
    data: pd.DataFrame,
    group_by: str,
) -> pd.DataFrame:
    """Calculate student-performance KPIs for each group.

    Supported groups are department, course, and semester.
    """
    supported_groups = ("department", "course", "semester")

    if group_by not in supported_groups:
        raise ValueError(
            f"group_by must be one of: {', '.join(supported_groups)}."
        )

    prepared = _prepare_data(data)
    prepared["_student_average"] = prepared.loc[
        :, list(SCORE_COLUMNS)
    ].mean(axis=1)
    prepared["_passed"] = (
        prepared["final_score"] >= PASS_MARK
    ).astype(float) * 100
    prepared["_low_attendance"] = (
        prepared["attendance_percentage"]
        < ATTENDANCE_WARNING_THRESHOLD
    ).astype(int)

    grouped = prepared.groupby(group_by, observed=True).agg(
        total_students=("student_id", "nunique"),
        average_academic_score=("_student_average", "mean"),
        average_attendance=("attendance_percentage", "mean"),
        low_attendance_count=("_low_attendance", "sum"),
        pass_rate=("_passed", "mean"),
    )

    grouped["average_academic_score"] = grouped[
        "average_academic_score"
    ].round(2)
    grouped["average_attendance"] = grouped["average_attendance"].round(2)
    grouped["pass_rate"] = grouped["pass_rate"].round(2)

    return grouped.reset_index()
