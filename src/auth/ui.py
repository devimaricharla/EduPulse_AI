
"""Streamlit login and logout interface for EduPulse AI."""

import streamlit as st

from src.auth.database import authenticate_user


def render_login():
    """Display the login form and authenticate submitted credentials."""
    st.title("EduPulse AI")
    st.subheader("Sign in to your account")
    st.caption("Access your academic dashboard securely.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
        )

    if submitted:
        user = authenticate_user(username, password)

        if user is None:
            st.error("Invalid username or password, or account inactive.")
            return

        st.session_state["authenticated_user"] = user
        st.rerun()


def render_logout():
    """Sign out the current user."""
    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state.pop("authenticated_user", None)
        st.rerun()
