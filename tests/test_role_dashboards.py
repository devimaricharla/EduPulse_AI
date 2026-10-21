"""Tests for EduPulse AI role-specific dashboard routing."""

from contextlib import nullcontext

import pandas as pd
import pytest

from src.auth import database
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
    monkeypatch.setattr(
        st,
        "write",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        st,
        "info",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        database,
        "get_student_profile_for_user",
        lambda user_id: None,
    )

    render_role_dashboard(
        {"id": 1, "username": "testuser", "role": role}
    )

    assert displayed_titles == [expected_title]


def setup_student_dashboard_mocks(monkeypatch, profile):
    import streamlit as st

    displayed_metrics = []
    displayed_text = []
    displayed_info = []
    displayed_errors = []

    monkeypatch.setattr(
        database,
        "get_student_profile_for_user",
        lambda user_id: profile if user_id == 7 else None,
    )
    monkeypatch.setattr(
        st, "title", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        st, "subheader", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        st,
        "columns",
        lambda count: [nullcontext() for _ in range(count)],
    )
    monkeypatch.setattr(
        st,
        "metric",
        lambda label, value, *args, **kwargs: displayed_metrics.append(
            (label, value)
        ),
    )
    monkeypatch.setattr(
        st,
        "write",
        lambda *args, **kwargs: displayed_text.append(args),
    )
    monkeypatch.setattr(
        st,
        "info",
        lambda message: displayed_info.append(message),
    )
    monkeypatch.setattr(
        st,
        "error",
        lambda message: displayed_errors.append(message),
    )

    return displayed_metrics, displayed_text, displayed_info, displayed_errors


@pytest.fixture
def student_profile():
    return {
        "profile_id": 10,
        "student_id": "STU00001",
        "student_name": "Test Student",
        "department_id": 1,
        "department_name": "Computer Science",
        "course_id": 1,
        "course_name": "BSc Computer Science",
        "semester": 3,
    }


def test_student_dashboard_displays_own_profile(
    monkeypatch,
    student_profile,
):
    displayed_metrics, displayed_text, _, _ = (
        setup_student_dashboard_mocks(monkeypatch, student_profile)
    )

    render_role_dashboard(
        {"id": 7, "username": "student1", "role": "student"}
    )

    assert ("Student ID", "STU00001") in displayed_metrics
    assert ("Department", "Computer Science") in displayed_metrics
    assert ("Course", "BSc Computer Science") in displayed_metrics
    assert ("Semester", 3) in displayed_metrics

    assert any(
        "Test Student" in str(args)
        for args in displayed_text
    )


def test_student_dashboard_displays_matching_academic_record(
    monkeypatch,
    student_profile,
):
    displayed_metrics, _, _, _ = setup_student_dashboard_mocks(
        monkeypatch,
        student_profile,
    )

    student_data = pd.DataFrame(
        [
            {
                "student_id": "STU00001",
                "student_name": "Test Student",
                "department": "Computer Science",
                "course": "BSc Computer Science",
                "semester": 3,
                "attendance_percentage": 90.0,
                "assignment_score": 85.0,
                "midterm_score": 80.0,
                "final_score": 88.0,
            },
            {
                "student_id": "STU00002",
                "student_name": "Other Student",
                "department": "Business",
                "course": "BBA",
                "semester": 2,
                "attendance_percentage": 50.0,
                "assignment_score": 20.0,
                "midterm_score": 25.0,
                "final_score": 30.0,
            },
        ]
    )

    render_role_dashboard(
        {"id": 7, "username": "student1", "role": "student"},
        student_data=student_data,
    )

    assert ("Attendance", "90.00%") in displayed_metrics
    assert ("Assignment Score", "85.00 / 100") in displayed_metrics
    assert ("Midterm Score", "80.00 / 100") in displayed_metrics
    assert ("Final Score", "88.00 / 100") in displayed_metrics

    displayed_values = [value for _, value in displayed_metrics]
    assert "50.00%" not in displayed_values
    assert "20.00 / 100" not in displayed_values
    assert "25.00 / 100" not in displayed_values
    assert "30.00 / 100" not in displayed_values


def test_student_dashboard_handles_missing_profile(monkeypatch):
    _, _, displayed_info, _ = setup_student_dashboard_mocks(
        monkeypatch,
        None,
    )

    render_role_dashboard(
        {"id": 8, "username": "student2", "role": "student"}
    )

    assert len(displayed_info) == 1
    assert "No student profile is linked" in displayed_info[0]


def test_student_dashboard_handles_missing_academic_data(
    monkeypatch,
    student_profile,
):
    _, _, displayed_info, _ = setup_student_dashboard_mocks(
        monkeypatch,
        student_profile,
    )

    render_role_dashboard(
        {"id": 7, "username": "student1", "role": "student"},
        student_data=None,
    )

    assert any(
        "Academic performance data is not available" in message
        for message in displayed_info
    )


def test_student_dashboard_handles_unmatched_student_id(
    monkeypatch,
    student_profile,
):
    _, _, displayed_info, _ = setup_student_dashboard_mocks(
        monkeypatch,
        student_profile,
    )

    student_data = pd.DataFrame(
        [
            {
                "student_id": "STU00002",
                "student_name": "Other Student",
                "department": "Business",
                "course": "BBA",
                "semester": 2,
                "attendance_percentage": 50.0,
                "assignment_score": 20.0,
                "midterm_score": 25.0,
                "final_score": 30.0,
            }
        ]
    )

    render_role_dashboard(
        {"id": 7, "username": "student1", "role": "student"},
        student_data=student_data,
    )

    assert any(
        "No academic results were found" in message
        for message in displayed_info
    )
