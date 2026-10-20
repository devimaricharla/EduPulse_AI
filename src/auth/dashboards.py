
"""Role-specific dashboard entry points for EduPulse AI."""

import streamlit as st


def render_role_dashboard(user):
    """Route an authenticated user to the appropriate role dashboard."""
    role = user["role"]

    if role == "student":
        st.title("Student Dashboard")
        st.write("View your academic results, attendance, and progress.")

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
