"""Role-specific dashboard entry points for EduPulse AI."""

import streamlit as st

from src.analytics.student_performance import get_student_academic_record
from src.auth import database


def render_student_dashboard(user, student_data=None):
    """Display the authenticated student's own profile and academic record."""
    st.title("Student Dashboard")
    st.write("View your academic results, attendance, and progress.")

    profile = database.get_student_profile_for_user(user["id"])

    if profile is None:
        st.info(
            "No student profile is linked to your account yet. "
            "Please contact your institution administrator."
        )
        return

    st.subheader("My Academic Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Student ID", profile["student_id"])
        st.metric("Department", profile["department_name"])
        st.metric("Course", profile["course_name"])

    with col2:
        st.metric("Semester", profile["semester"])
        st.write("**Student name:**", profile["student_name"])

    if student_data is None:
        st.info("Academic performance data is not available yet.")
        return

    try:
        academic_record = get_student_academic_record(
            student_data,
            profile["student_id"],
        )
    except ValueError as exc:
        st.error(f"Unable to retrieve academic results: {exc}")
        return

    if academic_record.empty:
        st.info(
            "No academic results were found for your student ID. "
            "Please contact your institution administrator."
        )
        return

    record = academic_record.iloc[0]

    st.subheader("My Academic Performance")

    metric_col1, metric_col2 = st.columns(2)

    with metric_col1:
        st.metric(
            "Attendance",
            f"{record['attendance_percentage']:.2f}%",
        )
        st.metric(
            "Assignment Score",
            f"{record['assignment_score']:.2f} / 100",
        )

    with metric_col2:
        st.metric(
            "Midterm Score",
            f"{record['midterm_score']:.2f} / 100",
        )
        st.metric(
            "Final Score",
            f"{record['final_score']:.2f} / 100",
        )

    st.caption(
        "These results are matched using your student ID. "
        "Support indicators and academic scores should be reviewed "
        "in accordance with your institution's policies."
    )


def render_role_dashboard(user, student_data=None):
    """Route an authenticated user to the appropriate role dashboard."""
    role = user["role"]

    if role == "student":
        render_student_dashboard(user, student_data)

    elif role == "faculty":
        st.title("Faculty Dashboard")
        st.write("Manage assigned courses, marks, and attendance.")

    elif role == "parent":
        st.title("Parent Dashboard")
        st.write("Review the academic progress of your linked child.")

    elif role == "hod":
        st.title("HOD Dashboard")
        st.write("Review performance and support needs within your department.")

    elif role == "admin":
        st.title("Admin Dashboard")
        st.write("Manage institutional analytics and authorized system settings.")

    else:
        st.error("Your account has an unsupported role.")
        st.session_state.pop("authenticated_user", None)
        st.stop()
