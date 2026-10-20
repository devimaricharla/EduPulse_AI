
"""Reusable Plotly charts for EduPulse AI."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data.schema import SCORE_COLUMNS


def show_department_comparison(data: pd.DataFrame) -> None:
    """Display average academic scores by department."""
    chart_data = data.copy()
    chart_data["average_academic_score"] = chart_data[
        list(SCORE_COLUMNS)
    ].mean(axis=1)

    summary = (
        chart_data.groupby("department", as_index=False)
        .agg(
            average_academic_score=("average_academic_score", "mean"),
            students=("student_id", "nunique"),
        )
        .sort_values("average_academic_score", ascending=False)
    )

    figure = px.bar(
        summary,
        x="department",
        y="average_academic_score",
        hover_data=["students"],
        title="Average Academic Score by Department",
        labels={
            "department": "Department",
            "average_academic_score": "Average score (out of 100)",
            "students": "Students",
        },
    )
    figure.update_yaxes(range=[0, 100])
    st.plotly_chart(figure, width="stretch")


def show_semester_performance(data: pd.DataFrame) -> None:
    """Display average academic scores across semesters."""
    chart_data = data.copy()
    chart_data["average_academic_score"] = chart_data[
        list(SCORE_COLUMNS)
    ].mean(axis=1)

    summary = (
        chart_data.groupby("semester", as_index=False)
        .agg(
            average_academic_score=("average_academic_score", "mean"),
            students=("student_id", "nunique"),
        )
        .sort_values("semester")
    )

    figure = px.line(
        summary,
        x="semester",
        y="average_academic_score",
        markers=True,
        hover_data=["students"],
        title="Academic Performance by Semester",
        labels={
            "semester": "Semester",
            "average_academic_score": "Average score (out of 100)",
            "students": "Students",
        },
    )
    figure.update_yaxes(range=[0, 100])
    st.plotly_chart(figure, width="stretch")

def show_attendance_vs_performance(data: pd.DataFrame) -> None:
    """Display the relationship between attendance and academic scores."""
    chart_data = data.copy()
    chart_data["average_academic_score"] = chart_data[
        list(SCORE_COLUMNS)
    ].mean(axis=1)

    figure = px.scatter(
        chart_data,
        x="attendance_percentage",
        y="average_academic_score",
        color="department",
        hover_data=["student_id", "semester"],
        title="Attendance vs. Academic Performance",
        labels={
            "attendance_percentage": "Attendance (%)",
            "average_academic_score": "Average academic score",
            "department": "Department",
            "semester": "Semester",
        },
    )
    figure.update_xaxes(range=[0, 100])
    figure.update_yaxes(range=[0, 100])
    st.plotly_chart(figure, width="stretch")