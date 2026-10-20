
"""Tests for EduPulse AI role-specific dashboard routing."""

import pytest

from src.auth.dashboards import render_role_dashboard


@pytest.mark.parametrize(
    ("role", "expected_title"),
    [
        ("student", "Student Dashboard"),
        ("faculty", "Faculty Dashboard"),
        ("parent", "Parent Dashboard"),
        ("hod", "HOD Dashboard"),
        ("admin", "Admin Dashboard"),
    ],
)
def test_each_role_has_its_own_dashboard(
    monkeypatch,
    role,
    expected_title,
):
    import streamlit as st

    displayed_titles = []

    monkeypatch.setattr(
        st,
        "title",
        lambda title: displayed_titles.append(title),
    )
    monkeypatch.setattr(st, "write", lambda *args, **kwargs: None)

    render_role_dashboard(
        {"id": 1, "username": "testuser", "role": role}
    )

    assert displayed_titles == [expected_title]
