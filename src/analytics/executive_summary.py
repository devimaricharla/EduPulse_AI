
"""Executive summary analytics for EduPulse AI."""

import pandas as pd

from src.analytics.department_performance import (
    calculate_department_performance,
)
from src.analytics.department_risk import calculate_department_risk
from src.analytics.kpis import calculate_overall_kpis
from src.analytics.risk import identify_student_risks


def calculate_executive_summary(data: pd.DataFrame) -> dict:
    """Calculate institution-wide performance and support highlights.

    The supplied data should already reflect any desired dashboard filters.
    Department highlights are descriptive comparisons, not causal judgments.
    """
    kpis = calculate_overall_kpis(data)
    risk_data = identify_student_risks(data)
    department_performance = calculate_department_performance(data)
    department_risk = calculate_department_risk(data)

    flagged_students = int(
        (risk_data["risk_indicator_count"] > 0).sum()
    )
    multiple_indicator_students = int(
        (risk_data["risk_indicator_count"] >= 2).sum()
    )

    total_students = len(risk_data)

    flagged_student_rate = (
        flagged_students / total_students * 100
        if total_students
        else 0.0
    )

    if department_performance.empty:
        highest_performing_department = None
    else:
        highest_performing_department = department_performance.iloc[0][
            "department"
        ]

    if department_risk.empty:
        highest_support_rate_department = None
    else:
        highest_support_rate_department = department_risk.iloc[0][
            "department"
        ]

    return {
        "total_students": kpis["total_students"],
        "average_academic_score": kpis["average_academic_score"],
        "average_attendance": kpis["average_attendance"],
        "pass_rate": kpis["pass_rate"],
        "low_attendance_count": kpis["low_attendance_count"],
        "flagged_students": flagged_students,
        "flagged_student_rate": flagged_student_rate,
        "multiple_indicator_students": multiple_indicator_students,
        "highest_performing_department": highest_performing_department,
        "highest_support_rate_department": highest_support_rate_department,
    }
