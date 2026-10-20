
"""Generate reproducible synthetic student records for EduPulse AI."""

import numpy as np
import pandas as pd

from src.data.schema import STUDENT_REQUIRED_COLUMNS


DEPARTMENT_COURSES = {
    "Computer Science": ("BSc Computer Science", "BCA"),
    "Information Technology": ("BSc Information Technology", "BCA"),
    "Electronics": ("BTech Electronics", "Diploma Electronics"),
    "Business": ("BBA", "BCom"),
}

SYNTHETIC_NAMES = (
    "Alex Morgan",
    "Jordan Taylor",
    "Casey Parker",
    "Riley Bennett",
    "Avery Collins",
    "Jamie Brooks",
    "Morgan Reed",
    "Taylor Quinn",
    "Cameron Blake",
    "Drew Ellis",
)


def generate_student_data(
    num_students: int = 200,
    seed: int = 42,
) -> pd.DataFrame:
    """Return reproducible, synthetic academic records.

    Args:
        num_students: Number of records to generate; must be positive.
        seed: Random seed for reproducible output.

    Returns:
        DataFrame containing the canonical student columns.

    Raises:
        ValueError: If num_students is not positive.
    """
    if isinstance(num_students, bool) or not isinstance(num_students, int):
        raise ValueError("num_students must be a positive integer.")

    if num_students <= 0:
        raise ValueError("num_students must be greater than zero.")

    rng = np.random.default_rng(seed)
    departments = tuple(DEPARTMENT_COURSES)
    department_choices = rng.choice(departments, size=num_students)

    courses = [
        rng.choice(DEPARTMENT_COURSES[department])
        for department in department_choices
    ]

    attendance = np.round(rng.uniform(45, 100, num_students), 2)
    assignment = np.round(rng.normal(72, 15, num_students).clip(0, 100), 2)
    midterm = np.round(rng.normal(68, 17, num_students).clip(0, 100), 2)
    final = np.round(rng.normal(70, 16, num_students).clip(0, 100), 2)

    names = [
        SYNTHETIC_NAMES[index % len(SYNTHETIC_NAMES)]
        for index in range(num_students)
    ]

    data = pd.DataFrame(
        {
            "student_id": [
                f"STU{index:05d}" for index in range(1, num_students + 1)
            ],
            "student_name": names,
            "department": department_choices,
            "course": courses,
            "semester": rng.integers(1, 9, size=num_students),
            "attendance_percentage": attendance,
            "assignment_score": assignment,
            "midterm_score": midterm,
            "final_score": final,
        }
    )

    # Keep the generator aligned with the canonical schema.
    return data.loc[:, list(STUDENT_REQUIRED_COLUMNS)]
